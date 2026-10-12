import os
import sqlite3
import json
import re
from difflib import SequenceMatcher
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "employers.db")
DEFAULT_CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "employers_registry.json")

CORPORATE_SUFFIX_REGEX = re.compile(
    r'\b(?:inc(?:orp(?:orated)?)?|llc|corp(?:oration)?|co(?:mpany)?|ltd|group|enterprises?|services?|usa|of\s+california)\b\.?',
    flags=re.IGNORECASE
)

DEFAULT_EMPLOYER_SECTORS = {
    "ace hardware": "Retail & Sales",
    "autozone": "Retail & Sales",
    "barnes & noble": "Retail & Sales",
    "american eagle": "Retail & Sales",
    "american eagle outfitters": "Retail & Sales",
    "best buy": "Retail & Sales",
    "target": "Retail & Sales",
    "walmart": "Retail & Sales",
    "home depot": "Retail & Sales",
    "lowes": "Retail & Sales",
    "dollar tree": "Retail & Sales",
    "batteries plus": "Retail & Sales",
    "costco": "Retail & Sales",
    "tj maxx": "Retail & Sales",
    "ross": "Retail & Sales",
    "mcdonalds": "Food & Restaurant",
    "taco bell": "Food & Restaurant",
    "in-n-out": "Food & Restaurant",
    "in-n-out burger": "Food & Restaurant",
    "dutch bros": "Food & Restaurant",
    "dutch bros coffee": "Food & Restaurant",
    "starbucks": "Food & Restaurant",
    "wendys": "Food & Restaurant",
    "burger king": "Food & Restaurant",
    "carls jr": "Food & Restaurant",
    "subway": "Food & Restaurant",
    "panda express": "Food & Restaurant",
    "chick-fil-a": "Food & Restaurant",
    "baskin robbins": "Food & Restaurant",
    "chipotle": "Food & Restaurant",
    "panera bread": "Food & Restaurant",
    "amazon": "Warehouse & Logistics",
    "fedex": "Warehouse & Logistics",
    "ups": "Warehouse & Logistics",
    "arcadia home care": "Healthcare & Caregiving",
    "arcadia home care and staffing": "Healthcare & Caregiving",
    "dignity health": "Healthcare & Caregiving",
    "mercy medical center": "Healthcare & Caregiving",
    "shasta community health center": "Healthcare & Caregiving",
    "abm industries": "Janitorial & Facilities",
    "armed guard private security": "Security & Public Safety",
    "armed guard private security inc": "Security & Public Safety",
    "beneficial insectary": "Agriculture & Groundskeeping",
}


