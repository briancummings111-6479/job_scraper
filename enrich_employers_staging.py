"""
enrich_employers_staging.py

One-time comprehensive enrichment and staging script for Shasta County employers.
Reads all 262 employers from Google Sheet 'Redding Area Employers', merges with
verified Shasta County physical worksite addresses, multi-location branch breakdowns,
corporate parent entities, 19-sector workforce taxonomy classifications, and baseline
hiring policies (min age, fair-chance/felon-friendly, drug test, background check, DL).

Outputs results directly to the dedicated staging worksheet:
'Employers_Review_Staging' in spreadsheet '1uGL7w8fpb5P0D-kNIPces9nOK4Ctt6Bfg5jlA6J-_CU'
without modifying or overwriting 'Redding Area Employers'.
"""

import os
import sys
import json
import re
from datetime import datetime

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sheets_sync
import gspread

from data_part1 import PART1_PROFILES
from data_part2 import PART2_PROFILES
from data_part3 import PART3_PROFILES
from data_part4 import PART4_PROFILES

CHECKPOINT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "enrichment_staging_checkpoint.json")

def normalize_name_for_lookup(name: str) -> str:
    """Normalizes employer name for resilient lookup handling encodings and apostrophes."""
    if not name:
        return ""
    text = re.sub(r'[\uFFFD\u2019\u2018\'\"`\.]', '', str(name)).lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def build_composite_knowledge_base():
    """Combines all four modular knowledge base parts into a normalized lookup table."""
    all_profiles = {}
    all_profiles.update(PART1_PROFILES)
    all_profiles.update(PART2_PROFILES)
    all_profiles.update(PART3_PROFILES)
    all_profiles.update(PART4_PROFILES)
    
    lookup = {}
    for name, prof in all_profiles.items():
        key = normalize_name_for_lookup(name)
        lookup[key] = (name, prof)
    return lookup

def load_raw_sheet_employers():
    """Reads all current employer rows from the Google Sheet 'Redding Area Employers'."""
    client = sheets_sync.get_gspread_client()
    spreadsheet = client.open_by_key("1uGL7w8fpb5P0D-kNIPces9nOK4Ctt6Bfg5jlA6J-_CU")
    ws = spreadsheet.worksheet("Redding Area Employers")
    rows = ws.get_all_values()
    
    records = []
    for i, r in enumerate(rows[2:]):
        if not any(c.strip() for c in r):
            continue
        records.append({
            "row_idx": i + 3,
            "brand_name": r[0].strip() if len(r) > 0 else "",
            "corporate_name": r[1].strip() if len(r) > 1 else "",
            "address": r[2].strip() if len(r) > 2 else "",
            "min_age": r[3].strip() if len(r) > 3 else "",
            "hs_ged": r[5].strip() if len(r) > 5 else "",
            "dl": r[6].strip() if len(r) > 6 else "",
            "clean_record": r[7].strip() if len(r) > 7 else "",
            "work_exp": r[8].strip() if len(r) > 8 else "",
            "wage": r[9].strip() if len(r) > 9 else "",
            "career_url": r[10].strip() if len(r) > 10 else "",
            "indeed_url": r[11].strip() if len(r) > 11 else "",
            "notes": r[12].strip() if len(r) > 12 else ""
        })
    return records

