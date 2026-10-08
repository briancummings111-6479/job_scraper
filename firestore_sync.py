import hashlib
import os
import re
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, firestore

try:
    from scrapper import is_rejected_job, is_expired_job_content, clean_job_title, determine_industry, extract_key_requirements, generate_key_description, clean_location_str, is_shasta_county_location, is_bogus_title, resolve_business_address, standardize_driver_license_requirement, is_teen_friendly
except ImportError:
    def is_teen_friendly(title: str = "", company: str = "", text: str = "", requirements: str = "", job_dict: dict = None, gemini_teen_friendly: bool = None) -> bool:
        return bool(gemini_teen_friendly)
    def standardize_driver_license_requirement(exp_str: str, text_context: str = "", gemini_license: str = None) -> str:
        return exp_str
    def is_bogus_title(title: str) -> bool:
        return False

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

    def resolve_business_address(company: str = "", location: str = "", description: str = "", gemini_address: str = None) -> str:
        return str(location or "Redding, CA").strip()

    def is_shasta_county_location(loc_str: str, text_context: str = "") -> tuple:
        return True, str(loc_str or "Redding, CA").strip()

    def determine_industry(job_title: str, company: str = "", description: str = "") -> str:
        return "Other"

    def extract_key_requirements(text: str = "", existing_exp: str = "", job_dict: dict = None) -> str:
        return existing_exp if existing_exp and existing_exp != "N/A" else "Entry-level / No experience required"

    def generate_key_description(title: str, company: str = "", location: str = "Redding, CA", sector: str = "Other", job_type: str = "N/A", schedule: str = "N/A", pay: str = "N/A", requirements: str = "") -> str:
        return f"{title} position at {company} in {location}."

_PROCESSED_JOB_IDS = set()
_REJECTED_JOB_IDS = set()

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

_RABA_TRANSIT = None

