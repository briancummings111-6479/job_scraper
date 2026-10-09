import os
import re
import csv
import pandas as pd
from scrapper import (
    generate_key_description,
    extract_pay,
    clean_job_title,
    clean_location_str
)

excel_path = r"C:\Users\brian\job_scraper\output\redding_only_20261008_171952.xlsx"
csv_path = r"C:\Users\brian\job_scraper\output\redding_only_20261008_171952.csv"
backup_csv = r"C:\Users\brian\job_scraper\output\redding_only_20261008_171952_corrupted_backup.csv"

# Backup corrupted csv
if not os.path.exists(backup_csv):
    import shutil
    shutil.copy2(csv_path, backup_csv)
    print(f"Backed up corrupted CSV to: {backup_csv}")

df_orig = pd.read_excel(excel_path)
print(f"Loaded {len(df_orig)} raw records from Excel.")

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
    teen = bool(r["Teen Friendly"])
    source = str(r["Source"]).strip()

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

    # Clean location
    clean_loc = re.sub(r'\s*,\s*', ', ', loc)
    clean_loc = re.sub(r'Redding,\s*CA,\s*Redding,\s*CA', 'Redding, CA', clean_loc, flags=re.IGNORECASE)
    clean_loc = re.sub(r'Redding,\s*CA\s+96002,\s*Redding,\s*CA', 'Redding, CA 96002', clean_loc, flags=re.IGNORECASE)
    clean_loc = re.sub(r',\s*Starting Pay,\s*CA', '', clean_loc, flags=re.IGNORECASE)
    clean_loc = clean_location_str(clean_loc)

    # Clean title
    clean_t = clean_job_title(title)

    # Clean pay: If Snagajob algorithmic $18.00 or $48.08, extract real pay from text
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
                real_pay = "Unstated"

    # Clean Requirements: Semicolons only, clean spacing
    clean_exp = exp.replace(",", ";")
    clean_exp = re.sub(r';\s*;', ';', clean_exp)
    clean_exp = re.sub(r'\s*;\s*', '; ', clean_exp).strip('; ')

    # Clean Summary: generate concise 2-sentence summary
    summary = generate_key_description(
        title=clean_t,
        company=comp,
        location=clean_loc,
        sector=sector,
        job_type=job_type,
        schedule=shift,
        pay=real_pay,
        requirements=clean_exp
    )

    # Clean, accurate column schema matching Google Sheet specification:
    cleaned_rows.append({
        "Source": source,
        "Job Title": clean_t,
        "Company": comp,
        "Location": clean_loc,
        "Pay Rate": real_pay,
        "Full / Part Time": job_type,
        "Schedule / Shift": shift,
        "Experience / Requirements": clean_exp,
        "Job Description Summary": summary,
        "Date Posted": posted_date,
        "Job Posting": url,
        "Industry Sector": sector,
        "Last Updated": str(r["Last Updated"]),
        "Teen Friendly": teen
    })

df_clean = pd.DataFrame(cleaned_rows)

# Save repaired clean Excel
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    df_clean.to_excel(writer, index=False, sheet_name='Active Job Openings')
print(f"[OK] Repaired Excel saved to: {excel_path} ({len(df_clean)} rows, {len(df_clean.columns)} columns)")

# Save repaired clean CSV
df_clean.to_csv(csv_path, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_MINIMAL)
print(f"[OK] Repaired CSV saved to: {csv_path} ({len(df_clean)} rows, {len(df_clean.columns)} columns)")

# Verify saved CSV
verify_df = pd.read_csv(csv_path)
print(f"Verified CSV Shape: {verify_df.shape}")
print("Verified CSV Columns:", list(verify_df.columns))
print(f"Unnamed columns in verified CSV: {[c for c in verify_df.columns if 'Unnamed' in c]}")
print(f"Null values in verified CSV:\n{verify_df.isnull().sum()}")
