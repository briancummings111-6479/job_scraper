import os
import json
import re
from datetime import datetime, timedelta
import pandas as pd
from google.oauth2.service_account import Credentials

try:
    from scrapper import is_rejected_job, is_expired_job_content, clean_job_title, determine_industry, extract_key_requirements, generate_key_description, clean_location_str, is_shasta_county_location, resolve_business_address, standardize_driver_license_requirement, evaluate_hs_ok, is_teen_friendly
except ImportError:
    def evaluate_hs_ok(title: str = "", company: str = "", text: str = "", requirements: str = "", job_type: str = "", shift: str = "", job_dict: dict = None, gemini_teen_friendly: bool = None) -> str:
        return ""
    def is_teen_friendly(title: str = "", company: str = "", text: str = "", requirements: str = "", job_dict: dict = None, gemini_teen_friendly: bool = None) -> bool:
        return bool(gemini_teen_friendly)
    def standardize_driver_license_requirement(exp_str: str, text_context: str = "", gemini_license: str = None) -> str:
        return exp_str
    def clean_job_title(title: str) -> str:
        if not title: return ""
        return re.sub(r'[\r\n\s]*-?\s*job post.*$', '', str(title), flags=re.IGNORECASE).strip()
    def is_expired_job_content(text: str) -> bool:
        return False
    def is_rejected_job(title: str, company: str = "", description: str = "", pay: str = "", location: str = "") -> tuple:
        return False, ""
    def clean_location_str(loc: str) -> str:
        return str(loc or "Redding, CA").strip()
    def resolve_business_address(company: str = "", location: str = "", description: str = "", gemini_address: str = None) -> str:
        return str(location or "Redding, CA").strip()
    def is_shasta_county_location(loc_str: str, text_context: str = "") -> tuple:
        return True, str(loc_str or "Redding, CA").strip()
    def determine_industry(job_title: str, company: str = "", description: str = "") -> str:
        return "Other"
    def extract_key_requirements(text: str = "", existing_exp: str = "", job_dict: dict = None) -> str:
        return existing_exp if existing_exp and existing_exp != "N/A" else "No experience required (On-the-job training provided)"
    def generate_key_description(title: str, company: str = "", location: str = "Redding, CA", sector: str = "Other", job_type: str = "N/A", schedule: str = "N/A", pay: str = "N/A", requirements: str = "") -> str:
        return f"{title} position at {company} in {location}."

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

        raw_loc = j.get("location", "Redding, CA")
        cleaned_loc = resolve_business_address(
            company=j.get("company", ""),
            location=raw_loc,
            description=j.get("description", "")
        )
        is_shasta, loc_reason = is_shasta_county_location(cleaned_loc)
        if not is_shasta:
            continue

        raw_desc = str(j.get("description") or "")
        if is_expired_job_content(raw_desc) or is_expired_job_content(clean_title):
            continue

        is_rej, _ = is_rejected_job(clean_title, j.get("company", ""), raw_desc, pay=j.get("pay", ""), location=cleaned_loc)
        if is_rej:
            continue

        raw_date = j.get("date_posted")
        posted_date = str(raw_date).strip() if raw_date and str(raw_date).strip() not in ["N/A", "None", ""] else today_str
        
        if posted_date < cutoff_date:
            continue

        sector = j.get("industry")
        if not sector or sector in ["Other", "N/A", ""]:
            sector = determine_industry(clean_title, j.get("company", ""), raw_desc)

        exp_req = j.get("experience") or j.get("requirements")
        exp_req = extract_key_requirements(
            text=raw_desc,
            existing_exp=exp_req or "",
            job_dict=j
        )

        exp_req = standardize_driver_license_requirement(
            exp_req,
            text_context=f"{clean_title} {j.get('company', '')} {raw_desc}",
            gemini_license=j.get("driverLicenseType") or j.get("driver_license_type")
        )

        final_desc = raw_desc
        if not final_desc or str(final_desc).strip() in ["N/A", "None", ""]:
            final_desc = generate_key_description(
                title=clean_title,
                company=j.get("company", ""),
                location=cleaned_loc,
                sector=sector,
                job_type=j.get("job_type_extracted") or "Unstated",
                schedule=j.get("shift_schedule") or "Unstated",
                pay=j.get("pay") or "Unstated",
                requirements=exp_req
            )

        raw_pay = j.get("pay")
        clean_pay = str(raw_pay).strip() if raw_pay and str(raw_pay).strip().lower() not in ["n/a", "none", "", "unstated", "nan"] else ""

        hs_ok_val = evaluate_hs_ok(
            title=clean_title,
            company=j.get("company", ""),
            text=raw_desc,
            requirements=exp_req,
            job_type=j.get("job_type_extracted") or "",
            shift=j.get("shift_schedule") or "",
            job_dict=j,
            gemini_teen_friendly=j.get("isTeenFriendly") or j.get("is_teen_friendly") or j.get("teen_friendly")
        )

        rows.append({
            "Source": j.get("source") or "Direct",
            "Job Title": clean_title,
            "Company": j.get("company", ""),
            "Location": cleaned_loc,
            "Pay Rate": clean_pay,
            "Full / Part Time": j.get("job_type_extracted") if j.get("job_type_extracted") and str(j.get("job_type_extracted")).strip() not in ["N/A", "None", "", "nan"] else "Unstated",
            "Schedule / Shift": j.get("shift_schedule") if j.get("shift_schedule") and str(j.get("shift_schedule")).strip() not in ["N/A", "None", "", "nan"] else "Unstated",
            "Experience / Requirements": exp_req,
            "H.S. OK": hs_ok_val,
            "Job Description Summary": final_desc,
            "Date Posted": posted_date,
            "Job Posting": j.get("job_url") or "",
            "Industry Sector": sector,
            "Last Updated": today_str
        })

    if not rows:
        print("[SHEETS] No active listings met the 15-day date criteria.")
        return

    df = pd.DataFrame(rows)
    df.fillna("", inplace=True)
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

    # Clear legacy boolean checkbox validation on H.S. OK column to allow emoji and blank values
    try:
        col_names = df.columns.values.tolist()
        for target_col in ["H.S. OK", "Teen Friendly"]:
            if target_col in col_names and len(df) > 0:
                c_idx = col_names.index(target_col)
                body = {
                    "requests": [
                        {
                            "setDataValidation": {
                                "range": {
                                    "sheetId": worksheet.id,
                                    "startRowIndex": 1,
                                    "endRowIndex": len(df) + 1,
                                    "startColumnIndex": c_idx,
                                    "endColumnIndex": c_idx + 1
                                },
                                "rule": None
                            }
                        }
                    ]
                }
                spreadsheet.batch_update(body)
    except Exception as cb_err:
        pass

    print(f"[SHEETS] Synchronized {len(df)} active listings to tab '{worksheet.title}'.")