def get_raba_transit_data():
    global _RABA_TRANSIT
    if _RABA_TRANSIT is not None:
        return _RABA_TRANSIT
    json_path = os.path.join(os.path.dirname(__file__), "raba_transit.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                _RABA_TRANSIT = json.load(f)
        except Exception:
            _RABA_TRANSIT = {}
    else:
        _RABA_TRANSIT = {}
    return _RABA_TRANSIT

LOCALITY_COORDS = {
    'downtown': (40.5841, -122.3926),
    'market st': (40.5835, -122.3926),
    'pine st': (40.5860, -122.3915),
    'hilltop': (40.5890, -122.3610),
    'dana dr': (40.5845, -122.3530),
    'churn creek': (40.5670, -122.3535),
    'cypress': (40.5700, -122.3650),
    'bechelli': (40.5630, -122.3700),
    'hartnell': (40.5610, -122.3600),
    'eureka way': (40.5835, -122.4265),
    'buenaventura': (40.5835, -122.4265),
    'lake blvd': (40.6120, -122.3850),
    'oasis rd': (40.6305, -122.3995),
    'shasta college': (40.6185, -122.3310),
    'south market': (40.5510, -122.3790),
    'bonnyview': (40.5360, -122.3710),
    'anderson': (40.4505, -122.2970),
    'shasta lake': (40.6810, -122.3720),
    'palo cedro': (40.5510, -122.2350),
    'bella vista': (40.6400, -122.2500),
    'burney': (40.8805, -121.6600)
}

def evaluate_raba_transit(location_str: str, full_text: str = ""):
    import math
    text = f"{location_str} {full_text}".lower()
    
    if any(u in text for u in ["palo cedro", "bella vista", "cottonwood", "fall river"]):
        return {
            "transitAccessible": False,
            "transitStopName": None,
            "transitRoutes": [],
            "transitDistanceMiles": 99.0
        }
        
    transit_data = get_raba_transit_data()
    stops = transit_data.get("stops", [])
    if not stops:
        is_acc = any(k in text for k in ["downtown", "hilltop", "dana", "cypress", "market", "eureka way", "churn creek"])
        return {
            "transitAccessible": is_acc,
            "transitStopName": "Downtown Terminal" if is_acc else None,
            "transitRoutes": ["Route 1", "Route 3"] if is_acc else [],
            "transitDistanceMiles": 0.3 if is_acc else 99.0
        }

    resolved_coords = None
    for loc_key, coords in LOCALITY_COORDS.items():
        if loc_key in text:
            resolved_coords = coords
            break
            
    if not resolved_coords:
        if "96001" in text or "redding" in text:
            resolved_coords = LOCALITY_COORDS['downtown']
        elif "96002" in text:
            resolved_coords = LOCALITY_COORDS['hilltop']
        elif "96003" in text:
            resolved_coords = LOCALITY_COORDS['lake blvd']
        elif "anderson" in text or "96007" in text:
            resolved_coords = LOCALITY_COORDS['anderson']
        elif "shasta lake" in text or "96019" in text:
            resolved_coords = LOCALITY_COORDS['shasta lake']

    if not resolved_coords:
        return {
            "transitAccessible": False,
            "transitStopName": None,
            "transitRoutes": [],
            "transitDistanceMiles": 99.0
        }

    target_lat, target_lon = resolved_coords
    best_stop = None
    min_dist = 999.0

    for s in stops:
        slat = s.get("lat")
        slon = s.get("lon")
        if not slat or not slon:
            continue
        dlat = math.radians(slat - target_lat)
        dlon = math.radians(slon - target_lon)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(target_lat)) * math.cos(math.radians(slat)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        dist = 3958.8 * c
        if dist < min_dist:
            min_dist = dist
            best_stop = s

    is_accessible = min_dist <= 0.6
    return {
        "transitAccessible": is_accessible,
        "transitStopName": best_stop.get("name") if best_stop else None,
        "transitRoutes": best_stop.get("routes", []) if best_stop else [],
        "transitDistanceMiles": round(min_dist, 2)
    }

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

    transit_info = evaluate_raba_transit(location, full_text)

    return {
        "requiresDrugTest": requires_drug_test,
        "requiresBackgroundCheck": requires_background_check,
        "requiresDriverLicense": requires_driver_license,
        "driverLicenseType": driver_license_type,
        "requiresHsDiplomaOrGed": requires_hs_ged,
        "minAge": min_age,
        "isYouthFriendly": is_youth_friendly,
        "neighborhood": neighborhood,
        "transitAccessible": transit_info["transitAccessible"],
        "transitStopName": transit_info["transitStopName"],
        "transitRoutes": transit_info["transitRoutes"],
        "transitDistanceMiles": transit_info["transitDistanceMiles"],
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
        if not clean_title or clean_title == "N/A" or is_bogus_title(clean_title):
            continue

        raw_loc = job.get("location", "Redding, CA")
        cleaned_loc = resolve_business_address(
            company=job.get("company", ""),
            location=raw_loc,
            description=job.get("description", "")
        )
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

        if doc_id in _REJECTED_JOB_IDS or doc_id in _PROCESSED_JOB_IDS:
            continue

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
                _REJECTED_JOB_IDS.add(doc_id)
                continue
            sector = gemini_res.sector
            if gemini_res.pay_rate and gemini_res.pay_rate != "N/A" and (not job.get("pay") or job.get("pay") == "N/A"):
                job["pay"] = gemini_res.pay_rate
            exp_req = extract_key_requirements(
                text=true_desc,
                existing_exp=gemini_res.experience_requirements,
                job_dict={"title": clean_title, "company": job.get("company", ""), "sector": sector, "location": cleaned_loc}
            )
            final_desc = gemini_res.job_description_summary if (not true_desc or len(true_desc) < 30) else true_desc
            parsed_attrs["requiresDrugTest"] = gemini_res.requires_drug_test
            parsed_attrs["requiresBackgroundCheck"] = gemini_res.requires_background_check
            parsed_attrs["requiresDriverLicense"] = gemini_res.requires_driver_license
            parsed_attrs["driverLicenseType"] = gemini_res.driver_license_type
            parsed_attrs["requiresHsDiplomaOrGed"] = gemini_res.requires_hs_ged
            parsed_attrs["minAge"] = gemini_res.min_age
            parsed_attrs["isYouthFriendly"] = gemini_res.is_youth_friendly
            parsed_attrs["isTeenFriendly"] = gemini_res.is_teen_friendly
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

        exp_req = standardize_driver_license_requirement(
            exp_req,
            text_context=f"{clean_title} {job.get('company', '')} {true_desc}",
            gemini_license=getattr(gemini_res, "driver_license_type", None) if gemini_res else None
        )

        gemini_tf = getattr(gemini_res, "is_teen_friendly", None) if gemini_res else None
        teen_friendly = is_teen_friendly(
            title=clean_title,
            company=job.get("company", ""),
            text=true_desc,
            requirements=exp_req,
            job_dict=job,
            gemini_teen_friendly=gemini_tf
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
            "isYouthFriendly": teen_friendly,
            "isTeenFriendly": teen_friendly,
            "teenFriendly": teen_friendly,
            "neighborhood": parsed_attrs.get("neighborhood"),
            "transitAccessible": parsed_attrs.get("transitAccessible", False),
            "transitStopName": parsed_attrs.get("transitStopName"),
            "transitRoutes": parsed_attrs.get("transitRoutes", []),
            "transitDistanceMiles": parsed_attrs.get("transitDistanceMiles"),
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "expiresAt": expiration_date,
            "status": "active"
        }

        batch.set(doc_ref, payload, merge=True)
        _PROCESSED_JOB_IDS.add(doc_id)
        batch_count += 1
        total_written += 1

        if batch_count >= 450:
            batch.commit()
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()

    print(f"[FIRESTORE] Synchronized {total_written} jobs with 15-day TTL.")