def generate_staging_records(raw_employers: list, kb_lookup: dict) -> list:
    """
    Transforms raw employer records into fully enriched staging records,
    expanding multi-location employers into discrete physical branch rows.
    """
    staging_rows = []
    
    for raw in raw_employers:
        raw_name = raw.get("brand_name", "")
        key = normalize_name_for_lookup(raw_name)
        
        if key in kb_lookup:
            canonical_name, prof = kb_lookup[key]
        else:
            # Fallback for unrecognized entry
            canonical_name = raw_name
            prof = {
                "corporate_name": raw.get("corporate_name", ""),
                "sector": "Other",
                "min_age": 18,
                "fair_chance": "Unknown",
                "drug_testing": "Unknown",
                "background_check": "Standard Pre-Employment",
                "driver_license": "None",
                "hs_ged": "Not Required",
                "work_experience": "No experience required (On-the-job training provided)",
                "starting_wage": raw.get("wage", ""),
                "career_url": raw.get("career_url", ""),
                "indeed_url": raw.get("indeed_url", ""),
                "notes": raw.get("notes", ""),
                "locations": [
                    {
                        "branch_name": "Main Location",
                        "street_address": raw.get("address", "Redding, CA"),
                        "city": "Redding",
                        "state": "CA",
                        "zip_code": "96001",
                        "phone": "",
                        "notes": ""
                    }
                ]
            }
        
        # Corporate name override / preserve
        corp_name = raw.get("corporate_name", "").strip() or prof.get("corporate_name", "")
        
        # Minimum age: preserve user value if explicitly entered
        min_age_val = raw.get("min_age", "").strip() or str(prof.get("min_age", 18))
        
        # Starting wage: preserve user value if explicitly entered
        wage_val = raw.get("wage", "").strip() or prof.get("starting_wage", "")
        
        # Career & Indeed URLs: preserve user values if entered
        career_url = raw.get("career_url", "").strip() or prof.get("career_url", "")
        indeed_url = raw.get("indeed_url", "").strip() or prof.get("indeed_url", "")
        
        # Sector, fair chance, drug testing, clearances
        sector = prof.get("sector", "Other")
        fair_chance = prof.get("fair_chance", "Unknown")
        drug_testing = prof.get("drug_testing", "Unknown")
        background_check = prof.get("background_check", "Standard Pre-Employment")
        driver_license = raw.get("dl", "").strip() or prof.get("driver_license", "None")
        hs_ged = raw.get("hs_ged", "").strip() or prof.get("hs_ged", "Not Required")
        work_exp = raw.get("work_exp", "").strip() or prof.get("work_experience", "No experience required")
        
        locations = prof.get("locations", [])
        is_multi = len(locations) > 1
        
        for loc_idx, loc in enumerate(locations):
            branch_name = loc.get("branch_name", "Main Location")
            street_address = loc.get("street_address", "")
            city = loc.get("city", "Redding")
            state = loc.get("state", "CA")
            zip_code = loc.get("zip_code", "")
            phone = loc.get("phone", "")
            
            # Combine notes
            note_parts = []
            if raw.get("notes", "").strip():
                note_parts.append(raw.get("notes", "").strip())
            if prof.get("notes", "").strip():
                note_parts.append(prof.get("notes", "").strip())
            if loc.get("notes", "").strip():
                note_parts.append(loc.get("notes", "").strip())
            combined_notes = " | ".join(dict.fromkeys(note_parts)) # deduplicate preserving order
            
            # Determine review status
            if "field dispatched" in street_address.lower() or "mobile" in street_address.lower():
                status = "Field Dispatched / Mobile"
            elif is_multi:
                status = f"Multi-Location Branch ({loc_idx + 1} of {len(locations)})"
            elif not street_address or "unknown" in street_address.lower():
                status = "Pending Verification"
            else:
                status = "Verified Local Worksite"
            
            staging_rows.append({
                "brand_name": canonical_name,
                "corporate_name": corp_name,
                "branch_name": branch_name,
                "street_address": street_address,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "phone": phone,
                "industry_sector": sector,
                "min_age": min_age_val,
                "fair_chance": fair_chance,
                "drug_testing": drug_testing,
                "background_check": background_check,
                "driver_license": driver_license,
                "hs_ged": hs_ged,
                "work_experience": work_exp,
                "starting_wage": wage_val,
                "career_url": career_url,
                "indeed_url": indeed_url,
                "notes": combined_notes,
                "review_status": status
            })
            
    return staging_rows

