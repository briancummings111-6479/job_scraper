import hashlib
import os
import re
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, firestore

try:
    from scrapper import is_rejected_job, is_expired_job_content, clean_job_title
except ImportError:
    def clean_job_title(title: str) -> str:
        if not title:
            return ""
        cleaned = re.sub(r'[\r\n\s]*-?\s*job post.*$', '', str(title), flags=re.IGNORECASE)
        return cleaned.strip()

    def is_expired_job_content(text: str) -> bool:
        if not text:
            return False
        for p in ["job has expired", "no longer available", "employer is not accepting applications", "not actively hiring"]:
            if p in str(text).lower():
                return True
        return False

    def is_rejected_job(title: str, company: str = "", description: str = "") -> tuple:
        return False, ""

def get_firestore_client():
    if firebase_admin._apps:
        return firestore.client()

    project_id = os.environ.get("FIREBASE_PROJECT_ID")
    client_email = os.environ.get("FIREBASE_CLIENT_EMAIL")
    private_key = os.environ.get("FIREBASE_PRIVATE_KEY")

    if project_id and client_email and private_key:
        cleaned_key = private_key.replace("\\n", "\n")
        cert_dict = {
            "type": "service_account",
            "project_id": project_id,
            "private_key": cleaned_key,
            "client_email": client_email,
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        cred = credentials.Certificate(cert_dict)
        firebase_admin.initialize_app(cred)
    elif os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()

    return firestore.client()

def generate_job_id(source: str, company: str, title: str, location: str) -> str:
    raw_key = f"{source.lower()}_{company.lower()}_{title.lower()}_{location.lower()}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:20]

def parse_job_requirements(job: dict) -> dict:
    title = str(job.get("job_title", "")).strip()
    company = str(job.get("company", "")).strip()
    location = str(job.get("location", "Redding, CA")).strip()
    experience = str(job.get("experience") or job.get("requirements") or "").strip()
    description = str(job.get("description") or "").strip()

    full_text = f"{title} {company} {location} {experience} {description}".lower()

    # 1. Drug Testing
    requires_drug_test = bool(
        "drug test" in full_text or 
        "drug screen" in full_text or 
        "drug-free" in full_text or
        "substance screen" in full_text
    )

    # 2. Background Check
    requires_background_check = bool(
        "background check" in full_text or 
        "criminal background" in full_text or 
        "livescan" in full_text or 
        "fingerprint" in full_text
    )

    # 3. Driver's License & CDL
    requires_driver_license = bool(
        "driver's license" in full_text or 
        "drivers license" in full_text or 
        "valid driver" in full_text or 
        "clean driving record" in full_text or 
        "cdl" in full_text
    )

    driver_license_type = "None"
    if requires_driver_license:
        if "cdl-a" in full_text or "class a" in full_text:
            driver_license_type = "Commercial Class A (CDL-A)"
        elif "cdl-b" in full_text or "class b" in full_text:
            driver_license_type = "Commercial Class B (CDL-B)"
        else:
            driver_license_type = "Class C (Standard)"

    # 4. High School Diploma / GED
    requires_hs_ged = bool(
        "high school diploma" in full_text or 
        "ged" in full_text or 
        "high school equivalent" in full_text
    )

    # 5. Age & Youth Friendly
    min_age = 18
    if "21 years" in full_text or "21 or older" in full_text or "at least 21" in full_text or "21+" in full_text:
        min_age = 21
    elif "16 years" in full_text or "16 or older" in full_text or "at least 16" in full_text or "16+" in full_text or "minor" in full_text or "youth" in full_text or "teen" in full_text:
        min_age = 16

    is_youth_friendly = bool(min_age < 18 or "youth" in full_text or "teen" in full_text or "16+" in full_text or "student" in full_text)

    # 6. Shasta County Neighborhoods / Zones
    neighborhood = None
    if "downtown" in full_text:
        neighborhood = "Downtown Redding"
    elif "anderson" in full_text:
        neighborhood = "Anderson"
    elif "shasta lake" in full_text:
        neighborhood = "City of Shasta Lake"
    elif "cottonwood" in full_text:
        neighborhood = "Cottonwood"
    elif "palo cedro" in full_text:
        neighborhood = "Palo Cedro"
    elif "burney" in full_text:
        neighborhood = "Burney"
    elif "hilltop" in full_text or "dana" in full_text:
        neighborhood = "East Redding / Hilltop"

    return {
        "requiresDrugTest": requires_drug_test,
        "requiresBackgroundCheck": requires_background_check,
        "requiresDriverLicense": requires_driver_license,
        "driverLicenseType": driver_license_type,
        "requiresHsDiplomaOrGed": requires_hs_ged,
        "minAge": min_age,
        "isYouthFriendly": is_youth_friendly,
        "neighborhood": neighborhood,
        "description": description if description else experience
    }

def sync_jobs_to_firestore(jobs_list: list, collection_name: str = "jobs"):
    if not jobs_list:
        return

    db = get_firestore_client()
    batch = db.batch()
    batch_count = 0
    total_written = 0

    expiration_date = datetime.now(timezone.utc) + timedelta(days=15)

    for job in jobs_list:
        clean_title = clean_job_title(job.get("job_title", ""))
        if not clean_title or clean_title == "N/A":
            continue

        raw_desc = str(job.get("description") or "")
        if is_expired_job_content(raw_desc) or is_expired_job_content(clean_title):
            print(f"[FIRESTORE] Skipping expired job: {clean_title}")
            continue

        is_rej, rej_reason = is_rejected_job(clean_title, job.get("company", ""), raw_desc, pay=job.get("pay", ""))
        if is_rej:
            print(f"[FIRESTORE] Skipping non-entry-level / rejected job: {clean_title} ({rej_reason})")
            continue

        doc_id = generate_job_id(
            source=job.get("source", "Web"),
            company=job.get("company", "N/A"),
            title=clean_title,
            location=job.get("location", "Redding, CA")
        )

        doc_ref = db.collection(collection_name).document(doc_id)
        job_copy = dict(job)
        job_copy["job_title"] = clean_title
        parsed_attrs = parse_job_requirements(job_copy)

        final_desc = raw_desc if raw_desc and raw_desc != "N/A" else (parsed_attrs.get("description") or "N/A")

        payload = {
            "title": clean_title,
            "company": job.get("company", "").strip(),
            "location": job.get("location", "Redding, CA").strip(),
            "sector": job.get("industry", "Other"),
            "category": job.get("industry", "Other"),
            "pay": job.get("pay") or "N/A",
            "jobType": job.get("job_type_extracted") or "N/A",
            "schedule": job.get("shift_schedule") or "N/A",
            "shift": job.get("shift_schedule") or "N/A",
            "experience": job.get("experience") or "N/A",
            "requirements": job.get("experience") or "N/A",
            "description": final_desc,
            "jobUrl": job.get("job_url") or "",
            "url": job.get("job_url") or "",
            "source": job.get("source") or "Direct",
            "datePosted": job.get("date_posted") or datetime.now().strftime("%Y-%m-%d"),
            "requiresDrugTest": parsed_attrs.get("requiresDrugTest"),
            "requiresBackgroundCheck": parsed_attrs.get("requiresBackgroundCheck"),
            "requiresDriverLicense": parsed_attrs.get("requiresDriverLicense"),
            "driverLicenseType": parsed_attrs.get("driverLicenseType"),
            "requiresHsDiplomaOrGed": parsed_attrs.get("requiresHsDiplomaOrGed"),
            "minAge": parsed_attrs.get("minAge"),
            "isYouthFriendly": parsed_attrs.get("isYouthFriendly"),
            "neighborhood": parsed_attrs.get("neighborhood"),
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "expiresAt": expiration_date,
            "status": "active"
        }

        batch.set(doc_ref, payload, merge=True)
        batch_count += 1
        total_written += 1

        if batch_count >= 450:
            batch.commit()
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()

    print(f"[FIRESTORE] Synchronized {total_written} jobs with 15-day TTL.")