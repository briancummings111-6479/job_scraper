import os
import json
import gspread
from sheets_sync import get_gspread_client

SHEET_ID = "1uGL7w8fpb5P0D-kNIPces9nOK4Ctt6Bfg5jlA6J-_CU"

def execute_replacement():
    client = get_gspread_client()
    spreadsheet = client.open_by_key(SHEET_ID)

    print("======================================================================")
    print("  EXECUTING EMPLOYER TAB REPLACEMENT & CONSOLIDATION")
    print("======================================================================")

    # 1. Verify staging worksheet exists
    try:
        ws_staging = spreadsheet.worksheet("Employers_Review_Staging")
        print("[Step 1] Found 'Employers_Review_Staging' tab.")
    except Exception as e:
        print(f"[ERROR] Could not find 'Employers_Review_Staging': {e}")
        return

    # 2. Add Sierra Pacific Industries branches if not already in staging
    staging_rows = ws_staging.get_all_values()
    existing_companies = {r[0].strip().lower() for r in staging_rows[1:] if r}
    
    if "sierra pacific industries" not in existing_companies:
        print("[Step 2] Migrating Sierra Pacific Industries (from Burney draft) to staging...")
        spi_rows = [
            [
                "Sierra Pacific Industries", "Sierra Pacific Industries Inc.", "Anderson Division & HQ",
                "19794 Riverside Ave", "Anderson", "CA", "96007", "(530) 378-8000", "",
                "Manufacturing & Forest Products", "18", "Case-by-case", "Safety-Sensitive Only",
                "Standard Pre-Employment", "None", "Not Required", "1 yr preferred", "$22.84 per hour",
                "Entry-level sawmill worker, green chain puller, lumber sorter, cleanup",
                "https://spi-ind.com/Employment",
                "Sawmill and forest products manufacturing. 1 yr work experience preferred. | Anderson; near I-5 & Riverside Ave.",
                "Yes", "Yes"
            ],
            [
                "Sierra Pacific Industries", "Sierra Pacific Industries Inc.", "Shasta Lake Division",
                "3791 Oasis Rd", "Shasta Lake", "CA", "96019", "(530) 275-8812", "",
                "Manufacturing & Forest Products", "18", "Case-by-case", "Safety-Sensitive Only",
                "Standard Pre-Employment", "None", "Not Required", "1 yr preferred", "$22.84 per hour",
                "Sawmill laborer, machinery operator helper, cleanup",
                "https://spi-ind.com/Employment",
                "Sawmill and forest products manufacturing. 1 yr work experience preferred. | Shasta Lake; Oasis Rd industrial corridor.",
                "Yes", "No"
            ],
            [
                "Sierra Pacific Industries", "Sierra Pacific Industries Inc.", "Burney Sawmill",
                "37559 CA-299", "Burney", "CA", "96013", "(530) 335-3681", "",
                "Manufacturing & Forest Products", "18", "Case-by-case", "Safety-Sensitive Only",
                "Standard Pre-Employment", "None", "Not Required", "1 yr preferred", "$22.84 per hour",
                "Sawmill laborer, green chain puller, millwright apprentice, cleanup",
                "https://spi-ind.com/Employment",
                "Sawmill and forest products manufacturing. 1 yr work experience preferred. | Burney sawmill along CA-299 corridor.",
                "Yes", "No"
            ]
        ]
        ws_staging.append_rows(spi_rows, value_input_option="USER_ENTERED")
        print(f" -> Added {len(spi_rows)} branches for Sierra Pacific Industries.")
    else:
        print("[Step 2] Sierra Pacific Industries already present in staging.")

    # 3. Rename 'Employers_Review_Staging' to 'Area Employers'
    print("[Step 3] Renaming 'Employers_Review_Staging' to 'Area Employers'...")
    # Check if a tab named 'Area Employers' already exists
    try:
        existing_target = spreadsheet.worksheet("Area Employers")
        print(" -> Existing 'Area Employers' found. Removing it before renaming.")
        spreadsheet.del_worksheet(existing_target)
    except Exception:
        pass

    ws_staging.update_title("Area Employers")
    print(" -> Successfully renamed worksheet to 'Area Employers'.")

    # 4. Remove obsolete tabs: 'Redding Area Employers' and 'Burney Area Employers (draft)'
    print("[Step 4] Removing legacy employer tabs...")
    for old_tab_name in ["Redding Area Employers", "Burney Area Employers (draft)"]:
        try:
            ws_old = spreadsheet.worksheet(old_tab_name)
            spreadsheet.del_worksheet(ws_old)
            print(f" -> Successfully removed legacy tab '{old_tab_name}'.")
        except Exception as e:
            print(f" -> Tab '{old_tab_name}' not found or already deleted: {e}")

    # 5. List current tabs in workbook
    worksheets = [ws.title for ws in spreadsheet.worksheets()]
    print(f"\n[Step 5] Workbook tabs now: {worksheets}")
    print("======================================================================")
    print("  CONSOLIDATION COMPLETE: 'Area Employers' IS NOW THE MASTER REGISTRY")
    print("======================================================================")

if __name__ == "__main__":
    execute_replacement()