def normalize_name(name: str) -> str:
    """
    Normalizes a business name for robust fuzzy matching by stripping punctuation,
    standardizing whitespace, and trimming common legal/corporate suffixes.
    """
    if not name:
        return ""
    text = str(name).strip().lower()
    text = re.sub(r'[\'\"’`\.]', '', text)
    text = CORPORATE_SUFFIX_REGEX.sub('', text)
    text = re.sub(r'[^a-z0-9\s&-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Creates a sqlite3 connection with Row factory and foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initializes the database schema if tables do not already exist."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Master Employers Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                name_normalized TEXT NOT NULL,
                aliases TEXT DEFAULT '[]',
                industry_sector TEXT DEFAULT 'Other',
                secondary_sector TEXT DEFAULT '',
                min_age_baseline INTEGER DEFAULT 18,
                hs_ged_baseline TEXT DEFAULT '',
                felon_friendly TEXT DEFAULT 'Unknown',
                background_check TEXT DEFAULT 'Unknown',
                drug_testing TEXT DEFAULT 'Unknown',
                drivers_license TEXT DEFAULT 'None',
                work_experience TEXT DEFAULT 'None',
                starting_wage TEXT DEFAULT '',
                career_url TEXT DEFAULT '',
                indeed_url TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                is_verified INTEGER DEFAULT 1,
                last_updated TEXT DEFAULT ''
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emp_norm ON employers (name_normalized)")

        # 2. Multi-Location Branches Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employer_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employer_id INTEGER NOT NULL REFERENCES employers(id) ON DELETE CASCADE,
                location_name TEXT DEFAULT '',
                street_address TEXT NOT NULL,
                city TEXT DEFAULT 'Redding',
                state TEXT DEFAULT 'CA',
                zip_code TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                manager_name TEXT DEFAULT '',
                is_primary INTEGER DEFAULT 0,
                raba_accessible INTEGER DEFAULT 0,
                raba_stop TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_loc_emp ON employer_locations (employer_id)")

        # 3. Unregistered Employers Queue Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unregistered_employers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                sample_title TEXT DEFAULT '',
                sample_location TEXT DEFAULT '',
                first_seen TEXT DEFAULT '',
                last_seen TEXT DEFAULT '',
                times_seen INTEGER DEFAULT 1,
                status TEXT DEFAULT 'pending'
            )
        """)
        conn.commit()

def upsert_employer(emp_data: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> int:
    """
    Inserts or updates a master employer record. Returns the employer ID.
    """
    name = str(emp_data.get("name", "")).strip()
    if not name:
        raise ValueError("Employer name cannot be empty.")

    norm_name = normalize_name(name)
    aliases = emp_data.get("aliases", [])
    if isinstance(aliases, list):
        aliases_json = json.dumps(aliases)
    else:
        aliases_json = str(aliases)

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM employers WHERE name = ? OR name_normalized = ?", (name, norm_name))
        row = cursor.fetchone()

        if row:
            emp_id = row["id"]
            cursor.execute("""
                UPDATE employers SET
                    name = ?,
                    name_normalized = ?,
                    aliases = ?,
                    industry_sector = ?,
                    secondary_sector = ?,
                    min_age_baseline = ?,
                    hs_ged_baseline = ?,
                    felon_friendly = ?,
                    background_check = ?,
                    drug_testing = ?,
                    drivers_license = ?,
                    work_experience = ?,
                    starting_wage = ?,
                    career_url = ?,
                    indeed_url = ?,
                    notes = ?,
                    is_verified = ?,
                    last_updated = ?
                WHERE id = ?
            """, (
                name,
                norm_name,
                aliases_json,
                emp_data.get("industry_sector", "Other"),
                emp_data.get("secondary_sector", ""),
                int(emp_data.get("min_age_baseline", 18)),
                str(emp_data.get("hs_ged_baseline", "")),
                str(emp_data.get("felon_friendly", "Unknown")),
                str(emp_data.get("background_check", "Unknown")),
                str(emp_data.get("drug_testing", "Unknown")),
                str(emp_data.get("drivers_license", "None")),
                str(emp_data.get("work_experience", "None")),
                str(emp_data.get("starting_wage", "")),
                str(emp_data.get("career_url", "")),
                str(emp_data.get("indeed_url", "")),
                str(emp_data.get("notes", "")),
                1 if emp_data.get("is_verified", True) else 0,
                now_iso,
                emp_id
            ))
        else:
            cursor.execute("""
                INSERT INTO employers (
                    name, name_normalized, aliases, industry_sector, secondary_sector,
                    min_age_baseline, hs_ged_baseline, felon_friendly, background_check,
                    drug_testing, drivers_license, work_experience, starting_wage,
                    career_url, indeed_url, notes, is_verified, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                norm_name,
                aliases_json,
                emp_data.get("industry_sector", "Other"),
                emp_data.get("secondary_sector", ""),
                int(emp_data.get("min_age_baseline", 18)),
                str(emp_data.get("hs_ged_baseline", "")),
                str(emp_data.get("felon_friendly", "Unknown")),
                str(emp_data.get("background_check", "Unknown")),
                str(emp_data.get("drug_testing", "Unknown")),
                str(emp_data.get("drivers_license", "None")),
                str(emp_data.get("work_experience", "None")),
                str(emp_data.get("starting_wage", "")),
                str(emp_data.get("career_url", "")),
                str(emp_data.get("indeed_url", "")),
                str(emp_data.get("notes", "")),
                1 if emp_data.get("is_verified", True) else 0,
                now_iso
            ))
            emp_id = cursor.lastrowid

        conn.commit()
        return emp_id

