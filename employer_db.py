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
                review_status TEXT DEFAULT 'Verified',
                is_verified INTEGER DEFAULT 1,
                last_updated TEXT DEFAULT ''
            )
        """)
        try:
            cursor.execute("ALTER TABLE employers ADD COLUMN review_status TEXT DEFAULT 'Verified'")
        except sqlite3.OperationalError:
            pass
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

def parse_raba_from_notes(notes: str, street_address: str = "", city: str = "") -> Tuple[bool, str]:
    """
    Infers RABA public transit accessibility and servicing routes from Location & Transit Notes
    and street address context.
    """
    text = f"{notes or ''} {street_address or ''} {city or ''}".lower()
    if any(neg in text for neg in [
        "no raba", "not directly on raba", "outside raba", "beyond raba",
        "limited raba", "not on raba", "personal vehicle recommended", "own transportation required"
    ]):
        return False, ""

    routes = re.findall(r'route\s*(\d+[a-z]?(?:\s*(?:&|and|,)\s*\d+[a-z]?)*)', notes or "", flags=re.IGNORECASE)
    stop_str = ""
    if routes:
        stop_str = f"RABA Route {', '.join(routes)}"
    elif "downtown transit" in text:
        stop_str = "RABA Downtown Transit Center"
    elif "raba" in (notes or "").lower():
        stop_str = "Near RABA Transit Route"

    if "raba" in (notes or "").lower():
        return True, stop_str

    if any(corridor in text for corridor in ["dana dr", "hilltop dr", "churn creek", "cypress ave", "market st", "pine st", "eureka way", "bechelli"]):
        return True, stop_str or "RABA Corridor"

    return False, ""

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

    review_status = str(emp_data.get("review_status") or ("Verified" if emp_data.get("is_verified", True) else "Pending")).strip()
    is_ver = 0 if review_status.lower() in ["pending", "unverified", "draft"] else (1 if emp_data.get("is_verified", True) else 0)
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
                    review_status = ?,
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
                review_status,
                is_ver,
                now_iso,
                emp_id
            ))
        else:
            cursor.execute("""
                INSERT INTO employers (
                    name, name_normalized, aliases, industry_sector, secondary_sector,
                    min_age_baseline, hs_ged_baseline, felon_friendly, background_check,
                    drug_testing, drivers_license, work_experience, starting_wage,
                    career_url, indeed_url, notes, review_status, is_verified, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                review_status,
                is_ver,
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
    notes = str(loc_data.get("notes", "")).strip()

    inferred_raba_acc, inferred_raba_stop = parse_raba_from_notes(notes, addr, city)
    raba_acc = 1 if (loc_data.get("raba_accessible") or inferred_raba_acc) else 0
    raba_stop = str(loc_data.get("raba_stop") or inferred_raba_stop or "").strip()

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
            # Also index individual slash-separated or semicolon-separated corporate aliases
            for sub_alias in re.split(r'[\/;]', str(alias)):
                sa_norm = normalize_name(sub_alias)
                if sa_norm and len(sa_norm) >= 3 and sa_norm not in _FAST_INDEX:
                    _FAST_INDEX[sa_norm] = emp

    return _FAST_CACHE

def resolve_branch_location(emp: Dict[str, Any], location_hint: str = "") -> Dict[str, Any]:
    """
    Given an employer and location context (e.g. from job posting), selects the best matching
    branch location record (or primary/first branch if none specifically match).
    """
    locations = emp.get("locations", [])
    if not locations:
        return {
            "location_name": "Main Location",
            "street_address": "Redding, CA",
            "city": "Redding",
            "state": "CA",
            "zip_code": "96002",
            "phone": "",
            "manager_name": "",
            "raba_accessible": False,
            "raba_stop": "",
            "notes": emp.get("notes", "")
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
        if len(key) >= 4 and (key in norm or norm in key):
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
    elif "bella vista" in lower_addr:
        city = "Bella Vista"
        if not zip_code: zip_code = "96008"
    elif "shingletown" in lower_addr:
        city = "Shingletown"
        if not zip_code: zip_code = "96088"
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

        raw_aliases = rec.get("aliases", [])
        if isinstance(raw_aliases, str):
            raw_aliases = [raw_aliases] if raw_aliases.strip() else []
        expanded_aliases = []
        for al in raw_aliases:
            al_str = str(al).strip()
            if al_str and al_str not in expanded_aliases:
                expanded_aliases.append(al_str)
            for sub in re.split(r'[\/;]', al_str):
                s_clean = sub.strip()
                if s_clean and s_clean.lower() != comp_name.lower() and s_clean not in expanded_aliases:
                    expanded_aliases.append(s_clean)

        rev_status = str(rec.get("review_status") or ("Verified" if rec.get("is_verified", True) else "Pending")).strip()

        emp_payload = {
            "name": comp_name,
            "aliases": expanded_aliases,
            "industry_sector": sector if sector else "Other",
            "secondary_sector": rec.get("secondary_sector", ""),
            "min_age_baseline": min_age_val,
            "hs_ged_baseline": rec.get("hs_ged_required") or rec.get("hs_ged_baseline") or "Not Required",
            "felon_friendly": rec.get("felon_friendly") or rec.get("fair_chance") or "Unknown",
            "background_check": rec.get("background_check") or rec.get("clean_record_required") or "Unknown",
            "drug_testing": rec.get("drug_testing") or "Unknown",
            "drivers_license": rec.get("drivers_license_required") or rec.get("drivers_license") or "Not Required",
            "work_experience": rec.get("work_experience_required") or rec.get("work_experience") or "None (Entry-Level)",
            "starting_wage": rec.get("wage") or rec.get("starting_wage") or "",
            "career_url": rec.get("career_url") or "",
            "indeed_url": rec.get("indeed_url") or "",
            "notes": rec.get("notes") or "",
            "review_status": rev_status,
            "is_verified": rev_status.lower() not in ["pending", "unverified", "draft"]
        }

        emp_id = upsert_employer(emp_payload, db_path=db_path)

        # Parse and insert branch locations
        raw_addr = str(rec.get("address") or rec.get("street_address") or "").strip()
        locations = rec.get("locations")
        if not locations:
            locations = parse_multi_locations(raw_addr, notes=rec.get("notes", ""), company_name=comp_name)

        # Replace locations cleanly when structured locations list is provided from Area Employers
        if rec.get("locations"):
            with get_connection(db_path) as conn:
                conn.execute("DELETE FROM employer_locations WHERE employer_id = ?", (emp_id,))
                conn.commit()

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


def resolve_job_with_employer_profile(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    2-Layer Resolution Engine aligning scraped job listings with the 'Area Employers' database
    (gid=1114754984) and Participant Job Profile:
      - Layer 1 (Default Baseline): Pulls verified employer baseline policies and branch location
        details from 'Area Employers' (employers.db / employers_registry.json).
      - Layer 2 (Job-Specific Override): Overwrites any baseline field whenever the job posting's
        title, description, or requirements explicitly state a role-specific value.
    """
    raw_title = str(job.get("job_title") or job.get("title") or "").strip()
    raw_company = str(job.get("company") or "").strip()
    raw_loc = str(job.get("location") or "Redding, CA").strip()
    raw_desc = str(job.get("description") or "").strip()
    raw_exp = str(job.get("experience") or job.get("requirements") or "").strip()
    raw_pay = str(job.get("pay") or "").strip()
    raw_type = str(job.get("job_type_extracted") or job.get("jobType") or "").strip()
    raw_shift = str(job.get("shift_schedule") or job.get("schedule") or job.get("shift") or "").strip()

    is_boilerplate = bool("industry sector:" in raw_desc.lower() or "key requirements:" in raw_desc.lower())
    true_desc = "" if is_boilerplate else raw_desc

    # 1. Match against Area Employers registry
    emp_match, loc_match = match_employer(
        company_name=raw_company,
        location_hint=f"{raw_loc} {true_desc}"
    )

    if not emp_match and raw_company and raw_company.lower() not in ["n/a", "none", "unknown", "confidential", "private employer"]:
        try:
            log_unregistered_employer(raw_company, sample_title=raw_title, sample_location=raw_loc)
        except Exception:
            pass

    # Check if job description explicitly contains a street address override
    desc_street = ""
    if true_desc:
        m_addr = re.search(
            r'\b(\d{2,5}\s+(?:[A-Z0-9][a-zA-Z0-9\.]*\s+){1,4}\b(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Way|Lane|Ln|Court|Ct|Parkway|Pkwy|Highway|Hwy)\b(?:,?\s*(?:Suite|Ste|Unit|#)\s*[A-Za-z0-9\-]+)?)',
            true_desc,
            re.IGNORECASE
        )
        if m_addr:
            cand = m_addr.group(1).strip()
            if not any(bad in cand.lower() for bad in ["pound", "lb", "lift", "must", "hour", "year", "week", "month", "associate", "percent"]):
                desc_street = cand
                if emp_match:
                    loc_match = resolve_branch_location(emp_match, location_hint=desc_street)

    # 2. Resolve Company, Branch, Address, City, State, Zip, Phone, Websites, Notes
    if emp_match and loc_match:
        company_brand = raw_company or emp_match.get("name", "")
        aliases_list = emp_match.get("aliases", [])
        corporate_aliases = aliases_list[0] if aliases_list else emp_match.get("name", "")
        branch_name = loc_match.get("location_name") or "Main Location"
        street_addr = loc_match.get("street_address") or desc_street or raw_loc
        city = loc_match.get("city") or "Redding"
        state = loc_match.get("state") or "CA"
        zip_code = loc_match.get("zip_code") or "96002"
        phone = loc_match.get("phone") or ""
        career_url = emp_match.get("career_url") or ""
        indeed_url = emp_match.get("indeed_url") or ""
        transit_notes = loc_match.get("notes") or emp_match.get("notes") or ""
        review_status = emp_match.get("review_status") or ("Verified" if emp_match.get("is_verified", 1) else "Pending")
        raba_acc = bool(loc_match.get("raba_accessible"))
        raba_stop = str(loc_match.get("raba_stop") or "")
    else:
        company_brand = raw_company
        corporate_aliases = ""
        branch_name = ""
        parsed_loc = parse_address_components(desc_street or raw_loc)
        street_addr = parsed_loc["street_address"]
        city = parsed_loc["city"]
        state = parsed_loc["state"]
        zip_code = parsed_loc["zip_code"]
        phone = ""
        career_url = ""
        indeed_url = ""
        transit_notes = ""
        review_status = "Unregistered"
        raba_acc, raba_stop = parse_raba_from_notes("", street_addr, city)

    # Build formatted Location string (Street, City, State Zip)
    if street_addr and city.lower() not in street_addr.lower():
        formatted_location = f"{street_addr}, {city}, {state} {zip_code}".strip(", ")
    elif street_addr and zip_code and zip_code not in street_addr:
        formatted_location = f"{street_addr} {zip_code}".strip()
    else:
        formatted_location = street_addr or f"{city}, {state} {zip_code}".strip()

    # 3. Resolve Industry Sector (Layer 1 Default + Layer 2 Role Override)
    base_sector = str(emp_match.get("industry_sector") or "Other").strip() if emp_match else "Other"
    raw_sector = str(job.get("industry") or job.get("sector") or "").strip()
    title_sector = "Other"
    try:
        from scrapper import determine_industry
        title_sector = determine_industry(raw_title, "", "")
    except Exception:
        pass

    distinct_role_sectors = {
        "Janitorial & Facilities",
        "Security & Public Safety",
        "Food & Restaurant",
        "Trades & Mechanics",
        "Transportation & Delivery",
        "Office & Clerical",
        "Childcare & Education Support",
        "Animal Care & Veterinary Services"
    }
    if title_sector in distinct_role_sectors and title_sector != base_sector:
        # Avoid reclassifying retail associates mentioning 'loss prevention' as Security
        if title_sector == "Security & Public Safety" and base_sector == "Retail & Sales" and not any(w in raw_title.lower() for w in ["guard", "security", "loss prevention", "asset protection"]):
            resolved_sector = base_sector
        else:
            resolved_sector = title_sector
    elif base_sector and base_sector not in ["Other", "N/A", ""]:
        resolved_sector = base_sector
    elif raw_sector and raw_sector not in ["Other", "N/A", ""]:
        resolved_sector = raw_sector
    elif title_sector and title_sector != "Other":
        resolved_sector = title_sector
    else:
        try:
            from scrapper import determine_industry
            resolved_sector = determine_industry(raw_title, company_brand, true_desc)
        except Exception:
            resolved_sector = "Other"

    # 4. Resolve Pay Rate / Starting Wage (Layer 1 Default + Layer 2 Job Override)
    base_wage = str(emp_match.get("starting_wage") or "").strip() if emp_match else ""
    if raw_pay and raw_pay.lower() not in ["n/a", "none", "", "unstated", "nan"]:
        resolved_pay = raw_pay
    elif base_wage and base_wage.lower() not in ["n/a", "none", "", "unstated", "nan", "varies"]:
        resolved_pay = base_wage
    else:
        resolved_pay = ""

    # Combine job-specific text for Layer 2 override detection
    job_text = f"{raw_title} {true_desc} {raw_exp}".lower()
    t_lower = raw_title.lower()
    shift_lower = raw_shift.lower()

    # 5. Resolve Min Age (Layer 1 Default + Layer 2 Job Override)
    base_min_age = 18
    if emp_match:
        raw_base_age = str(emp_match.get("min_age_baseline", 18)).strip()
        m_ba = re.search(r'\b(14|15|16|17|18|21)\b', raw_base_age)
        if m_ba:
            base_min_age = int(m_ba.group(1))

    job_age_override = None
    # Check 21+ role or text override
    if (
        re.search(r'\b(?:must\s*be\s*|minimum\s*age(?:\s*of)?\s*|at\s*least\s*|age\s*)21\b(?:\s*\+|\s*years?(?:\s*old)?|\s*or\s*older)?', job_text)
        or re.search(r'\b21\s*\+\b', job_text)
        or any(k in t_lower for k in ["bartender", "bar tender", "cocktail server", "casino", "gaming", "bus driver", "school bus"])
    ):
        job_age_override = 21
    # Check 18+ role or text override
    elif (
        re.search(r'\b(?:must\s*be\s*|minimum\s*age(?:\s*of)?\s*|at\s*least\s*|age\s*)(?:1[89]|20)\b(?:\s*\+|\s*years?(?:\s*old)?|\s*or\s*older)?', job_text)
        or re.search(r'\b18\s*\+\b', job_text)
        or any(k in shift_lower for k in ["graveyard", "noc", "overnight", "3rd shift", "third shift"])
        or any(k in t_lower for k in ["security guard", "forklift", "heavy equipment", "machine operator", "delivery driver", "route driver", "van driver", "courier", "truck driver"])
    ):
        job_age_override = 18
    # Check 16+ / youth friendly text override
    elif (
        re.search(r'\b(?:must\s*be\s*|minimum\s*age(?:\s*of)?\s*|at\s*least\s*|age\s*)1[4-7]\b(?:\s*\+|\s*years?(?:\s*old)?|\s*or\s*older)?', job_text)
        or re.search(r'\b1[4-7]\s*\+\b', job_text)
        or re.search(r'\b(?:youth[\s\-]friendly|teen[\s\-]friendly|teens\s*welcome|minors\s*welcome|hire\s*minors|hiring\s*minors|under\s*18\s*welcome|high\s*school\s*students?|student\s*position|work\s*permit)\b', job_text)
    ):
        job_age_override = 16

    resolved_min_age = job_age_override if job_age_override is not None else base_min_age

    # 6. Resolve Driver License Policy (Layer 1 Default + Layer 2 Job Override)
    base_dl = str(emp_match.get("drivers_license") or "Not Required").strip() if emp_match else "Not Required"
    explicit_no_dl = bool(re.search(
        r'\b(?:no\s+driver\'?s?\s*license(?:\s+required)?|driver\'?s?\s*license\s+not\s+required|no\s+dl\s+required|without\s+a\s+driver\'?s?\s*license)\b',
        job_text
    ))
    optional_cdl = bool(re.search(
        r'\bcdl[^\.\n;]{0,30}\b(?:a\s+plus|not\s+required|preferred|optional|helpful)\b',
        job_text
    ))
    has_cdl_a = not optional_cdl and bool(
        re.search(r'\b(?:class\s*a\s*cdl|cdl[\s\-]?a|commercial\s*driver\'?s?\s*license\s*\(?cdl[\s\-]?a\)?|class\s*a\s*commercial)\b', job_text)
        or (str(job.get("driverLicenseType") or "").lower().find("class a") >= 0)
    )
    has_cdl_b = not optional_cdl and (
        bool(re.search(r'\b(?:class\s*b\s*cdl|cdl[\s\-]?b|commercial\s*driver\'?s?\s*license\s*\(?cdl[\s\-]?b\)?|class\s*b\s*commercial)\b', job_text))
        or any(k in t_lower for k in ["bus driver", "school bus", "transit bus", "coach driver"])
        or (str(job.get("driverLicenseType") or "").lower().find("class b") >= 0)
    )
    has_class_c = not explicit_no_dl and (
        bool(re.search(
            r'\b(?:valid\s+(?:ca\s+|california\s+)?driver\'?s?\s*license|driver\'?s?\s*license\s*(?:\(class\s*c\))?\s*required|must\s+(?:have|possess)\s+(?:a\s+)?(?:valid\s+)?driver\'?s?\s*license|clean\s*(?:dmv|driving\s*record|mvr)|valid\s+class\s*c)\b',
            job_text
        ))
        or any(k in t_lower for k in ["driver", "delivery", "courier", "shuttle", "hauling", "trucker", "lot attendant", "valet", "porter"])
    )

    if has_cdl_a:
        resolved_dl = "Required (CDL Class A)"
    elif has_cdl_b:
        resolved_dl = "Required (CDL Class B)"
    elif has_class_c:
        resolved_dl = "Required (Class C)"
    elif explicit_no_dl:
        resolved_dl = "Not Required"
    else:
        if base_dl.lower() in ["role-dependent", "none", "unknown", "no", "not required", ""]:
            resolved_dl = "Not Required"
        else:
            resolved_dl = base_dl

    requires_dl_bool = ("required" in resolved_dl.lower() and "not required" not in resolved_dl.lower())
    if "class a" in resolved_dl.lower() or "cdl-a" in resolved_dl.lower():
        dl_type = "Commercial Class A (CDL-A)"
        resolved_min_age = max(resolved_min_age, 21)
    elif "class b" in resolved_dl.lower() or "cdl-b" in resolved_dl.lower():
        dl_type = "Commercial Class B (CDL-B)"
        resolved_min_age = max(resolved_min_age, 21)
    elif requires_dl_bool:
        dl_type = "Class C (Standard)"
        resolved_min_age = max(resolved_min_age, 18)
    else:
        dl_type = "None"

    # 7. Resolve HS Dip / GED Policy (Layer 1 Default + Layer 2 Job Override)
    base_hs = str(emp_match.get("hs_ged_baseline") or "Not Required").strip() if emp_match else "Not Required"
    explicit_no_hs = bool(re.search(
        r'\b(?:no\s+(?:high\s*school\s*)?(?:diploma|ged|degree)\s*(?:or\s*ged\s*)?(?:required|necessary)?|(?:high\s*school\s*diploma|ged)\s+not\s+required)\b',
        job_text
    ))
    mentions_hs = bool(re.search(
        r'\b(?:high\s*school\s*(?:diploma|equivalent|education|graduate)|h\.?s\.?\s*diploma|ged)\b',
        job_text
    ))
    if explicit_no_hs:
        resolved_hs = "Not Required"
    elif mentions_hs:
        if re.search(r'\b(?:high\s*school\s*(?:diploma|equivalent)|ged)[^\.\n;]{0,25}\b(?:preferred|desired|a\s+plus)\b', job_text) and not re.search(r'\b(?:high\s*school\s*(?:diploma|equivalent)|ged)[^\.\n;]{0,25}\b(?:required|mandatory|must)\b', job_text):
            resolved_hs = "Preferred"
        else:
            resolved_hs = "Required"
    else:
        if base_hs.lower() in ["no", "false", "none", "not required", "role-dependent", "unknown", ""]:
            resolved_hs = "Not Required"
        elif "pref" in base_hs.lower():
            resolved_hs = "Preferred"
        elif base_hs.lower() in ["yes", "true", "required"]:
            resolved_hs = "Required"
        else:
            resolved_hs = base_hs

    requires_hs_bool = (resolved_hs.lower() == "required")

    # 8. Resolve Drug Testing Policy (Layer 1 Default + Layer 2 Job Override)
    base_drug = str(emp_match.get("drug_testing") or "None").strip() if emp_match else "None"
    explicit_no_drug = bool(re.search(
        r'\b(?:no\s+drug\s*(?:test|screen|testing|screening)(?:\s+required)?|drug\s*(?:test|screen)\s+not\s+required)\b',
        job_text
    ))
    mentions_dot_drug = bool(re.search(r'\bdot\s+(?:pre[\s\-]?employment\s+)?drug\b', job_text)) or dl_type.startswith("Commercial")
    mentions_drug = bool(re.search(
        r'\b(?:drug\s*test(?:ing)?|drug\s*screen(?:ing)?|pre[\s\-]?employment\s*drug|substance\s*abuse\s*screen(?:ing)?)\b',
        job_text
    ))

    if explicit_no_drug:
        resolved_drug = "None"
    elif mentions_dot_drug:
        resolved_drug = "Required (DOT Panel)"
    elif mentions_drug:
        resolved_drug = "Required (Pre-employment)"
    else:
        if "role-dependent" in base_drug.lower():
            is_safety_role = requires_dl_bool or any(k in t_lower for k in [
                "forklift", "machine", "operator", "mechanic", "installer", "laborer", "construction",
                "warehouse", "material handler", "maintenance", "security", "caregiver", "cna", "medical", "nurse"
            ])
            resolved_drug = "Required (Safety-Sensitive Role)" if is_safety_role else "Role-Dependent"
        elif base_drug in ["Unknown", ""]:
            resolved_drug = "None"
        else:
            resolved_drug = base_drug

    requires_drug_bool = (
        "required" in resolved_drug.lower()
        and "not required" not in resolved_drug.lower()
        and "none" not in resolved_drug.lower()
    )

    # 9. Resolve Background Check Policy & Fair Chance / Felon Friendly (Layer 1 Default + Layer 2 Job Override)
    base_bg = str(emp_match.get("background_check") or "None").strip() if emp_match else "None"
    base_felon = str(emp_match.get("felon_friendly") or "Unknown").strip() if emp_match else "Unknown"

    explicit_no_bg = bool(re.search(
        r'\b(?:no\s+background\s*check(?:\s+required)?|background\s*check\s+not\s+required)\b',
        job_text
    ))
    mentions_livescan = bool(re.search(
        r'\b(?:live\s*scan|livescan|doj\s*clearance|fbi\s*fingerprint|fingerprint\s*clearance|criminal\s*justice\s*clearance)\b',
        job_text
    ))
    mentions_bg = bool(re.search(
        r'\b(?:background\s*check|criminal\s*background|background\s*screen(?:ing)?|background\s*investigation)\b',
        job_text
    ))

    if explicit_no_bg:
        resolved_bg = "None"
    elif mentions_livescan:
        resolved_bg = "Live Scan (DOJ/FBI)"
    elif mentions_bg:
        if "live scan" in base_bg.lower():
            resolved_bg = "Live Scan (DOJ/FBI)"
        elif base_bg in ["None", "Unknown", ""]:
            resolved_bg = "Standard"
        else:
            resolved_bg = base_bg
    else:
        if base_bg in ["Unknown", ""]:
            resolved_bg = "Live Scan (DOJ/FBI)" if resolved_sector in ["Childcare & Education Support", "Security & Public Safety"] else "None"
        else:
            resolved_bg = base_bg

    requires_bg_bool = (resolved_bg.lower() not in ["none", "no", "not required", "unknown", ""])

    if re.search(r'\b(?:fair[\s\-]chance|felon[\s\-]friendly|second[\s\-]chance\s*employer|background[\s\-]friendly|conviction[\s\-]friendly)\b', job_text):
        resolved_felon = "Yes"
    elif "live scan" in resolved_bg.lower() or re.search(r'\b(?:no\s+felon(?:y|ies)|clean\s+criminal\s+record\s+required)\b', job_text):
        resolved_felon = "No (Live Scan)" if "live scan" in resolved_bg.lower() else "No"
    elif base_felon not in ["Unknown", ""]:
        resolved_felon = base_felon
    else:
        resolved_felon = "Yes" if not requires_bg_bool else "Case-by-Case"

    # 10. Resolve Work Experience Policy (Layer 1 Default + Layer 2 Job Override)
    base_work_exp = str(emp_match.get("work_experience") or "None (Entry-Level)").strip() if emp_match else "None (Entry-Level)"
    if re.search(r'\b(?:no\s+(?:prior\s+)?experience\s+(?:required|necessary|needed)|0\s+years?\s+experience|zero\s+experience)\b', job_text):
        resolved_work_exp = "None (Entry-Level)"
    elif exp_yr_m := re.search(r'\b([1-2])\+?\s*(?:to\s*[2-3])?\s*years?(?:\s+of)?\s+(?:relevant\s+|related\s+|prior\s+|work\s+)?experience\b', job_text):
        ctx_window = job_text[max(0, exp_yr_m.start() - 25):min(len(job_text), exp_yr_m.end() + 35)]
        if any(w in ctx_window for w in ["prefer", "desire", "plus", "helpful"]):
            resolved_work_exp = f"{exp_yr_m.group(1)}+ Year Preferred"
        else:
            resolved_work_exp = f"{exp_yr_m.group(1)}+ Year Required"
    elif re.search(r'\b(?:6\s*months?|six\s*months?)\s+(?:of\s+)?(?:prior\s+|related\s+)?experience\b', job_text):
        resolved_work_exp = "Preferred (6+ mos)"
    else:
        resolved_work_exp = base_work_exp if base_work_exp not in ["None", "Unknown", ""] else "None (Entry-Level)"

    return {
        "employer_matched": bool(emp_match),
        "company_brand": company_brand,
        "corporate_aliases": corporate_aliases,
        "branch_name": branch_name,
        "street_address": street_addr,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "phone": phone,
        "location_full": formatted_location,
        "industry_sector": resolved_sector,
        "pay_rate": resolved_pay,
        "starting_wage_baseline": base_wage,
        "min_age": resolved_min_age,
        "fair_chance": resolved_felon,
        "drug_testing_policy": resolved_drug,
        "background_check_policy": resolved_bg,
        "driver_license_policy": resolved_dl,
        "hs_ged_policy": resolved_hs,
        "work_experience_policy": resolved_work_exp,
        "career_url": career_url,
        "indeed_url": indeed_url,
        "location_transit_notes": transit_notes,
        "review_status": review_status,
        "raba_accessible": raba_acc,
        "raba_stop": raba_stop,
        # Structured booleans/enums for Firestore & WRTP-CMS
        "requiresDrugTest": requires_drug_bool,
        "requiresBackgroundCheck": requires_bg_bool,
        "requiresDriverLicense": requires_dl_bool,
        "driverLicenseType": dl_type,
        "requiresHsDiplomaOrGed": requires_hs_bool,
    }