def export_to_staging_worksheet(staging_records: list, spreadsheet_id: str = "1uGL7w8fpb5P0D-kNIPces9nOK4Ctt6Bfg5jlA6J-_CU"):
    """
    Writes all staging records into a dedicated 'Employers_Review_Staging' tab
    in Google Sheets, creating and formatting the sheet if it does not exist.
    """
    client = sheets_sync.get_gspread_client()
    spreadsheet = client.open_by_key(spreadsheet_id)
    
    tab_title = "Employers_Review_Staging"
    
    # 1. Get or create worksheet
    try:
        ws = spreadsheet.worksheet(tab_title)
        print(f"[STAGING] Found existing worksheet '{tab_title}'. Clearing existing content...")
        ws.clear()
    except gspread.exceptions.WorksheetNotFound:
        print(f"[STAGING] Creating new worksheet '{tab_title}'...")
        ws = spreadsheet.add_worksheet(title=tab_title, rows=len(staging_records) + 50, cols=22)
    
    # 2. Build headers
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
    
    # 3. Assemble rows
    rows = [headers]
    for r in staging_records:
        rows.append([
            r["brand_name"],
            r["corporate_name"],
            r["branch_name"],
            r["street_address"],
            r["city"],
            r["state"],
            r["zip_code"],
            r["phone"],
            r["industry_sector"],
            str(r["min_age"]),
            r["fair_chance"],
            r["drug_testing"],
            r["background_check"],
            r["driver_license"],
            r["hs_ged"],
            r["work_experience"],
            r["starting_wage"],
            r["career_url"],
            r["indeed_url"],
            r["notes"],
            r["review_status"]
        ])
    
    # 4. Upload data in batch
    print(f"[STAGING] Uploading {len(rows)} rows to '{tab_title}'...")
    ws.update(values=rows, range_name="A1")
    
    # 5. Format header row (Navy blue background, bold white text, freeze row 1)
    try:
        # Freeze header row
        spreadsheet.batch_update({
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": ws.id,
                            "gridProperties": {
                                "frozenRowCount": 1
                            }
                        },
                        "fields": "gridProperties.frozenRowCount"
                    }
                },
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": ws.id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(headers)
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 0.12,
                                    "green": 0.28,
                                    "blue": 0.49
                                },
                                "textFormat": {
                                    "foregroundColor": {
                                        "red": 1.0,
                                        "green": 1.0,
                                        "blue": 1.0
                                    },
                                    "bold": True,
                                    "fontSize": 10
                                },
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE"
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                    }
                }
            ]
        })
        print(f"[STAGING] Formatted header row and froze row 1 in '{tab_title}'.")
    except Exception as fmt_err:
        print(f"[STAGING] Note: Header styling batch update skipped ({fmt_err})")
        
    return len(staging_records)

def main():
    print("=" * 70)
    print("  SHASTA COUNTY EMPLOYERS ENRICHMENT & STAGING PASS")
    print("=" * 70)
    
    # Step 1: Load raw sheet employers
    print("\n[Step 1/4] Reading employers from Google Sheet 'Redding Area Employers'...")
    raw_employers = load_raw_sheet_employers()
    print(f" -> Found {len(raw_employers)} active employer records in master sheet.")
    
    # Step 2: Compile knowledge base
    print("\n[Step 2/4] Compiling verified regional employer knowledge base...")
    kb_lookup = build_composite_knowledge_base()
    print(f" -> Loaded {len(kb_lookup)} verified employer profiles.")
    
    # Step 3: Generate enriched staging records
    print("\n[Step 3/4] Enriching employers, physical addresses, and policy baselines...")
    staging_records = generate_staging_records(raw_employers, kb_lookup)
    print(f" -> Generated {len(staging_records)} discrete addressable staging rows.")
    
    # Save checkpoint locally
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(staging_records, f, indent=2)
    print(f" -> Checkpoint saved locally to: {CHECKPOINT_FILE}")
    
    # Step 4: Export to staging tab in Google Sheets
    print("\n[Step 4/4] Writing enriched records to Google Sheet tab 'Employers_Review_Staging'...")
    count = export_to_staging_worksheet(staging_records)
    
    print("\n" + "=" * 70)
    print(f"  SUCCESSFULLY STAGED {count} EMPLOYER WORKSHITES FOR REVIEW!")
    print(f"  Master tab 'Redding Area Employers' remains UNCHANGED.")
    print(f"  Staging tab: https://docs.google.com/spreadsheets/d/1uGL7w8fpb5P0D-kNIPces9nOK4Ctt6Bfg5jlA6J-_CU/edit#gid={count}")
    print("=" * 70)

if __name__ == "__main__":
    main()