def upsert_location(employer_id: int, loc_data: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> int:
    """
    Inserts or updates a branch location for an employer.
    """
    addr = str(loc_data.get("street_address", "")).strip()
    if not addr:
        addr = "Redding, CA"

    loc_name = str(loc_data.get("location_name", "")).strip()
    city = str(loc_data.get("city", "Redding")).strip()
    state = str(loc_data.get("state", "CA")).strip()
    zip_code = str(loc_data.get("zip_code", "")).strip()
    phone = str(loc_data.get("phone", "")).strip()
    manager = str(loc_data.get("manager_name", "")).strip()
    is_primary = 1 if loc_data.get("is_primary", False) else 0
    raba_acc = 1 if loc_data.get("raba_accessible", False) else 0
    raba_stop = str(loc_data.get("raba_stop", "")).strip()
    notes = str(loc_data.get("notes", "")).strip()

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Check if this exact address exists for this employer
        cursor.execute("""
            SELECT id FROM employer_locations 
            WHERE employer_id = ? AND (street_address = ? OR (location_name = ? AND location_name != ''))
        """, (employer_id, addr, loc_name))
        row = cursor.fetchone()

        if row:
            loc_id = row["id"]
            cursor.execute("""
                UPDATE employer_locations SET
                    location_name = ?,
                    street_address = ?,
                    city = ?,
                    state = ?,
                    zip_code = ?,
                    phone = ?,
                    manager_name = ?,
                    is_primary = ?,
                    raba_accessible = ?,
                    raba_stop = ?,
                    notes = ?
                WHERE id = ?
            """, (loc_name, addr, city, state, zip_code, phone, manager, is_primary, raba_acc, raba_stop, notes, loc_id))
        else:
            cursor.execute("""
                INSERT INTO employer_locations (
                    employer_id, location_name, street_address, city, state, zip_code,
                    phone, manager_name, is_primary, raba_accessible, raba_stop, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (employer_id, loc_name, addr, city, state, zip_code, phone, manager, is_primary, raba_acc, raba_stop, notes))
            loc_id = cursor.lastrowid

        conn.commit()
        return loc_id

def get_employer(employer_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Returns a full employer record with all its branch locations."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employers WHERE id = ?", (employer_id,))
        emp_row = cursor.fetchone()
        if not emp_row:
            return None

        emp_dict = dict(emp_row)
        try:
            emp_dict["aliases"] = json.loads(emp_dict["aliases"])
        except Exception:
            emp_dict["aliases"] = []

        cursor.execute("SELECT * FROM employer_locations WHERE employer_id = ? ORDER BY is_primary DESC, id ASC", (employer_id,))
        loc_rows = cursor.fetchall()
        emp_dict["locations"] = [dict(lr) for lr in loc_rows]
        return emp_dict

def get_all_employers(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns all employers with their nested branch locations."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employers ORDER BY name ASC")
        emp_rows = cursor.fetchall()

        results = []
        for er in emp_rows:
            emp_dict = dict(er)
            try:
                emp_dict["aliases"] = json.loads(emp_dict["aliases"])
            except Exception:
                emp_dict["aliases"] = []

            cursor.execute("SELECT * FROM employer_locations WHERE employer_id = ? ORDER BY is_primary DESC, id ASC", (emp_dict["id"],))
            emp_dict["locations"] = [dict(lr) for lr in cursor.fetchall()]
            results.append(emp_dict)
        return results

def log_unregistered_employer(name: str, sample_title: str = "", sample_location: str = "", db_path: str = DEFAULT_DB_PATH) -> None:
    """Logs an unrecognized employer into the unregistered queue for staff review."""
    cleaned = str(name).strip()
    if not cleaned or len(cleaned) < 2:
        return

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, times_seen FROM unregistered_employers WHERE name = ?", (cleaned,))
        row = cursor.fetchone()
        if row:
            cursor.execute("""
                UPDATE unregistered_employers SET 
                    times_seen = times_seen + 1,
                    last_seen = ?,
                    sample_title = CASE WHEN sample_title = '' THEN ? ELSE sample_title END,
                    sample_location = CASE WHEN sample_location = '' THEN ? ELSE sample_location END
                WHERE id = ?
            """, (now_iso, sample_title, sample_location, row["id"]))
        else:
            cursor.execute("""
                INSERT INTO unregistered_employers (name, sample_title, sample_location, first_seen, last_seen, times_seen, status)
                VALUES (?, ?, ?, ?, ?, 1, 'pending')
            """, (cleaned, sample_title, sample_location, now_iso, now_iso))
        conn.commit()

def get_unregistered_employers(status: str = "pending", db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns list of unrecognized employers pending staff review."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if status == "all":
            cursor.execute("SELECT * FROM unregistered_employers ORDER BY times_seen DESC, last_seen DESC")
        else:
            cursor.execute("SELECT * FROM unregistered_employers WHERE status = ? ORDER BY times_seen DESC, last_seen DESC", (status,))
        return [dict(r) for r in cursor.fetchall()]

def export_to_json(json_path: str = DEFAULT_CACHE_PATH, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Exports all employers and locations to a JSON cache file for high-speed in-memory lookup."""
    employers = get_all_employers(db_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(employers, f, indent=2)
    return employers

_FAST_CACHE: Optional[List[Dict[str, Any]]] = None
_FAST_INDEX: Dict[str, Dict[str, Any]] = {}

def load_fast_cache(json_path: str = DEFAULT_CACHE_PATH, force_reload: bool = False) -> List[Dict[str, Any]]:
    """Loads and builds the in-memory lookup index for sub-millisecond matching."""
    global _FAST_CACHE, _FAST_INDEX
    if _FAST_CACHE is not None and not force_reload:
        return _FAST_CACHE

    if not os.path.exists(json_path):
        # Auto-export if DB exists
        if os.path.exists(DEFAULT_DB_PATH):
            export_to_json(json_path)
        else:
            init_db()
            export_to_json(json_path)

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            _FAST_CACHE = json.load(f)
    except Exception:
        _FAST_CACHE = []

    _FAST_INDEX.clear()
    for emp in _FAST_CACHE:
        norm = normalize_name(emp["name"])
        if norm:
            _FAST_INDEX[norm] = emp
        for alias in emp.get("aliases", []):
            a_norm = normalize_name(alias)
            if a_norm and a_norm not in _FAST_INDEX:
                _FAST_INDEX[a_norm] = emp

    return _FAST_CACHE

def resolve_branch_location(emp: Dict[str, Any], location_hint: str = "") -> Dict[str, Any]:
    """
    Given an employer and location context (e.g. from job posting), selects the best matching
    branch location record (or primary/first branch if none specifically match).
    """
    locations = emp.get("locations", [])
    if not locations:
        return {
            "street_address": "Redding, CA",
            "city": "Redding",
            "state": "CA",
            "zip_code": "96002",
            "phone": "",
            "manager_name": "",
            "raba_accessible": False,
            "raba_stop": ""
        }

    if len(locations) == 1 or not location_hint:
        # Default to primary or first
        for loc in locations:
            if loc.get("is_primary"):
                return loc
        return locations[0]

    hint_lower = location_hint.lower()
    
    # 1. Exact street name / address number match
    for loc in locations:
        addr = loc.get("street_address", "").lower()
        loc_name = loc.get("location_name", "").lower()
        zip_c = loc.get("zip_code", "")
        
        # Check zip code match
        if zip_c and zip_c in hint_lower:
            return loc

        # Extract address street name (e.g. 'Hartnell' from '1350 Hartnell Ave')
        street_parts = [p.strip() for p in re.split(r'[,\s]+', addr) if len(p.strip()) > 3]
        for part in street_parts:
            if part in hint_lower:
                return loc

        # Check location_name / store id
        if loc_name and any(part in hint_lower for part in re.split(r'[\s\(\)]+', loc_name) if len(part) > 3):
            return loc

    # Fallback to primary
    for loc in locations:
        if loc.get("is_primary"):
            return loc
    return locations[0]

def match_employer(
    company_name: str,
    location_hint: str = "",
    json_path: str = DEFAULT_CACHE_PATH,
    fuzzy_threshold: float = 0.88
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Matches a scraped company name against the employer registry.
    Returns a tuple of (matched_employer, matched_location) or (None, None).
    """
    if not company_name:
        return None, None

    load_fast_cache(json_path)
    norm = normalize_name(company_name)
    if not norm:
        return None, None

    # 1. Exact match against normalized name or aliases
    if norm in _FAST_INDEX:
        emp = _FAST_INDEX[norm]
        loc = resolve_branch_location(emp, location_hint)
        return emp, loc

    # 2. Substring matching for distinctive company names
    for key, emp in _FAST_INDEX.items():
        if len(key) >= 5 and (key in norm or norm in key):
            # Verify high token overlap
            k_words = set(key.split())
            n_words = set(norm.split())
            if k_words.issubset(n_words) or n_words.issubset(k_words):
                loc = resolve_branch_location(emp, location_hint)
                return emp, loc

    # 3. Fuzzy similarity matching using SequenceMatcher
    best_match = None
    best_score = 0.0

    for key, emp in _FAST_INDEX.items():
        score = SequenceMatcher(None, norm, key).ratio()
        if score > best_score:
            best_score = score
            best_match = emp

    if best_score >= fuzzy_threshold and best_match:
        loc = resolve_branch_location(best_match, location_hint)
        return best_match, loc

    return None, None

def parse_address_components(raw_address: str) -> Dict[str, str]:
    """
    Parses a raw address string to extract city, state, and zip code.
    Defaults to Redding, CA 96002 if unspecified.
    """
    cleaned = str(raw_address or "").strip()
    if not cleaned or cleaned.lower() in ["area facilities jobs", "8 locations", "various", "multiple", "n/a", "none"]:
        return {
            "street_address": "Redding, CA",
            "city": "Redding",
            "state": "CA",
            "zip_code": "96002"
        }

    zip_match = re.search(r'\b(96\d{3})\b', cleaned)
    zip_code = zip_match.group(1) if zip_match else ""

    city = "Redding"
    lower_addr = cleaned.lower()
    if "anderson" in lower_addr:
        city = "Anderson"
        if not zip_code: zip_code = "96007"
    elif "shasta lake" in lower_addr:
        city = "Shasta Lake"
        if not zip_code: zip_code = "96019"
    elif "burney" in lower_addr:
        city = "Burney"
        if not zip_code: zip_code = "96013"
    elif "palo cedro" in lower_addr:
        city = "Palo Cedro"
        if not zip_code: zip_code = "96073"
    elif "cottonwood" in lower_addr:
        city = "Cottonwood"
        if not zip_code: zip_code = "96022"
    elif not zip_code:
        zip_code = "96002"

    return {
        "street_address": cleaned,
        "city": city,
        "state": "CA",
        "zip_code": zip_code
    }

def parse_multi_locations(raw_addr: str, notes: str = "", company_name: str = "") -> List[Dict[str, Any]]:
    """
    Extracts multiple branch locations from raw address and notes fields.
    Handles Store ID formats, piped delimiters, or newline/semicolon separation.
    """
    locations = []
    
    # 1. Check notes for Store ID / multi-branch patterns (e.g., 'Store ID: ca44ad1f = 1350 Hartnell Ave, Redding, | e191628a = 4490 Westside Rd, Redding, |')
    if notes and ("store id" in notes.lower() or "|" in notes):
        segments = [s.strip() for s in notes.split("|") if s.strip()]
        for idx, seg in enumerate(segments):
            m = re.search(r'(?:store\s*id:?\s*)?([a-zA-Z0-9_-]+)\s*=\s*(.+)', seg, flags=re.IGNORECASE)
            if m:
                store_id = m.group(1).strip()
                branch_addr = m.group(2).strip().rstrip(',')
                parsed = parse_address_components(branch_addr)
                locations.append({
                    "location_name": f"Store ID {store_id}",
                    "street_address": parsed["street_address"],
                    "city": parsed["city"],
                    "state": parsed["state"],
                    "zip_code": parsed["zip_code"],
                    "phone": "",
                    "manager_name": "",
                    "is_primary": (idx == 0)
                })

    # 2. If no multi-location extracted from notes, parse raw_addr
    if not locations and raw_addr:
        clean_addr = raw_addr.strip()
        # Check if comma-separated list of towns (e.g. 'Bella Vista, Anderson, Caterpillar, Tanqueray')
        if any(w in clean_addr.lower() for w in ["locations", "area facilities", "various"]):
            parsed = parse_address_components("Redding, CA")
            locations.append({
                "location_name": "Area Operations",
                "street_address": "Redding, CA",
                "city": parsed["city"],
                "state": parsed["state"],
                "zip_code": parsed["zip_code"],
                "phone": "",
                "manager_name": "",
                "is_primary": True
            })
        else:
            parsed = parse_address_components(clean_addr)
            locations.append({
                "location_name": "Main Location",
                "street_address": parsed["street_address"],
                "city": parsed["city"],
                "state": parsed["state"],
                "zip_code": parsed["zip_code"],
                "phone": "",
                "manager_name": "",
                "is_primary": True
            })

    # 3. Default fallback if still empty
    if not locations:
        locations.append({
            "location_name": "Main Location",
            "street_address": "Redding, CA",
            "city": "Redding",
            "state": "CA",
            "zip_code": "96002",
            "phone": "",
            "manager_name": "",
            "is_primary": True
        })

    return locations

def import_from_records(records: List[Dict[str, Any]], db_path: str = DEFAULT_DB_PATH) -> int:
    """
    Bulk imports or updates employer records and branch locations into SQLite,
    then updates the JSON fast cache.
    """
    init_db(db_path)
    count = 0

    for rec in records:
        comp_name = str(rec.get("company") or rec.get("name") or "").strip()
        if not comp_name:
            continue

        # Extract industry sector if provided or try to determine
        sector = str(rec.get("industry_sector") or rec.get("industry") or rec.get("sector") or "").strip()
        if not sector or sector in ["Other", "N/A", ""]:
            norm_c = normalize_name(comp_name)
            if norm_c in DEFAULT_EMPLOYER_SECTORS:
                sector = DEFAULT_EMPLOYER_SECTORS[norm_c]
            else:
                try:
                    from scrapper import determine_industry
                    sector = determine_industry(job_title="", company=comp_name, description=rec.get("notes", ""))
                except Exception:
                    sector = "Other"

        min_age_val = 18
        raw_age = str(rec.get("min_age") or rec.get("min_age_baseline") or "").strip()
        if raw_age:
            age_m = re.search(r'\b(14|15|16|17|18|21)\b', raw_age)
            if age_m:
                min_age_val = int(age_m.group(1))

        emp_payload = {
            "name": comp_name,
            "aliases": rec.get("aliases", []),
            "industry_sector": sector if sector else "Other",
            "secondary_sector": rec.get("secondary_sector", ""),
            "min_age_baseline": min_age_val,
            "hs_ged_baseline": rec.get("hs_ged_required") or rec.get("hs_ged_baseline") or "",
            "felon_friendly": rec.get("felon_friendly") or rec.get("clean_record_required") or "Unknown",
            "background_check": rec.get("background_check") or rec.get("clean_record_required") or "Unknown",
            "drug_testing": rec.get("drug_testing") or "Unknown",
            "drivers_license": rec.get("drivers_license_required") or rec.get("drivers_license") or "None",
            "work_experience": rec.get("work_experience_required") or rec.get("work_experience") or "None",
            "starting_wage": rec.get("wage") or rec.get("starting_wage") or "",
            "career_url": rec.get("career_url") or "",
            "indeed_url": rec.get("indeed_url") or "",
            "notes": rec.get("notes") or "",
            "is_verified": rec.get("is_verified", True)
        }

        emp_id = upsert_employer(emp_payload, db_path=db_path)

        # Parse and insert branch locations
        raw_addr = str(rec.get("address") or rec.get("street_address") or "").strip()
        locations = rec.get("locations")
        if not locations:
            locations = parse_multi_locations(raw_addr, notes=rec.get("notes", ""), company_name=comp_name)

        for loc in locations:
            upsert_location(emp_id, loc, db_path=db_path)

        count += 1

    # Re-export to cache
    export_to_json(db_path=db_path)
    load_fast_cache(force_reload=True)
    return count

def import_legacy_employers_json(json_path: str = None, db_path: str = DEFAULT_DB_PATH) -> int:
    """Imports the local redding_area_employers.json file into employers.db."""
    if not json_path:
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "redding_area_employers.json")
    if not os.path.exists(json_path):
        return 0

    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    return import_from_records(records, db_path=db_path)

