import os
import re
import csv
import sys
import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

sys.stdout.reconfigure(encoding='utf-8')

from scrapper import (
    generate_key_description,
    extract_pay,
    clean_job_title,
    clean_location_str,
    evaluate_hs_ok
)

excel_path = r"C:\Users\brian\job_scraper\output\redding_only_20261008_171952.xlsx"
csv_path = r"C:\Users\brian\job_scraper\output\redding_only_20261008_171952.csv"
backup_csv = r"C:\Users\brian\job_scraper\output\redding_only_20261008_171952_corrupted_backup.csv"

# Backup corrupted csv if not already backed up
if not os.path.exists(backup_csv):
    import shutil
    shutil.copy2(csv_path, backup_csv)
    print(f"Backed up corrupted CSV to: {backup_csv}")

df_orig = pd.read_excel(excel_path)
print(f"Loaded {len(df_orig)} records from Excel.")

cleaned_rows = []
rejected_log = []

for idx, r in df_orig.iterrows():
    title = str(r["Job Title"]).strip()
    comp = str(r["Company"]).strip()
    loc = str(r["Location"]).strip()
    raw_pay = str(r["Pay Rate"]).strip()
    job_type = str(r["Full / Part Time"]).strip()
    shift = str(r["Schedule / Shift"]).strip()
    exp = str(r["Experience / Requirements"]).strip()
    raw_desc = str(r["Job Description Summary"]).strip()
    posted_date = str(r["Date Posted"]).strip()
    url = str(r["Job Posting"]).strip()
    sector = str(r["Industry Sector"]).strip()
    raw_hs_ok = str(r.get("H.S. OK", r.get("Teen Friendly", ""))).strip()
    source = str(r["Source"]).strip()
    last_upd = str(r["Last Updated"]).strip()

    t_lower = title.lower()
    c_lower = comp.lower()
    d_lower = raw_desc.lower()

    # 1. Reject specialized medical doctor / oncologist / locums
    if any(k in t_lower for k in ["oncologist", "hematologist", "physician", "doctor", "surgeon", "locums"]):
        rejected_log.append((idx + 2, title, comp, "Specialized Medical Physician / Oncologist"))
        continue

    # 2. Reject remote / telehealth
    if any(k in t_lower for k in ["telehealth", "telecommute", "100% remote"]) or "telehealth" in d_lower[:200]:
        rejected_log.append((idx + 2, title, comp, "Remote / Telehealth position"))
        continue

    # 3. Reject OTR / Long haul / Commercial CDL A
    if any(k in t_lower for k in ["class a", "cdl a", "cdl-a", "cdl required", "inexperienced drivers for the west coast", "owner operator", "otr"]):
        rejected_log.append((idx + 2, title, comp, "Commercial CDL-A / OTR Truck Driving"))
        continue

    # 4. Reject out-of-area locations (e.g. Holmdel NJ)
    if "holmdel" in loc.lower() or "nj" in loc.lower():
        rejected_log.append((idx + 2, title, comp, f"Out of area location ({loc})"))
        continue

    # 5. Reject compensation exceeding $75k annual entry-level ceiling
    if any(k in raw_pay for k in ["80,000", "220,000"]) or "lf sales rep" in t_lower:
        rejected_log.append((idx + 2, title, comp, f"Exceeds entry-level annual pay ceiling ({raw_pay})"))
        continue

    # Clean location
    clean_loc = re.sub(r'\s*,\s*', ', ', loc)
    clean_loc = re.sub(r'Redding,\s*CA,\s*Redding,\s*CA', 'Redding, CA', clean_loc, flags=re.IGNORECASE)
    clean_loc = re.sub(r'Redding,\s*CA\s+96002,\s*Redding,\s*CA', 'Redding, CA 96002', clean_loc, flags=re.IGNORECASE)
    clean_loc = re.sub(r',\s*Starting Pay,\s*CA', '', clean_loc, flags=re.IGNORECASE)
    clean_loc = clean_location_str(clean_loc)

    # Clean title
    clean_t = clean_job_title(title)

    # Clean pay: leave blank if unstated
    real_pay = raw_pay
    if source == "Snagajob" and raw_pay in ["$18.00", "$48.08"]:
        desc_pay = extract_pay(raw_desc)
        if desc_pay and not any(art in desc_pay.lower() for art in ["53.85", "112,000", "115,000", "100,000", "48.08", "55.29", "18.00"]):
            real_pay = desc_pay
        elif desc_pay and "18.00" in desc_pay:
            real_pay = desc_pay
        else:
            wage_matches = re.findall(r'\$\d+(?:\.\d{2})?\s*(?:-|to)\s*\$\d+(?:\.\d{2})?(?:\s*(?:per\s+hour|\/hr|hr))?', raw_desc)
            if wage_matches:
                real_pay = wage_matches[0]
            else:
                real_pay = ""

    if not real_pay or str(real_pay).strip().lower() in ['n/a', 'none', '', 'unstated', 'nan']:
        real_pay = ""

    # Clean Requirements: Semicolons only, clean spacing
    clean_exp = exp.replace(",", ";")
    clean_exp = re.sub(r';\s*;', ';', clean_exp)
    clean_exp = re.sub(r'\s*;\s*', '; ', clean_exp).strip('; ')

    # Evaluate H.S. OK ('✅' for pass, '❌' for fail, '' for unknown)
    hs_ok = evaluate_hs_ok(
        title=clean_t,
        company=comp,
        text=raw_desc,
        requirements=clean_exp,
        job_type=job_type,
        shift=shift
    )

    # Clean Summary: generate concise 2-sentence summary
    summary = generate_key_description(
        title=clean_t,
        company=comp,
        location=clean_loc,
        sector=sector,
        job_type=job_type,
        schedule=shift,
        pay=real_pay if real_pay else "Unstated",
        requirements=clean_exp
    )

    # Exact 14-Column Master Layout matching Google Sheet and Career Miner App:
    # Col A (1): Source
    # Col B (2): Job Title
    # Col C (3): Company
    # Col D (4): Location
    # Col E (5): Pay Rate (blank if unstated)
    # Col F (6): Full / Part Time
    # Col G (7): Schedule / Shift
    # Col H (8): Experience / Requirements
    # Col I (9): H.S. OK (✅, ❌, or blank)
    # Col J (10): Job Description Summary
    # Col K (11): Date Posted
    # Col L (12): Job Posting
    # Col M (13): Industry Sector
    # Col N (14): Last Updated
    cleaned_rows.append({
        "Source": source,
        "Job Title": clean_t,
        "Company": comp,
        "Location": clean_loc,
        "Pay Rate": real_pay,
        "Full / Part Time": job_type,
        "Schedule / Shift": shift,
        "Experience / Requirements": clean_exp,
        "H.S. OK": hs_ok,
        "Job Description Summary": summary,
        "Date Posted": posted_date,
        "Job Posting": url,
        "Industry Sector": sector,
        "Last Updated": last_upd
    })

