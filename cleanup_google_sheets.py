import sys
import argparse
from datetime import datetime
import pandas as pd
import gspread
import sheets_sync
import firestore_sync
from scrapper import is_rejected_job, is_expired_job_content, clean_job_title, extract_key_requirements, generate_key_description, clean_location_str, is_shasta_county_location

SHEET_ID = "1uGL7w8fpb5P0D-kNIPces9nOK4Ctt6Bfg5jlA6J-_CU"

def cleanup_sheets(dry_run=True):
    client = sheets_sync.get_gspread_client()
    spreadsheet = client.open_by_key(SHEET_ID)

    # 1. Inspect & Clean Automated_Posts
    print("=" * 50)
    print("ANALYZING TAB: Automated_Posts")
    print("=" * 50)
    
    db = firestore_sync.get_firestore_client()
    fs_docs = list(db.collection('jobs').stream())
    print(f"Total jobs in Firestore: {len(fs_docs)}")

    ws_auto = None
    try:
        ws_auto = spreadsheet.worksheet("Automated_Posts")
        curr_auto_rows = ws_auto.get_all_values()
        print(f"Current rows in Automated_Posts: {len(curr_auto_rows)}")
    except Exception as e:
        print(f"Could not read Automated_Posts: {e}")

    # Build the fresh rows from Firestore verified jobs
    fresh_auto_rows = []
    for d in fs_docs:
        j = d.to_dict()
        raw_loc = j.get("location", "Redding, CA")
        cleaned_loc = clean_location_str(raw_loc)
        is_shasta, loc_reason = is_shasta_county_location(cleaned_loc)
        if not is_shasta:
            continue

        title = j.get("title", "")
        company = j.get("company", "")
        cleaned_t = clean_job_title(title)
        sector = j.get("sector") or j.get("category") or "Other"
        pay = j.get("pay") or "N/A"
        job_type = j.get("jobType") or "N/A"
        schedule = j.get("schedule") or j.get("shift") or "N/A"
        raw_desc = str(j.get("description") or "").strip()
        raw_exp = str(j.get("requirements") or j.get("experience") or "").strip()

        is_boilerplate = bool("industry sector:" in raw_desc.lower() or "key requirements:" in raw_desc.lower() or "position with" in raw_desc.lower())
        true_desc = "" if is_boilerplate else raw_desc

        is_exp = is_expired_job_content(true_desc) or is_expired_job_content(cleaned_t)
        is_rej, _ = is_rejected_job(cleaned_t, company, true_desc, pay=pay, location=cleaned_loc)
        if is_exp or is_rej:
            continue

        exp_req = extract_key_requirements(
            text=true_desc,
            existing_exp="",
            job_dict={"title": cleaned_t, "company": company, "sector": sector, "location": cleaned_loc}
        )
        
        final_desc = generate_key_description(
            title=cleaned_t,
            company=company,
            location=cleaned_loc,
            sector=sector,
            job_type=job_type,
            schedule=schedule,
            pay=pay,
            requirements=exp_req
        )

        fresh_auto_rows.append({
            "Date Posted": j.get("datePosted") or datetime.now().strftime("%Y-%m-%d"),
            "Job Title": cleaned_t,
            "Company": company,
            "Sector": sector,
            "Location": cleaned_loc,
            "Pay Rate": pay,
            "Job Type": job_type,
            "Schedule / Shift": schedule,
            "Experience / Requirements": exp_req,
            "Job Description": final_desc,
            "Application Link": j.get("jobUrl") or j.get("url") or "",
            "Source": j.get("source") or "Direct"
        })

    df_auto = pd.DataFrame(fresh_auto_rows)
    df_auto.sort_values(by="Date Posted", ascending=False, inplace=True)
    print(f"Prepared {len(df_auto)} verified, Shasta County entry-level listings for Automated_Posts.")

    # 2. Inspect & Clean Redding Area Job Postings
    print("\n" + "=" * 50)
    print("ANALYZING TAB: Redding Area Job Postings")
    print("=" * 50)
    
    ws_redding = spreadsheet.worksheet("Redding Area Job Postings")
    redding_rows = ws_redding.get_all_values()
    print(f"Total rows in Redding Area Job Postings: {len(redding_rows)}")

    # Rows 0 and 1 are metadata / headers
    meta_row = redding_rows[0] if len(redding_rows) > 0 else []
    header_row = redding_rows[1] if len(redding_rows) > 1 else []
    
    # Map header names to column index
    header_map = {str(col).strip().lower(): i for i, col in enumerate(header_row)}
    title_idx = header_map.get("job title", 1)
    comp_idx = header_map.get("company", 2)
    loc_idx = header_map.get("location", 3)
    pay_idx = header_map.get("pay", 4)

    retained_redding = []
    rejected_redding = []

    for idx, r in enumerate(redding_rows[2:], start=3):
        if not any(r):
            continue
        title = r[title_idx] if len(r) > title_idx else ""
        company = r[comp_idx] if len(r) > comp_idx else ""
        raw_loc = r[loc_idx] if len(r) > loc_idx else ""
        raw_pay = r[pay_idx] if len(r) > pay_idx else ""
        cleaned_loc = clean_location_str(raw_loc) if raw_loc else ""
        cleaned_t = clean_job_title(title)
        
        is_shasta, loc_reason = is_shasta_county_location(cleaned_loc) if cleaned_loc else (True, "")
        is_rej, reason = is_rejected_job(cleaned_t, company, pay=raw_pay, location=cleaned_loc if cleaned_loc else "")

        if not is_shasta:
            rejected_redding.append((idx, title, company, loc_reason))
        elif is_rej:
            rejected_redding.append((idx, title, company, reason))
        else:
            # Clean title and location in the row
            r_copy = list(r)
            if len(r_copy) > title_idx:
                r_copy[title_idx] = cleaned_t
            if len(r_copy) > loc_idx and cleaned_loc:
                r_copy[loc_idx] = cleaned_loc
            retained_redding.append(r_copy)

    print(f"Redding Area Job Postings: {len(rejected_redding)} non-entry-level rows identified for removal.")
    print(f"Redding Area Job Postings: {len(retained_redding)} valid entry-level rows to retain.")
    print("\nSample rejected rows from Redding Area Job Postings:")
    for item in rejected_redding[:10]:
        print(f"  - Line {item[0]}: [{item[3]}] {item[1]} at {item[2]}")

    if dry_run:
        print("\n[DRY RUN COMPLETE] No changes were written to Google Sheets.")
        print("To apply these changes, run with '--execute'.")
        return

    # EXECUTE CHANGES
    print("\n" + "=" * 50)
    print("EXECUTING GOOGLE SHEETS UPDATES")
    print("=" * 50)

    # 1. Update Automated_Posts
    if ws_auto:
        print("Updating 'Automated_Posts' tab...")
        ws_auto.clear()
        ws_auto.update(values=[df_auto.columns.values.tolist()] + df_auto.values.tolist(), range_name="A1")
        print(f"Successfully updated 'Automated_Posts' with {len(df_auto)} verified listings.")

    # 2. Update Redding Area Job Postings
    print("Updating 'Redding Area Job Postings' tab...")
    try:
        new_redding_content = [meta_row, header_row] + retained_redding
        ws_redding.clear()
        ws_redding.update(values=new_redding_content, range_name="A1")
        print(f"Successfully updated 'Redding Area Job Postings' (removed {len(rejected_redding)} rejected rows, retained {len(retained_redding)}).")
    except Exception as e:
        print(f"[NOTE] 'Redding Area Job Postings' could not be modified directly: {e}")
        print("  This tab contains protected ranges in Google Sheets.")

    print("\nGoogle Sheet sync finished.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Clean up Google Sheets job listings")
    parser.add_argument('--execute', action='store_true', help='Execute updates to Google Sheets')
    args = parser.parse_args()

    cleanup_sheets(dry_run=not args.execute)
