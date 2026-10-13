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

    try:
        from employer_db import resolve_job_with_employer_profile
    except ImportError:
        resolve_job_with_employer_profile = None

    rows = []
    for j in jobs_data:
        clean_title = clean_job_title(j.get("job_title", ""))
        if not clean_title or clean_title == "N/A":
            continue

        j_copy = dict(j)
        j_copy["job_title"] = clean_title
        resolved = resolve_job_with_employer_profile(j_copy) if resolve_job_with_employer_profile else {}

        raw_loc = resolved.get("location_full") or j.get("location", "Redding, CA")
        cleaned_loc = clean_location_str(raw_loc) if resolved.get("location_full") else resolve_business_address(
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

        company_name = resolved.get("company_brand") or j.get("company", "")
        clean_pay = resolved.get("pay_rate") if resolved else ""
        if not clean_pay:
            raw_pay = j.get("pay")
            clean_pay = str(raw_pay).strip() if raw_pay and str(raw_pay).strip().lower() not in ["n/a", "none", "", "unstated", "nan"] else ""

        is_rej, _ = is_rejected_job(clean_title, company_name, raw_desc, pay=clean_pay, location=cleaned_loc)
        if is_rej:
            continue

        raw_date = j.get("date_posted")
        posted_date = str(raw_date).strip() if raw_date and str(raw_date).strip() not in ["N/A", "None", ""] else today_str
        
        if posted_date < cutoff_date:
            continue

        sector = resolved.get("industry_sector") or j.get("industry")
        if not sector or sector in ["Other", "N/A", ""]:
            sector = determine_industry(clean_title, company_name, raw_desc)

        j_enriched = {
            **j_copy,
            "company": company_name,
            "location": cleaned_loc,
            "industry": sector,
            "pay": clean_pay,
            "resolved_profile": resolved
        }

        exp_req = j.get("experience") or j.get("requirements")
        exp_req = extract_key_requirements(
            text=raw_desc,
            existing_exp=exp_req or "",
            job_dict=j_enriched
        )

        exp_req = standardize_driver_license_requirement(
            exp_req,
            text_context=f"{clean_title} {company_name} {raw_desc}",
            gemini_license=resolved.get("driverLicenseType") or j.get("driverLicenseType") or j.get("driver_license_type")
        )

        final_desc = raw_desc
        if not final_desc or str(final_desc).strip() in ["N/A", "None", ""]:
            final_desc = generate_key_description(
                title=clean_title,
                company=company_name,
                location=cleaned_loc,
                sector=sector,
                job_type=j.get("job_type_extracted") or "Unstated",
                schedule=j.get("shift_schedule") or "Unstated",
                pay=clean_pay or "Unstated",
                requirements=exp_req
            )

        hs_ok_val = evaluate_hs_ok(
            title=clean_title,
            company=company_name,
            text=raw_desc,
            requirements=exp_req,
            job_type=j.get("job_type_extracted") or "",
            shift=j.get("shift_schedule") or "",
            job_dict=j_enriched,
            gemini_teen_friendly=j.get("isTeenFriendly") or j.get("is_teen_friendly") or j.get("teen_friendly")
        )

        rows.append({
            "Source": j.get("source") or "Direct",
            "Job Title": clean_title,
            "Company": company_name,
            "Location": cleaned_loc,
            "Pay Rate": clean_pay,
            "Full / Part Time": j.get("job_type_extracted") if j.get("job_type_extracted") and str(j.get("job_type_extracted")).strip() not in ["N/A", "None", "", "nan"] else "Unstated",
            "Schedule / Shift": j.get("shift_schedule") if j.get("shift_schedule") and str(j.get("shift_schedule")).strip() not in ["N/A", "None", "", "nan"] else "Unstated",
            "Experience / Requirements": exp_req,
            "H.S. OK": hs_ok_val,
            "Job Description Summary": final_desc,
            "Date Posted": posted_date,
            "Job Posting": j.get("job_url") or resolved.get("career_url") or "",
            "Industry Sector": sector,
            "Last Updated": today_str,
            "Branch / Location Name": resolved.get("branch_name", ""),
            "City": resolved.get("city", "Redding"),
            "State": resolved.get("state", "CA"),
            "Zip Code": resolved.get("zip_code", ""),
            "Phone": resolved.get("phone", ""),
            "Min Age": str(resolved.get("min_age", 18)),
            "Fair Chance / Felon Friendly": resolved.get("fair_chance", "Unknown"),
            "Drug Testing Policy": resolved.get("drug_testing_policy", "None"),
            "Background Check Policy": resolved.get("background_check_policy", "None"),
            "Driver License": resolved.get("driver_license_policy", "Not Required"),
            "HS Dip / GED": resolved.get("hs_ged_policy", "Not Required"),
            "Work Experience": resolved.get("work_experience_policy", "None (Entry-Level)"),
            "Location & Transit Notes": resolved.get("location_transit_notes", "")
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
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=30)
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
    Reads the 'Area Employers' (gid=1114754984) 21-column tab (or legacy fallback tabs),
    dynamically maps all 21 columns, and syncs into the local SQLite employers.db and fast JSON cache.
    """
    if not output_json:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_json = os.path.join(base_dir, "redding_area_employers.json")

    client = get_gspread_client()
    spreadsheet = client.open_by_key(sheet_id)

    tab_names = [ws.title for ws in spreadsheet.worksheets()]
    if "Area Employers" in tab_names:
        tabs_to_scan = ["Area Employers"]
    else:
        tabs_to_scan = [t for t in ["Redding Area Employers", "Burney Area Employers (draft)"] if t in tab_names]

    all_combined_records = []
    structured_employers = {}

    for tab_name in tabs_to_scan:
        try:
            ws = spreadsheet.worksheet(tab_name)
        except Exception:
            continue

        all_rows = ws.get_all_values()
        if len(all_rows) < 2:
            continue

        row1 = all_rows[0]
        row1_lower = [h.strip().lower() for h in row1]
        is_area_employers_layout = (
            any("street address" in h for h in row1_lower)
            or any("branch" in h for h in row1_lower)
            or any("brand name" in h for h in row1_lower)
            or tab_name == "Area Employers"
        )

        if is_area_employers_layout:
            col_map = {h: idx for idx, h in enumerate(row1_lower)}
            for r in all_rows[1:]:
                if not any(r):
                    continue

                def get_c(pattern, default=""):
                    for h, idx in col_map.items():
                        if pattern in h and idx < len(r):
                            return r[idx].strip()
                    return default

                comp = get_c("brand name") or get_c("employer name") or get_c("company")
                if not comp:
                    continue

                corp = get_c("corporate")
                branch = get_c("branch")
                street = get_c("street address") or get_c("address")
                city = get_c("city", "Redding")
                state = get_c("state", "CA")
                zip_code = get_c("zip")
                phone = get_c("phone")
                manager = get_c("manager") or get_c("contact")
                sector = get_c("sector") or get_c("industry")
                min_age = get_c("min age") or get_c("age", "18")
                fair_chance = get_c("fair chance") or get_c("felon")
                drug_testing = get_c("drug")
                bg_check = get_c("background") or get_c("clean record")
                dl = get_c("driver") or get_c("dl")
                hs_ged = get_c("hs dip") or get_c("high school") or get_c("ged")
                work_exp = get_c("work exp") or get_c("experience") or "None (Entry-Level)"
                wage = get_c("starting wage") or get_c("wage") or get_c("pay")
                career_url = get_c("career")
                indeed_url = get_c("indeed")
                notes = get_c("location & transit") or get_c("transit") or get_c("note") or get_c("barrier")
                review_status = get_c("review status") or get_c("status") or "Verified"

                is_first_branch = comp not in structured_employers
                loc_item = {
                    "location_name": branch or ("Main Location" if is_first_branch else "Branch Location"),
                    "street_address": street,
                    "city": city if city else "Redding",
                    "state": state if state else "CA",
                    "zip_code": zip_code,
                    "phone": phone,
                    "manager_name": manager,
                    "is_primary": 1 if is_first_branch else 0,
                    "notes": notes
                }

                # Expand slash-separated aliases while keeping full string first for round-trip export
                aliases_list = []
                if corp:
                    aliases_list.append(corp)
                    for sub_al in re.split(r'[\/;]', corp):
                        s_clean = sub_al.strip()
                        if s_clean and s_clean.lower() != comp.lower() and s_clean not in aliases_list:
                            aliases_list.append(s_clean)

                if is_first_branch:
                    structured_employers[comp] = {
                        "name": comp,
                        "company": comp,
                        "aliases": aliases_list,
                        "industry_sector": sector,
                        "min_age": min_age,
                        "min_age_baseline": min_age,
                        "fair_chance": fair_chance,
                        "felon_friendly": fair_chance,
                        "drug_testing": drug_testing,
                        "background_check": bg_check,
                        "clean_record_required": bg_check,
                        "drivers_license_required": dl,
                        "drivers_license": dl,
                        "hs_ged_required": hs_ged,
                        "hs_ged_baseline": hs_ged,
                        "work_experience": work_exp,
                        "work_experience_required": work_exp,
                        "wage": wage,
                        "starting_wage": wage,
                        "career_url": career_url,
                        "indeed_url": indeed_url,
                        "notes": notes,
                        "review_status": review_status,
                        "is_verified": review_status.lower() not in ["pending", "unverified", "draft"],
                        "locations": [loc_item]
                    }
                else:
                    structured_employers[comp]["locations"].append(loc_item)
                    for al in aliases_list:
                        if al not in structured_employers[comp]["aliases"]:
                            structured_employers[comp]["aliases"].append(al)

                all_combined_records.append({
                    "company": comp,
                    "corporate_aliases": corp,
                    "branch_name": branch,
                    "street_address": street,
                    "city": city,
                    "state": state,
                    "zip_code": zip_code,
                    "address": f"{street}, {city}, {state} {zip_code}".strip(", "),
                    "min_age": min_age,
                    "hs_ged_required": hs_ged,
                    "drivers_license_required": dl,
                    "clean_record_required": bg_check,
                    "background_check": bg_check,
                    "work_experience_required": work_exp,
                    "wage": wage,
                    "career_url": career_url,
                    "indeed_url": indeed_url,
                    "phone": phone,
                    "manager_name": manager,
                    "felon_friendly": fair_chance,
                    "drug_testing": drug_testing,
                    "industry_sector": sector,
                    "notes": notes,
                    "review_status": review_status
                })

        else:
            # Legacy 2-header layout
            if len(all_rows) < 3:
                continue
            row2 = all_rows[1]
            col_map = {}
            max_cols = max(len(row1), len(row2))

            for col_idx in range(max_cols):
                h1 = row1[col_idx].strip() if col_idx < len(row1) else ""
                h2 = row2[col_idx].strip() if col_idx < len(row2) else ""
                combined_h = f"{h1} {h2}".lower().strip()

                if any(k in combined_h for k in ["company", "employer"]):
                    col_map["company"] = col_idx
                elif any(k in combined_h for k in ["address", "locations"]):
                    col_map["address"] = col_idx
                elif "age" in combined_h:
                    col_map["min_age"] = col_idx
                elif any(k in combined_h for k in ["hs dip", "ged", "high school"]):
                    col_map["hs_ged"] = col_idx
                elif combined_h.startswith("dl") or "driver" in combined_h:
                    col_map["dl"] = col_idx
                elif any(k in combined_h for k in ["clean record", "background"]):
                    col_map["clean_record"] = col_idx
                elif any(k in combined_h for k in ["work exp", "experience"]):
                    col_map["work_exp"] = col_idx
                elif any(k in combined_h for k in ["wage", "pay"]):
                    col_map["wage"] = col_idx
                elif "career" in combined_h:
                    col_map["career_url"] = col_idx
                elif "indeed" in combined_h:
                    col_map["indeed_url"] = col_idx
                elif "phone" in combined_h:
                    col_map["phone"] = col_idx
                elif "manager" in combined_h:
                    col_map["manager"] = col_idx
                elif any(k in combined_h for k in ["felon", "fair chance"]):
                    col_map["felon_friendly"] = col_idx
                elif "drug" in combined_h:
                    col_map["drug_testing"] = col_idx
                elif any(k in combined_h for k in ["sector", "industry"]):
                    col_map["industry"] = col_idx
                elif "note" in combined_h:
                    col_map["notes"] = col_idx

            if "company" not in col_map: col_map["company"] = 0
            if "address" not in col_map: col_map["address"] = 1
            if "min_age" not in col_map: col_map["min_age"] = 2
            if "hs_ged" not in col_map: col_map["hs_ged"] = 4
            if "dl" not in col_map: col_map["dl"] = 5
            if "clean_record" not in col_map: col_map["clean_record"] = 6
            if "work_exp" not in col_map: col_map["work_exp"] = 7
            if "wage" not in col_map: col_map["wage"] = 8
            if "career_url" not in col_map: col_map["career_url"] = 9
            if "indeed_url" not in col_map: col_map["indeed_url"] = 10
            if "notes" not in col_map: col_map["notes"] = 11

            for r in all_rows[2:]:
                comp = r[col_map["company"]].strip() if col_map["company"] < len(r) else ""
                if not comp or comp.startswith("http"):
                    continue

                addr = r[col_map["address"]].strip() if col_map["address"] < len(r) else ""
                min_age = r[col_map["min_age"]].strip() if col_map["min_age"] < len(r) else ""
                hs_ged = r[col_map["hs_ged"]].strip() if col_map["hs_ged"] < len(r) else ""
                dl = r[col_map["dl"]].strip() if col_map["dl"] < len(r) else ""
                clean_rec = r[col_map["clean_record"]].strip() if col_map["clean_record"] < len(r) else ""
                work_exp = r[col_map["work_exp"]].strip() if col_map["work_exp"] < len(r) else ""
                wage = r[col_map["wage"]].strip() if col_map["wage"] < len(r) else ""
                career_url = r[col_map["career_url"]].strip() if col_map["career_url"] < len(r) else ""
                indeed_url = r[col_map["indeed_url"]].strip() if col_map["indeed_url"] < len(r) else ""
                notes = r[col_map["notes"]].strip() if col_map["notes"] < len(r) else ""
                phone = r[col_map["phone"]].strip() if "phone" in col_map and col_map["phone"] < len(r) else ""
                manager = r[col_map["manager"]].strip() if "manager" in col_map and col_map["manager"] < len(r) else ""
                felon_friendly = r[col_map["felon_friendly"]].strip() if "felon_friendly" in col_map and col_map["felon_friendly"] < len(r) else ""
                drug_testing = r[col_map["drug_testing"]].strip() if "drug_testing" in col_map and col_map["drug_testing"] < len(r) else ""
                industry = r[col_map["industry"]].strip() if "industry" in col_map and col_map["industry"] < len(r) else ""

                all_combined_records.append({
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
                    "phone": phone,
                    "manager_name": manager,
                    "felon_friendly": felon_friendly,
                    "drug_testing": drug_testing,
                    "industry_sector": industry,
                    "notes": notes
                })

    # Save to legacy json
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_combined_records, f, indent=2)

    # Ingest into SQLite employers.db and fast cache
    try:
        import employer_db
        if structured_employers:
            count = employer_db.import_from_records(list(structured_employers.values()))
        else:
            count = employer_db.import_from_records(all_combined_records)
        print(f"[SHEETS] Ingested {count} employers into employers.db & employers_registry.json")
    except Exception as e:
        print(f"[SHEETS] Error ingesting to employer_db: {e}")

    print(f"[SHEETS] Cached {len(all_combined_records)} employer branch rows from Google Sheets to {output_json}")
    return all_combined_records

sync_area_employers = sync_redding_area_employers

def export_employers_to_google_sheet(sheet_id: str = "1uGL7w8fpb5P0D-kNIPces9nOK4Ctt6Bfg5jlA6J-_CU") -> int:
    """
    Exports the verified employers from local SQLite employers.db back to the
    'Area Employers' Google Sheet tab using the exact 21-column schema.
    """
    try:
        import employer_db
        employers = employer_db.get_all_employers()
        if not employers:
            return 0

        client = get_gspread_client()
        spreadsheet = client.open_by_key(sheet_id)
        
        tab_name = "Area Employers"
        try:
            ws = spreadsheet.worksheet(tab_name)
        except Exception:
            try:
                ws = spreadsheet.worksheet("Redding Area Employers")
            except Exception:
                ws = spreadsheet.add_worksheet(title="Area Employers", rows=500, cols=25)

        headers = [
            "Company / Brand Name",
            "Corporate Name / Aliases",
            "Branch / Location Name",
            "Physical Street Address",
            "City",
            "State",
            "Zip Code",
            "Phone",
            "Industry Sector",
            "Min Age",
            "Fair Chance / Felon Friendly",
            "Drug Testing Policy",
            "Background Check Policy",
            "Driver License",
            "HS Dip / GED",
            "Work Experience",
            "Starting Wage",
            "Career Website",
            "Indeed Website",
            "Location & Transit Notes",
            "Review Status"
        ]

        rows = [headers]
        for emp in employers:
            locations = emp.get("locations", [])
            corp = emp.get("aliases", [emp.get("name", "")])[0] if emp.get("aliases") else emp.get("name", "")
            rev_status = emp.get("review_status") or ("Verified" if emp.get("is_verified", 1) else "Pending")
            
            if not locations:
                rows.append([
                    emp.get("name", ""),
                    corp,
                    "Main Location",
                    "Redding, CA",
                    "Redding",
                    "CA",
                    "96001",
                    "",
                    emp.get("industry_sector", ""),
                    str(emp.get("min_age_baseline", "18")),
                    emp.get("felon_friendly", ""),
                    emp.get("drug_testing", ""),
                    emp.get("background_check", ""),
                    emp.get("drivers_license", ""),
                    emp.get("hs_ged_baseline", ""),
                    emp.get("work_experience", "None (Entry-Level)"),
                    emp.get("starting_wage", ""),
                    emp.get("career_url", ""),
                    emp.get("indeed_url", ""),
                    emp.get("notes", ""),
                    rev_status
                ])
            else:
                for loc in locations:
                    rows.append([
                        emp.get("name", ""),
                        corp,
                        loc.get("location_name", ""),
                        loc.get("street_address", ""),
                        loc.get("city", "Redding"),
                        loc.get("state", "CA"),
                        loc.get("zip_code", ""),
                        loc.get("phone", ""),
                        emp.get("industry_sector", ""),
                        str(emp.get("min_age_baseline", "18")),
                        emp.get("felon_friendly", ""),
                        emp.get("drug_testing", ""),
                        emp.get("background_check", ""),
                        emp.get("drivers_license", ""),
                        emp.get("hs_ged_baseline", ""),
                        emp.get("work_experience", "None (Entry-Level)"),
                        emp.get("starting_wage", ""),
                        emp.get("career_url", ""),
                        emp.get("indeed_url", ""),
                        loc.get("notes") or emp.get("notes", ""),
                        rev_status
                    ])

        ws.clear()
        ws.update(values=rows, range_name="A1")
        print(f"[SHEETS] Exported {len(rows)-1} worksite rows for {len(employers)} employers to tab '{ws.title}'.")
        return len(employers)
    except Exception as e:
        print(f"[SHEETS] Error exporting employers to Google Sheet: {e}")
        return 0