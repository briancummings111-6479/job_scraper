import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import firestore_sync
import sheets_sync
from scrapper import is_rejected_job, is_expired_job_content, clean_job_title, clean_location_str, is_shasta_county_location, extract_key_requirements, determine_industry

def fetch_on_page_description(driver, url, source="Snagajob"):
    try:
        driver.get(url)
        time.sleep(3)
        page_source = driver.page_source
        if is_expired_job_content(page_source):
            return None, True # expired
        
        # 1. Snagajob
        if "snagajob.com" in url.lower():
            try:
                desc_headings = driver.find_elements(By.XPATH, "//h2[contains(text(), 'Job Description')] | //h3[contains(text(), 'Job Description')] | //div[contains(text(), 'About this job')]")
                for dh in desc_headings:
                    parent_box = dh.find_element(By.XPATH, "..")
                    d_text = parent_box.text.strip()
                    d_text = re.sub(r'^(?:About this job\s*|Job Description\s*)+', '', d_text, flags=re.IGNORECASE).strip()
                    if d_text and len(d_text) > 30:
                        return d_text, False
            except:
                pass

        # 2. Indeed
        if "indeed.com" in url.lower():
            for sel in ["#jobDescriptionText", "div.jobsearch-jobDescriptionText", "[data-testid='job-description']"]:
                try:
                    el = driver.find_element(By.CSS_SELECTOR, sel)
                    d_text = el.text.strip()
                    if d_text and len(d_text) > 30:
                        return d_text, False
                except:
                    continue

        # 3. Fallback generic
        for sel in ["div[class*='description']", "section[class*='description']", "article"]:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                d_text = el.text.strip()
                if d_text and len(d_text) > 30:
                    return d_text, False
            except:
                continue

    except Exception as e:
        print(f"  [WARN] Error fetching {url}: {e}")
    return None, False

def main():
    print("Initializing browser to verify on-page job descriptions...")
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    db = firestore_sync.get_firestore_client()
    docs = list(db.collection('jobs').stream())
    print(f"Total Firestore documents: {len(docs)}")

    to_delete = []
    to_update = []
    retained = []

    for d in docs:
        data = d.to_dict()
        doc_id = d.id
        title = clean_job_title(data.get('title', ''))
        company = data.get('company', '')
        loc = clean_location_str(data.get('location', 'Redding, CA'))
        pay = data.get('pay', '')
        url = data.get('jobUrl') or data.get('url') or ''
        source = data.get('source', 'Direct')
        stored_desc = str(data.get('description') or '')

        print(f"\nChecking: {title} at {company} ({url})")
        on_page_desc, is_exp = (None, False)
        if url and url.startswith("http"):
            on_page_desc, is_exp = fetch_on_page_description(driver, url, source)

        if is_exp:
            print(f"  -> [DELETE] Expired job on page: {title}")
            to_delete.append((doc_id, title, company, "Expired on live page"))
            continue

        active_desc = on_page_desc if on_page_desc else stored_desc
        is_rej, rej_reason = is_rejected_job(title, company, active_desc, pay=pay, location=loc)
        if is_rej:
            print(f"  -> [DELETE] Rejected non-entry-level / OTR / qualification: {title} ({rej_reason})")
            to_delete.append((doc_id, title, company, rej_reason))
            continue

        # Attempt Gemini semantic analysis if description is present
        gemini_res = None
        if active_desc and len(active_desc) > 30:
            try:
                from gemini_parser import analyze_job_with_gemini
                gemini_res = analyze_job_with_gemini(
                    title=title,
                    company=company,
                    location=loc,
                    description_text=active_desc,
                    raw_pay=pay or "N/A"
                )
            except Exception:
                gemini_res = None

        if gemini_res:
            if not gemini_res.is_entry_level:
                print(f"  -> [DELETE] Rejected via Gemini: {title} ({gemini_res.rejection_reason})")
                to_delete.append((doc_id, title, company, gemini_res.rejection_reason or "Non-entry level"))
                continue
            sector = gemini_res.sector
            exp_req = gemini_res.experience_requirements
            gemini_pay = gemini_res.pay_rate
        else:
            # If retained, update with on-page description and clean requirements
            sector = determine_industry(title, company, active_desc)
            exp_req = extract_key_requirements(
                text=active_desc,
                existing_exp="",
                job_dict={"title": title, "company": company, "sector": sector, "location": loc}
            )
            gemini_pay = None

        updates = {}
        if on_page_desc and on_page_desc != stored_desc:
            updates['description'] = on_page_desc
        if data.get('experience') != exp_req:
            updates['experience'] = exp_req
            updates['requirements'] = exp_req
        if data.get('sector') != sector:
            updates['sector'] = sector
            updates['category'] = sector
        if gemini_pay and gemini_pay != "N/A" and (not pay or pay == "N/A"):
            updates['pay'] = gemini_pay

        if updates:
            to_update.append((doc_id, updates, title))
            print(f"  -> [UPDATE] {title}: updated fields {list(updates.keys())}")
        else:
            print(f"  -> [OK] {title}")
        retained.append((doc_id, title, company))

    driver.quit()

    print(f"\n{'='*50}")
    print(f"SUMMARY:")
    print(f"  To Delete: {len(to_delete)}")
    print(f"  To Update: {len(to_update)}")
    print(f"  Retained:  {len(retained)}")
    print(f"{'='*50}")

    if to_delete:
        print("\nDeleting rejected jobs from Firestore...")
        for item in to_delete:
            db.collection('jobs').document(item[0]).delete()
            print(f"  Deleted: {item[1]} at {item[2]} ({item[3]})")

    if to_update:
        print("\nUpdating enriched jobs in Firestore...")
        for doc_id, fields, title in to_update:
            db.collection('jobs').document(doc_id).update(fields)
            print(f"  Updated: {title}")

    print("\nSyncing updated jobs to Google Sheets (Automated_Posts)...")
    try:
        final_docs = list(db.collection('jobs').stream())
        sheet_payload = []
        for d in final_docs:
            d_dict = d.to_dict()
            if d_dict.get('status', 'active') == 'active':
                sheet_payload.append({
                    "job_title": d_dict.get("title", ""),
                    "company": d_dict.get("company", ""),
                    "location": d_dict.get("location", "Redding, CA"),
                    "industry": d_dict.get("sector") or d_dict.get("category", "Other"),
                    "pay": d_dict.get("pay", "N/A"),
                    "job_type_extracted": d_dict.get("jobType", "N/A"),
                    "shift_schedule": d_dict.get("schedule") or d_dict.get("shift", "N/A"),
                    "experience": d_dict.get("experience", "N/A"),
                    "requirements": d_dict.get("requirements", "N/A"),
                    "description": d_dict.get("description", "N/A"),
                    "job_url": d_dict.get("jobUrl") or d_dict.get("url", ""),
                    "source": d_dict.get("source", "Direct"),
                    "date_posted": d_dict.get("datePosted", "")
                })
        sheets_sync.update_google_sheet(sheet_payload)
        print("[SHEETS] Google Sheets (Automated_Posts) updated successfully!")
    except Exception as e:
        print(f"[SHEETS] Sync warning: {e}")

    print("\nEnrichment complete.")

if __name__ == "__main__":
    main()
