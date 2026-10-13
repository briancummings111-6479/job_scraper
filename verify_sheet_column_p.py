import sheets_sync

gc = sheets_sync.get_gspread_client()
ss = gc.open_by_key("1uGL7w8fpb5P0D-kNIPces9nOK4Ctt6Bfg5jlA6J-_CU")
TARGET_GID = 280720545
tab_name = "Automated_Posts"

try:
    ws = ss.worksheet(tab_name)
except Exception:
    matched = [w for w in ss.worksheets() if w.id == TARGET_GID]
    ws = matched[0] if matched else ss.sheet1

all_vals = ws.get_all_values()
print(f"Worksheet: '{ws.title}' (id: {ws.id})")
print(f"Total rows: {len(all_vals)}, Col count: {ws.col_count}")

header_row = all_vals[0] if all_vals else []
col_map = {c.strip().lower(): idx for idx, c in enumerate(header_row)}
status_idx = col_map.get("status", 27)

print(f"Header count: {len(header_row)}")
print(f"Status column header: '{header_row[status_idx]}' (index {status_idx})" if len(header_row) > status_idx else "Status column header: NOT YET APPENDED")

expired_rows = []
active_rows = []
company_rows = []

for i in range(1, len(all_vals)):
    r = all_vals[i]
    src = r[0].strip() if len(r) > 0 else ""
    title = r[1].strip() if len(r) > 1 else ""
    status = r[status_idx].strip() if len(r) > status_idx else ""
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
