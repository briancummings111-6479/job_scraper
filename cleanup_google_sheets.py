import sys
import argparse
from datetime import datetime
import pandas as pd
import gspread
import sheets_sync
import firestore_sync
from scrapper import is_rejected_job, is_expired_job_content, clean_job_title, extract_key_requirements, generate_key_description

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
    print(f"Active valid jobs in Firestore available to sync: {len(fs_docs)}")

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
        title = j.get("title", "")
        company = j.get("company", "")
        sector = j.get("sector") or j.get("category") or "Other"
        location = j.get("location", "Redding, CA")
        pay = j.get("pay") or "N/A"
        job_type = j.get("jobType") or "N/A"
        schedule = j.get("schedule") or j.get("shift") or "N/A"
        raw_desc = str(j.get("description") or "").strip()
        raw_exp = str(j.get("requirements") or j.get("experience") or "").strip()

        exp_req = extract_key_requirements(text=raw_desc if raw_desc != "N/A" else "", existing_exp=raw_exp, job_dict=j)
        
        final_desc = raw_desc
        if not final_desc or final_desc in ["N/A", "None", ""]:
            final_desc = generate_key_description(
                title=title,
                company=company,
                location=location,
                sector=sector,
                job_type=job_type,
                schedule=schedule,
                pay=pay,
                requirements=exp_req
            )

        fresh_auto_rows.append({
            "Date Posted": j.get("datePosted") or datetime.now().strftime("%Y-%m-%d"),
            "Job Title": title,
            "Company": company,
            "Sector": sector,
            "Location": location,
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
    print(f"Prepared {len(df_auto)} verified, entry-level listings for Automated_Posts.")

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
    
    retained_redding = []
    rejected_redding = []

    for idx, r in enumerate(redding_rows[2:], start=3):
        if not any(r):
            continue
        title = r[1] if len(r) > 1 else ""
        company = r[2] if len(r) > 2 else ""
        cleaned_t = clean_job_title(title)
        
        is_rej, reason = is_rejected_job(cleaned_t, company)
        if is_rej:
            rejected_redding.append((idx, title, company, reason))
        else:
            # Clean title in the row
            r_copy = list(r)
            r_copy[1] = cleaned_t
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
