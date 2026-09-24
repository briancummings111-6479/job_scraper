import os
import json
import re
from datetime import datetime, timedelta
import pandas as pd
from google.oauth2.service_account import Credentials

try:
    from scrapper import is_rejected_job, is_expired_job_content, clean_job_title, determine_industry
except ImportError:
    def clean_job_title(title: str) -> str:
        if not title: return ""
        return re.sub(r'[\r\n\s]*-?\s*job post.*$', '', str(title), flags=re.IGNORECASE).strip()
    def is_expired_job_content(text: str) -> bool:
        return False
    def is_rejected_job(title: str, company: str = "", description: str = "") -> tuple:
        return False, ""
    def determine_industry(job_title: str, company: str = "", description: str = "") -> str:
        return "Other"

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import gspread
except ImportError as exc:
    raise RuntimeError(
        "The 'gspread' package is required. Install it with: pip install gspread"
    ) from exc

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_gspread_client():
    if os.path.exists("serviceAccountKey.json"):
        creds = Credentials.from_service_account_file("serviceAccountKey.json", scopes=SCOPES)
    else:
        private_key = os.environ.get("FIREBASE_PRIVATE_KEY", "")
        if private_key:
            private_key = private_key.replace("\\n", "\n")

        info = {
            "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
            "private_key": private_key,
            "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)

def update_google_sheet(jobs_data: list, sheet_id: str = "1uGL7w8fpb5P0D-kNIPces9nOK4Ctt6Bfg5jlA6J-_CU"):
    if not jobs_data:
        print("[SHEETS] No job data provided to sync.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    cutoff_date = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
    
    rows = []
    for j in jobs_data:
        clean_title = clean_job_title(j.get("job_title", ""))
        if not clean_title or clean_title == "N/A":
            continue

        raw_desc = str(j.get("description") or "")
        if is_expired_job_content(raw_desc) or is_expired_job_content(clean_title):
            continue

        is_rej, _ = is_rejected_job(clean_title, j.get("company", ""), raw_desc, pay=j.get("pay", ""))
        if is_rej:
            continue

        raw_date = j.get("date_posted")
        posted_date = str(raw_date).strip() if raw_date and str(raw_date).strip() not in ["N/A", "None", ""] else today_str
        
        if posted_date < cutoff_date:
            continue

        sector = j.get("industry")
        if not sector or sector == "Other":
            sector = determine_industry(clean_title, j.get("company", ""), raw_desc)

        rows.append({
            "Date Posted": posted_date,
            "Job Title": clean_title,
            "Company": j.get("company", ""),
            "Sector": sector,
            "Location": j.get("location", "Redding, CA"),
            "Pay Rate": j.get("pay") or "N/A",
            "Job Type": j.get("job_type_extracted") or "N/A",
            "Schedule / Shift": j.get("shift_schedule") or "N/A",
            "Experience / Requirements": j.get("experience") or "N/A",
            "Job Description": raw_desc if raw_desc else "N/A",
            "Application Link": j.get("job_url") or "",
            "Source": j.get("source") or "Direct"
        })

    if not rows:
        print("[SHEETS] No active listings met the 15-day date criteria.")
        return

    df = pd.DataFrame(rows)
    df.fillna("N/A", inplace=True)
    df.sort_values(by="Date Posted", ascending=False, inplace=True)

    client = get_gspread_client()
    spreadsheet = client.open_by_key(sheet_id)
    
    tab_name = "Automated_Posts"
    try:
        worksheet = spreadsheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"[SHEETS] Tab '{tab_name}' not found. Creating it...")
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=20)
    except Exception as e:
        print(f"[WARN] Error finding '{tab_name}': {e}. Defaulting to first sheet.")
        worksheet = spreadsheet.sheet1

    worksheet.clear()
    worksheet.update(values=[df.columns.values.tolist()] + df.values.tolist(), range_name="A1")
    print(f"[SHEETS] Synchronized {len(df)} active listings to tab '{worksheet.title}'.")