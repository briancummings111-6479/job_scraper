import os
import re
import json
import time
import argparse
from datetime import datetime
from urllib.parse import urljoin, urlparse
import pandas as pd
from playwright.sync_api import sync_playwright

# Blacklisted senior/clinical roles that are not entry-level
TITLE_BLACKLIST = [
    r"\bgeneral manager\b", r"\bstore manager\b", r"\bdistrict manager\b", r"\bregional manager\b",
    r"\bdirector\b", r"\bvice president\b", r"\bphysician\b", r"\bdentist\b", r"\bpharmacist\b",
    r"\bregistered nurse\b", r"\brn\b", r"\bnurse practitioner\b", r"\battorney\b", r"\bcounsel\b",
    r"\bexecutive\b", r"\bcontroller\b", r"\baccountant\b", r"\bsoftware engineer\b", r"\barchitect\b"
]

# Non-job navigation labels
GENERIC_LABELS = [
    "apply", "apply now", "view job", "details", "learn more", "careers", "search jobs",
    "home", "about us", "privacy policy", "terms of use", "contact", "sign in", "login",
    "current associates", "explore jobs", "see all", "back", "next", "previous",
    "location", "map", "directions", "view map", "share", "save", "save job", "alert",
    "cookies", "cookie", "cookie settings", "cookies settings", "privacy settings"
]

# Positive entry-level indicators
ENTRY_LEVEL_KEYWORDS = [
    r"\bcashier\b", r"\bassociate\b", r"\bcrew\b", r"\bstocker\b", r"\bclerk\b", r"\bbarista\b",
    r"\bserver\b", r"\bcook\b", r"\bcooks\b", r"\bdishwasher\b", r"\bcustodian\b", r"\bjanitor\b",
    r"\bcleaner\b", r"\bcaregiver\b", r"\baide\b", r"\bassistant\b", r"\bdriver\b", r"\bcourier\b",
    r"\bpackage\b", r"\bwarehouse\b", r"\bloader\b", r"\bhandler\b", r"\bcustomer service\b",
    r"\bfront desk\b", r"\battendant\b", r"\bteam member\b", r"\bretail\b", r"\bsales\b",
    r"\boperator\b", r"\blaborer\b", r"\bmaintenance\b", r"\breceptionist\b", r"\bhelper\b",
    r"\bapprentice\b", r"\bspecialist\b", r"\bguest service\b"
]

LOCAL_GEO_INDICATORS = [
    "redding", "shasta", "96001", "96002", "96003", "anderson", "cottonwood", "palo cedro",
    "shasta lake", "coram", "keswick", "mountain gate", "bella vista"
]

def is_blacklisted_title(title):
    t_lower = title.lower()
    for pat in TITLE_BLACKLIST:
        if re.search(pat, t_lower):
            if "assistant" in t_lower or "lead" in t_lower or "shift" in t_lower:
                return False
            return True
    return False

def is_local_location(text, job_url=""):
    combined = (text + " " + job_url).lower()
    for geo in LOCAL_GEO_INDICATORS:
        if geo in combined:
            return True
    if "california" in combined or ", ca" in combined:
        return True
    return False

def extract_wage(text):
    match = re.search(r"\$\d{2}(?:\.\d{2})?(?:\s*(?:-|to)\s*\$\d{2}(?:\.\d{2})?)?(?:\s*\/\s*(?:hr|hour))?", text, re.IGNORECASE)
    if match:
        return match.group(0).strip()
    return ""

def extract_job_type(text):
    t = text.lower()
    if "part-time" in t or "part time" in t:
        return "Part-Time"
    elif "full-time" in t or "full time" in t:
        return "Full-Time"
    elif "seasonal" in t:
        return "Seasonal"
    elif "temporary" in t or "temp" in t:
        return "Temporary"
    return "Not Specified"

