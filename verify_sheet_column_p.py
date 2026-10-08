import sheets_sync

gc = sheets_sync.get_gspread_client()
ss = gc.open_by_key("1uGL7w8fpb5P0D-kNIPces9nOK4Ctt6Bfg5jlA6J-_CU")
ws = ss.worksheet("Redding Area Job Postings")
all_vals = ws.get_all_values()

print("Row 2 (Header) Col P:", all_vals[1][15] if len(all_vals[1]) > 15 else "MISSING")

expired_rows = []
active_rows = []
company_rows = []

for i in range(2, 207):
    r = all_vals[i]
    src = r[0].strip() if len(r) > 0 else ""
    title = r[1].strip() if len(r) > 1 else ""
    status = r[15].strip() if len(r) > 15 else ""
    if src.lower() == "company":
        company_rows.append((i+1, title, status))
    elif status == "Expired":
        expired_rows.append((i+1, src, title))
    elif status == "Active":
        active_rows.append((i+1, src, title))

print(f"\nTotal Company rows: {len(company_rows)}")
print("Company status values (should be blank):", set(s for _, _, s in company_rows))
print(f"Sample Company rows: {company_rows[:3]}")

print(f"\nTotal Expired rows: {len(expired_rows)}")
print(f"Sample Expired rows:")
for r, s, t in expired_rows[:5]:
    print(f"  Row {r}: [{s}] {t}")

print(f"\nTotal Active rows: {len(active_rows)}")
print(f"Sample Active rows:")
for r, s, t in active_rows[:5]:
    print(f"  Row {r}: [{s}] {t}")
