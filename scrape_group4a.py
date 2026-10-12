import os
import re
import json
import time
import argparse
from datetime import datetime
from urllib.parse import urljoin, urlparse
import pandas as pd
from playwright.sync_api import sync_playwright

TITLE_BLACKLIST = [
    r"\bgeneral manager\b", r"\bstore manager\b", r"\bdistrict manager\b", r"\bregional manager\b",
    r"\bdirector\b", r"\bvice president\b", r"\bphysician\b", r"\bdentist\b", r"\bpharmacist\b",
    r"\bregistered nurse\b", r"\brn\b", r"\bnurse practitioner\b", r"\battorney\b", r"\bcounsel\b",
    r"\bexecutive\b", r"\bcontroller\b", r"\baccountant\b", r"\bsoftware engineer\b", r"\barchitect\b"
]

GENERIC_LABELS = [
    "apply", "apply now", "view job", "details", "learn more", "careers", "search jobs",
    "home", "about us", "privacy policy", "terms of use", "contact", "sign in", "login",
    "current associates", "explore jobs", "see all", "back", "next", "previous",
    "location", "map", "directions", "view map", "share", "save", "save job", "alert",
    "cookies", "cookie", "cookie settings", "cookies settings", "privacy settings",
    "manage options", "manage services", "skip navigation", "skip to content", "overview",
    "job search", "job alerts", "submit a job", "staffing & recruiting"
]

ENTRY_LEVEL_KEYWORDS = [
    r"\bcashier\b", r"\bassociate\b", r"\bcrew\b", r"\bstocker\b", r"\bclerk\b", r"\bbarista\b",
    r"\bserver\b", r"\bcook\b", r"\bcooks\b", r"\bdishwasher\b", r"\bcustodian\b", r"\bjanitor\b",
    r"\bcleaner\b", r"\bcaregiver\b", r"\baide\b", r"\bassistant\b", r"\bdriver\b", r"\bcourier\b",
    r"\bpackage\b", r"\bwarehouse\b", r"\bloader\b", r"\bhandler\b", r"\bcustomer service\b",
    r"\bfront desk\b", r"\battendant\b", r"\bteam member\b", r"\bretail\b", r"\bsales\b",
    r"\boperator\b", r"\blaborer\b", r"\bmaintenance\b", r"\breceptionist\b", r"\bhelper\b",
    r"\bapprentice\b", r"\bspecialist\b", r"\bguest service\b", r"\blifeguard\b", r"\bdock\b",
    r"\bdeckhand\b", r"\brecycling\b", r"\bfacility\b", r"\bhouseboat\b", r"\bline cook\b",
    r"\bprep cook\b", r"\bbusser\b", r"\bhost\b", r"\bhostess\b", r"\blight industrial\b"
]

# Refined direct career links for specific Group 4A employers
LOCAL_SPECIFIC_URL_OVERRIDES = {
    "Peloria Bridge Bay LLC": "https://jobs.gusto.com/boards/peloria-bridge-bay-llc-9150dd84-6f52-4751-bb05-0952093554b7",
    "O2 Employment": "https://jobs.o2employmentservices.com/job-board/",
    "Custom Personnel": "https://www.careers-page.com/custom-personnel",
    "From the Hearth Bakery & Cafe": "https://fromthehearthkp.com/careers",
    "Waterworks Park": "https://ats.bbsi.com/applicant/job-list/baeeda24-29e0-4282-a83f-b70e7f9ff3a0",
    "Hambro Recycling": "https://www.hambrocrvbuyback.com/jobs",
    "GLOBAL BUILDING SERVICES, INC.": "https://global-building-services-inc.epayhire.com/",
    "COMMUNITY BEHAVIORAL HEALTH": "https://www.cbh.us/we-are-hiring"
}

def is_blacklisted_title(title):
    t_lower = title.lower()
    for pat in TITLE_BLACKLIST:
        if re.search(pat, t_lower):
            if "assistant" in t_lower or "lead" in t_lower or "shift" in t_lower:
                return False
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