def sync_redding_area_employers(sheet_id: str = "1uGL7w8fpb5P0D-kNIPces9nOK4Ctt6Bfg5jlA6J-_CU", output_json: str = None) -> list:
    """
    Reads the 'Redding Area Employers' tab from the Google Sheet and updates the local
    cache file redding_area_employers.json.
    """
    if not output_json:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_json = os.path.join(base_dir, "redding_area_employers.json")

    client = get_gspread_client()
    spreadsheet = client.open_by_key(sheet_id)
    try:
        ws = spreadsheet.worksheet("Redding Area Employers")
    except Exception as e:
        print(f"[WARN] Worksheet 'Redding Area Employers' not found: {e}")
        return []

    all_rows = ws.get_all_values()
    if len(all_rows) < 3:
        print("[WARN] Insufficient data in 'Redding Area Employers' tab.")
        return []

    employers_data = []
    for r in all_rows[2:]:
        comp = r[0].strip() if len(r) > 0 else ""
        if not comp:
            continue
        addr = r[1].strip() if len(r) > 1 else ""
        min_age = r[2].strip() if len(r) > 2 else ""
        hs_ged = r[4].strip() if len(r) > 4 else ""
        dl = r[5].strip() if len(r) > 5 else ""
        clean_rec = r[6].strip() if len(r) > 6 else ""
        work_exp = r[7].strip() if len(r) > 7 else ""
        wage = r[8].strip() if len(r) > 8 else ""
        career_url = r[9].strip() if len(r) > 9 else ""
        indeed_url = r[10].strip() if len(r) > 10 else ""
        notes = r[11].strip() if len(r) > 11 else ""

        employers_data.append({
            "company": comp,
            "address": addr,
            "min_age": min_age,
            "hs_ged_required": hs_ged,
            "drivers_license_required": dl,
            "clean_record_required": clean_rec,
            "work_experience_required": work_exp,
            "wage": wage,
            "career_url": career_url,
            "indeed_url": indeed_url,
            "notes": notes
        })

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(employers_data, f, indent=2)

    print(f"[SHEETS] Cached {len(employers_data)} employers from 'Redding Area Employers' to {output_json}")
    return employers_data