df_clean = pd.DataFrame(cleaned_rows)
print(f"Total valid cleaned rows: {len(df_clean)}")
if rejected_log:
    print(f"Rejected {len(rejected_log)} rows:")
    for rj in rejected_log:
        print(f"  - {rj[1]} at {rj[2]}: {rj[3]}")

# Master column order confirmation
expected_columns = [
    "Source", "Job Title", "Company", "Location", "Pay Rate",
    "Full / Part Time", "Schedule / Shift", "Experience / Requirements",
    "H.S. OK", "Job Description Summary", "Date Posted",
    "Job Posting", "Industry Sector", "Last Updated"
]
df_clean = df_clean[expected_columns]

# Save styled Excel
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    df_clean.to_excel(writer, index=False, sheet_name='Active Job Openings')
    ws = writer.sheets['Active Job Openings']
    ws.freeze_panes = 'A2'

    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1E293B', end_color='1E293B', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    for col_num in range(1, len(df_clean.columns) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=False)
        cell.border = thin_border
        ws.row_dimensions[1].height = 26

    for col_idx, col in enumerate(df_clean.columns, start=1):
        max_len = len(str(col))
        col_letter = get_column_letter(col_idx)

        for row_idx in range(2, len(df_clean) + 2):
            cell = ws.cell(row=row_idx, column=col_idx)
            val_str = str(cell.value or '')
            
            if col == 'Job Posting' and val_str.startswith(('http://', 'https://')):
                cell.hyperlink = val_str
                cell.font = Font(name='Calibri', size=10, color='2563EB', underline='single')
            elif col == 'H.S. OK':
                cell.alignment = Alignment(horizontal='center', vertical='center')
                if val_str == '✅':
                    cell.font = Font(name='Segoe UI Emoji', size=11, bold=True, color='16A34A')
                elif val_str == '❌':
                    cell.font = Font(name='Segoe UI Emoji', size=11, bold=True, color='DC2626')
                else:
                    cell.font = Font(name='Calibri', size=10)
            else:
                cell.font = Font(name='Calibri', size=10)

            cell.border = thin_border
            if col != 'H.S. OK':
                cell.alignment = Alignment(vertical='center')

            if len(val_str) > max_len:
                max_len = len(val_str)

        if col == 'H.S. OK':
            ws.column_dimensions[col_letter].width = 12
        else:
            ws.column_dimensions[col_letter].width = max(12, min(max_len + 3, 45))

print(f"[OK] Repaired Excel saved to: {excel_path} ({len(df_clean)} rows, {len(df_clean.columns)} columns)")

# Save repaired clean CSV
df_clean.to_csv(csv_path, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_MINIMAL)
print(f"[OK] Repaired CSV saved to: {csv_path} ({len(df_clean)} rows, {len(df_clean.columns)} columns)")

# Verification step
verify_df = pd.read_csv(csv_path)
print(f"Verified CSV Shape: {verify_df.shape}")
print("Verified CSV Columns:")
for i, col in enumerate(verify_df.columns, 1):
    col_letter = chr(64 + i)
    print(f"  Col {col_letter} ({i}): {col}")
print(f"Unnamed columns: {[c for c in verify_df.columns if 'Unnamed' in c]}")
print(f"Null count:\n{verify_df.isnull().sum()}")
print("\nSample Row 1:")
for k, v in verify_df.iloc[0].to_dict().items():
    print(f"  {k}: {str(v)[:70]}")