def scrape_local_employer(page, emp):
    name = emp["name"]
    # Use override URL if available for high accuracy
    url = LOCAL_SPECIFIC_URL_OVERRIDES.get(name, emp["url"])
    print(f"\n[{name}] Loading {url[:70]}...", flush=True)

    jobs = []
    try:
        page.goto(url, timeout=22000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        try:
            page.evaluate("window.scrollBy(0, 600)")
            page.wait_for_timeout(1000)
        except Exception:
            pass

        # Strategy: capture link cards or listing elements
        anchors = page.eval_on_selector_all("a", """elements => elements.map(e => {
            let container = e.closest('li, tr, .job-card, .card, article, .job-item, .posting, [data-testid="job-card"]') || e;
            return {
                text: e.innerText.trim(),
                href: e.href || '',
                containerText: container ? container.innerText.trim() : ''
            };
        }).filter(e => e.text.length > 2 && e.text.length < 120)""")

        seen_titles = set()
        for a in anchors:
            raw_title = a["text"].strip()
            href = a["href"].strip()
            container = a["containerText"]
            combined = (raw_title + " " + container).lower()

            if raw_title.lower() in GENERIC_LABELS or len(raw_title) < 4:
                continue
            if "google.com/maps" in href or "maps.google" in href or not href.startswith("http"):
                continue
            if re.search(r"\(\d+\)$", raw_title):
                continue
            if is_blacklisted_title(raw_title):
                continue

            # Must match entry level keyword
            has_entry_keyword = any(re.search(pat, combined) for pat in ENTRY_LEVEL_KEYWORDS)
            if not has_entry_keyword:
                continue

            # Clean raw title
            lines = [l.strip() for l in raw_title.split('\n') if l.strip()]
            clean_title = lines[0] if lines else raw_title
            for l in lines:
                if any(w in l.lower() for w in ['maintenance', 'attendant', 'crew', 'associate', 'cashier', 'deckhand', 'cleaner', 'driver', 'worker', 'server', 'cook', 'aide', 'assistant']):
                    clean_title = l
                    break
            clean_title = re.sub(r"^\d+-\s*", "", clean_title) # Strip job IDs like "9016-Facility..."
            clean_title = re.sub(r"\s*\.\.\.\s*$", "", clean_title).strip()

            dedup_key = f"{name}_{clean_title.lower()}_{href}"
            if dedup_key in seen_titles:
                continue
            seen_titles.add(dedup_key)

            wage = extract_wage(container) or emp.get("starting_wage", "")
            job_type = extract_job_type(container)

            job_obj = {
                "source": "Local Employer Portal",
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

def run_group4a_scraper(limit=None, target_company=None, headless=True):
    config_path = "output/group_4a_employers.json"
    if not os.path.exists(config_path):
        import subprocess
        subprocess.run(["python", "scratch/extract_group4a.py"], check=True)

    with open(config_path, "r", encoding="utf-8") as f:
        employers = json.load(f)

    if target_company:
        employers = [e for e in employers if target_company.lower() in e["name"].lower()]
        print(f"Filtered for company matching '{target_company}': {len(employers)} found.", flush=True)
    elif limit:
        employers = employers[:limit]
        print(f"Running on first {limit} local employers.", flush=True)
    else:
        print(f"Running full Group 4A local scan across all {len(employers)} employers.", flush=True)

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
            emp_jobs = scrape_local_employer(page, emp)
            all_jobs.extend(emp_jobs)
            time.sleep(0.5)

        browser.close()

    elapsed = round(time.time() - start_time, 1)
    print(f"\n{'='*50}", flush=True)
    print(f"Local Scrape Complete in {elapsed}s!", flush=True)
    print(f"Total Local Jobs Harvested: {len(all_jobs)}", flush=True)

    if not all_jobs:
        print("No jobs found in this run.", flush=True)
        return

    # Deduplicate
    unique_jobs = []
    seen = set()
    for j in all_jobs:
        key = (j["company"], j["job_title"], j["job_url"])
        if key not in seen:
            seen.add(key)
            unique_jobs.append(j)

    # Save to Group 4A JSON
    json_out = "output/group4a_direct_jobs.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(unique_jobs, f, indent=2)
    print(f"Saved JSON to {json_out}", flush=True)

    # Save to Group 4A Excel
    df_4a = pd.DataFrame(unique_jobs)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_out = f"output/direct_jobs_group4a_{timestamp}.xlsx"
    latest_excel = "output/direct_jobs_group4a_latest.xlsx"
    df_4a.to_excel(excel_out, index=False)
    df_4a.to_excel(latest_excel, index=False)
    print(f"Saved Excel reports to:\n  - {excel_out}\n  - {latest_excel}", flush=True)

    # Also build the master combined dataset: Group 3 + Group 4A!
    try:
        combined_jobs = []
        if os.path.exists("output/group3_direct_jobs.json"):
            with open("output/group3_direct_jobs.json", "r", encoding="utf-8") as f:
                combined_jobs.extend(json.load(f))
        combined_jobs.extend(unique_jobs)

        # Deduplicate combined
        dedup_combined = []
        seen_comb = set()
        for j in combined_jobs:
            k = (j["company"], j["job_title"], j["job_url"])
            if k not in seen_comb:
                seen_comb.add(k)
                dedup_combined.append(j)

        df_comb = pd.DataFrame(dedup_combined)
        master_excel = "output/direct_jobs_master_latest.xlsx"
        df_comb.to_excel(master_excel, index=False)
        print(f"\n[MASTER REPORT] Saved {len(dedup_combined)} combined local jobs to {master_excel}!", flush=True)
    except Exception as e:
        print(f"Error merging master report: {e}", flush=True)

    print(f"\n{'='*50}", flush=True)
    print("LOCAL HARVEST SUMMARY BY EMPLOYER:", flush=True)
    company_counts = df_4a["company"].value_counts()
    for comp, count in company_counts.items():
        print(f"  * {comp:30}: {count} jobs", flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Group 4A Local Shasta County Employer Sites")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of employers to scrape")
    parser.add_argument("--company", type=str, default=None, help="Filter for specific employer name")
    parser.add_argument("--headful", action="store_true", help="Run browser in headful mode")
    args = parser.parse_args()

    run_group4a_scraper(limit=args.limit, target_company=args.company, headless=not args.headful)
