import hashlib
import os
import re
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, firestore

try:
    from scrapper import is_rejected_job, is_expired_job_content, clean_job_title, determine_industry, extract_key_requirements, generate_key_description, clean_location_str, is_shasta_county_location
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

    def is_rejected_job(title: str, company: str = "", description: str = "", pay: str = "", location: str = "") -> tuple:
        return False, ""

    def clean_location_str(loc: str) -> str:
        return str(loc or "Redding, CA").strip()

    def is_shasta_county_location(loc_str: str, text_context: str = "") -> tuple:
        return True, str(loc_str or "Redding, CA").strip()

    def determine_industry(job_title: str, company: str = "", description: str = "") -> str:
        return "Other"

    def extract_key_requirements(text: str = "", existing_exp: str = "", job_dict: dict = None) -> str:
        return existing_exp if existing_exp and existing_exp != "N/A" else "Entry-level / No experience required"

    def generate_key_description(title: str, company: str = "", location: str = "Redding, CA", sector: str = "Other", job_type: str = "N/A", schedule: str = "N/A", pay: str = "N/A", requirements: str = "") -> str:
        return f"{title} position at {company} in {location}."

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
        re.search(r'\b(?:drug\s*test|drug\s*screen|drug-free\s*workplace|substance\s*screen)\b', full_text)
    )

    # 2. Background Check
    requires_background_check = bool(
        re.search(r'\b(?:background\s*check|criminal\s*background|livescan|fingerprint)\b', full_text)
    )

    # 3. Driver's License & CDL
    requires_driver_license = bool(
        re.search(r'\b(?:driver\'?s?\s*license|valid\s*driver|clean\s*dmv|clean\s*driving\s*record|cdl)\b', full_text)
        or any(k in title.lower() for k in ["driver", "delivery", "courier", "shuttle", "hauling", "trucker"])
    )

    driver_license_type = "None"
    if requires_driver_license:
        if "cdl-a" in full_text or "class a" in full_text:
            driver_license_type = "Commercial Class A (CDL-A)"
        elif "cdl-b" in full_text or "class b" in full_text:
            driver_license_type = "Commercial Class B (CDL-B)"
        else:
            driver_license_type = "Class C (Standard)"

    # 4. High School Diploma / GED (Strict word boundaries)
    requires_hs_ged = bool(
        re.search(r'\b(?:high\s*school\s*(?:diploma|equivalent)|ged|h\.?s\.?\s*diploma)\b', full_text)
    )

    # 5. Age & Youth Friendly (Strict word boundary patterns)
    min_age = 18
    is_youth_friendly = False
    if re.search(r'\b(?:must\s*be\s*|minimum\s*age(?:\s*of)?\s*|at\s*least\s*|age\s*)21\s*(?:\+|years?(?:\s*old)?|\s*or\s*older)\b', full_text) or re.search(r'\b21\+\b', full_text) or any(k in title.lower() for k in ["bartender", "gaming"]):
        min_age = 21
    elif re.search(r'\b(?:must\s*be\s*|minimum\s*age(?:\s*of)?\s*|at\s*least\s*|age\s*)16\s*(?:\+|years?(?:\s*old)?|\s*or\s*older)\b', full_text) or re.search(r'\b16\+\b', full_text) or any(w in full_text for w in ["minor", "youth friendly", "youth-friendly", "teen", "student position"]):
        min_age = 16
        is_youth_friendly = True
    elif re.search(r'\b(?:must\s*be\s*|minimum\s*age(?:\s*of)?\s*|at\s*least\s*|age\s*)18\s*(?:\+|years?(?:\s*old)?|\s*or\s*older)\b', full_text) or re.search(r'\b18\+\b', full_text):
        min_age = 18

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

        raw_loc = job.get("location", "Redding, CA")
        cleaned_loc = clean_location_str(raw_loc)
        is_shasta, loc_reason = is_shasta_county_location(cleaned_loc)
        if not is_shasta:
            print(f"[FIRESTORE] Skipping out-of-county job: {clean_title} ({loc_reason})")
            continue

        raw_desc = str(job.get("description") or "")
        if is_expired_job_content(raw_desc) or is_expired_job_content(clean_title):
            print(f"[FIRESTORE] Skipping expired job: {clean_title}")
            continue

        is_rej, rej_reason = is_rejected_job(clean_title, job.get("company", ""), raw_desc, pay=job.get("pay", ""), location=cleaned_loc)
        if is_rej:
            print(f"[FIRESTORE] Skipping non-entry-level / rejected job: {clean_title} ({rej_reason})")
            continue

        doc_id = generate_job_id(
            source=job.get("source", "Web"),
            company=job.get("company", "N/A"),
            title=clean_title,
            location=cleaned_loc
        )

        doc_ref = db.collection(collection_name).document(doc_id)
        job_copy = dict(job)
        job_copy["job_title"] = clean_title
        job_copy["location"] = cleaned_loc
        parsed_attrs = parse_job_requirements(job_copy)

        is_boilerplate = bool("industry sector:" in raw_desc.lower() or "key requirements:" in raw_desc.lower())
        true_desc = "" if is_boilerplate else raw_desc

        gemini_res = None
        if true_desc and len(true_desc) > 30:
            try:
                from gemini_parser import analyze_job_with_gemini
                gemini_res = analyze_job_with_gemini(
                    title=clean_title,
                    company=job.get("company", ""),
                    location=cleaned_loc,
                    description_text=true_desc,
                    raw_pay=job.get("pay") or "N/A",
                    raw_type=job.get("job_type_extracted") or "N/A",
                    raw_schedule=job.get("shift_schedule") or "N/A"
                )
            except Exception:
                gemini_res = None

        if gemini_res:
            if not gemini_res.is_entry_level:
                print(f"[FIRESTORE] Skipping rejected job via Gemini: {clean_title} ({gemini_res.rejection_reason})")
                continue
            sector = gemini_res.sector
            if gemini_res.pay_rate and gemini_res.pay_rate != "N/A" and (not job.get("pay") or job.get("pay") == "N/A"):
                job["pay"] = gemini_res.pay_rate
            exp_req = gemini_res.experience_requirements
            final_desc = gemini_res.job_description_summary if (not true_desc or len(true_desc) < 30) else true_desc
            parsed_attrs["requiresDrugTest"] = gemini_res.requires_drug_test
            parsed_attrs["requiresBackgroundCheck"] = gemini_res.requires_background_check
            parsed_attrs["requiresDriverLicense"] = gemini_res.requires_driver_license
            parsed_attrs["driverLicenseType"] = gemini_res.driver_license_type
            parsed_attrs["requiresHsDiplomaOrGed"] = gemini_res.requires_hs_ged
            parsed_attrs["minAge"] = gemini_res.min_age
            parsed_attrs["isYouthFriendly"] = gemini_res.is_youth_friendly
        else:
            sector = job.get("industry")
            if not sector or sector == "Other":
                sector = determine_industry(clean_title, job.get("company", ""), true_desc)

            exp_req = extract_key_requirements(
                text=true_desc,
                existing_exp=job.get("experience") or job.get("requirements"),
                job_dict={"title": clean_title, "company": job.get("company", ""), "sector": sector, "location": cleaned_loc}
            )

            final_desc = true_desc
            if not final_desc or final_desc == "N/A" or len(final_desc.strip()) < 30:
                final_desc = generate_key_description(
                    title=clean_title,
                    company=job.get("company", ""),
                    location=cleaned_loc,
                    sector=sector,
                    job_type=job.get("job_type_extracted") or "N/A",
                    schedule=job.get("shift_schedule") or "N/A",
                    pay=job.get("pay") or "N/A",
                    requirements=exp_req
                )

        payload = {
            "title": clean_title,
            "company": job.get("company", "").strip(),
            "location": cleaned_loc,
            "sector": sector,
            "category": sector,
            "pay": job.get("pay") or "N/A",
            "jobType": job.get("job_type_extracted") or "N/A",
            "schedule": job.get("shift_schedule") or "N/A",
            "shift": job.get("shift_schedule") or "N/A",
            "experience": exp_req,
            "requirements": exp_req,
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