def scrape_employer(page, emp):
    name = emp["name"]
    url = emp["url"]
    print(f"\n[{name}] Loading {url[:70]}...", flush=True)
    
    jobs = []
    try:
        page.goto(url, timeout=25000, wait_until="domcontentloaded")
        page.wait_for_timeout(3500)
        
        try:
            page.evaluate("window.scrollBy(0, 500)")
            page.wait_for_timeout(1000)
        except Exception:
            pass

        anchors = page.eval_on_selector_all("a", """elements => elements.map(e => {
            let container = e.closest('li, tr, .job-card, .card, [data-ph-at-id], article, .direct_joblisting, .jobs-list-item') || e;
            return {
                text: e.innerText.trim(),
                href: e.href,
                containerText: container ? container.innerText.trim() : ''
            };
        }).filter(e => e.text.length > 2 && e.text.length < 110)""")
        
        seen_titles = set()
        for a in anchors:
            raw_title = a["text"].strip()
            href = a["href"].strip()
            container = a["containerText"]
            combined = (raw_title + " " + container).lower()

            # Ignore generic navigation or non-job links
            if raw_title.lower() in GENERIC_LABELS or len(raw_title) < 4:
                continue
            if "google.com/maps" in href or "maps.google" in href:
                continue
            # Ignore category count pills like "Store Associate (2)"
            if re.search(r"\(\d+\)$", raw_title):
                continue
            
            # Skip if blacklisted senior title
            if is_blacklisted_title(raw_title):
                continue

            # Must contain an entry-level keyword in title or container
            has_entry_keyword = any(re.search(pat, combined) for pat in ENTRY_LEVEL_KEYWORDS)
            if not has_entry_keyword:
                continue

            # Verify local geographic match
            if not is_local_location(combined, href):
                continue

            # Clean raw title from multi-line text or trailing ellipses
            lines = [l.strip() for l in raw_title.split('\n') if l.strip()]
            clean_title = lines[0] if lines else raw_title
            for l in lines:
                if any(w in l.lower() for w in ['crew', 'associate', 'cashier', 'teammate', 'technician', 'member', 'aide', 'caregiver', 'driver', 'worker', 'lead', 'stocker', 'server', 'cook']):
                    clean_title = l
                    break
            clean_title = re.sub(r"\s*\.\.\.\s*$", "", clean_title).strip()

            dedup_key = f"{name}_{clean_title.lower()}_{href}"
            if dedup_key in seen_titles:
                continue
            seen_titles.add(dedup_key)

            wage = extract_wage(container) or emp.get("starting_wage", "")
            job_type = extract_job_type(container)
            
            job_obj = {
                "source": "Direct Employer Portal",
                "job_title": clean_title,
                "company": name,
                "location": "Redding, CA",
                "pay": wage,
                "job_type_extracted": job_type,
                "shift_schedule": "",
                "experience": emp.get("work_experience", "Entry-Level"),
                "date_posted": datetime.now().strftime("%Y-%m-%d"),
                "industry": emp.get("industry", "General"),
                "job_url": href,
                "felon_friendly": emp.get("felon_friendly", "Unspecified"),
                "notes": emp.get("notes", "")
            }
            jobs.append(job_obj)

        print(f"[{name}] Extracted {len(jobs)} local opening(s).", flush=True)
    except Exception as e:
        print(f"[{name}] Scraping error: {e}", flush=True)
        
    return jobs

def run_group3_scraper(limit=None, target_company=None, headless=True):
    config_path = "output/group_3_employers.json"
    if not os.path.exists(config_path):
        import subprocess
        subprocess.run(["python", "scratch/extract_group3.py"], check=True)
        
    with open(config_path, "r", encoding="utf-8") as f:
        employers = json.load(f)

    if target_company:
        employers = [e for e in employers if target_company.lower() in e["name"].lower()]
        print(f"Filtered for company matching '{target_company}': {len(employers)} found.", flush=True)
    elif limit:
        employers = employers[:limit]
        print(f"Running on first {limit} employers.", flush=True)
    else:
        print(f"Running full Group 3 scan across all {len(employers)} employers.", flush=True)

    all_jobs = []
    start_time = time.time()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        for idx, emp in enumerate(employers, 1):
            print(f"\n--- Progress: {idx}/{len(employers)} ---", flush=True)
            emp_jobs = scrape_employer(page, emp)
            all_jobs.extend(emp_jobs)
            time.sleep(0.5)

        browser.close()

    elapsed = round(time.time() - start_time, 1)
    print(f"\n{'='*50}", flush=True)
    print(f"Scrape Complete in {elapsed}s!", flush=True)
    print(f"Total Live Jobs Harvested: {len(all_jobs)}", flush=True)

    if not all_jobs:
        print("No jobs found in this run.", flush=True)
        return

    unique_jobs = []
    seen = set()
    for j in all_jobs:
        key = (j["company"], j["job_title"], j["job_url"])
        if key not in seen:
            seen.add(key)
            unique_jobs.append(j)

    json_out = "output/group3_direct_jobs.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(unique_jobs, f, indent=2)
    print(f"Saved JSON to {json_out}", flush=True)

    df = pd.DataFrame(unique_jobs)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_out = f"output/direct_jobs_group3_{timestamp}.xlsx"
    latest_excel = "output/direct_jobs_group3_latest.xlsx"
    df.to_excel(excel_out, index=False)
    df.to_excel(latest_excel, index=False)
    print(f"Saved Excel reports to:\n  - {excel_out}\n  - {latest_excel}", flush=True)

    print(f"\n{'='*50}", flush=True)
    print("HARVEST SUMMARY BY EMPLOYER:", flush=True)
    company_counts = df["company"].value_counts()
    for comp, count in company_counts.items():
        print(f"  * {comp:30}: {count} jobs", flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Group 3 Pre-Filtered Employer Portals")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of employers to scrape")
    parser.add_argument("--company", type=str, default=None, help="Filter for specific employer name")
    parser.add_argument("--headful", action="store_true", help="Run browser in headful mode")
    args = parser.parse_args()

    run_group3_scraper(limit=args.limit, target_company=args.company, headless=not args.headful)
