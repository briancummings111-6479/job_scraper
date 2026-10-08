"""
Job Scraper for Indeed and Glassdoor - 2025 UC Version
Uses undetected-chromedriver to bypass Cloudflare
Educational purposes only - Review ToS before use
"""

import time
import random
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
    WebDriverException
)
import re
import json
from datetime import datetime, timedelta
import os
import pdfplumber

def load_search_config(config_file="search_config.json"):
    """Load search configuration from JSON file with fallback defaults."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, config_file)
    
    defaults = {
        "keywords": ["warehouse", "retail", "cashier", "cook", "dishwasher", "server", "custodian", "laborer", "stocker", "delivery", "caregiver", "groundskeeper"],
        "standard_keywords": ["warehouse", "retail", "cashier", "cook", "dishwasher", "server", "custodian", "laborer", "stocker", "delivery", "caregiver", "groundskeeper"],
        "all_keywords": ["account executive", "admin", "assistant", "Associate", "Attendant", "baker", "bar", "barista", "builder", "burger", "butcher", "cafe", "care", "caregiver", "carpenter", "cashier", "cdl", "chef", "clerk", "clinic", "cna", "construction", "consultant", "cook", "coordinator", "courier", "crew", "Custodian", "Customer Service", "data entry", "delivery", "dental", "dining", "dishwasher", "driver", "electrician", "engineer", "executive", "fast food", "food", "foreman", "Groundskeeper", "Handler", "health", "heavy equipment", "hospital", "host", "housekeeper", "hvac", "installer", "it", "janitor", "kitchen", "laborer", "landscaper", "lead", "maintenance", "management", "manager", "mechanic", "medical", "merchandiser", "network", "nurse", "office", "operations", "patient", "pharmacy", "pizza", "plumber", "receptionist", "representative", "restaurant", "retail", "rn", "sales", "sales associate", "secretary", "security guard", "server", "shipping", "site", "software", "Stocker", "store", "supervisor", "support", "systems", "taco", "team lead", "technician", "therapist", "transport", "truck", "warehouse", "welder"],
        "channels": ["Indeed", "Snagajob"],
        "location": ["Redding, CA 96002"],
        "radius": 15,
        "job_types": ["parttime", "fulltime"],
        "days_ago": 4,
        "max_pages": 3,
        "rejected_titles": ["surrogate", "surrogacy", "Owner Operator", "CDL A", "CDL B", "physician", "doctor", "registered nurse", "travel nurse", "rn", "director", "executive", "vice president", "vp", "chief", "manager", "supervisor", "attorney", "radiology", "therapist", "engineer", "software"],
        "rejected_employers": ["navy", "marines", "u.s. customs", "maersk", "vector marketing", "doordash", "uber", "lyft"],
        "industry_keywords": {
            "Animal Care & Veterinary Services": ["kennel", "veterinary", "vet aide", "pet bather", "groomer", "animal care", "shelter caretaker"],
            "Agriculture & Groundskeeping": ["farm hand", "nursery worker", "landscaper", "grounds maintenance", "groundskeeper", "farming"],
            "Childcare & Education Support": ["daycare aide", "preschool assistant", "tutor", "instructional aide", "childcare", "babysitter", "nanny"],
            "Construction & Laborers": ["construction laborer", "carpenter helper", "drywall apprentice", "site cleanup", "concrete laborer", "construction"],
            "Customer Service & Hospitality": ["front desk clerk", "guest services agent", "call center rep", "concierge", "customer service", "csr"],
            "Food & Restaurant": ["cook", "prep cook", "line cook", "dishwasher", "server", "busser", "host", "barista", "kitchen"],
            "Healthcare & Caregiving": ["caregiver", "home health aide", "direct support professional", "dsp", "cna", "nursing assistant"],
            "Janitorial & Facilities": ["custodian", "janitor", "housekeeper", "floor tech", "evs specialist", "cleaner"],
            "Manufacturing & Production": ["assembly line worker", "packaging operator", "production helper", "qa sorter", "machine operator", "assembler"],
            "Office & Clerical": ["receptionist", "file clerk", "data entry operator", "office assistant", "bank teller", "clerk"],
            "Personal Care & Services": ["salon assistant", "barber apprentice", "spa attendant", "hair stylist", "barber"],
            "Retail & Sales": ["sales associate", "canvasser", "appointment setter", "cashier", "stock associate", "merchandiser", "retail"],
            "Security & Public Safety": ["unarmed security guard", "gate attendant", "loss prevention associate", "security guard", "security officer"],
            "Social & Human Services": ["community outreach aide", "food bank sorter", "shelter support worker", "case aide"],
            "Technology & IT Support": ["helpdesk technician", "pc repair assistant", "cable installer helper", "it support"],
            "Trades & Mechanics": ["mechanic helper", "lube tech", "tire technician", "appliance repair assistant", "hvac helper", "plumber assistant", "electrician helper", "trade apprentice", "mechanic"],
            "Transportation & Delivery": ["route driver", "van delivery courier", "non-cdl delivery helper", "delivery driver", "courier"],
            "Warehouse & Logistics": ["package handler", "order picker", "forklift operator", "staging associate", "warehouse", "material handler"],
            "Other": ["general service worker", "event staff"]
        }
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                for key, val in loaded.items():
                    defaults[key] = val
        except Exception as e:
            print(f"[WARN] Error loading {config_file}: {e}. Using built-in defaults.")
            
    if not defaults.get("channels"):
        defaults["channels"] = ["Indeed", "Snagajob"]
    if not defaults.get("standard_keywords"):
        defaults["standard_keywords"] = list(defaults.get("keywords", []))
    if not defaults.get("all_keywords"):
        defaults["all_keywords"] = list(defaults.get("standard_keywords", []))
    if not defaults.get("keyword_groups"):
        defaults["keyword_groups"] = dict(defaults.get("industry_keywords", {}))
            
    return defaults

EXPIRED_JOB_PHRASES = [
    "this job has expired on indeed",
    "reasons could include: the employer is not accepting applications",
    "the employer is not accepting applications",
    "not actively hiring",
    "is reviewing applications",
    "job has expired",
    "job is no longer available",
    "the job below is no longer available",
    "is no longer available",
    "position has been filled",
    "job is closed",
    "no longer accepting applications",
    "this listing has expired",
    "posting has closed",
]

DEGREE_QUALIFICATION_REJECTIONS = [
    r"\bbachelor'?s(?:\s+degree)?\s+required\b",
    r"\bmaster'?s(?:\s+degree)?\b",
    r"\bph\.?d\b",
    r"\bdoctorate\b",
    r"\bboard certified\b",
    r"\bbcba\b",
    r"\bboard\s+certified\s+behavior\s+analyst\b",
    r"\blcsw\b",
    r"\blmft\b",
    r"\blpcc\b",
    r"\blpc\b",
    r"\blicensed professional counselor\b",
    r"\blicensed\s+(?:prosthetist|orthotist)\b",
    r"\b(?:registered|licensed)\s+dieti[tc]ian\b",
    r"\b(?:licensed\s+veterinarian|dvm\s+required)\b",
    r"\blvn\b",
    r"\blpn\b",
    r"\blicensed vocational nurse\b",
    r"\botr\b",
    r"\bover[\s\-]the[\s\-]road\b",
    r"\bactive secret clearance\b",
    r"\btop secret clearance\b",
    r"\brespiratory\s+(?:care\s+)?practitioner\b",
    r"\b(?:must\s+be\s+a\s+|licensed\s+|certified\s+)(?:respiratory|physical|occupational)\s+therapist\b",
    r"\brrt\b",
    r"\bcrt\b",
    r"\b(?:must\s+be\s+a\s+|licensed\s+|certified\s+)speech\s+(?:language\s+)?pathologist\b",
    r"\b(?:must\s+be\s+a\s+|licensed\s+|certified\s+)radiologic\s+technologist\b",
    r"\barrt(?:\s*\([a-z\s]+\))?\b",
    r"\bepa\s+(?:universal|section\s+608|608)\b",
    r"\b1099\s+(?:contractor|position|basis)\b",
    r"\bindependent\s+contractor\b",
    r"\bown\s+(?:tools|vehicle|equipment)\s+required\b",
    r"\bmust\s+provide\s+own\s+tools\b",
    r"\bmust\s+have\s+(?:own\s+)?tools\b",
    r"\b(?:current\s+)?forklift\s+certif(?:ication|ied)\s+required\b",
    r"\bmust\s+be\s+forklift\s+certified\b",
    r"\bassociate\s+(?:ii|iii|iv|v)\b",
    r"\blevel\s+(?:ii|iii|iv|v|2|3|4|5)\b",
    r"\btier\s+(?:ii|iii|iv|v|2|3|4|5)\b",
    r"\b(?:experience|experienced)\s+only\b",
    r"\b(?:must\s+be\s+willing\s+to\s+travel|extensive\s+travel\s+required)\b",
]

def check_excessive_experience_requirement(text: str) -> tuple[bool, str]:
    """
    Evaluates whether candidate work experience prerequisites exceed entry-level ceilings (3+ years).
    Explicitly filters out false positives from company history ('serving for 25 years')
    and driver license duration ('licensed for 3 years').
    """
    if not text:
        return False, ""
    patterns = [
        r'\b(?:minimum(?:\s+of)?|at\s+least|must\s+have|require[ds]?)\s+([3-9]|\d{2,})\+?\s*years?(?:\s+of)?(?:\s+[A-Za-z\/\-]{1,25}){0,3}\s+experience\b',
        r'\b([3-9]|\d{2,})\+?\s*years?(?:\s+of)?(?:\s+[A-Za-z\/\-]{1,25}){0,4}\s+experience(?:\s+[A-Za-z\/\-]{1,25}){0,3}\s+(?:is\s+)?required\b',
        r'\bminimum\s+(?:of\s+)?([3-9]|\d{2,})\+?\s*years\b',
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            start = max(0, m.start() - 50)
            end = min(len(text), m.end() + 50)
            ctx = text[start:end].lower()
            if any(h in ctx for h in ['in business', 'serving', 'founded', 'our company', 'we have', 'combined experience', 'years of excellence', 'years serving']):
                continue
            if 'driving' in ctx or "driver's license" in ctx or 'licensed driver' in ctx:
                continue
            return True, f"Requires 3+ years experience: '{m.group(0)}'"
    return False, ""

def is_expired_job_content(text: str) -> bool:
    if not text:
        return False
    text_lower = str(text).lower()
    for phrase in EXPIRED_JOB_PHRASES:
        if phrase in text_lower:
            return True
    return False

SHASTA_CITIES = [
    "redding", "anderson", "shasta lake", "burney", "cottonwood",
    "palo cedro", "bella vista", "millville", "fall river mills",
    "mcarthur", "shingletown", "castella", "french gulch", "igo",
    "ono", "oak run", "round mountain", "montgomery creek", "cassel",
    "old station", "whitmore", "platina", "hat creek", "lakehead",
    "keswick", "shasta"
]

SHASTA_ZIPS = [
    "96001", "96002", "96003", "96007", "96008", "96011", "96013",
    "96016", "96019", "96022", "96028", "96033", "96040", "96047",
    "96049", "96051", "96056", "96062", "96065", "96069", "96070",
    "96071", "96073", "96084", "96087", "96088", "96089", "96096", "96099"
]

def clean_location_str(loc: str) -> str:
    if not loc:
        return "Redding, CA"
    # Remove UI artifacts from web scrapers like 'open_in_new'
    cleaned = re.sub(r'open_in_new|open in new', '', str(loc), flags=re.IGNORECASE)
    # Replace newlines with comma-space
    cleaned = re.sub(r'[\r\n]+', ', ', cleaned)
    cleaned = re.sub(r'\s*,\s*', ', ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(' ,')
    # Standardize 'California' to 'CA'
    cleaned = re.sub(r'\bCalifornia\b', 'CA', cleaned, flags=re.IGNORECASE)
    return cleaned if cleaned else "Redding, CA"

KNOWN_REDDING_ADDRESSES = {
    "dick's sporting goods": "1030 Dana Dr, Redding, CA 96002",
    "dicks sporting goods": "1030 Dana Dr, Redding, CA 96002",
    "five below": "1476 Dana Dr, Redding, CA 96002",
    "safeway": "1070 E Cypress Ave, Redding, CA 96002",
    "safeway 1070": "1070 E Cypress Ave, Redding, CA 96002",
    "safeway pine": "2275 Pine St, Redding, CA 96001",
    "bechelli ampm": "2686 Bechelli Ln, Redding, CA 96002",
    "ampm": "2686 Bechelli Ln, Redding, CA 96002",
    "dabella": "3685 Caterpillar Rd, Redding, CA 96003",
    "lkq": "3737 Mountain Lakes Blvd, Redding, CA 96003",
    "lkq corporation": "3737 Mountain Lakes Blvd, Redding, CA 96003",
    "jd residential": "1530 Victor Ave, Redding, CA 96003",
    "jd residential services": "1530 Victor Ave, Redding, CA 96003",
    "nafe": "Redding, CA 96002",
    "winco": "1050 Old Alturas Rd, Redding, CA 96003",
    "winco foods": "1050 Old Alturas Rd, Redding, CA 96003",
    "walmart": "1515 Dana Dr, Redding, CA 96002",
    "target": "1280 Dana Dr, Redding, CA 96002",
    "home depot": "1201 Dana Dr, Redding, CA 96002",
    "lowe's": "1800 Churn Creek Rd, Redding, CA 96002",
    "lowes": "1800 Churn Creek Rd, Redding, CA 96002",
    "in-n-out": "1275 Dana Dr, Redding, CA 96002",
    "in n out": "1275 Dana Dr, Redding, CA 96002",
    "costco": "1525 Dana Dr, Redding, CA 96002",
    "ross": "1650 Hilltop Dr, Redding, CA 96002",
    "tj maxx": "1235 Dana Dr, Redding, CA 96002",
    "marshalls": "1235 Dana Dr, Redding, CA 96002",
    "dollar tree": "2600 Churn Creek Rd, Redding, CA 96002",
    "dollar general": "1940 Shasta St, Redding, CA 96001",
    "autozone": "2280 Pine St, Redding, CA 96001",
    "o'reilly": "2450 Athens Ave, Redding, CA 96001",
    "oreilly": "2450 Athens Ave, Redding, CA 96001",
    "hobby lobby": "945 Dana Dr, Redding, CA 96002",
    "tractor supply": "2850 Churn Creek Rd, Redding, CA 96002",
    "harbor freight": "1705 E Cypress Ave, Redding, CA 96002",
    "dutch bros": "1980 E Cypress Ave, Redding, CA 96002",
    "mcdonald's": "1245 Dana Dr, Redding, CA 96002",
    "mcdonalds": "1245 Dana Dr, Redding, CA 96002",
    "wendy's": "1210 Dana Dr, Redding, CA 96002",
    "taco bell": "1225 Dana Dr, Redding, CA 96002",
    "starbucks": "1520 Dana Dr, Redding, CA 96002",
    "panda express": "1220 Dana Dr, Redding, CA 96002",
    "chipotle": "1100 Dana Dr, Redding, CA 96002",
    "mercy medical center": "2175 Rosaline Ave, Redding, CA 96001",
    "shasta regional": "1100 Butte St, Redding, CA 96001",
    "hilltop medical": "1093 Hilltop Dr, Redding, CA 96003",
    "shasta community health": "1035 Placer St, Redding, CA 96001",
    "fedex": "6310 Mountain Shadows Dr, Redding, CA 96003",
    "ups": "4660 Mountain Lakes Blvd, Redding, CA 96003",
    "usps": "1647 Court St, Redding, CA 96001",
    "sierra pacific": "19794 Riverside Ave, Anderson, CA 96007",
}

def resolve_business_address(company: str = "", location: str = "", description: str = "", gemini_address: str = None) -> str:
    """
    Resolves the physical street address of the employer/worksite in the Redding/Shasta County area.
    Crucial for workforce participants who rely on Redding Area Bus Authority (RABA) transit lines.
    """
    # 1. Use Gemini-resolved address if it includes a street number and valid locality
    if gemini_address and str(gemini_address).strip() not in ["N/A", "None", "", "Unstated"]:
        clean_g = clean_location_str(gemini_address)
        if not any(bad in clean_g.lower() for bad in ["pound", "lb", "lift", "associate must", "year", "hour", "week"]):
            if re.search(r'\d+', clean_g) and ("redding" in clean_g.lower() or "anderson" in clean_g.lower() or "shasta" in clean_g.lower() or "ca" in clean_g.lower()):
                return clean_g

    # 2. Check known employer physical directory
    c_lower = str(company or "").lower().strip()
    for known_name, addr in KNOWN_REDDING_ADDRESSES.items():
        if known_name in c_lower or c_lower in known_name:
            return addr

    # 3. Search description text for street address patterns in Shasta County
    if description:
        m = re.search(
            r'\b(\d{2,5}\s+(?:[A-Z0-9][a-zA-Z0-9\.]*\s+){1,4}\b(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Way|Lane|Ln|Court|Ct|Parkway|Pkwy|Highway|Hwy)\b(?:,?\s*(?:Suite|Ste|Unit|#)\s*[A-Za-z0-9\-]+)?)(?:,?\s*([A-Za-z\s]+),?\s*(?:CA)?\s*(\d{5})?)?',
            description,
            re.IGNORECASE
        )
        if m:
            street = m.group(1).strip()
            # Discard false positives (e.g. "35 pounds... The associate must")
            if not any(bad in street.lower() for bad in ["pound", "lb", "lift", "must", "hour", "year", "week", "month", "associate", "percent"]):
                city = m.group(2).strip() if m.group(2) else "Redding"
                if "redding" not in city.lower() and "anderson" not in city.lower():
                    city = "Redding"
                return clean_location_str(f"{street}, {city}, CA")

    # 4. Fallback to cleaned location string or default Redding zip
    return clean_location_str(location or "Redding, CA 96002")


def is_shasta_county_location(loc_str: str, text_context: str = "") -> tuple:
    if not loc_str or str(loc_str).strip() in ["N/A", "None", ""]:
        return False, "Empty location"

    cleaned_loc = clean_location_str(loc_str)
    loc_lower = cleaned_loc.lower()

    # 1. Check for Shasta County zip codes
    for z in SHASTA_ZIPS:
        if re.search(r'\b' + z + r'\b', loc_lower):
            return True, cleaned_loc

    # 2. Check for Shasta County city/community names
    for city in SHASTA_CITIES:
        if re.search(r'\b' + re.escape(city) + r'\b', loc_lower):
            return True, cleaned_loc

    # 3. Explicit Shasta County mention
    if "shasta county" in loc_lower or "shasta county, ca" in loc_lower:
        return True, cleaned_loc

    return False, f"Out of Shasta County: {cleaned_loc}"

def clean_job_title(title: str) -> str:
    if not title:
        return ""
    cleaned = str(title)
    # Fix unicode replacement and special characters
    cleaned = cleaned.replace('\ufffd', ' - ').replace('\u2013', '-').replace('\u2014', '-').replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"')
    cleaned = re.sub(r'[\r\n\s]*-?\s*job post.*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'^[•▪\-\*]\s*|^[oO]\s+', '', cleaned)
    cleaned = re.sub(r'\s*-\s*-+\s*', ' - ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip(' -')

BOGUS_TITLE_PATTERNS = [
    r'\bjobs\s+in\b',                             # e.g., "retail jobs in Redding, CA 96002"
    r"we\s+can'?t\s+find\s+this\s+page",          # Indeed 404 page heading
    r"page\s+not\s+found",                        # Generic 404
    r"additional\s+verification\s+required",      # Bot verification prompt
    r"verify\s+you\s+are\s+human",                # Captcha
    r"just\s+a\s+moment",                         # Cloudflare
    r"attention\s+required",                      # Cloudflare
    r"access\s+denied",                           # 403 Forbidden
    r"error\s+404",                               # Error code
    r"security\s+check",                          # Security check
    r"please\s+enable\s+cookies",                 # Cookie warning
    r"enable\s+javascript",                       # JS warning
    r"^job\s+search\b",                           # Search header
    r"^search\s+results\b",                       # Search results header
]

def is_bogus_title(title: str) -> bool:
    if not title:
        return True
    t = str(title).strip()
    if len(t) <= 2:
        return True
    for pat in BOGUS_TITLE_PATTERNS:
        if re.search(pat, t, re.IGNORECASE):
            return True
    return False

def is_pay_exceeding_ceiling(pay_text: str, max_hourly: float = 38.0, max_annual: float = 75000.0) -> tuple:
    if not pay_text or pay_text == "N/A":
        return False, ""
    s = str(pay_text).lower().replace(",", "")

    # Check 'k' notation: $80k, $100k - $120k
    k_matches = re.findall(r'(\d+(?:\.\d+)?)\s*k\b', s)
    if k_matches:
        vals = [float(x) * 1000 for x in k_matches]
        if min(vals) >= max_annual:
            return True, f"Annual pay exceeds entry-level ceiling: ${min(vals):,.0f}"

    is_annual = any(w in s for w in ["year", "yr", "annual", "annually", "/yr", "per year"])
    is_monthly = any(w in s for w in ["month", "mo", "monthly", "/mo", "per month"])
    is_weekly = any(w in s for w in ["week", "wk", "weekly", "/wk", "per week"])
    is_hourly = any(w in s for w in ["hour", "hr", "hourly", "/hr", "per hour"])
    
    # Extract numbers with optional decimals
    raw_nums = re.findall(r'\$(\d+(?:\.\d+)?)', s)
    if not raw_nums:
        raw_nums = re.findall(r'\b(\d+(?:\.\d+)?)\b', s)

    if raw_nums:
        try:
            nums = [float(x) for x in raw_nums]
            min_val = min(nums)
            max_val = max(nums)

            # Weekly pay ceiling: e.g. $2,616 per week -> exceeds $1,520/wk ($38/hr * 40h or $75k / 52)
            if is_weekly:
                max_weekly = max(max_hourly * 40.0, max_annual / 52.0)
                if min_val >= max_weekly or min_val * 52 >= max_annual:
                    return True, f"Weekly compensation exceeds entry-level ceiling: ${min_val:,.0f}/wk"
                elif max_val >= max_weekly + 300.0:
                    return True, f"Weekly compensation range exceeds entry-level ceiling: up to ${max_val:,.0f}/wk"

            # Monthly pay ceiling: e.g. $6,500/month -> exceeds $6,250/mo ($75k / 12)
            elif is_monthly:
                max_monthly = max_annual / 12.0
                if min_val >= max_monthly or min_val * 12 >= max_annual:
                    return True, f"Monthly compensation exceeds entry-level ceiling: ${min_val:,.0f}/mo"
                elif max_val >= max_monthly + 1000.0:
                    return True, f"Monthly compensation range exceeds entry-level ceiling: up to ${max_val:,.0f}/mo"

            # Annual pay ceiling: e.g. $80,000/yr or standalone >= $15,000
            elif is_annual or min_val >= 15000:
                if min_val >= max_annual:
                    return True, f"Annual compensation exceeds entry-level ceiling: ${min_val:,.0f}"
                elif max_val >= max_annual + 15000:
                    return True, f"Annual compensation range exceeds entry-level ceiling: up to ${max_val:,.0f}"

            # Hourly pay ceiling: e.g. $39/hr or standalone < 1000
            else:
                if min_val >= max_hourly:
                    return True, f"Hourly compensation exceeds entry-level ceiling: ${min_val:.2f}/hr"
                elif max_val >= max_hourly + 10.0:
                    return True, f"Hourly compensation range exceeds entry-level ceiling: up to ${max_val:.2f}/hr"
        except:
            pass

    return False, ""

def is_rejected_job(title: str, company: str = "", description: str = "", config: dict = None, pay: str = "", location: str = "") -> tuple:
    if config is None:
        config = load_search_config()
    
    # Check bogus or error title
    if not title or is_bogus_title(title):
        return True, f"Bogus or invalid title: '{title}'"

    # Location Check: Must reside in Shasta County, CA
    if location and str(location).strip() not in ["N/A", "None", ""]:
        is_shasta, loc_reason = is_shasta_county_location(location)
        if not is_shasta:
            return True, loc_reason

    t_clean = clean_job_title(title)
    if is_bogus_title(t_clean):
        return True, f"Bogus or invalid title: '{t_clean}'"
    t_lower = t_clean.lower()
    c_lower = str(company or "").lower().strip()
    d_lower = str(description or "").lower()

    # Check pay ceiling
    if pay and pay != "N/A":
        # Guard against known promotional / gig banner artifacts (e.g. DoorDash "$53.85/hr", Surrogacy "$100k-$115k", Panel "$50-$100") on standard entry-level titles
        is_standard_entry = any(k in t_lower for k in [
            "dish", "cook", "cashier", "server", "barista", "food service", "team member", "guest advocate",
            "attendant", "host", "custodian", "janitor", "cleaner", "laundry", "housekeeper", "stocker",
            "clerk", "retail", "laborer", "aide", "caregiver", "babysitter", "childcare", "nanny",
            "child care", "front desk", "receptionist", "customer service", "demonstrator", "driver",
            "helper", "associate", "camp staff", "assistant", "flagger", "parts washer", "crew", "sales",
            "stylist", "line cook", "prep cook", "dining"
        ])
        is_promo_wage = any(art in str(pay).lower() for art in [
            "53.85", "112,000", "115,000", "100,000", "48.08", "55.29", "50k", "60k", "75k", "85k"
        ])
        if is_standard_entry and is_promo_wage:
            pass  # Ignore promotional banner artifact on entry-level titles
        else:
            exceeds, reason = is_pay_exceeding_ceiling(pay)
            if exceeds:
                return True, reason

    # Check rejected employers
    rejected_employers = config.get("rejected_employers", [])
    for rej_emp in rejected_employers:
        if rej_emp.lower() in c_lower:
            return True, f"Rejected employer: {rej_emp}"

    # Check rejected titles
    rejected_titles = config.get("rejected_titles", [])
    for rej_title in rejected_titles:
        r_t = rej_title.lower()
        if r_t in ["senior", "sr."]:
            # Disambiguate: protect senior citizen care/living positions
            if any(elder in t_lower for elder in ["senior care", "senior living", "senior companion", "caregiver", "senior community", "senior services"]):
                continue
        if re.search(r'\b' + re.escape(r_t) + r'\b', t_lower):
            return True, f"Rejected title keyword: {rej_title}"

    # Check Remote / Work-from-home / Online survey or research panels
    if re.search(r'\b(?:remote|work\s+from\s+home|wfh|out\s+of\s+office|telecommute|virtual)\b', t_lower):
        return True, f"Remote / Work-from-home position: '{t_clean}'"
    if re.search(r'\b(?:paid\s+research\s+panelist|focus\s+group\s+participant|paid\s+focus\s+group|paid\s+study\s+panelist|online\s+survey\s+taker|survey\s+panelist|research\s+study\s+panelist|research\s+panelist)\b', t_lower):
        return True, f"Online survey / focus group panel position: '{t_clean}'"
    if d_lower and re.search(r'\b(?:100%\s+remote|fully\s+remote|work\s+from\s+home\s+position|remote\s+paid\s+research|paid\s+research\s+panelist|paid\s+focus\s+group|focus\s+group\s+participant|online\s+survey\s+taker|survey\s+panelist|research\s+study\s+panelist)\b', d_lower):
        return True, "Remote / Online survey or panel position in description"

    # Check Travel Healthcare / Travel Contract / Radiologic Technologist positions
    if re.search(r'\b(?:travel\s+ct|travel\s+tech|travel\s+technologist|travel\s+nurse|traveling\s+nurse|travel\s+contract|travel\s+assignment|allied\s+travel)\b', t_lower):
        return True, f"Travel healthcare / contract assignment: '{t_clean}'"
    if re.search(r'\b(?:ct\s+(?:tech|technologist)|radiologic\s+technologist|radiology\s+tech(?:nologist)?|ultrasound\s+tech|x[\s\-]ray\s+tech|mri\s+tech)\b', t_lower):
        return True, f"Radiology / Imaging technologist requires ARRT radiology credentials: '{t_clean}'"
    if d_lower and re.search(r'\b(?:travel\s+assignment|travel\s+contract|allied\s+travel\s+careers|travel\s+healthcare)\b', d_lower):
        return True, "Travel healthcare / non-local assignment in description"

    # Check Surrogacy / Egg Donor / Plasma Donation / Clinical study positions
    if re.search(r'\b(?:surrogate|surrogacy|egg\s+donor|sperm\s+donor|plasma\s+donor|plasma\s+donation|healthy\s+pregnancy)\b', t_lower):
        return True, f"Surrogacy / Medical donor opportunity: '{t_clean}'"
    is_care_role = any(k in t_lower for k in ["caregiver", "personal assistant", "babysitter", "childcare", "nanny", "child care", "hospitality aide", "senior care", "companion"])
    if not is_care_role and d_lower and re.search(r'\b(?:become\s+a\s+surrogate|earn\s+up\s+to\s+\$?\d+[\d,]*\s+as\s+a\s+surrogate|surrogacy\s+journey|egg\s+donation\s+program)\b', d_lower):
        return True, "Surrogacy / Medical donor opportunity in description"

    # Check Foreman / Supervisory
    if re.search(r'\bforeman\b', t_lower):
        return True, f"Supervisory role (Foreman): '{t_clean}'"

    # Check Experienced trade prefix (e.g. Experienced Carpenter, Experienced Welder)
    if re.search(r'\bexperienced\s+(?:carpenter|welder|technician|tech|plumber|electrician|installer|mechanic|driver|operator|laborer)\b', t_lower) or t_lower.startswith("experienced "):
        return True, f"Non-entry-level: '{t_clean}' (requires experienced journeyman)"

    # Check Professional planning roles
    if re.search(r'\b(?:municipal|urban|city|regional|land\s+use|environmental)?\s*planner\b', t_lower):
        return True, f"Professional planning role: '{t_clean}' (requires urban planning/public admin degree)"

    # Check Senior tiers (Associate II, Associate III, Level II, Level III, Tier II, etc.)
    if re.search(r'\b(?:associate|clerk|technician|assistant|operator|specialist|analyst|worker)\s+(?:ii|iii|iv|v|2|3|4|5)\b', t_lower) or re.search(r'\b(?:level|tier|grade)\s+(?:ii|iii|iv|v|2|3|4|5)\b', t_lower):
        return True, f"Senior tier level: '{t_clean}'"

    # Check Skilled trade installers (e.g. Acrylic Bath Installer)
    if re.search(r'\b(?:acrylic\s+)?bath\s+installer\b', t_lower) or (re.search(r'\binstaller\b', t_lower) and any(w in t_lower for w in ["bath", "cabinet", "flooring", "granite", "roofing", "solar", "hvac"])):
        return True, f"Skilled trade installer (not helper/apprentice): '{t_clean}'"

    # Check HVAC technician unless accompanied by helper/assistant/apprentice/trainee
    if re.search(r'\bhvac\s+(?:technician|tech|installer|mechanic)\b', t_lower):
        if not any(w in t_lower for w in ["helper", "assistant", "apprentice", "trainee"]):
            return True, f"HVAC technician requires trade certification (not helper/apprentice): '{t_clean}'"

    # Check Lead / Master / Field / Heavy Equipment Mechanic & Trade Leadership
    if re.search(r'\b(?:lead|master|chief|supervising)\s+(?:mechanic|carpenter|technician|tech|installer|electrician|plumber|painter|driver|operator|cook)\b', t_lower):
        return True, f"Lead / Supervisory trade role: '{t_clean}'"
    if re.search(r'\bfield\s+mechanic\b', t_lower):
        return True, f"Field Mechanic requires journeyman diagnostic & field experience: '{t_clean}'"
    if re.search(r'\b(?:heavy\s+equipment|diesel)\s+mechanic\b', t_lower) and not any(w in t_lower for w in ["helper", "assistant", "apprentice", "trainee"]):
        return True, f"Heavy equipment / diesel mechanic requires journeyman skills: '{t_clean}'"
    if re.search(r'\b(?:experience|experienced)\s+only\b', t_lower):
        return True, f"Non-entry-level ('experience only' specified in title): '{t_clean}'"

    # Check On-Call / IT Field Technician (1099 independent contractor)
    if re.search(r'\b(?:on[\s\-]call\s+)?(?:it\s+)?field\s+technician\b', t_lower):
        return True, f"Field technician / 1099 on-call tech role: '{t_clean}'"

    # Check Out-of-area staffing syndication tags like (ONTB)
    if re.search(r'\((?:ontb?|lax|chi|phx|dal|hou|dfw|atl)\)', t_lower):
        return True, f"Out-of-area staffing syndication tag in title: '{t_clean}'"

    # Check candidate excessive experience requirements (3+ years work experience)
    comb_text = f"{t_lower}\n{d_lower}"
    is_exp_rej, exp_reason = check_excessive_experience_requirement(comb_text)
    if is_exp_rej:
        return True, exp_reason

    # Check degree & qualification rejections
    for pat in DEGREE_QUALIFICATION_REJECTIONS:
        if re.search(pat, comb_text, re.IGNORECASE):
            return True, f"Non-entry-level requirement matched pattern: {pat}"

    # Check pay ceiling from description if not passed explicitly
    if not pay and d_lower:
        desc_pay = extract_pay(description)
        is_promo = any(art in str(desc_pay).lower() for art in ["53.85", "112,000", "115,000", "100,000", "48.08", "55.29", "50k", "60k", "75k", "85k"])
        if desc_pay and not is_promo:
            exceeds, reason = is_pay_exceeding_ceiling(desc_pay)
            if exceeds:
                return True, reason

    return False, ""


def determine_industry(job_title, company, description=""):
    title = str(job_title).lower() if job_title else ""
    comp = str(company).lower() if company else ""
    desc = str(description).lower() if description else ""
    t_c = f"{title} {comp}"
    
    config = load_search_config()
    keywords = config.get('industry_keywords', {})
    
    # Flatten and sort pairs by tag length descending so specific multi-word phrases match before generic single words
    sorted_pairs = []
    for industry, tags in keywords.items():
        for tag in tags:
            sorted_pairs.append((industry, str(tag).strip().lower()))
    sorted_pairs.sort(key=lambda x: len(x[1]), reverse=True)
    
    # Pass 1: Title + Company
    for industry, tag in sorted_pairs:
        pattern = r'\b' + re.escape(tag) + r'\b'
        if re.search(pattern, t_c):
            return industry

    # Pass 2: Description (duties and context)
    if desc:
        for industry, tag in sorted_pairs:
            pattern = r'\b' + re.escape(tag) + r'\b'
            if re.search(pattern, desc):
                return industry
                    
    return "Other"

# ============================================================
# TEEN-FRIENDLY QUALIFICATION & EMPLOYER REGISTRY
# Grounded in Redding Area Employers database & known under-18 employers
# ============================================================
KNOWN_TEEN_EMPLOYERS = {
    # Fast food & quick service (classic under-18 employers)
    "mcdonald's", "mcdonalds",
    "taco bell",
    "chick-fil-a", "chick fil a", "bird hospitality",
    "in-n-out burger", "in-n-out", "in n out",
    "dutch bros coffee", "dutch bros",
    "wendy's", "wendys",
    "burger king", "bk",
    "carl's jr.", "carl's jr", "carls jr",
    "jack in the box",
    "subway",
    "panda express",
    "dairy queen", "dq", "blue jay foods",
    "sonic drive-in", "sonic drive in", "sonic",
    "raising cane's", "raising canes",
    "chipotle", "chipotle mexican grill",
    "arby's", "arbys",
    "little caesars", "little caesar",
    "papa murphy's", "papa murphys",
    "baskin-robbins", "baskin robbins",
    "cold stone creamery", "cold stone",
    "crumbl cookies", "crumbl",
    "jamba", "jamba juice",
    "auntie anne's", "auntie annes",
    "wetzel's pretzels", "wetzels pretzels",
    "panera bread", "panera",
    "chuck e. cheese", "chuck e cheese",
    "kfc", "kentucky fried chicken",
    "popeyes", "popeyes louisiana kitchen",
    "wingstop",
    "wienerschnitzel",
    "a&w", "a&w restaurant",
    "starbucks", "starbucks coffee",

    # Retail / entertainment employers officially hiring age 14-17 (from Redding Area Employers)
    "ace hardware",
    "american eagle outfitters", "american eagle",
    "autozone",
    "barnes & noble", "barnes and noble",
    "best buy",
    "buckle", "the buckle",
    "cattlemans steakhouse", "cattlemans",
    "cinemark", "cinemark theaters",
    "claire's", "claires",
    "cvs", "cvs pharmacy", "cvs health",
    "five below",
    "grocery outlet",
    "home depot", "the home depot",
    "hot topic",
    "journey's", "journeys",
    "logan's roadhouse", "logans roadhouse",
    "michaels stores", "michaels",
    "premier oil change",
    "spencer gifts", "spencers",
    "sprouts farmers market", "sprouts",
    "target",
    "tractor supply company", "tractor supply",
    "regal cinemas", "regal",
    "menchie's", "menchies",
    "yogurtland",
    "old navy",
    "ross dress for less", "ross stores", "ross",
    "kohl's", "kohls",
    "jcpenney",
}

def normalize_company_for_matching(comp: str) -> str:
    if not comp:
        return ""
    s = str(comp).lower()
    s = re.sub(r'[\'\’\`]', '', s)
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def is_known_teen_employer(comp: str) -> bool:
    if not comp:
        return False
    norm = normalize_company_for_matching(comp)
    if not norm:
        return False
    for known in KNOWN_TEEN_EMPLOYERS:
        k_norm = normalize_company_for_matching(known)
        if k_norm == norm:
            return True
        if f" {k_norm} " in f" {norm} " or norm.startswith(f"{k_norm} ") or norm.endswith(f" {k_norm}"):
            return True
    return False

def is_teen_friendly(
    title: str = "",
    company: str = "",
    text: str = "",
    requirements: str = "",
    job_dict: dict = None,
    gemini_teen_friendly: bool = None
) -> bool:
    """
    Evaluates whether a job posting is available to youth under 18 years of age (ages 14-17).
    Rule: Do not check this box unless the employer is specifically known to hire under age 18
    (like McDonald's or Taco Bell) or it is clearly stated in the job description.
    """
    if job_dict:
        title = title or str(job_dict.get('job_title') or job_dict.get('title') or '')
        company = company or str(job_dict.get('company') or '')
        text = text or str(job_dict.get('description') or '')
        requirements = requirements or str(job_dict.get('experience') or job_dict.get('requirements') or '')

    combined_text = f"{title} {company} {text} {requirements}".lower()

    # 1. HARD DISQUALIFICATIONS (Overrides everything - minors cannot do these or employers explicitly exclude them)
    # A. Explicit adult age requirement (18+, 21+, 22+, 25+, etc.)
    if re.search(r'\b(?:must\s*be\s*|minimum\s*age(?:\s*of)?\s*|at\s*least\s*|age\s*)(?:1[89]|[2-6]\d)\b(?:\s*\+|\s*years?(?:\s*old)?|\s*or\s*older)?', combined_text):
        return False
    if re.search(r'\b(?:1[89]|[2-6]\d)\s*\+\b', combined_text):
        return False
    if re.search(r'\b(?:1[89]|[2-6]\d)\s*years?(?:\s*old)?\b(?!\s*(?:of\s+)?experience)', combined_text):
        return False
    if any(k in title.lower() for k in ["bartender", "bar tender", "cocktail server", "casino", "gaming associate"]):
        return False

    # B. Commercial driving / vehicle route duties (restricted for minors under child labor laws)
    if re.search(r'\b(?:cdl[\s\-]?a|cdl[\s\-]?b|class\s*[ab])\b', combined_text):
        return False
    if any(k in title.lower() for k in ["delivery driver", "route driver", "van driver", "courier", "truck driver", "shuttle driver", "bus driver", "medical transportation"]):
        return False

    # D. Supervisory / Management roles (require adult legal responsibility)
    supervisor_patterns = [
        r'\b(?:general\s+manager|gm)\b',
        r'\b(?:assistant\s+manager|asst\s+manager)\b',
        r'\b(?:store\s+manager|branch\s+manager)\b',
        r'\b(?:manager|director|executive|chief|coordinator)\b',
        r'\b(?:shift\s+(?:manager|supervisor|lead))\b',
        r'\b(?:team\s+lead|crew\s+lead|operations\s+lead|sales\s+lead|front\s+end\s+lead|dept\s+lead|department\s+lead)\b',
        r'\b(?:lead\s+(?:person|hand|worker|tech|technician|operator))\b',
        r'\b(?:supervisor|foreman|superintendent)\b',
        r'\b(?:department\s+manager|dept\s+manager)\b',
    ]
    for sp in supervisor_patterns:
        if re.search(sp, title.lower()):
            return False

    # 2. POSITIVE CRITERIA
    # Criterion A: Clearly stated in the job description as available to minors / under 18
    under_18_patterns = [
        r'\b(?:must\s*be\s*|minimum\s*age(?:\s*of)?\s*|at\s*least\s*|age\s*)1[4-7]\b(?:\s*\+|\s*years?(?:\s*old)?|\s*or\s*older)?',
        r'\b1[4-7]\s*\+\b',
        r'\b(?:youth[\s\-]friendly|teen[\s\-]friendly|teens\s*welcome|minors\s*welcome|hire\s*minors|hiring\s*minors|under\s*18\s*welcome|under\s*18\s*eligible|high\s*school\s*students?|student\s*position|student\s*worker)\b',
        r'\b(?:work\s*permit\s*(?:required|accepted)|with\s*valid\s*work\s*permit)\b',
    ]
    for pat in under_18_patterns:
        if re.search(pat, combined_text):
            return True

    # Criterion B: Employer is specifically known to hire under age 18
    if is_known_teen_employer(company):
        return True

    # Criterion C: Gemini structured parser verified under 18 suitability
    if gemini_teen_friendly is True:
        return True

    return False

def extract_key_requirements(text: str = "", existing_exp: str = "", job_dict: dict = None) -> str:
    """
    Extracts, summarizes, and structures key entry-level qualification requirements:
    - Experience level (No experience / On-the-job training vs 1-2 years preferred)
    - Minimum age (18+, 21+, or 16+ youth) - only if explicitly stated in text
    - Driver's License & endorsements (Class C, CDL-A, CDL-B)
    - Role-specific certifications (CPR, Food Handler, ServSafe, Forklift, Guard card, Cosmetology, etc.)
    - Education (High School Diploma / GED / None required) - only if explicitly stated in text
    - Screenings (Drug screen, background check) - only if explicitly stated in text
    - Physical demands (lifting requirements) - only if explicitly stated in text
    """
    title = ""
    company = ""
    sector = ""
    location = ""
    if job_dict:
        title = str(job_dict.get('title') or job_dict.get('job_title') or '').strip()
        company = str(job_dict.get('company', '')).strip()
        sector = str(job_dict.get('sector') or job_dict.get('industry') or '').strip()
        location = str(job_dict.get('location', '')).strip()

    combined_text = f"{title} {company} {sector} {location} {text or ''} {existing_exp or ''}".lower()

    items = []

    # Process existing items first if provided
    if existing_exp and str(existing_exp).strip() not in ["N/A", "None", "", "Entry-level / No prior experience required", "Entry-level (no experience required; on-the-job training provided)"]:
        for part in str(existing_exp).split(";"):
            p_clean = part.strip()
            if p_clean and not any(bad in p_clean for bad in ["00+", "40 years", "50+"]):
                # Avoid keeping generic 'Valid CA Driver License' if we can determine reliable vehicle / clean DMV
                if "driver" in p_clean.lower() and "license" in p_clean.lower():
                    continue
                if p_clean not in items:
                    items.append(p_clean)

    # 1. Concrete Experience / Training Requirements
    exp_m = re.search(r'\b([1-3])\+?\s*(?:to\s*[2-4])?\s*years?(?:\s+of)?\s+(?:relevant\s+|related\s+|prior\s+)?experience\b', combined_text)
    if exp_m:
        exp_txt = f"{exp_m.group(0).strip().capitalize()} preferred"
        if not any("experience" in it.lower() for it in items):
            items.append(exp_txt)

    # 2. Minimum Age & Youth
    explicit_age_m = re.search(r'\b(?:must\s*be\s*|minimum\s*age(?:\s*of)?\s*|at\s*least\s*|age\s*)(\d{2})\b(?:\s*\+|\s*years?(?:\s*old)?|\s*or\s*older)?', combined_text)
    plus_age_m = re.search(r'\b(1[89]|2\d)\s*\+', combined_text)
    bare_age_m = re.search(r'\b(1[89]|2\d)\s*years?(?:\s*old)?\b(?!\s*(?:of\s+)?experience)', combined_text)

    found_age = None
    if explicit_age_m and 16 <= int(explicit_age_m.group(1)) <= 65:
        found_age = int(explicit_age_m.group(1))
    elif plus_age_m and 16 <= int(plus_age_m.group(1)) <= 65:
        found_age = int(plus_age_m.group(1))
    elif bare_age_m and 16 <= int(bare_age_m.group(1)) <= 65:
        found_age = int(bare_age_m.group(1))

    # Alcohol, gaming, commercial transit role age floors
    if any(k in title.lower() for k in ["bartender", "bar tender", "cocktail server", "casino gaming", "gaming associate", "bus driver", "school bus"]):
        found_age = max(found_age or 18, 21)

    has_16_youth = bool(
        found_age == 16
        or any(w in combined_text for w in ["minor", "youth friendly", "youth-friendly", "teen", "student position"])
    )

    if found_age and found_age >= 18:
        if not any(f"{found_age}+" in it for it in items):
            items.append(f"Must be {found_age}+ years old")
    elif has_16_youth and not any("16+" in it for it in items):
        items.append("Youth-friendly (Age 16+)")
    elif not found_age and re.search(r'\b18\b', combined_text):
        if not any("18+" in it for it in items):
            items.append("Must be 18+ years old")

    # 3. Driver's License, Vehicle, & DMV Record
    has_veh = bool(re.search(r'\b(?:reliable\s*(?:vehicle|transportation|auto|car)|personal\s*(?:vehicle|transportation|car)|insured\s*(?:vehicle|car|automobile))\b', combined_text))
    has_dmv = bool(re.search(r'\b(?:clean\s*(?:driving\s*record|dmv|mvr)|clean\s*driving\s*history|good\s*driving\s*record)\b', combined_text))

    is_bus_driver = any(k in title.lower() for k in ["bus driver", "school bus", "transit bus", "coach driver"])

    if re.search(r'\b(?:class\s*a|cdl[\s\-]?a)\b', combined_text):
        if not any("cdl-a" in it.lower() for it in items):
            items.append("Commercial Driver's License (CDL-A) required")
    elif is_bus_driver or re.search(r'\b(?:class\s*b|cdl[\s\-]?b)\b', combined_text):
        if not any("cdl-b" in it.lower() for it in items):
            items.append("Commercial Driver's License (CDL-B) required")
    elif re.search(r'\b(?:class\s*c|driver\'?s?\s*license|valid\s*driver|clean\s*dmv|clean\s*driving\s*record)\b', combined_text) or any(k in title.lower() for k in ["driver", "delivery", "courier", "shuttle", "hauling", "trucker", "transport"]):
        if has_veh and has_dmv:
            items.append("Valid Driver's License (Class C), reliable vehicle, and clean DMV record required")
        elif has_veh:
            items.append("Valid Driver's License (Class C) and reliable vehicle required")
        elif has_dmv:
            items.append("Valid Driver's License (Class C) and clean DMV record required")
        else:
            items.append("Valid Driver's License (Class C) required")
    elif has_veh and not any("reliable vehicle" in it.lower() or "reliable transportation" in it.lower() for it in items):
        items.append("Reliable vehicle / personal transportation required")

    # 4. Role-Specific Licenses / Certifications
    has_chha = bool(re.search(r'\b(?:chha|hha|home\s*health\s*aide)\b', combined_text))
    has_cna = bool(any(k in combined_text for k in ["cna", "certified nursing assistant"]))
    if has_chha and has_cna and not any("chha" in it.lower() for it in items):
        items.append("Active CHHA or CNA certification required")
    elif has_chha and not any("chha" in it.lower() for it in items):
        items.append("Active Home Health Aide (CHHA) certification required")
    elif has_cna and not any("cna" in it.lower() for it in items):
        items.append("Active CNA certification required")

    if re.search(r'\b(?:paraprofessional|paraeducator|instructional\s*(?:aide|assistant)|teacher(?:\'s)?\s*aide|special\s*ed(?:ucation)?\s*aide)\b', combined_text):
        if not any("paraprofessional" in it.lower() for it in items):
            items.append("Paraprofessional assessment / 48 college units / Paraeducator credential required/preferred")

    if "forklift" in combined_text and not any("forklift" in it.lower() for it in items):
        items.append("Forklift certification preferred / training provided")
    if any(k in combined_text for k in ["hair stylist", "barber", "cosmetolog"]) and not any("cosmetology" in it.lower() for it in items):
        items.append("Cosmetology or Barbering License required")
    if any(k in combined_text for k in ["flagger", "traffic control"]) and not any("flagger" in it.lower() for it in items):
        items.append("Flagger certification required / provided")
    if "dental assistant" in combined_text and not any("dental assistant" in it.lower() for it in items):
        items.append("Dental Assistant training / RDA preferred")
    if ("welder" in combined_text or "welding" in combined_text) and not any("welding" in it.lower() for it in items):
        items.append("Welding experience / certification preferred")
    if any(k in combined_text for k in ["cpr", "first aid", "bls", "basic life support"]) and not any("cpr" in it.lower() for it in items):
        items.append("CPR / BLS / First Aid certification required/preferred")
    if any(k in combined_text for k in ["food handler", "servsafe", "food safety cert"]) and not any("food handler" in it.lower() for it in items):
        items.append("Food Handler Card / ServSafe required")
    if "guard card" in combined_text and not any("guard card" in it.lower() for it in items):
        items.append("Security Guard Card required")
    if re.search(r'\b(?:phlebotom\w+|cpt[\s\-]?1)\b', combined_text) and not any("phlebotomy" in it.lower() for it in items):
        items.append("Phlebotomy certification (CPT-1) required/preferred")
    if re.search(r'\b(?:dsp[\s\-]?1|dsp[\s\-]?2|direct\s*support\s*professional)\b', combined_text) and not any("dsp" in it.lower() for it in items):
        items.append("Direct Support Professional (DSP) training/certification preferred/provided")

    # 5. Education
    if re.search(r'\b(?:high\s*school\s*(?:diploma|equivalent)|ged|h\.?s\.?\s*diploma)\b', combined_text):
        if not any("diploma" in it.lower() or "ged" in it.lower() for it in items):
            if re.search(r'\b(?:no\s*diploma|no\s*degree)\b', combined_text):
                items.append("No High School Diploma or Degree required")
            elif "preferred" in combined_text and ("diploma" in combined_text or "ged" in combined_text):
                items.append("High School Diploma or GED preferred")
            else:
                items.append("High School Diploma or GED required")

    if re.search(r'\b(?:48\s*(?:semester\s*)?units|associate(?:\'s)?\s*degree)\b', combined_text) and not any("48" in it for it in items):
        items.append("48+ college semester units or Associate's degree required/preferred")

    # 6. Clearances & Screenings
    if re.search(r'\b(?:drug\s*test|drug\s*screen|drug-free\s*workplace|substance\s*screen)\b', combined_text):
        if not any("drug" in it.lower() for it in items):
            items.append("Drug screening required")
    if re.search(r'\b(?:background\s*check|criminal\s*background|livescan|live\s*scan|fingerprint)\b', combined_text):
        if not any("background" in it.lower() or "live scan" in it.lower() for it in items):
            items.append("Background check / Live Scan required")
    if re.search(r'\b(?:tb\s*(?:test|clearance|screen)|tuberculosis)\b', combined_text):
        if not any("tb" in it.lower() for it in items):
            items.append("TB (Tuberculosis) clearance required")

    # 7. Physical Demands & Lifting
    lift_m = re.search(
        r'\b(?:lift|lifting|carry|carrying|move|moving|push|pull|load|loading|unload|unloading)\b'
        r'(?:[^\.\n;]{0,35}?\b(?:up\s*to|at\s*least|to|minimum\s+of|of)\b)?'
        r'\s*(\d{2,3})(?:\s*(?:-|to)\s*(\d{2,3}))?\s*(?:\+\s*)?(?:lbs|pounds?)\b',
        combined_text
    )
    if lift_m and not any(re.search(r'\b(?:ability\s+to\s+lift|lift\s*\d|lifting)\b', it.lower()) for it in items):
        low, high = lift_m.group(1), lift_m.group(2)
        if high:
            items.append(f"Ability to lift {low}-{high} lbs")
        else:
            items.append(f"Ability to lift up to {low} lbs")

    if re.search(r'\b(?:standing\s*for\s*extended\s*periods|stand\s*for\s*(?:long|extended)\s*periods|prolonged\s*standing)\b', combined_text):
        if not any("stand" in it.lower() for it in items):
            items.append("Ability to stand for extended periods")

    # 8. Operational / Job Specifics
    if re.search(r'\b(?:smart\s*phone|smartphone|mobile\s*app(?:lication)?|timekeeping\s*app)\b', combined_text):
        if not any("smartphone" in it.lower() for it in items):
            items.append("Smartphone required for timekeeping/apps")

    if re.search(r'\b(?:weekends?|saturdays?|sundays?)\b', combined_text) and re.search(r'\b(?:ability|availability|available|required|schedule)\b', combined_text):
        if not any("weekend" in it.lower() for it in items):
            items.append("Weekend availability required")

    # 9. Training or No Experience note
    has_training = bool(any(p in combined_text for p in ["paid training", "training provided", "will train", "on-the-job training"]))
    has_no_exp = bool(any(p in combined_text for p in ["no experience required", "no experience necessary", "no prior experience", "0 years experience", "zero experience"]))

    if has_no_exp and not any("no experience" in it.lower() for it in items):
        items.append("No experience required (On-the-job training provided)")
    elif has_training and not any("training" in it.lower() for it in items):
        items.append("On-the-job training provided")
    elif not items:
        items.append("No experience required (On-the-job training provided)")

    # Deduplicate and return
    deduped = []
    has_cdl_a = any("cdl-a" in it.lower() or "class a" in it.lower() for it in items)
    has_cdl_b = any("cdl-b" in it.lower() or "class b" in it.lower() for it in items)
    for it in items:
        if (has_cdl_a or has_cdl_b) and ("class c" in it.lower() or "no driver license" in it.lower()):
            continue
        if it not in deduped:
            deduped.append(it)

    final_str = "; ".join(deduped) if deduped else "No experience required (On-the-job training provided)"
    return standardize_driver_license_requirement(final_str, text_context=combined_text)

def standardize_driver_license_requirement(exp_str: str, text_context: str = "", gemini_license: str = None) -> str:
    """
    Ensures that Commercial Driver License (Class A or Class B) requirements are never missed or downgraded to Class C.
    """
    clean_exp = str(exp_str or "").strip()
    comb = f"{clean_exp} {text_context}".lower()
    
    is_class_a = bool(
        (gemini_license and "class a" in gemini_license.lower())
        or re.search(r'\b(?:class\s*a|cdl[\s\-]?a)\b', comb)
    )
    is_class_b = bool(
        (gemini_license and "class b" in gemini_license.lower())
        or re.search(r'\b(?:class\s*b|cdl[\s\-]?b)\b', comb)
        or any(b in comb for b in ["bus driver", "school bus", "transit bus", "coach driver", "passenger bus"])
    )
    
    if is_class_a:
        cdl_text = "Commercial Driver's License (CDL-A) required"
        parts = [p.strip() for p in clean_exp.split(";") if p.strip()]
        filtered = [p for p in parts if not ("class c" in p.lower() or "no driver license" in p.lower() or "cdl-b" in p.lower())]
        if not any("cdl-a" in p.lower() or "class a" in p.lower() for p in filtered):
            filtered.insert(0, cdl_text)
        else:
            for idx, p in enumerate(filtered):
                if "cdl-a" in p.lower() or "class a" in p.lower():
                    filtered[idx] = cdl_text
        return "; ".join(filtered)
        
    elif is_class_b:
        cdl_text = "Commercial Driver's License (CDL-B) required"
        parts = [p.strip() for p in clean_exp.split(";") if p.strip()]
        filtered = [p for p in parts if not ("class c" in p.lower() or "no driver license" in p.lower() or "cdl-a" in p.lower())]
        if not any("cdl-b" in p.lower() or "class b" in p.lower() for p in filtered):
            filtered.insert(0, cdl_text)
        else:
            for idx, p in enumerate(filtered):
                if "cdl-b" in p.lower() or "class b" in p.lower():
                    filtered[idx] = cdl_text
        return "; ".join(filtered)
        
    return clean_exp

def generate_key_description(title: str, company: str = "", location: str = "Redding, CA", sector: str = "Other", job_type: str = "N/A", schedule: str = "N/A", pay: str = "N/A", requirements: str = "") -> str:
    """
    Generates an authentic, informative job duties summary for Column J based on role and sector.
    Focuses 100% on job responsibilities and daily tasks without duplicating metadata from other columns.
    """
    t_lower = str(title or "").lower()
    c_lower = str(company or "").lower()
    s_lower = str(sector or "").lower()

    # Role-specific job duties mappings
    if any(k in t_lower for k in ["cake decorator", "baker", "bakery"]):
        return "Decorates cakes, pastries, and specialty desserts according to customer requests and display standards. Prepares icings, operates bakery equipment, packages finished goods, and maintains clean, sanitary work areas in compliance with food safety regulations."
    
    if any(k in t_lower for k in ["dishwasher", "dish machine", "steward"]):
        return "Operates commercial dishwashing machinery, cleans and sanitizes pots, pans, glassware, and kitchen utensils. Maintains organized dish pit areas, assists with kitchen trash removal, and ensures sanitation standards are met."

    if any(k in t_lower for k in ["cashier", "courtesy clerk", "front end clerk", "grocery clerk"]):
        return "Operates point-of-sale cash registers, scans items accurately, processes cash and electronic payments, bags merchandise, assists customers with checkout inquiries, and keeps the front-end checkout area clean and stocked."

    if any(k in t_lower for k in ["sales associate", "merchandiser", "retail associate", "store associate", "framer"]):
        return "Assists retail customers with product selections, provides attentive service, stocks and faces merchandise on sales floor shelves, creates attractive displays, and supports inventory organization and store cleanliness."

    if any(k in t_lower for k in ["waitstaff", "server", "dietary aide", "food server", "dining"]):
        return "Greets dining guests, takes food and beverage orders, delivers prepared meals promptly, cleans and resets tables, restocks service stations, and maintains a welcoming, sanitary dining environment."

    if any(k in t_lower for k in ["bartender", "bar tender"]):
        return "Prepares and serves alcoholic and non-alcoholic beverages in accordance with recipes and state liquor laws. Checks patron identification, maintains bar cleanliness, manages beverage inventory, and delivers friendly customer service."

    if any(k in t_lower for k in ["cook", "prep cook", "line cook", "crew member", "team member"]) and ("food" in s_lower or "restaurant" in s_lower or any(r in c_lower for r in ["chicken", "pizza", "burger", "taco", "deli"])):
        return "Prepares and cooks menu items following established food safety guidelines and recipe recipes. Operates kitchen prep equipment, maintains proper food storage temperatures, and keeps work stations clean and sanitized."

    if any(k in t_lower for k in ["custodian", "janitor", "cleaner", "housekeeper", "housekeeping"]):
        return "Performs regular cleaning, sanitizing, and maintenance duties throughout facilities. Sweeps, mops, vacuums floors, cleans and restocks restrooms, empties trash receptacles, and ensures a clean, safe environment for visitors and staff."

    if any(k in t_lower for k in ["warehouse", "package handler", "loader", "unloader", "material handler", "stocker"]):
        return "Handles inbound and outbound inventory, sorts and scans packages, picks and packs customer orders, loads and unloads delivery trailers, and operates hand trucks or material handling equipment safely."

    if any(k in t_lower for k in ["caregiver", "home health aide", "personal care", "resident assistant", "senior care"]):
        return "Provides compassionate personal care assistance and companionship to clients or residents. Supports daily living routines, monitors safety and comfort, assists with light household tasks, and fosters a positive care environment."

    if any(k in t_lower for k in ["direct support", "job coach", "community engagement", "dsp"]):
        return "Supports individuals with developmental and intellectual disabilities in building life skills, engaging in vocational activities, participating in community outings, and achieving personal growth goals."

    if any(k in t_lower for k in ["auto body", "mechanic", "lube tech", "technician", "service technician", "installer"]):
        return "Assists senior technicians with equipment maintenance, vehicle prep, parts assembly, repairs, and installations. Organizes tools, follows safety protocols, and maintains clean, orderly shop and job site conditions."

    if any(k in t_lower for k in ["welder", "welding", "fabricat"]):
        return "Assists with structural or ornamental metal fabrication, measuring, cutting, and welding tasks. Sets up welding equipment, cleans finished welds, and maintains shop safety standards."

    if any(k in t_lower for k in ["class a", "cdl-a", "cdl a", "semi truck", "tractor trailer"]):
        return "Operates commercial motor vehicles (Class A) safely to transport freight along regional or dedicated routes. Inspects vehicle equipment, secures cargo, maintains electronic logs (ELD), and adheres to all DOT and FMCSA safety regulations."

    if any(k in t_lower for k in ["class b", "cdl-b", "cdl b"]):
        return "Operates commercial vehicles (Class B) to transport cargo or passengers safely. Performs pre- and post-trip vehicle inspections, adheres to assigned schedules and routes, and follows all transportation safety regulations."

    if any(k in t_lower for k in ["driver", "delivery", "courier", "hauling", "truck", "shuttle", "transport", "sanitation"]):
        return "Operates transport, utility, or delivery vehicles safely to distribute goods or provide site services. Verifies work manifests, adheres to scheduled routes, and conducts basic vehicle safety checks."

    if any(k in t_lower for k in ["receptionist", "office", "clerk", "administrative", "front desk"]):
        return "Greets visitors, answers telephone inquiries, routes calls to appropriate staff, schedules appointments, processes incoming and outgoing mail, and performs general administrative filing and data entry tasks."

    if any(k in t_lower for k in ["customer service", "gaming associate", "intake"]):
        return "Assists clients and patrons with service requests, answers questions accurately, resolves customer issues, handles transaction records, and promotes a positive customer experience."

    if any(k in t_lower for k in ["hair stylist", "stylist", "barber"]):
        return "Provides hair cutting, washing, and styling services tailored to client preferences. Consults with clients, cleans and sanitizes styling tools, and maintains an orderly salon work area."

    if any(k in t_lower for k in ["childcare", "teacher aide", "youth", "instructional", "daycare aide", "preschool assistant", "tutor"]):
        return "Assists in supervising children during classroom activities, structured play, and meal times. Supports teachers with activity preparation and helps maintain a safe, nurturing learning environment."

    if any(k in t_lower for k in ["kennel", "pet bather", "veterinary aide", "vet assistant", "shelter caretaker", "animal care", "pet groomer"]) or "animal care" in s_lower:
        return "Provides attentive care, feeding, bathing, grooming, and kennel maintenance for domestic animals and shelter pets. Assists veterinary or facility staff, sanitizes animal enclosures, and ensures animal health, comfort, and safety."

    if any(k in t_lower for k in ["farm hand", "nursery worker", "landscaper", "grounds maintenance", "groundskeeper", "lawn care", "horticulture"]) or "agriculture" in s_lower:
        return "Maintains outdoor grounds, landscapes, nurseries, or agricultural operations. Operates basic groundskeeping equipment, plants, trims, weeds, waters greenery, and ensures clean, well-kept property grounds."

    if any(k in t_lower for k in ["construction laborer", "carpenter helper", "drywall apprentice", "site cleanup", "general laborer", "demolition"]) or ("construction" in s_lower and "labor" in t_lower):
        return "Assists tradespeople and contractors on construction and renovation job sites. Performs site cleanup, material handling, demolition, operates hand and power tools safely, and prepares work areas for building projects."

    if any(k in t_lower for k in ["assembly line", "packaging operator", "production helper", "qa sorter", "machine operator", "plant worker", "mill worker", "sawmill"]) or "manufacturing" in s_lower:
        return "Operates production line machinery, packages finished goods, inspects product quality for defects, and prepares materials for shipment. Follows manufacturing plant safety standards and maintains clean assembly workstations."

    if any(k in t_lower for k in ["security guard", "unarmed security", "gate attendant", "loss prevention", "security officer", "patrol"]) or "security" in s_lower:
        return "Monitors premises, controls access points, conducts routine security patrols, and deters property loss or unauthorized entry. Greets visitors, reports safety hazards or incidents, and ensures a secure environment."

    if any(k in t_lower for k in ["community outreach", "food bank sorter", "shelter support", "case aide", "social service aide", "outreach worker"]) or "social & human" in s_lower:
        return "Supports non-profit, community, or transitional shelter operations. Assists clients with essential resources, sorts and distributes donations or food bank supplies, and provides compassionate service to vulnerable community members."

    if any(k in t_lower for k in ["helpdesk", "pc repair", "cable installer", "telecom helper", "it support", "desktop support"]) or "technology" in s_lower:
        return "Assists users with basic hardware, software, and peripheral troubleshooting. Pulls and terminates cables, assists with PC and device setup, logs technical support requests, and maintains IT equipment inventory."

    # General fallback tailored by company and title
    comp_phrase = f" at {company}" if company and company != "N/A" else ""
    return f"Performs routine duties and operational support for the {title} role{comp_phrase}. Works collaboratively with team members, follows workplace safety procedures, and ensures reliable, quality service."

def extract_pay(text):
    if not text:
        return None
    text_clean = str(text).replace('\ufffd', ' ').replace('\u2013', '-').replace('\u2014', '-')
    
    # Scrub known promotional / surrogacy / gig advertisement snippets before extracting true employer pay
    promo_scrub_patterns = [
        r'(?i)(?:become\s+a\s+surrogate|earn\s+up\s+to\s+\$?(?:100,000|112,000|115,000|60k|75k|85k)[^\.\n]*|surrogate\s+mothers?|gestational\s+carrier|miracle\s+of\s+life|healthy\s+pregnancy\?\s+learn\s+about)[^\.\n]*[\.\n]?',
        r'(?i)(?:doordash\s+shopper|drive\s+with\s+doordash|deliver\s+with\s+uber|looking\s+for\s+part-time\s+jobs\?\s*-\s*deliver)[^\.\n]*[\.\n]?',
        r'(?i)(?:paid\s+focus\s+group|paid\s+research\s+panelist|online\s+survey\s+taker|research\s+study\s+panelist)[^\.\n]*[\.\n]?'
    ]
    for p_pat in promo_scrub_patterns:
        text_clean = re.sub(p_pat, ' ', text_clean)

    pay_patterns = [
        # Range with units: $16.50 - $19.00 per hour / /hr / hr / yr / annually / per week / per month
        r'\$\d+(?:,\d+)?(?:\.\d+)?\s*(?:-|to)\s*\$\d+(?:,\d+)?(?:\.\d+)?(?:\s*(?:per\s+hour|per\s+year|per\s+week|per\s+month|\/hr|\/yr|\/week|\/mo|\/month|yr|hr|annually|hourly|monthly))?',
        # Single value with units: $20.00 per hour / $23.53 / hr / $2,616 per week
        r'\$\d+(?:,\d+)?(?:\.\d+)?\s*(?:per\s+hour|per\s+year|per\s+week|per\s+month|\/hr|\/yr|\/week|\/mo|\/month|yr|hr|annually|hourly|monthly)',
        # Range with k: $50k - $70k
        r'\$\d+k\s*(?:-|to)\s*\$\d+k',
        r'\b\d+k\s*(?:-|to)\s*\d+k\b',
        # Standalone pay range: $18.00 - $22.00
        r'\$\d+(?:,\d+)?(?:\.\d+)?\s*(?:-|to)\s*\$\d+(?:,\d+)?(?:\.\d+)?',
        # Explicit wage label: Pay: $20.00
        r'(?:pay|rate|compensation|wage|starting\s*at)\s*:\s*\$\d+(?:,\d+)?(?:\.\d+)?',
    ]
    for pattern in pay_patterns:
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            val = match.group(0).strip()
            val = re.sub(r'^(?:pay|rate|compensation|wage|starting\s*at)\s*:\s*', '', val, flags=re.IGNORECASE).strip()
            # Double check if extracted value is a known promotional ad artifact
            if any(art in val.lower() for art in ["53.85", "112,000", "115,000", "100,000", "48.08", "55.29"]):
                continue
            return val
    return None

def extract_job_type(text):
    if not text:
        return None
    types = ["Full-time", "Part-time", "Contract", "Temporary", "Internship"]
    found_types = []
    for t in types:
        if re.search(r'\b' + re.escape(t) + r'\b', text, re.IGNORECASE):
            found_types.append(t)
    return ', '.join(found_types) if found_types else None

def extract_shift(text):
    if not text:
        return None
    shifts = ["Day shift", "Night shift", "Overnight shift", "Monday to Friday", "Weekend availability", "8 hour shift", "10 hour shift", "12 hour shift"]
    found_shifts = []
    for s in shifts:
        if re.search(r'\b' + re.escape(s) + r'\b', text, re.IGNORECASE):
            found_shifts.append(s)
    return ', '.join(found_shifts) if found_shifts else None

def get_company_context(text, default="N/A"):
    if not text:
        return default
    text_lower = text.lower().replace("shasta county area job listings", "")
    if "macy's" in text_lower or "macys" in text_lower:
        return "Macy's"
    if "planet fitness" in text_lower:
        return "Planet Fitness"
    if "cinemark" in text_lower:
        return "Cinemark"
    if "walgreen" in text_lower:
        return "Walgreens"
    if "walmart" in text_lower:
        return "Walmart"
    if "target" in text_lower:
        return "Target"
    if "safeway" in text_lower:
        return "Safeway"
    if "holiday market" in text_lower:
        return "Holiday Market"
    if "oak river" in text_lower:
        return "Oak River Rehab"
    if "us restaurants" in text_lower:
        return "US Restaurants"
    if "michaels" in text_lower:
        return "Michaels"
    if "shasta county" in text_lower or "county of shasta" in text_lower:
        return "County of Shasta"
    if "superior court" in text_lower or "court services" in text_lower or "courtroom clerk" in text_lower or "jury coordinator" in text_lower or "deputy marshal" in text_lower or "court reporter" in text_lower:
        return "Superior Court of California"
    if "marquis" in text_lower:
        return "Marquis Shasta Post-Acute Rehab"
    if "petsmart" in text_lower:
        return "Petsmart"
    if "cvs" in text_lower:
        return "CVS Health"
    if "mikala" in text_lower:
        return "Mikala Forestry"
    if "girls inc" in text_lower:
        return "Girls Inc."
    if "vestra" in text_lower:
        return "VESTRA Resources"
    if "patients' hospital" in text_lower or "patients hospital" in text_lower:
        return "Patients' Hospital of Redding"
    if "k2 development" in text_lower:
        return "K2 Development Company"
    if "ready set goal" in text_lower:
        return "Ready Set Goal"
    if "partners in care" in text_lower:
        return "Partners In Care"
    if "sierra pacific" in text_lower or "spi" in text_lower:
        return "Sierra Pacific Industries"
    if "shasta treatment" in text_lower:
        return "Shasta Treatment Associates"
    if "us-offsite" in text_lower or "offsite design" in text_lower:
        return "US-Offsite Design Build Factory"
    if "dollar general" in text_lower:
        return "Dollar General"
    if "trader joe" in text_lower:
        return "Trader Joe's"
    if "labcorp" in text_lower or "laboratory corporation" in text_lower:
        return "Labcorp"
    if "vans" in text_lower:
        return "Vans"
    if "mercy medical" in text_lower or "dignity health" in text_lower:
        return "Mercy Medical Center Redding"
    if "raleys" in text_lower or "raley's" in text_lower:
        return "Raley's"
    if re.search(r'\bross\b', text_lower):
        return "Ross Stores"
    return default

def clean_company_name(comp, page_text=""):
    if not comp:
        return "N/A"
    comp_clean = str(comp).strip()
    comp_clean = re.sub(r'^[•▪\-]\s*|^[oO]\s+', '', comp_clean).strip()
    comp_lower = comp_clean.lower()
    
    noise_words = [
        "new", "easily apply", "posted on", "select", "apply now", "read more", 
        "view job", "save", "savesave", "full-time", "part-time", "full time", "part time"
    ]
    if comp_lower in noise_words or comp_lower == "n/a" or not comp_lower:
        return get_company_context(page_text)
        
    if any(city in comp_lower for city in ["redding", "anderson", "burney", "shasta lake", "cottonwood"]) and ("ca" in comp_lower or "california" in comp_lower or re.search(r'\b\d{5}\b', comp_lower)):
        return get_company_context(page_text)
        
    return comp_clean

def clean_location_name(loc):
    if not loc:
        return "Redding, CA"
    s = str(loc).strip()
    s = re.sub(r'^[•▪\-]\s*|^[oO]\s+', '', s).strip()
    
    for prefix in ["address:", "location:", "location", "work location"]:
        if s.lower().startswith(prefix):
            s = s[len(prefix):].strip()
            
    if s.lower() in ["redding, california", "redding ca", "redding,ca", "redding, ca."]:
        return "Redding, CA"
    return s

def clean_val(val):
    if val is None:
        return ""
    s = str(val).strip()
    s = re.sub(r'^[•▪\-]\s*|^[oO]\s+', '', s)
    return s

def extract_company_from_description(desc):
    match = re.search(r'^([A-Z][A-Za-z0-9\s&,\.\-\’\']+?)\s+(?:is\s+looking|is\s+seeking|is\s+hiring|hiring|partnering|working\s+with|seeking|looking\s+for)\b', desc)
    if match:
        comp = match.group(1).strip()
        if comp.lower().endswith(" company") or comp.lower().endswith(" corp") or comp.lower().endswith(" inc"):
            return comp
        if len(comp.split()) <= 5:
            return comp
    return "N/A"

def is_detail_line(line):
    line_lower = line.lower()
    if line_lower in ["select", "apply now", "read more", "view job", "save", "savesave"]:
        return True
    if line_lower.startswith(("address", "location", "job id", "req id", "job type", "salary", "closing", "posting date", "posted")):
        return True
    if line_lower in ["full-time", "part-time", "full-time/part-time", "full time", "part time", "temporary", "contract", "internship"]:
        return True
    if "$" in line or "per hour" in line_lower or "hourly" in line_lower or "annually" in line_lower:
        return True
    if re.match(r'^\d{2}/\d{2}/\d{2,4}$', line):
        return True
    if re.match(r'^\d\.\d$', line):
        return True
    if any(city in line_lower for city in ["redding", "anderson", "burney", "shasta lake", "cottonwood", "sacramento"]) and ("ca" in line_lower or "california" in line_lower or re.search(r'\b\d{5}\b', line_lower)):
        return True
    return False

def is_description_or_noise(line):
    line_lower = line.lower()
    words = line.split()
    if len(words) > 10:
        return True
    if any(phrase in line_lower for phrase in ["is responsible", "responsible for", "seeking a", "looking for", "offers career", "join our team"]):
        return True
    return False

def is_potential_job_title_start(line, lookahead_lines):
    if not line:
        return False
    if not line[0].isupper() and not line[0].isdigit():
        return False
    if is_detail_line(line):
        return False
    if is_description_or_noise(line):
        return False
    if len(line) > 100:
        return False
    if any(h in line.lower() for h in ["shasta county", "published date", "table of contents", "please note", "job description", "complete list", "please visit", "above link"]):
        return False
    if lookahead_lines and len(lookahead_lines) > 1:
        next_line = lookahead_lines[1]
        if is_detail_line(next_line):
            return True
        if any(city in next_line.lower() for city in ["redding", "anderson", "burney", "shasta lake", "ca"]):
            return True
    return False

def parse_stacked_lines(lines, page_num, default_company="N/A"):
    jobs = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        
        if any(h in line.lower() for h in ["shasta county", "published date", "table of contents", "please note", "job description", "complete list", "please visit", "above link"]):
            idx += 1
            continue
            
        if is_detail_line(line) or is_description_or_noise(line):
            idx += 1
            continue
            
        if not line[0].isupper() and not line[0].isdigit():
            idx += 1
            continue
            
        title = line
        company = default_company
        location = "Redding, CA"
        pay = "N/A"
        job_type = "N/A"
        shift = "N/A"
        
        details_lines = []
        look_idx = idx + 1
        while look_idx < len(lines):
            next_line = lines[look_idx]
            if is_potential_job_title_start(next_line, lines[look_idx:look_idx+3]):
                break
            details_lines.append(next_line)
            look_idx += 1
            
        for d_line in details_lines:
            d_line_lower = d_line.lower()
            if "address" in d_line_lower or "location" in d_line_lower or any(city in d_line_lower for city in ["redding", "anderson", "burney", "shasta lake", "bella vista", "cottonwood"]):
                cleaned_loc = d_line
                for prefix in ["address:", "location:", "location"]:
                    if cleaned_loc.lower().startswith(prefix):
                        cleaned_loc = cleaned_loc[len(prefix):].strip()
                cleaned_loc = cleaned_loc.replace("Save for Later", "").strip()
                location = cleaned_loc
            elif "$" in d_line or "wage:" in d_line_lower or "salary:" in d_line_lower or "pay range:" in d_line_lower:
                pay = extract_pay(d_line)
            elif "job type:" in d_line_lower or "type:" in d_line_lower or any(t.lower() in d_line_lower for t in ["full-time", "part-time", "temporary", "contract", "full time", "part time"]):
                job_type = extract_job_type(d_line)
            elif "shift" in d_line_lower or "schedule:" in d_line_lower:
                shift = extract_shift(d_line)
                
            if len(d_line) > 40 and company == "N/A":
                comp_from_desc = extract_company_from_description(d_line)
                if comp_from_desc != "N/A":
                    company = comp_from_desc
            
        if "wm supercenter" in title.lower():
            company = "Walmart"
            title = title.replace("WM Supercenter #2537", "").strip()
            
        if re.match(r'^\d+\s+[A-Za-z]', title) or "cypress ave" in title.lower() or "balls ferry" in title.lower():
            idx = look_idx
            continue
            
        jobs.append({
            "job_title": title,
            "company": company,
            "location": location,
            "pay": pay,
            "job_type_extracted": job_type,
            "shift_schedule": shift,
            "page": page_num + 1
        })
        
        idx = look_idx
        
    return jobs

def parse_indeed_style_table(table, page_num):
    col0_texts = []
    col1_texts = []
    for row in table:
        c0 = clean_val(row[0]) if len(row) > 0 else ""
        c1 = clean_val(row[1]) if len(row) > 1 else ""
        if c0 and c0.lower() != "none":
            col0_texts.append(c0)
        if c1 and c1.lower() != "none":
            col1_texts.append(c1)
            
    if not col0_texts:
        return []
        
    title = col0_texts[0]
    if not title[0].isupper() and not title[0].isdigit():
        return []
        
    skip_labels = ["new", "easily apply", "responsive employer", "often replies in", "hiring ongoing", "urgently hiring", "temporary"]
    company = "N/A"
    location = "Redding, CA"
    
    idx = 1
    while idx < len(col0_texts):
        text = col0_texts[idx].lower()
        if any(label in text for label in skip_labels):
            idx += 1
            continue
        company = col0_texts[idx]
        idx += 1
        break
        
    while idx < len(col0_texts):
        text = col0_texts[idx].lower()
        if any(label in text for label in skip_labels):
            idx += 1
            continue
        location = col0_texts[idx]
        break
        
    full_text = " ".join(col0_texts + col1_texts)
    pay = extract_pay(full_text)
    job_type = extract_job_type(full_text)
    shift = extract_shift(full_text)
    
    return [{
        "job_title": title,
        "company": company,
        "location": location,
        "pay": pay,
        "job_type_extracted": job_type,
        "shift_schedule": shift,
        "page": page_num + 1
    }]

def parse_safeway_style_table(table, page_num):
    jobs = []
    current_job = None
    
    for row in table:
        row_str = " ".join([str(c) for c in row if c is not None])
        match_header = re.match(r'^\s*[•▪]\s*(.+)', row_str)
        if match_header:
            if current_job:
                jobs.append(current_job)
            title = clean_val(match_header.group(1))
            if not title or not (title[0].isupper() or title[0].isdigit()):
                current_job = None
                continue
            if re.match(r'^\d+\s+[A-Za-z]', title) or "cypress ave" in title.lower() or "balls ferry" in title.lower():
                current_job = None
                continue
            current_job = {
                "job_title": title,
                "company": "Safeway",
                "location": "Redding, CA",
                "pay": "N/A",
                "job_type_extracted": "N/A",
                "shift_schedule": "N/A",
                "page": page_num + 1
            }
            continue
            
        if current_job is None:
            continue
            
        if "BANNER" in row_str:
            current_job["company"] = "Safeway"
        elif "WORK LOCATION" in row_str:
            for cell in row:
                if cell and "WORK LOCATION" not in str(cell):
                    current_job["location"] = clean_val(cell)
        elif "MINIMUM PAY RATE" in row_str or "MAXIMUM PAY RATE" in row_str or "pay" in row_str.lower():
            for cell in row:
                if cell and "$" in str(cell):
                    current_job["pay"] = clean_val(cell)
                    
    if current_job:
        jobs.append(current_job)
        
    return jobs

def parse_grid_style_table(table, page_num, company_context="N/A"):
    jobs = []
    headers = [str(c).lower() if c is not None else "" for c in table[0]]
    start_row = 1 if any(h in ["position", "job title", "title"] for h in headers) else 0
    
    for row in table[start_row:]:
        clean_row = [clean_val(c) for c in row if c is not None]
        if not clean_row or len(clean_row) < 2:
            continue
            
        title = clean_row[0]
        if not title or title.lower() in ["none", "", "position", "job title", "title", "job opportunities"]:
            continue
            
        if not title[0].isupper() and not title[0].isdigit():
            continue
            
        company = company_context
        location = "Redding, CA"
        pay = "N/A"
        job_type = "N/A"
        
        if len(clean_row) == 4 and "ross" in clean_row[1].lower():
            company = clean_row[1]
            location = f"{clean_row[2]}, {clean_row[3]}"
        elif len(clean_row) == 3 and clean_row[1].isdigit():
            company = "Michaels"
            location = clean_row[2]
        elif len(clean_row) >= 11 and "tsc" in [str(c).lower() for c in clean_row]:
            title = clean_row[1]
            location = clean_row[4]
            company = "Tractor Supply Co."
        elif len(clean_row) >= 5:
            salary_cell = ""
            dept_cell = ""
            for cell in clean_row:
                if "$" in cell:
                    salary_cell = cell
                elif cell.lower().endswith("department") or cell.lower().endswith("branch") or cell.lower().endswith("agency"):
                    dept_cell = cell
                    
            title = clean_row[0]
            if len(clean_row) > 1 and clean_row[1] and clean_row[1].lower() != "none" and not clean_row[1].startswith("$") and not "time" in clean_row[1].lower():
                title += " " + clean_row[1]
                
            company = "County of Shasta"
            if dept_cell:
                company += f" - {dept_cell}"
            if salary_cell:
                pay = salary_cell
            location = "Shasta County, CA"
            
        if title and not any(k in title.lower() for k in ["job description", "complete list", "please visit", "above link"]):
            jobs.append({
                "job_title": title,
                "company": company,
                "location": location,
                "pay": pay,
                "job_type_extracted": job_type,
                "shift_schedule": "N/A",
                "page": page_num + 1
            })
            
    return jobs

def parse_single_col_table(table, page_num):
    jobs = []
    lines = [clean_val(row[0]) for row in table if row and row[0] is not None]
    lines = [l for l in lines if l]
    
    if not lines:
        return []
        
    if len(lines) >= 3 and re.match(r'^\d{2}/\d{2}/\d{4}', lines[1]):
        idx = 0
        while idx + 2 < len(lines):
            if re.match(r'^\d{2}/\d{2}/\d{4}', lines[idx+1]):
                jobs.append({
                    "job_title": lines[idx],
                    "company": lines[idx+2],
                    "location": "Redding, CA",
                    "pay": "N/A",
                    "job_type_extracted": "N/A",
                    "shift_schedule": "N/A",
                    "page": page_num + 1
                })
                idx += 3
            else:
                idx += 1
        return jobs
        
    if len(lines) >= 6 and "marquis" in "".join(lines).lower():
        idx = 0
        while idx + 5 < len(lines):
            if "req id" in lines[idx+1].lower():
                jobs.append({
                    "job_title": lines[idx],
                    "company": lines[idx+3],
                    "location": lines[idx+2],
                    "pay": "N/A",
                    "job_type_extracted": lines[idx+5],
                    "shift_schedule": "N/A",
                    "page": page_num + 1
                })
                idx += 6
            else:
                idx += 1
        return jobs
        
    if any("sheraton" in l.lower() for l in lines):
        title = lines[0]
        job_type = lines[1]
        comp_loc = lines[2]
        company = "Sheraton Redding Hotel"
        location = "Redding, CA"
        if "-" in comp_loc:
            parts = comp_loc.split("-")
            company = parts[0].strip()
            location = parts[1].strip()
            
        full_text = " ".join(lines)
        pay = extract_pay(full_text)
        
        return [{
            "job_title": title,
            "company": company,
            "location": location,
            "pay": pay,
            "job_type_extracted": job_type,
            "shift_schedule": "N/A",
            "page": page_num + 1
        }]
        
    if any("holiday market" in l.lower() for l in lines):
        title = lines[0]
        comp_loc = lines[1]
        company = "Holiday Market"
        location = "Redding, CA"
        if "-" in comp_loc:
            parts = comp_loc.split("-")
            company = parts[0].strip()
            location = parts[1].strip()
            
        full_text = " ".join(lines)
        pay = extract_pay(full_text)
        
        return [{
            "job_title": title,
            "company": company,
            "location": location,
            "pay": pay,
            "job_type_extracted": extract_job_type(full_text),
            "shift_schedule": extract_shift(full_text),
            "page": page_num + 1
        }]
        
    return []

def parse_glassdoor_text(text, page_num):
    raw_lines = [l.strip() for l in text.split('\n') if l.strip()]
    bullet_lines = []
    
    skip_keywords = ["glassdoor", "please note", "complete list", "above link", "jobs available", "full job description"]
    
    for line in raw_lines:
        if line.startswith('•') or line.startswith('▪'):
            cleaned = line[1:].strip()
            if cleaned and not any(k in cleaned.lower() for k in skip_keywords):
                bullet_lines.append(cleaned)
                
    starts = []
    for idx in range(len(bullet_lines)):
        line = bullet_lines[idx]
        if idx + 1 < len(bullet_lines):
            next_line = bullet_lines[idx+1]
            if re.match(r'^\d\.\d$', next_line):
                starts.append(idx)
                continue
        if idx == 0:
            starts.append(idx)
            
    jobs = []
    for idx, start_idx in enumerate(starts):
        end_idx = starts[idx+1] if idx + 1 < len(starts) else len(bullet_lines)
        job_lines = bullet_lines[start_idx:end_idx]
        if not job_lines:
            continue
            
        if len(job_lines) > 2 and re.match(r'^\d\.\d$', job_lines[1]):
            company = job_lines[0]
            title = job_lines[2]
            loc_idx = 3
        else:
            company = "N/A"
            title = job_lines[0]
            loc_idx = 1
            
        if len(title) > 100 or "please note" in title.lower() or not (title[0].isupper() or title[0].isdigit()):
            continue
            
        location = "Redding, CA"
        if loc_idx < len(job_lines):
            location = job_lines[loc_idx]
            
        pay = "N/A"
        for line in job_lines:
            if '$' in line:
                pay = line
                break
                
        full_text = " ".join(job_lines)
        jobs.append({
            "job_title": title,
            "company": company,
            "location": location,
            "pay": pay,
            "job_type_extracted": extract_job_type(full_text),
            "shift_schedule": extract_shift(full_text),
            "page": page_num + 1
        })
        
    return jobs

def parse_big5_text(text, page_num):
    blocks = text.split('\n\n')
    jobs = []
    for block in blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if len(lines) < 4:
            continue
            
        title = lines[0]
        if any(h in title.lower() for h in ["shasta county", "published date", "table of contents", "please note"]):
            continue
            
        if "requisition number" in block.lower() or "schedule:" in block.lower():
            location = "Redding, CA"
            schedule = "Part Time"
            for line in lines:
                if "schedule:" in line.lower():
                    schedule = line.replace("Schedule:", "").strip()
                elif "usa" in line.lower() and "ca" in line.lower():
                    location = line
            
            desc = " ".join(lines[5:]) if len(lines) > 5 else " ".join(lines)
            company = extract_company_from_description(desc)
            if company == "N/A":
                company = "Big 5 Sporting Goods" if "big 5" in block.lower() else "Quick Quack Car Wash"
                
            jobs.append({
                "job_title": title,
                "company": company,
                "location": location,
                "pay": "N/A",
                "job_type_extracted": schedule,
                "shift_schedule": "N/A",
                "page": page_num + 1
            })
    return jobs

def parse_petsmart_text(text, page_num):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    jobs = []
    idx = 0
    while idx + 3 < len(lines):
        if "req id:" in lines[idx+1].lower() and "location" in lines[idx+2].lower():
            title = lines[idx]
            loc = lines[idx+2].replace("Location", "").strip()
            jobs.append({
                "job_title": title,
                "company": "Petsmart",
                "location": loc,
                "pay": "N/A",
                "job_type_extracted": extract_job_type(title),
                "shift_schedule": "N/A",
                "page": page_num + 1
            })
            idx += 4
        else:
            idx += 1
    return jobs

def parse_cvs_text(text, page_num):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    jobs = []
    idx = 0
    while idx + 4 < len(lines):
        if "location:" in lines[idx+1].lower() and "job id:" in lines[idx+2].lower() and "category:" in lines[idx+3].lower():
            title = lines[idx]
            loc = lines[idx+1].replace("Location:", "").strip()
            jobs.append({
                "job_title": title,
                "company": "CVS Health",
                "location": loc,
                "pay": "N/A",
                "job_type_extracted": extract_job_type(title),
                "shift_schedule": "N/A",
                "page": page_num + 1
            })
            idx += 5
        else:
            idx += 1
    return jobs

def parse_mikala_text(text, page_num):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    jobs = []
    idx = 0
    while idx + 4 < len(lines):
        if lines[idx+4].lower() == "view job" or (idx+5 < len(lines) and lines[idx+4].lower() == "redding, ca" and lines[idx+3].lower() == "view job"):
            title = lines[idx]
            job_type = lines[idx+1]
            pay = lines[idx+2]
            loc = lines[idx+3]
            jobs.append({
                "job_title": title,
                "company": "Mikala Forestry / Corporation",
                "location": loc,
                "pay": pay,
                "job_type_extracted": job_type,
                "shift_schedule": "N/A",
                "page": page_num + 1
            })
            idx += 5
        else:
            idx += 1
    return jobs

def is_single_column_dominant(table):
    cols_count = len(table[0]) if table else 0
    if cols_count <= 1:
        return True, 0
    non_empty_counts = [0] * cols_count
    for row in table:
        for c_idx in range(min(cols_count, len(row))):
            val = row[c_idx]
            if val is not None and str(val).strip():
                non_empty_counts[c_idx] += 1
    total_non_empty = sum(non_empty_counts)
    if total_non_empty == 0:
        return False, -1
    for c_idx, count in enumerate(non_empty_counts):
        if count / total_non_empty > 0.85:
            return True, c_idx
    return False, -1

class JobScraper:
    def __init__(self, headless=None):
        """Initialize the scraper with undetected Chrome driver"""
        if headless is None:
            headless = (os.name != 'nt') or (os.environ.get("HEADLESS", "0") == "1")
        
        self.headless = headless
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        chrome_profile_path = os.path.join(self.base_dir, "chrome_profile")
        if not os.path.exists(chrome_profile_path):
            os.makedirs(chrome_profile_path)
        
        print(f"[OK] Using Chrome profile: {chrome_profile_path}")
        
        options = uc.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-notifications')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        if headless:
            options.add_argument('--headless=new')
            print("[OK] Running Chrome in headless mode for server/container execution.")
        
        driver_path = os.path.join(self.base_dir, "drivers", "chromedriver.exe")
        
        chrome_major = None
        try:
            from download_driver import get_chrome_version
            chrome_ver = get_chrome_version()
            if chrome_ver:
                chrome_major = int(chrome_ver.split('.')[0])
                print(f"[OK] Detected Chrome major version: {chrome_major}")
        except Exception as ex:
            print(f"[!] Error detecting Chrome version: {ex}")
            
        def try_init_chrome(opts, use_local_path=True, ver_main=None):
            kwargs = {
                "options": opts,
                "user_data_dir": chrome_profile_path
            }
            if ver_main:
                kwargs["version_main"] = ver_main
            if use_local_path and os.path.exists(driver_path):
                kwargs["driver_executable_path"] = driver_path
                print(f"[OK] Attempting to use local driver at {driver_path} with version_main={ver_main}")
            else:
                print(f"[INFO] Letting uc handle driver with version_main={ver_main}")
            return uc.Chrome(**kwargs)

        try:
            self.driver = try_init_chrome(options, use_local_path=True, ver_main=chrome_major)
        except Exception as e:
            print(f"[!] First init attempt failed: {e}")
            err_msg = str(e)
            detected_ver_from_err = None
            match = re.search(r"Current browser version is (\d+)", err_msg)
            if match:
                detected_ver_from_err = int(match.group(1))
                print(f"[OK] Extracted Chrome major version from exception: {detected_ver_from_err}")
                chrome_major = detected_ver_from_err
                
            try:
                print("[INFO] Attempting to download matching ChromeDriver...")
                from download_driver import download_chromedriver
                download_chromedriver()
            except Exception as dl_err:
                print(f"[!] Failed to auto-download driver: {dl_err}")
                
            try:
                print("[INFO] Retrying initialization with freshly downloaded local driver...")
                self.driver = try_init_chrome(options, use_local_path=True, ver_main=chrome_major)
            except Exception as e2:
                print(f"[!] Retry with local driver failed: {e2}")
                try:
                    print("[INFO] Attempting fallback letting uc handle driver dynamically...")
                    fallback_options = uc.ChromeOptions()
                    fallback_options.add_argument('--start-maximized')
                    fallback_options.add_argument('--disable-notifications')
                    if headless:
                        fallback_options.add_argument('--headless=new')
                    self.driver = try_init_chrome(fallback_options, use_local_path=False, ver_main=chrome_major)
                except Exception as e3:
                    print(f"[!] Fallback failed: {e3}")
                    raise e3
        
        self.wait = WebDriverWait(self.driver, 20)
        self.short_wait = WebDriverWait(self.driver, 5)
        
        self.jobs_data = []
        self.seen_jobs = set()
        self.pdf_published_date = None
        
        time.sleep(random.uniform(2, 5))
    
    def determine_industry(self, job_title, company, description=""):
        return determine_industry(job_title, company, description)

    def random_delay(self, min_s=2, max_s=5):
        time.sleep(random.uniform(min_s, max_s))

    def extract_email(self, text):
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return ', '.join(set(emails)) if emails else None
    
    def extract_phone(self, text):
        phone_patterns = [
            r'\+92[\s-]?\d{3}[\s-]?\d{7}',
            r'0\d{3}[\s-]?\d{7}',
            r'\d{4}[\s-]?\d{7}',
            r'\(\d{3}\)\s*\d{3}[-\s]?\d{4}'
        ]
        phones = []
        for pattern in phone_patterns:
            found = re.findall(pattern, text)
            phones.extend(found)
        return ', '.join(set(phones)) if phones else None

    def extract_pay(self, text):
        return extract_pay(text)

    def extract_job_type(self, text):
        return extract_job_type(text)

    def extract_min_age(self, text):
        age_patterns = [
            r'(\d{2})\s*years\s*(?:or)?\s*older',
            r'must\s*be\s*(\d{2})',
            r'minimum\s*age\s*(\d{2})',
            r'(\d{2})\+',
            r'at\s*least\s*(\d{2})'
        ]
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def extract_date_posted(self, text):
        if not text: return None
        
        today = datetime.now()
        text = text.lower().strip()
        
        if "today" in text:
            return today.strftime("%Y-%m-%d")
        if "yesterday" in text:
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")
            
        try:
            days_match = re.search(r'(\d+)\+?\s*d', text)
            if days_match:
                days = int(days_match.group(1))
                return (today - timedelta(days=days)).strftime("%Y-%m-%d")
        except: pass

    def scrape_local_pdf(self, days_ago=3, pdf_path=None, dry_run=False, config_dict=None):
        def de_double_word(word):
            if len(word) < 2:
                return word
            is_doubled = True
            for i in range(0, len(word) - 1, 2):
                if word[i].lower() != word[i+1].lower():
                    is_doubled = False
                    break
            if is_doubled:
                return "".join(word[i] for i in range(0, len(word), 2))
            return word

        def clean_doubled_line(line):
            words = line.split()
            cleaned_words = [de_double_word(w) for w in words]
            return " ".join(cleaned_words)

        def get_word_links(page):
            links = []
            if hasattr(page, "hyperlinks") and page.hyperlinks:
                links = page.hyperlinks
            elif page.annots:
                for annot in page.annots:
                    uri = annot.get('uri') or annot.get('data', {}).get('uri')
                    if uri:
                        links.append({
                            'x0': annot.get('x0'),
                            'top': annot.get('top'),
                            'x1': annot.get('x1'),
                            'bottom': annot.get('bottom'),
                            'uri': uri
                        })
            return links

        def find_link_for_box(word, links, tolerance=8):
            if not word or not links:
                return None
                
            x0, y0, x1, y1 = word['x0'], word['top'], word['x1'], word['bottom']
            best_link = None
            max_overlap = 0
            
            for link in links:
                if link.get('top', 0) < 130:
                    continue
                    
                uri = link.get('uri')
                if not uri:
                    continue
                    
                uri_clean = uri.lower().strip()
                if uri_clean.startswith("javascript:"):
                    continue
                    
                if any(uri_clean == base for base in [
                    "http://www.caljobs.ca.gov/", "http://www.caljobs.ca.gov", "https://northstatejobs.com/smart/", 
                    "https://www.edjoin.org/", "https://www.edjoin.org", "http://www.indeed.com/", "http://www.indeed.com",
                    "https://www.indeed.com", "https://www.indeed.com/jobs"
                ]):
                    continue
                    
                lx0, ltop, lx1, lbottom = link['x0'], link['top'], link['x1'], link['bottom']
                
                if (x0 <= lx1 + tolerance and x1 >= lx0 - tolerance) and \
                   (y0 <= lbottom + tolerance and y1 >= ltop - tolerance):
                    
                    ox0 = max(x0, lx0)
                    oy0 = max(y0, ltop)
                    ox1 = min(x1, lx1)
                    oy1 = min(y1, lbottom)
                    
                    overlap_area = max(0, ox1 - ox0) * max(0, oy1 - oy0)
                    
                    if overlap_area > max_overlap:
                        max_overlap = overlap_area
                        best_link = uri
                    elif best_link is None and overlap_area == 0:
                        best_link = uri
                        
            return best_link

        def find_link_for_text(text, words, links, tolerance=8):
            lines = {}
            for w in words:
                y = round(w['top'])
                if y not in lines: lines[y] = []
                lines[y].append(w)
            
            best_match_y = None
            best_match_score = 0
            text_clean = text.strip()
            
            for y, line_words in lines.items():
                line_text = ' '.join(w['text'] for w in line_words).strip()
                if text_clean == line_text or text_clean in line_text or line_text in text_clean:
                    best_match_y = y
                    break
                
                line_tokens = set(line_text.lower().split())
                text_tokens = set(text_clean.lower().split())
                if not line_tokens or not text_tokens: continue
                intersection = line_tokens.intersection(text_tokens)
                union = line_tokens.union(text_tokens)
                score = len(intersection) / len(union)
                if score > best_match_score and score > 0.5:
                    best_match_score = score
                    best_match_y = y
                    
            if best_match_y is not None:
                for w in lines[best_match_y]:
                    url = find_link_for_box(w, links, tolerance)
                    if url: return url
            return None

        def extract_requirements(text):
            if not text:
                return "N/A"
            reqs = []
            
            age_match = re.search(r'(?:must\s*be\s*|minimum\s*age\s*|at\s*least\s*|age\s*|18\s*years\s*\+)(\d{2})?', text, re.IGNORECASE)
            if age_match:
                age = age_match.group(1) or "18"
                reqs.append(f"Min age {age}")
                
            exp_match = re.search(r'(\d+\+?)\s*(?:-|to)?\s*\d*\s*years?\s*(?:of)?\s*(?:experience|work)', text, re.IGNORECASE)
            if exp_match:
                reqs.append(f"{exp_match.group(0).strip()}")
                
            edu_patterns = [
                ("degree", "Degree"), 
                ("diploma", "Diploma"), 
                ("GED", "GED"), 
                ("bachelor's", "Bachelor's"), 
                (r"bachelors\s+degree", "Bachelor's"), 
                ("master's", "Master's"), 
                (r"masters\s+degree", "Master's"), 
                ("associate's", "Associate's"), 
                (r"associates\s+degree", "Associate's"),
                (r"high school(?:\s+diploma|\s+or\s+equivalent)?", "High School")
            ]
            
            for pattern, label in edu_patterns:
                if re.search(r'\b' + pattern + r'\b', text, re.IGNORECASE):
                    match = re.search(r'[^.\n]*?\b' + pattern + r'\b[^.\n]*', text, re.IGNORECASE)
                    if match:
                        cleaned_req = match.group(0).strip()
                        if len(cleaned_req) < 40:
                            reqs.append(f"Requires {label}")
                        elif len(cleaned_req) < 100:
                            reqs.append(cleaned_req)
                        else:
                            reqs.append(f"Requires {label}")
                        break
                        
            dl_match = re.search(r'(?:driver\'s\s*license|valid\s*license|driver\s*license|valid\s*dl|clean\s*dmv)', text, re.IGNORECASE)
            if dl_match:
                reqs.append("Driver's License")
                
            return '; '.join(reqs) if reqs else "N/A"

        def calculate_date_posted(text, ref_date):
            if not text:
                return ""
            text = text.lower().strip()
            if "today" in text or "posted yesterday" in text or "posted 1 day ago" in text or "1 day ago" in text:
                if "yesterday" in text or "1 day" in text:
                    return (ref_date - timedelta(days=1)).strftime("%Y-%m-%d")
                return ref_date.strftime("%Y-%m-%d")
            
            match = re.search(r'(\d+)\s+days?\s+ago', text)
            if match:
                days = int(match.group(1))
                return (ref_date - timedelta(days=days)).strftime("%Y-%m-%d")
                
            match_past = re.search(r'posted\s+(\d+)\s+days?\s+ago', text)
            if match_past:
                days = int(match_past.group(1))
                return (ref_date - timedelta(days=days)).strftime("%Y-%m-%d")
            
            abs_date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', text)
            if abs_date_match:
                try:
                    date_str = abs_date_match.group(1)
                    if len(date_str.split('/')[-1]) == 2:
                        return datetime.strptime(date_str, "%m/%d/%y").strftime("%Y-%m-%d")
                    else:
                        return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
                except:
                    pass
                    
            months = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }
            month_pattern = r'\b(' + '|'.join(months.keys()) + r')[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(\d{4})?'
            match_month = re.search(month_pattern, text, re.IGNORECASE)
            if match_month:
                try:
                    m = months[match_month.group(1).lower()[:3]]
                    d = int(match_month.group(2))
                    y = int(match_month.group(3)) if match_month.group(3) else ref_date.year
                    return datetime(y, m, d).strftime("%Y-%m-%d")
                except:
                    pass
                    
            return ""

        def determine_industry_from_section(section_name, title, company):
            section_name = section_name.lower()
            title_comp = f"{str(title).lower()} {str(company).lower()}"
            
            if "veterinar" in title_comp or "animal" in title_comp or "kennel" in title_comp or "pet bather" in title_comp:
                return "Animal Care & Veterinary Services"
            if "landscap" in title_comp or "groundskeeper" in title_comp or "farm" in title_comp or "nursery" in title_comp:
                return "Agriculture & Groundskeeping"
            if "child" in title_comp or "daycare" in title_comp or "preschool" in title_comp or "tutor" in title_comp or "instructional aide" in title_comp:
                return "Childcare & Education Support"
            if "construction" in title_comp or "drywall" in title_comp or "roofing" in title_comp or "carpenter" in title_comp:
                return "Construction & Laborers"
            if "hotel" in title_comp or "motel" in title_comp or "front desk" in title_comp or "guest service" in title_comp or "concierge" in title_comp:
                return "Customer Service & Hospitality"
            if "restaurant" in title_comp or "cook" in title_comp or "food" in title_comp or "server" in title_comp or "dining" in title_comp or "dish" in title_comp or "bartender" in title_comp:
                return "Food & Restaurant"
            if "caregiver" in title_comp or "home health" in title_comp or "cna" in title_comp or "dsp" in title_comp or "patient" in title_comp:
                return "Healthcare & Caregiving"
            if "custodian" in title_comp or "janitor" in title_comp or "housekeep" in title_comp or "cleaner" in title_comp:
                return "Janitorial & Facilities"
            if "assembly" in title_comp or "packaging operator" in title_comp or "production helper" in title_comp or "qa sorter" in title_comp or "factory" in title_comp or "plant worker" in title_comp:
                return "Manufacturing & Production"
            if "receptionist" in title_comp or "file clerk" in title_comp or "data entry" in title_comp or "teller" in title_comp:
                return "Office & Clerical"
            if "salon" in title_comp or "barber" in title_comp or "stylist" in title_comp or "spa" in title_comp:
                return "Personal Care & Services"
            if "cashier" in title_comp or "retail" in title_comp or "sales" in title_comp or "canvass" in title_comp or "door to door" in title_comp or "appointment setter" in title_comp or "merchandis" in title_comp:
                return "Retail & Sales"
            if "security" in title_comp or "guard" in title_comp or "patrol" in title_comp or "loss prevention" in title_comp:
                return "Security & Public Safety"
            if "outreach" in title_comp or "food bank" in title_comp or "shelter support" in title_comp:
                return "Social & Human Services"
            if "helpdesk" in title_comp or "pc repair" in title_comp or "cable installer" in title_comp or "it support" in title_comp:
                return "Technology & IT Support"
            if "driver" in title_comp or "truck" in title_comp or "delivery" in title_comp or "route" in title_comp or "transport" in title_comp or "courier" in title_comp:
                return "Transportation & Delivery"
            if "warehouse" in title_comp or "stocker" in title_comp or "loader" in title_comp or "forklift" in title_comp or "puller" in title_comp or "order picker" in title_comp:
                return "Warehouse & Logistics"
            if "mechanic" in title_comp or "lube" in title_comp or "tire" in title_comp or "appliance" in title_comp or "hvac" in title_comp or "plumber" in title_comp or "electrician" in title_comp or "maintenance" in title_comp:
                return "Trades & Mechanics"
            if "laborer" in title_comp:
                return "Construction & Laborers"
            
            if "food" in section_name:
                return "Food & Restaurant"
            if "clerical" in section_name or "office" in section_name:
                return "Office & Clerical"
            if "customer" in section_name:
                return "Customer Service & Hospitality"
            if "health" in section_name:
                return "Healthcare & Caregiving"
            if "labor" in section_name:
                return "Construction & Laborers"
            if "schools" in section_name or "education" in section_name:
                return "Childcare & Education Support"
            if "social" in section_name:
                return "Social & Human Services"
                
            return "Other"

        def parse_pdf_published_date(text):
            match = re.search(r'Published Date\s+(\d{1,2}/\d{1,2}/\d{2,4})', text)
            if match:
                date_str = match.group(1)
                try:
                    if len(date_str.split('/')[-1]) == 2:
                        return datetime.strptime(date_str, "%m/%d/%y")
                    else:
                        return datetime.strptime(date_str, "%m/%d/%Y")
                except:
                    pass
            return None

        def parse_toc(text):
            toc = []
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'^(.*?)\s+\.{3,}\s+(\d+)$', line.strip())
                if match:
                    section_name = match.group(1).strip()
                    page_num = int(match.group(2))
                    toc.append((section_name, page_num))
            return toc

        def get_section_for_page(page_num, toc):
            if not toc:
                return "Other"
            current_section = "Other"
            for section, start_page in toc:
                if page_num >= start_page:
                    current_section = section
                else:
                    break
            return current_section

        def detect_company_anchor(line, words, links):
            line_clean = line.strip().lower()
            if not line_clean:
                return None
                
            for kw, clean_name, source, base_url in company_mappings_compiled:
                if kw in line_clean:
                    url = find_link_for_text(line, words, links) or base_url
                    if url:
                        url = re.sub(r'/(?:Please|note|Apply|person|your|application).*$', '', url, flags=re.IGNORECASE)
                    return {
                        "company": clean_name,
                        "source": source,
                        "url": url
                    }
            return None

        def override_context_by_keywords(block_text):
            text_lower = block_text.lower()
            for kw, clean_name, source, base_url in overrides_compiled:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    return clean_name, source, base_url
            return None

        def determine_government_company(url, dept):
            url_lower = url.lower() if url else ""
            dept_lower = dept.lower() if dept else ""
            if "shastacourts" in url_lower:
                return "Shasta County Superior Court"
            elif "reddingca" in url_lower or "city of redding" in dept_lower:
                return "City of Redding"
            else:
                return "Shasta County"

        def merge_rows(table):
            merged = []
            current = None
            for row in table:
                if not row or not any(row):
                    continue
                if current is not None and (row[0] is None or str(row[0]).strip() == ""):
                    for i in range(len(row)):
                        if row[i] is not None:
                            val = str(row[i]).strip()
                            if val:
                                current[i] = (str(current[i]) + " " + val).strip()
                else:
                    if current is not None:
                        merged.append(current)
                    current = [str(c).strip() if c is not None else "" for c in row]
            if current is not None:
                merged.append(current)
            return merged

        config_path = os.path.join(self.base_dir, "pdf_config.json")
        invalid_titles = [
            "new", "petco", "posted", "retail", "burney", "safeway", "hot job", "seasonal", 
            "view job", "apply now", "full time", "part time", "position:", "see redding", 
            "how to apply", "human resources", "currently accepting applications for:", 
            "working title:", "job control:", "salary range:", "department:", "publish date:", 
            "until filled", "telework:", "location:", "work type/schedule:", "filing deadline:", 
            "department position title city state community", "download application (pdf)", 
            "available careers", "log in to save job", "apply in person", "national labor exchange - nlx"
        ]
        
        company_mappings_compiled = [
            ("indeed.com", "Indeed", "Indeed", "https://www.indeed.com"),
            ("caljobs.ca.gov", "CalJobs", "CalJobs", "https://www.caljobs.ca.gov"),
            ("edjoin.org", "EdJoin", "EdJoin", "https://www.edjoin.org"),
            ("northstatejobs.com", "NorthStateJobs", "NorthStateJobs", "https://northstatejobs.com"),
            ("calcareers.ca.gov", "CalCareers", "CalCareers", "https://calcareers.ca.gov"),
            ("governmentjobs.com/careers/shasta", "Shasta County", "GovernmentJobs", "https://www.governmentjobs.com/careers/shasta"),
            ("governmentjobs.com/careers/reddingca", "City of Redding", "GovernmentJobs", "https://www.governmentjobs.com/careers/reddingca"),
            ("governmentjobs.com/careers/shastacourts", "Shasta County Superior Court", "GovernmentJobs", "https://www.governmentjobs.com/careers/shastacourts"),
            ("governmentjobs.com", "GovernmentJobs", "GovernmentJobs", "https://www.governmentjobs.com"),
            ("turtlebay.org", "Turtle Bay Exploration Park", "Company Website", "https://www.turtlebay.org/jobs"),
            ("sbgi.jobs", "Sinclair, Inc", "Company Website", "https://sbgi.jobs"),
            ("rossstores.com", "Ross Stores", "Company Website", "https://jobs.rossstores.com"),
            ("bestbuy.com", "Best Buy", "Company Website", "https://jobs.bestbuy.com"),
            ("careersatbig5.com", "Big 5 Sporting Goods", "Company Website", "https://www.careersatbig5.com"),
            ("ulta.com", "Ulta Beauty", "Company Website", "https://careers.ulta.com"),
            ("spencersandspiritjobs.com", "Spencer's", "Company Website", "https://www.spencersandspiritjobs.com"),
            ("quickquack.com", "Quick Quack Car Wash", "Company Website", "https://www.quickquack.com"),
            ("michaels.com", "Michaels", "Company Website", "https://careers.michaels.com"),
            ("cvshealth.com", "CVS Health", "Company Website", "https://jobs.cvshealth.com"),
            ("walgreens.com", "Walgreens", "Company Website", "https://jobs.walgreens.com"),
            ("dollartree.com", "Dollar Tree", "Company Website", "https://careers.dollartree.com"),
            ("target.com", "Target", "Company Website", "https://corporate.target.com/careers"),
            ("lowes.com", "Lowe's", "Company Website", "https://talent.lowes.com"),
            ("autozone.com", "AutoZone", "Company Website", "https://careers.autozone.com"),
            ("oreillyauto.com", "O'Reilly Auto Parts", "Company Website", "https://careers.oreillyauto.com"),
            ("petco.com", "Petco", "Company Website", "https://careers.petco.com"),
            ("walmart.com", "Walmart", "Company Website", "https://careers.walmart.com"),
            ("petsmart.com", "Petsmart", "Company Website", "https://careers.petsmart.com"),
            ("hobbylobby.com", "Hobby Lobby", "Company Website", "https://careers.hobbylobby.com"),
            ("dickssportinggoods", "Dick's Sporting Goods", "Company Website", "https://www.dickssportinggoods.jobs"),
            ("tractorsupply", "Tractor Supply Co.", "Company Website", "https://www.tractorsupply.careers"),
            ("planetfitness", "Planet Fitness", "Company Website", "https://planetfitnessredding.careerplug.com"),
            ("cinemark.com", "Cinemark", "Company Website", "https://careers.cinemark.com"),
            ("macys.com", "Macy's", "Company Website", "https://macysjobs.com"),
            ("azulhospitality", "Sheraton Redding Hotel", "Company Website", "https://azulhospitalitygroup.com"),
            ("whiskeytown", "Whiskeytown Marinas, LLC", "Company Website", "https://whiskeytownmarinas.com"),
            ("winriver", "Win-River Resort & Casino", "Company Website", "https://www.winriver.com"),
            ("randrqualitymeats", "R&R Quality Meats & Seafood", "Company Website", "https://www.randrqualitymeats.net"),
            ("safeway.com", "Safeway", "Company Website", "https://www.safeway.com/careers.html"),
            ("raleys.com", "Raley's", "Company Website", "https://www.raleys.com"),
            ("savemart.csod.com", "Save Mart", "Company Website", "https://savemart.csod.com"),
            ("sprouts.com", "Sprouts Farmers Market", "Company Website", "https://jobs.sprouts.com"),
            ("shopholidaymarket", "Holiday Market", "Company Website", "https://www.shopholidaymarket.com"),
            ("starbucks.com", "Starbucks", "Company Website", "https://careers.starbucks.com"),
            ("pandacareers", "Panda Express", "Company Website", "https://www.pandacareers.com"),
            ("vittles", "Vittles Family Restaurant", "Company Website", "vittlesfamilyrestaurant@gmail.com"),
            ("cattlemens", "Cattlemens Steakhouse", "Company Website", "https://www.cattlemens.com"),
            ("applebees", "Applebee's", "Company Website", "https://www.applebees.com/careers"),
            ("logansroadhouse", "Logan's Roadhouse", "Company Website", "https://logansroadhouse.com/careers"),
            ("redrobin", "Red Robin", "Company Website", "https://www.redrobin.com/jobs-and-careers"),
            ("chick-fil-a", "Chick-fil-A", "Company Website", "https://jobs.chick-fil-a.com"),
            ("olivegarden", "Olive Garden", "Company Website", "https://jobs.olivegarden.com"),
            ("mchire.com", "McDonald's", "Company Website", "https://jobs.mchire.com"),
            ("raisingcanes", "Raising Cane's", "Company Website", "https://jobs.raisingcanes.com"),
            ("tacobell", "Taco Bell", "Company Website", "https://jobs.tacobell.com"),
            ("in-n-out", "In-N-Out Burger", "Company Website", "https://www.in-n-out.com"),
            ("chipotle", "Chipotle", "Company Website", "https://jobs.chipotle.com"),
            ("outback", "Outback Steakhouse", "Company Website", "https://outbackcareers.com"),
            ("panerabread", "Panera Bread", "Company Website", "https://careers.panerabread.com"),
            ("kentsmeats", "Kent's Meats & Groceries", "Company Website", "Apply in Person"),
            ("marquiscompanies", "Marquis Companies", "Company Website", "https://www.marquiscompanies.com/careers"),
            ("shastaregional", "Shasta Regional Medical Center", "Company Website", "https://shastaregional.com/careers"),
            ("commonspirit", "Mercy Medical Center Redding", "Company Website", "https://www.commonspirit.careers"),
            ("dignityhealth", "Mercy Medical Center Redding", "Company Website", "https://www.commonspirit.careers"),
            ("vibrahealthcare", "Vibra Healthcare", "Company Website", "https://careers.vibrahealthcare.com"),
            ("interimhealthcare", "Interim Healthcare", "Company Website", "https://www.interimhealthcare.com"),
            ("partnershiphp", "Partnership HealthPlan of California", "Company Website", "https://careers-partnershiphp.icims.com"),
            ("reddingrancheria", "Redding Rancheria", "Company Website", "https://www.reddingrancheria-nsn.gov"),
            ("restpadd", "Restpadd", "Company Website", "https://www.restpadd.com"),
            ("hillcountryclinic", "Hill Country Community Clinic", "Company Website", "https://hillcountryclinic.org"),
            ("workatcrestwood", "Crestwood Behavioral Health", "Company Website", "https://workatcrestwood.com"),
            ("sierraoaks", "Sierra Oaks Assisted Living", "Company Website", "https://sierraoaksredding.com/careers"),
            ("vcacareers", "VCA Animal Hospitals", "Company Website", "https://www.vcacareers.com"),
            ("spi-ind", "Sierra Pacific Industries", "Company Website", "https://spi-ind.com/careers"),
            ("whiterock", "White Rock Trucking", "Company Website", "https://www.whiterocktruckingco.com"),
            ("rlttrucking", "Redding Lumber Transport", "Company Website", "https://www.rlttrucking.com"),
            ("mikalacorp", "Mikala Forestry", "Company Website", "https://www.mikalacorp.com"),
            ("usoffsite", "US-Offsite Design Build Factory", "Company Website", "https://usoffsite.com"),
            ("lkqcorp", "LKQ Corporation", "Company Website", "https://careers.lkqcorp.com"),
            ("amazon.jobs", "Amazon", "Company Website", "https://www.amazon.jobs"),
            ("wm.com", "Waste Management", "Company Website", "https://www.wm.com"),
            ("insectary.com", "Beneficial Insectary", "Company Website", "https://insectary.com"),
            ("bridgebay", "Peloria Bridge Bay", "Company Website", "https://bridgebayhouseboats.com"),
            ("expresspros", "Express Employment Professionals", "Company Website", "https://jobs.expresspros.com"),
            ("northstatesecurity", "North State Security", "Company Website", "https://www.northstatesecurity.com"),
            ("shastaheadstart", "Shasta Head Start", "Company Website", "https://www.shastaheadstart.org"),
            ("shastacc", "Shasta College", "Company Website", "https://shastacc.attract.neoed.com"),
            ("secure.onehcm.com", "Simpson University", "Company Website", "https://secure.onehcm.com"),
            ("remivistainc", "Remi Vista", "Company Website", "https://remivistainc.org"),
            ("o2employmentservices", "O2 Employment Services", "Company Website", "https://jobs.o2employmentservices.com"),
            ("ci.anderson", "City of Anderson", "Company Website", "https://www.ci.anderson.ca.us"),
            ("oakriver-rehab", "Oak River Rehab", "Company Website", "https://oakriver-rehab.com"),
            ("jobs-ups", "UPS", "Company Website", "https://www.jobs-ups.com"),
            ("cityofshastalake", "City of Shasta Lake", "Company Website", "https://cityofshastalake.org/Jobs.aspx"),
            ("jafoods", "J&A Food Service", "Company Website", "https://www.dev.jafoods.com"),
            ("mchire", "McDonald's", "Company Website", "https://jobs.mchire.com"),
            ("raisingcanes", "Raising Cane's", "Company Website", "https://jobs.raisingcanes.com"),
            ("hilltopspringssl", "Hilltop Springs Senior Living", "Company Website", "https://hilltopspringssl.com"),
            ("shastaregionalmedicalgroup", "Shasta Regional Medical Group", "Company Website", "https://shastaregionalmedicalgroup.com")
        ]
        
        overrides_compiled = [
            ("quick quack", "Quick Quack Car Wash", "Company Website", "https://www.quickquack.com"),
            ("duck", "Quick Quack Car Wash", "Company Website", "https://www.quickquack.com"),
            ("michaels", "Michaels", "Company Website", "https://careers.michaels.com"),
            ("big 5", "Big 5 Sporting Goods", "Company Website", "https://www.careersatbig5.com"),
            ("big5", "Big 5 Sporting Goods", "Company Website", "https://www.careersatbig5.com"),
            ("ulta", "Ulta Beauty", "Company Website", "https://careers.ulta.com"),
            ("salon", "Ulta Beauty", "Company Website", "https://careers.ulta.com"),
            ("stylist", "Ulta Beauty", "Company Website", "https://careers.ulta.com"),
            ("spencer", "Spencer's", "Company Website", "https://www.spencersandspiritjobs.com"),
            ("spirit", "Spirit Halloween", "Company Website", "https://www.spencersandspiritjobs.com"),
            ("cvs", "CVS Health", "Company Website", "https://jobs.cvshealth.com"),
            ("walgreens", "Walgreens", "Company Website", "https://jobs.walgreens.com"),
            ("dollar tree", "Dollar Tree", "Company Website", "https://careers.dollartree.com"),
            ("target", "Target", "Company Website", "https://corporate.target.com/careers"),
            ("lowe's", "Lowe's", "Company Website", "https://talent.lowes.com"),
            ("lowes", "Lowe's", "Company Website", "https://talent.lowes.com"),
            ("autozone", "AutoZone", "Company Website", "https://careers.autozone.com"),
            ("oreilly", "O'Reilly Auto Parts", "Company Website", "https://careers.oreillyauto.com"),
            ("o'reilly", "O'Reilly Auto Parts", "Company Website", "https://careers.oreillyauto.com"),
            ("petco", "Petco", "Company Website", "https://careers.petco.com"),
            ("walmart", "Walmart", "Company Website", "https://careers.walmart.com"),
            ("petsmart", "Petsmart", "Company Website", "https://careers.petsmart.com"),
            ("hobbylobby", "Hobby Lobby", "Company Website", "https://careers.hobbylobby.com"),
            ("dick's", "Dick's Sporting Goods", "Company Website", "https://www.dickssportinggoods.jobs"),
            ("dicks", "Dick's Sporting Goods", "Company Website", "https://www.dickssportinggoods.jobs"),
            ("tractor supply", "Tractor Supply Co.", "Company Website", "https://www.tractorsupply.careers"),
            ("planet fitness", "Planet Fitness", "Company Website", "https://planetfitnessredding.careerplug.com"),
            ("cinemark", "Cinemark", "Company Website", "https://careers.cinemark.com"),
            ("macy", "Macy's", "Company Website", "https://macysjobs.com"),
            ("sheraton", "Sheraton Redding Hotel", "Company Website", "https://azulhospitalitygroup.com"),
            ("whiskeytown", "Whiskeytown Marinas, LLC", "Company Website", "https://whiskeytownmarinas.com"),
            ("win-river", "Win-River Resort & Casino", "Company Website", "https://www.winriver.com"),
            ("win river", "Win-River Resort & Casino", "Company Website", "https://www.winriver.com"),
            ("randrqualitymeats", "R&R Quality Meats & Seafood", "Company Website", "https://www.randrqualitymeats.net"),
            ("safeway", "Safeway", "Company Website", "https://www.safeway.com/careers.html"),
            ("raleys", "Raley's", "Company Website", "https://www.raleys.com"),
            ("save mart", "Save Mart", "Company Website", "https://savemart.csod.com"),
            ("sprouts", "Sprouts Farmers Market", "Company Website", "https://jobs.sprouts.com"),
            ("holiday market", "Holiday Market", "Company Website", "https://www.shopholidaymarket.com"),
            ("starbucks", "Starbucks", "Company Website", "https://careers.starbucks.com"),
            ("panda express", "Panda Express", "Company Website", "https://www.pandacareers.com"),
            ("vittles", "Vittles Family Restaurant", "Company Website", "vittlesfamilyrestaurant@gmail.com"),
            ("cattlemens", "Cattlemens Steakhouse", "Company Website", "https://www.cattlemens.com"),
            ("applebee", "Applebee's", "Company Website", "https://www.applebees.com/careers"),
            ("logansroadhouse", "Logan's Roadhouse", "Company Website", "https://logansroadhouse.com/careers"),
            ("red robin", "Red Robin", "Company Website", "https://www.redrobin.com/jobs-and-careers"),
            ("chick-fil-a", "Chick-fil-A", "Company Website", "https://jobs.chick-fil-a.com"),
            ("olive garden", "Olive Garden", "Company Website", "https://jobs.olivegarden.com"),
            ("mcdonald", "McDonald's", "Company Website", "https://jobs.mchire.com"),
            ("raising cane", "Raising Cane's", "Company Website", "https://jobs.raisingcanes.com"),
            ("taco bell", "Taco Bell", "Company Website", "https://jobs.tacobell.com"),
            ("in-n-out", "In-N-Out Burger", "Company Website", "https://www.in-n-out.com"),
            ("chipotle", "Chipotle", "Company Website", "https://jobs.chipotle.com"),
            ("outback", "Outback Steakhouse", "Company Website", "https://outbackcareers.com"),
            ("panera", "Panera Bread", "Company Website", "https://careers.panerabread.com"),
            ("kent", "Kent's Groceries", "Company Website", "Apply in Person"),
            ("marquis", "Marquis Companies", "Company Website", "https://www.marquiscompanies.com/careers"),
            ("shasta regional", "Shasta Regional Medical Center", "Company Website", "https://shastaregional.com/careers"),
            ("mercy", "Mercy Medical Center Redding", "Company Website", "https://www.commonspirit.careers"),
            ("dignity", "Mercy Medical Center Redding", "Company Website", "https://www.commonspirit.careers"),
            ("vibra", "Vibra Healthcare", "Company Website", "https://careers.vibrahealthcare.com"),
            ("interim", "Interim Healthcare", "Company Website", "https://www.interimhealthcare.com"),
            ("partnership", "Partnership HealthPlan of California", "Company Website", "https://careers-partnershiphp.icims.com"),
            ("rancheria", "Redding Rancheria", "Company Website", "https://www.reddingrancheria-nsn.gov"),
            ("restpadd", "Restpadd", "Company Website", "https://www.restpadd.com"),
            ("hill country", "Hill Country Community Clinic", "Company Website", "https://hillcountryclinic.org"),
            ("crestwood", "Crestwood Behavioral Health", "Company Website", "https://workatcrestwood.com"),
            ("sierra oaks", "Sierra Oaks Assisted Living", "Company Website", "https://sierraoaksredding.com/careers"),
            ("vca", "VCA Animal Hospitals", "Company Website", "https://www.vcacareers.com"),
            ("sierra pacific", "Sierra Pacific Industries", "Company Website", "https://spi-ind.com/careers"),
            ("white rock", "White Rock Trucking", "Company Website", "https://www.whiterocktruckingco.com"),
            ("lumber transport", "Redding Lumber Transport", "Company Website", "https://www.rlttrucking.com"),
            ("mikala", "Mikala Forestry", "Company Website", "https://www.mikalacorp.com"),
            ("us-offsite", "US-Offsite Design Build Factory", "Company Website", "https://usoffsite.com"),
            ("lkq", "LKQ Corporation", "Company Website", "https://careers.lkqcorp.com"),
            ("amazon", "Amazon", "Company Website", "https://www.amazon.jobs"),
            ("waste management", "Waste Management", "Company Website", "https://www.wm.com"),
            ("bridge bay", "Peloria Bridge Bay", "Company Website", "https://bridgebayhouseboats.com"),
            ("express employment", "Express Employment Professionals", "Company Website", "https://jobs.expresspros.com"),
            ("security officers", "North State Security", "Company Website", "https://www.northstatesecurity.com"),
            ("head start", "Shasta Head Start", "Company Website", "https://www.shastaheadstart.org"),
            ("shasta college", "Shasta College", "Company Website", "https://shastacc.attract.neoed.com"),
            ("simpson", "Simpson University", "Company Website", "https://secure.onehcm.com"),
            ("remi vista", "Remi Vista", "Company Website", "https://remivistainc.org"),
            ("o2 employment", "O2 Employment Services", "Company Website", "https://jobs.o2employmentservices.com"),
            ("ci.anderson", "City of Anderson", "Company Website", "https://www.ci.anderson.ca.us"),
            ("oak river", "Oak River Rehab", "Company Website", "https://oakriver-rehab.com")
        ]
        
        layout_overrides = {}
        
        if config_dict:
            invalid_titles = config_dict.get("invalid_titles", invalid_titles)
            if "company_mappings" in config_dict:
                company_mappings_compiled = [tuple(m) for m in config_dict["company_mappings"]]
            if "overrides" in config_dict:
                overrides_compiled = [tuple(o) for o in config_dict["overrides"]]
            layout_overrides = config_dict.get("layout_overrides", layout_overrides)
        elif os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    invalid_titles = config.get("invalid_titles", invalid_titles)
                    if "company_mappings" in config:
                        company_mappings_compiled = [tuple(m) for m in config["company_mappings"]]
                    if "overrides" in config:
                        overrides_compiled = [tuple(o) for o in config["overrides"]]
                    layout_overrides = config.get("layout_overrides", layout_overrides)
            except Exception as e:
                print(f"[WARN] Error loading pdf_config.json: {e}")

        print(f"\n{'='*60}")
        print("Searching for weekly job list PDFs...")
        print(f"{'='*60}\n")
        
        if pdf_path:
            pdf_files_info = [(os.path.basename(pdf_path), pdf_path)]
        else:
            pdf_files = [f for f in os.listdir(self.base_dir) if f.endswith('.pdf') and ('weekly' in f.lower() or 'job' in f.lower())]
            pdf_files_info = [(f, os.path.join(self.base_dir, f)) for f in pdf_files]
        
        if not pdf_files_info:
            print("[INFO] No relevant PDF files found in the folder.")
            return [] if dry_run else None
            
        all_pdf_jobs = []
        published_date_ref = datetime.now()
        
        for pdf_file, full_path in pdf_files_info:
            print(f"Processing PDF: {pdf_file}")
            
            try:
                with pdfplumber.open(full_path) as pdf:
                    toc_page_text = pdf.pages[0].extract_text() or ""
                    parsed_pub_date = parse_pdf_published_date(toc_page_text)
                    if parsed_pub_date:
                        published_date_ref = parsed_pub_date
                        self.pdf_published_date = published_date_ref.strftime("%Y-%m-%d")
                        print(f"[OK] PDF Published Date: {self.pdf_published_date}")
                    else:
                        self.pdf_published_date = datetime.now().strftime("%Y-%m-%d")
                        
                    toc_sections = parse_toc(toc_page_text)
                    total_pages = len(pdf.pages)
                    
                    active_company = "Indeed"
                    active_source = "Indeed"
                    active_url = "https://www.indeed.com"
                    
                    for page_idx in range(1, total_pages):
                        page_num = page_idx + 1
                        page = pdf.pages[page_idx]
                        
                        section = get_section_for_page(page_num, toc_sections)
                        links = get_word_links(page)
                        words = page.extract_words()
                        
                        content_words = [w for w in words if w['top'] > 130]
                        is_two_col = False
                        
                        page_key = str(page_num)
                        if page_key in layout_overrides:
                            is_two_col = (layout_overrides[page_key] == "2-column")
                        elif content_words:
                            mid = page.width / 2
                            left_words = [w for w in content_words if w['x1'] < mid]
                            right_words = [w for w in content_words if w['x0'] > mid]
                            middle_words = [w for w in content_words if w['x0'] <= mid and w['x1'] >= mid]
                            if len(left_words) > 30 and len(right_words) > 30 and len(middle_words) < 5:
                                is_two_col = True
                                
                        if is_two_col:
                            bullets = [w for w in words if w['text'] in ['\uFFFD', '▪', '•']]
                            y_bullet = min(w['top'] for w in bullets) if bullets else 130
                            y_split = max(100, min(y_bullet - 5, page.height - 100))
                            
                            header_p = page.crop((0, 0, page.width, y_split))
                            left_p = page.crop((0, y_split, page.width/2, page.height))
                            right_p = page.crop((page.width/2, y_split, page.width, page.height))
                            
                            text = (header_p.extract_text() or "") + "\n" + (left_p.extract_text() or "") + "\n" + (right_p.extract_text() or "")
                            print(f"[LAYOUT] Page {page_num} -> Extracted text as 2-column layout split at y={y_split}")
                        else:
                            text = page.extract_text() or ""
                            
                        text = re.sub(r'[\uFFFD▪•]', '•', text)
                        text_lower = text.lower()
                        
                        raw_lines = [l.strip() for l in text.split('\n') if l.strip()]
                        processed_lines = []
                        for rl in raw_lines:
                            processed_lines.append(clean_doubled_line(rl))
                            
                        cleaned_lines = []
                        line_companies = []
                        for l in processed_lines:
                            anchor_info = detect_company_anchor(l, words, links)
                            if anchor_info:
                                active_company = anchor_info["company"]
                                active_source = anchor_info["source"]
                                active_url = anchor_info["url"]
                                print(f"[CONTEXT] Page {page_num} -> Employer updated to: {active_company} ({active_source})")
                                continue
                                
                            if any(h in l for h in ["Shasta County Area Job Listings", "Published Date", "sample of jobs as listed on sites", "https://www.edjoin.org/,and", "try hitting Ctrl before clicking"]):
                                continue
                            if l.isdigit() and int(l) == page_num:
                                continue
                            cleaned_lines.append(l)
                            line_companies.append({
                                "company": active_company,
                                "source": active_source,
                                "url": active_url
                            })
                            
                        page_text_clean = "\n".join(cleaned_lines)
                        page_jobs = []
                        
                        if active_source == "Indeed":
                            blocks = re.split(r'\n\s*•\s*|^\s*•\s*', page_text_clean)
                            for block in blocks:
                                block_lines = [l.strip() for l in block.split('\n') if l.strip()]
                                if not block_lines:
                                    continue
                                title = block_lines[0]
                                
                                if title.startswith('o ') or title.startswith('o') or len(title) < 4 or any(k in title.lower() for k in ["please note", "complete list", "above link", "table of contents", "published date", "customer service"]):
                                    continue
                                if len(title) > 80:
                                    continue
                                    
                                company_idx = 1
                                skip_phrases = ["easily apply", "often replies in", "hiring ongoing", "urgently hiring"]
                                while company_idx < len(block_lines) and any(sp in block_lines[company_idx].lower() for sp in skip_phrases):
                                    company_idx += 1
                                
                                if company_idx >= len(block_lines):
                                    continue
                                    
                                company = block_lines[company_idx]
                                if company.lower() in skip_phrases or company.lower() == "new":
                                    if company_idx + 1 < len(block_lines):
                                        company = block_lines[company_idx + 1]
                                        company_idx += 1
                                        
                                location = "Redding, CA"
                                if company_idx + 1 < len(block_lines):
                                    loc_cand = block_lines[company_idx + 1]
                                    if any(city in loc_cand.lower() for city in ["redding", "anderson", "burney", "ca"]):
                                        location = loc_cand
                                        
                                block_text = " ".join(block_lines)
                                pay = extract_pay(block_text)
                                job_type = extract_job_type(block_text)
                                shift = extract_shift(block_text)
                                reqs = extract_requirements(block_text)
                                date_posted_str = calculate_date_posted(block_text, published_date_ref)
                                job_url = find_link_for_text(title, words, links) or active_url
                                if job_url:
                                    job_url = re.sub(r'/(?:Please|note|Apply|person|your|application).*$', '', job_url, flags=re.IGNORECASE)
                                category = determine_industry_from_section(section, title, company)
                                
                                overridden = override_context_by_keywords(block_text)
                                if overridden:
                                    company = overridden[0]
                                    
                                page_jobs.append({
                                    "source": "Indeed",
                                    "job_title": title,
                                    "company": company,
                                    "location": location,
                                    "pay": pay,
                                    "job_type_extracted": job_type,
                                    "shift_schedule": shift,
                                    "experience": reqs,
                                    "date_posted": date_posted_str,
                                    "job_url": job_url,
                                    "industry": category,
                                    "page": page_num
                                })
                            
                        elif active_source == "CalCareers":
                            listings = re.split(r'\n(?=[A-Z\s]{4,}\b)', page_text_clean)
                            for lst in listings:
                                lst_lines = [l.strip() for l in lst.split('\n') if l.strip()]
                                if len(lst_lines) < 3:
                                    continue
                                title = lst_lines[0]
                                if title.lower() in invalid_titles or title.lower().startswith("close:"):
                                    continue
                                if not title or len(title) < 4 or title.lower() in ["none", "job title", "position"]:
                                    continue
                                    
                                working_title = title
                                department = "Department of Forestry & Fire Protection"
                                location = "Shasta County"
                                pay = "N/A"
                                schedule = "N/A"
                                pub_date = self.pdf_published_date or "N/A"
                                
                                for idx, line in enumerate(lst_lines):
                                    if "working title:" in line.lower() and idx + 1 < len(lst_lines):
                                        working_title = lst_lines[idx+1]
                                    elif "salary range:" in line.lower() and idx + 1 < len(lst_lines):
                                        pay = lst_lines[idx+1]
                                    elif "work type/schedule:" in line.lower() and idx + 1 < len(lst_lines):
                                        schedule = lst_lines[idx+1]
                                    elif "department:" in line.lower() and idx + 1 < len(lst_lines):
                                        department = lst_lines[idx+1]
                                    elif "location:" in line.lower() and idx + 1 < len(lst_lines):
                                        location = lst_lines[idx+1]
                                    elif "publish date:" in line.lower() and idx + 1 < len(lst_lines):
                                        pub_date = lst_lines[idx+1]
                                        
                                date_posted_str = calculate_date_posted(pub_date, published_date_ref)
                                job_url = find_link_for_text(title, words, links) or active_url
                                if job_url:
                                    job_url = re.sub(r'/(?:Please|note|Apply|person|your|application).*$', '', job_url, flags=re.IGNORECASE)
                                category = determine_industry_from_section(section, working_title, department)
                                reqs = extract_requirements(lst)
                                
                                page_jobs.append({
                                    "source": "CalCareers",
                                    "job_title": working_title,
                                    "company": department,
                                    "location": location + ", CA",
                                    "pay": pay,
                                    "job_type_extracted": schedule,
                                    "shift_schedule": "N/A",
                                    "experience": reqs,
                                    "date_posted": date_posted_str,
                                    "job_url": job_url,
                                    "industry": category,
                                    "page": page_num
                                })
                                
                        elif active_source == "EdJoin":
                            idx = 0
                            while idx < len(cleaned_lines):
                                line = cleaned_lines[idx]
                                if "deadline:" in line.lower() or "until filled" in line.lower():
                                    title = "N/A"
                                    company = "N/A"
                                    location = "Shasta County, CA"
                                    pay = "N/A"
                                    
                                    if idx - 1 >= 0 and cleaned_lines[idx-1] == "CA" and idx - 3 >= 0:
                                        title = cleaned_lines[idx-3]
                                        company_info = cleaned_lines[idx-2] + " CA"
                                        if " - " in company_info:
                                            parts = company_info.split(" - ")
                                            company = parts[0].strip()
                                            location = parts[1].strip()
                                        else:
                                            company = company_info
                                    elif idx - 2 >= 0:
                                        title = cleaned_lines[idx-2]
                                        company_info = cleaned_lines[idx-1]
                                        if " - " in company_info:
                                            parts = company_info.split(" - ")
                                            company = parts[0].strip()
                                            location = parts[1].strip()
                                        else:
                                            company = company_info
                                    elif idx - 1 >= 0:
                                        title = cleaned_lines[idx-1]
                                        
                                    if idx + 1 < len(cleaned_lines):
                                        pay_line = cleaned_lines[idx+1]
                                        if "hour" in pay_line.lower() or "per" in pay_line.lower() or "$" in pay_line or re.search(r'\d+', pay_line):
                                            pay = pay_line
                                            
                                    job_url = find_link_for_text(title, words, links) or active_url
                                    if job_url:
                                        job_url = re.sub(r'/(?:Please|note|Apply|person|your|application).*$', '', job_url, flags=re.IGNORECASE)
                                    category = determine_industry_from_section(section, title, company)
                                    reqs = extract_requirements(title + " " + pay)
                                    
                                    page_jobs.append({
                                        "source": "EdJoin",
                                        "job_title": title,
                                        "company": company,
                                        "location": location,
                                        "pay": pay,
                                        "job_type_extracted": "N/A",
                                        "shift_schedule": "N/A",
                                        "experience": reqs,
                                        "date_posted": "",
                                        "job_url": job_url,
                                        "industry": category,
                                        "page": page_num
                                    })
                                    idx += 2
                                else:
                                    idx += 1
                                    
                        elif active_source == "Glassdoor":
                            blocks = re.split(r'\n•\s*', page_text_clean)
                            for block in blocks:
                                block_lines = [l.strip() for l in block.split('\n') if l.strip()]
                                if len(block_lines) < 2:
                                    continue
                                company = block_lines[0]
                                if "glassdoor" in company.lower():
                                    continue
                                title = block_lines[1]
                                location = "Redding, CA"
                                if len(block_lines) > 2:
                                    location = block_lines[2]
                                    
                                pay = extract_pay(block)
                                reqs = extract_requirements(block)
                                job_url = find_link_for_text(title, words, links) or active_url
                                if job_url:
                                    job_url = re.sub(r'/(?:Please|note|Apply|person|your|application).*$', '', job_url, flags=re.IGNORECASE)
                                category = determine_industry_from_section(section, title, company)
                                
                                page_jobs.append({
                                    "source": "Glassdoor",
                                    "job_title": title,
                                    "company": company,
                                    "location": location,
                                    "pay": pay,
                                    "job_type_extracted": "N/A",
                                    "shift_schedule": "N/A",
                                    "experience": reqs,
                                    "date_posted": "",
                                    "job_url": job_url,
                                    "industry": category,
                                    "page": page_num
                                })
                                
                        raw_tables = page.extract_tables()
                        valid_tables = []
                        if raw_tables:
                            for table in raw_tables:
                                if not table or not table[0]:
                                    continue
                                cols = len(table[0])
                                if cols >= 3:
                                    valid_rows = sum(1 for row in table if len([str(c).strip() for c in row if c is not None and str(c).strip() != ""]) >= 2)
                                    if valid_rows >= 2:
                                        valid_tables.append(table)
                                        
                        if valid_tables and not any(k in text_lower for k in ["calcareers", "edjoin", "glassdoor"]):
                            if section == "GOVERNMENT":
                                for table in valid_tables:
                                    cols = len(table[0]) if table else 0
                                    if cols >= 10:
                                        merged = merge_rows(table)
                                        for r_idx, row in enumerate(merged[1:]):
                                            clean_cells = [str(c).replace('\n', ' ').strip() if c is not None else "" for c in row]
                                            salary = "N/A"
                                            closing = "N/A"
                                            job_type = "N/A"
                                            dept = "N/A"
                                            salary_idx = -1
                                            closing_idx = -1
                                            job_type_idx = -1
                                            dept_idx = -1
                                            
                                            for idx in range(3, len(clean_cells)):
                                                cell = clean_cells[idx]
                                                cell_lower = cell.lower()
                                                if not cell:
                                                    continue
                                                if "$" in cell and salary_idx == -1:
                                                    salary = cell
                                                    salary_idx = idx
                                                    continue
                                                if (re.search(r'\b\d{2}/\d{2}/\d{2}\b', cell) or "continuous" in cell_lower) and closing_idx == -1:
                                                    closing = cell
                                                    closing_idx = idx
                                                    continue
                                                if any(t in cell_lower for t in ["time", "help", "regular", "temporary", "seasonal", "intermittent", "status"]) and job_type_idx == -1:
                                                    job_type = cell
                                                    job_type_idx = idx
                                                    continue
                                                if any(d in cell_lower for d in ["department", "branch", "agency", "office", "services", "probation", "works", "health", "counsel", "administration", "division", "recorder", "attorney", "sheriff", "district"]) and dept_idx == -1:
                                                    dept = cell
                                                    dept_idx = idx
                                                    continue

                                            if dept == "N/A":
                                                for idx in range(min(10, len(clean_cells)), len(clean_cells)):
                                                    if clean_cells[idx] and idx not in [salary_idx, closing_idx, job_type_idx]:
                                                        dept = clean_cells[idx]
                                                        dept_idx = idx
                                                        break
                                                        
                                            metadata_indices = [idx for idx in [salary_idx, closing_idx, job_type_idx, dept_idx] if idx != -1]
                                            title_end_idx = min(metadata_indices) if metadata_indices else len(clean_cells)
                                            title_parts = [clean_cells[i] for i in range(title_end_idx) if clean_cells[i]]
                                            title_clean = " ".join(title_parts)
                                            title_clean = re.sub(r'\bNew\b', '', title_clean).strip()
                                            
                                            if not title_clean or title_clean.lower() in ["job title", "title", "position"]:
                                                continue
                                                
                                            job_url = find_link_for_text(title_clean, words, links) or "https://www.governmentjobs.com/careers/shasta"
                                            if job_url:
                                                job_url = re.sub(r'/(?:Please|note|Apply|person|your|application).*$', '', job_url, flags=re.IGNORECASE)
                                            company = determine_government_company(job_url, dept)
                                            location = "Redding, CA" if "redding" in company.lower() else "Shasta County, CA"
                                            category = determine_industry_from_section(section, title_clean, company)
                                            reqs = extract_requirements(title_clean + " " + salary + " " + job_type)
                                            
                                            page_jobs.append({
                                                "source": "GovernmentJobs",
                                                "job_title": title_clean,
                                                "company": company,
                                                "location": location,
                                                "pay": salary,
                                                "job_type_extracted": job_type,
                                                "shift_schedule": "N/A",
                                                "experience": reqs,
                                                "date_posted": "",
                                                "job_url": job_url,
                                                "industry": category,
                                                "page": page_num
                                            })
                                            
                            else:
                                for table in valid_tables:
                                    cols = len(table[0]) if table else 0
                                    if cols >= 3:
                                        headers = [str(c).lower() if c is not None else "" for c in table[0]]
                                        start_row = 1 if any(h in ["position", "job title", "title"] for h in headers) else 0
                                        
                                        for row in table[start_row:]:
                                            clean_row = [str(c).strip() for c in row if c is not None]
                                            if not clean_row or len(clean_row) < 2:
                                                continue
                                            title = clean_row[0]
                                            if not title or title.lower() in ["none", "", "position", "job title", "title", "job opportunities", "store", "location"]:
                                                continue
                                                
                                            company = active_company
                                            location = "Redding, CA"
                                            pay = "N/A"
                                            job_type = "N/A"
                                            shift = "N/A"
                                            date_posted_str = ""
                                            job_url = find_link_for_text(title, words, links) or active_url
                                            if job_url:
                                                job_url = re.sub(r'/(?:Please|note|Apply|person|your|application).*$', '', job_url, flags=re.IGNORECASE)
                                                
                                            if "ross" in text_lower and len(clean_row) >= 4:
                                                company = "Ross Stores"
                                                location = f"{clean_row[2]}, {clean_row[3]}"
                                            elif "michaels" in text_lower and len(clean_row) >= 3:
                                                company = "Michaels"
                                                location = clean_row[2]
                                            elif "oakmont" in text_lower and len(clean_row) >= 5:
                                                company = "Oakmont of Redding"
                                                title = clean_row[1]
                                                location = f"{clean_row[2]}, {clean_row[3]}"
                                            elif "tractor" in text_lower and len(clean_row) >= 4:
                                                company = "Tractor Supply Co."
                                                location = clean_row[1]
                                                
                                            block_text = " ".join(clean_row)
                                            overridden = override_context_by_keywords(block_text)
                                            if overridden:
                                                company, source, job_url = overridden[0], overridden[1], overridden[2]
                                                
                                            category = determine_industry_from_section(section, title, company)
                                            reqs = extract_requirements(title + " " + pay + " " + job_type)
                                            
                                            page_jobs.append({
                                                "source": "GovernmentJobs" if "governmentjobs" in (job_url or "") or "government" in company.lower() else active_source,
                                                "job_title": title,
                                                "company": company,
                                                "location": location,
                                                "pay": pay,
                                                "job_type_extracted": job_type,
                                                "shift_schedule": shift,
                                                "experience": reqs,
                                                "date_posted": date_posted_str,
                                                "job_url": job_url,
                                                "industry": category,
                                                "page": page_num
                                            })
                                            
                        if "sierra pacific" in text_lower:
                            lines = [l.strip() for l in page_text_clean.split('\n') if l.strip()]
                            for i in range(1, len(lines)):
                                if lines[i] in ["Full-Time", "Part-Time"]:
                                    title = lines[i-1]
                                    if title.lower() in invalid_titles or len(title) < 4 or title.lower().startswith("close:") or title.lower().startswith("deadline:"):
                                        continue
                                        
                                    location = "Shasta County, CA"
                                    for j in range(i-1, max(-1, i-10), -1):
                                        if "burney" in lines[j].lower():
                                            location = "Burney, CA"
                                            break
                                        elif "redding" in lines[j].lower():
                                            location = "Redding, CA"
                                            break
                                        elif "anderson" in lines[j].lower():
                                            location = "Anderson, CA"
                                            break
                                            
                                    job_url = find_link_for_text(title, words, links) or active_url
                                    if job_url:
                                        job_url = re.sub(r'/(?:Please|note|Apply|person|your|application).*$', '', job_url, flags=re.IGNORECASE)
                                    category = "Trades & Mechanics"
                                    
                                    page_jobs.append({
                                        "source": "Company Website",
                                        "job_title": title,
                                        "company": "Sierra Pacific Industries",
                                        "location": location,
                                        "pay": "N/A",
                                        "job_type_extracted": lines[i],
                                        "shift_schedule": "N/A",
                                        "experience": "N/A",
                                        "date_posted": "",
                                        "job_url": job_url,
                                        "industry": category,
                                        "page": page_num
                                    })
                                    
                        if not page_jobs:
                            if "•" in page_text_clean:
                                blocks = re.split(r'\n\s*•\s*|^\s*•\s*', page_text_clean)
                            else:
                                blocks = re.split(r'\n\n|\n(?=[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*[:\-\n])', page_text_clean)
                            current_line_idx = 0
                            for block in blocks:
                                block_lines = [l.strip() for l in block.split('\n') if l.strip()]
                                if len(block_lines) < 2:
                                    continue
                                    
                                try:
                                    idx = cleaned_lines.index(block_lines[0], current_line_idx)
                                    current_line_idx = idx + len(block_lines)
                                except ValueError:
                                    idx = current_line_idx
                                    
                                ctx = line_companies[idx] if idx < len(line_companies) else {"company": active_company, "source": active_source, "url": active_url}
                                
                                title = block_lines[0]
                                if title.lower() in invalid_titles or title.lower().startswith("close:") or title.lower().startswith("deadline:") or title.lower().startswith("primary responsibilities:") or title.lower().startswith("qualification standard:"):
                                    continue
                                if len(title) > 80 or len(title) < 4 or any(k in title.lower() for k in ["please note", "job description", "complete list", "above link", "no current", "visit this link", "hiring apply in person", "shasta county area"]):
                                    continue
                                if not (title[0].isupper() or title[0].isdigit()):
                                    continue
                                    
                                company = ctx["company"]
                                job_url = find_link_for_text(title, words, links) or ctx["url"]
                                if job_url:
                                    job_url = re.sub(r'/(?:Please|note|Apply|person|your|application).*$', '', job_url, flags=re.IGNORECASE)
                                source = ctx["source"]
                                
                                if len(block_lines) > 1 and block_lines[1][0].isupper() and company == "Company Website":
                                    if "redding" not in block_lines[1].lower() and "anderson" not in block_lines[1].lower() and "burney" not in block_lines[1].lower():
                                        company = block_lines[1]
                                        
                                location = "Redding, CA"
                                for line in block_lines:
                                    if any(city in line.lower() for city in ["redding", "anderson", "burney", "shasta lake", "cottonwood"]):
                                        location = line
                                        break
                                        
                                pay = extract_pay(block)
                                job_type = extract_job_type(block)
                                shift = extract_shift(block)
                                reqs = extract_requirements(block)
                                date_posted_str = calculate_date_posted(block, published_date_ref)
                                
                                block_text = " ".join(block_lines)
                                overridden = override_context_by_keywords(block_text)
                                if overridden:
                                    company, source, job_url = overridden[0], overridden[1], overridden[2]
                                    
                                if any(k in title.lower() for k in ["schedule", "job type", "hours", "posting date", "posted on", "address", "location", "requisition number"]):
                                    continue
                                    
                                category = determine_industry_from_section(section, title, company)
                                
                                exp_info = extract_key_requirements(text=block, existing_exp=reqs)
                                page_jobs.append({
                                    "source": source,
                                    "job_title": title,
                                    "company": company,
                                    "location": location,
                                    "pay": pay,
                                    "job_type_extracted": job_type,
                                    "shift_schedule": shift,
                                    "experience": exp_info,
                                    "requirements": exp_info,
                                    "description": block,
                                    "date_posted": date_posted_str,
                                    "job_url": job_url,
                                    "industry": category,
                                    "page": page_num
                                })
                                
                        all_pdf_jobs.extend(page_jobs)
                        
            except Exception as e:
                print(f"[ERROR] Error processing PDF {pdf_file}: {e}")
                import traceback
                traceback.print_exc()

        cleaned_pdf_jobs = []
        seen = set()
        for job in all_pdf_jobs:
            title_clean = re.sub(r'^[•▪\.\-\s]+', '', str(job["job_title"])).strip()
            job["job_title"] = title_clean
            
            hash_key = (title_clean.lower(), str(job["company"]).lower().strip(), str(job["location"]).lower().strip())
            if hash_key in seen:
                continue
            seen.add(hash_key)
            cleaned_pdf_jobs.append(job)

        if dry_run:
            return cleaned_pdf_jobs
            
        for job in cleaned_pdf_jobs:
            exp_val = extract_key_requirements(text=job.get("description", ""), existing_exp=job.get("experience", ""), job_dict=job)
            desc_val = job.get("description")
            if not desc_val or desc_val == "N/A":
                desc_val = generate_key_description(
                    title=job["job_title"],
                    company=job["company"],
                    location=job["location"],
                    sector=job["industry"],
                    job_type=job["job_type_extracted"],
                    schedule=job["shift_schedule"],
                    pay=job["pay"],
                    requirements=exp_val
                )

            job_data = {
                "source": job["source"],
                "job_title": job["job_title"],
                "company": job["company"],
                "location": job["location"],
                "pay": job["pay"],
                "job_type_extracted": job["job_type_extracted"],
                "shift_schedule": job["shift_schedule"],
                "experience": exp_val,
                "requirements": exp_val,
                "description": desc_val,
                "date_posted": job["date_posted"],
                "job_url": job["job_url"],
                "industry": job["industry"],
            }
            job_data["teen_friendly"] = is_teen_friendly(
                title=job["job_title"],
                company=job["company"],
                text=desc_val,
                requirements=exp_val,
                job_dict=job_data
            )
            
            if self.pdf_published_date:
                try:
                    p_date = datetime.strptime(self.pdf_published_date, "%Y-%m-%d")
                    if (datetime.now() - p_date).days > days_ago:
                        continue
                except:
                    pass
                    
            if not self.is_duplicate(job_data):
                self.jobs_data.append(job_data)
                print(f"  [PDF] Extracted: {job_data['job_title']} at {job_data['company']}")
                
        return cleaned_pdf_jobs

    def scrape_snagajob(self, job_title, location, max_pages=5):
        """Scrape Snagajob listings with keyword and location"""
        search_url = f"https://www.snagajob.com/search?q={job_title.replace(' ', '+')}&w={location.replace(' ', '+')}"
        print(f"Starting Snagajob scrape: {search_url}")
        
        try:
            self.driver.get(search_url)
            self.check_cloudflare()
            
            for page in range(max_pages):
                print(f"Scraping page {page + 1}")
                self.random_delay()
                
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay(2, 4)
                
                try:
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "job-card")))
                    job_cards = self.driver.find_elements(By.TAG_NAME, "job-card")
                except TimeoutException:
                    print("No job cards found on this page.")
                    break
                
                print(f"Found {len(job_cards)} job cards. Processing...")
                
                job_links = []
                for card in job_cards:
                    try:
                        link_elem = card.find_element(By.TAG_NAME, "a")
                        url = link_elem.get_attribute("href")
                        if url:
                            job_links.append(url)
                    except Exception as e:
                        print(f"Error extracting link from card: {e}")
                        continue
                        
                for url in job_links:
                    if url in self.seen_jobs:
                        continue
                    
                    try:
                        print(f"  Visiting: {url}")
                        self.driver.get(url)
                        self.random_delay(2, 4)
                        self.check_cloudflare() 
                        
                        page_source = self.driver.page_source
                        if is_expired_job_content(page_source):
                            print(f"    [SKIP] Job expired / no longer available: {url}")
                            continue
                            
                        job_data = {
                            "source": "Snagajob",
                            "job_title": "N/A",
                            "company": "N/A",
                            "location": "N/A",
                            "pay": "N/A",
                            "job_type_extracted": "N/A",
                            "shift_schedule": "N/A",
                            "experience": "N/A",
                            "description": "N/A",
                            "date_posted": "N/A",
                            "job_url": url,
                            "scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        try:
                            main_content = self.driver.find_element(By.ID, "main-content")
                        except:
                            main_content = self.driver

                        try:
                            job_data["job_title"] = main_content.find_element(By.ID, "jobTitle").text.strip()
                        except:
                            try:
                                job_data["job_title"] = main_content.find_element(By.TAG_NAME, "h1").text.strip()
                            except: 
                                try:
                                    job_data["job_title"] = main_content.find_element(By.CSS_SELECTOR, "[data-snagtag='job-title']").text.strip()
                                except: pass

                        job_data["job_title"] = clean_job_title(job_data["job_title"])

                        try:
                            job_data["company"] = main_content.find_element(By.CSS_SELECTOR, "[data-snagtag='company-name']").text.strip()
                        except: pass
                        
                        try:
                            raw_loc = main_content.find_element(By.CSS_SELECTOR, "[data-snagtag='location']").text.strip()
                            job_data["location"] = clean_location_str(raw_loc)
                        except: pass
                        
                        verified_pay = None
                        try:
                            v_elem = main_content.find_element(By.CSS_SELECTOR, "[data-snagtag='job-verified-wage']")
                            v_text = v_elem.text.strip()
                            if v_text:
                                verified_pay = v_text
                        except: pass
                            
                        try:
                            job_data["job_type_extracted"] = main_content.find_element(By.CSS_SELECTOR, "[data-snagtag='job-categories']").text.strip()
                        except: pass
                        
                        try:
                            company_elem = main_content.find_element(By.CSS_SELECTOR, "[data-snagtag='company-name']")
                            date_elem = company_elem.find_element(By.XPATH, "./../../following-sibling::div[contains(@class, 'text-gray-700')]")
                            date_text = date_elem.text.replace("•", "").strip()
                            job_data["date_posted"] = self.extract_date_posted(date_text)
                        except: 
                            try:
                                potential_date = main_content.find_element(By.XPATH, ".//div[contains(text(), 'days ago') or contains(text(), 'Today') or contains(text(), 'Yesterday')]")
                                job_data["date_posted"] = self.extract_date_posted(potential_date.text.replace("•", "").strip())
                            except: pass

                        # Strip unwanted sidebars, recommendation carousels, promos, ads, and footers from Snagajob page
                        try:
                            self.driver.execute_script("""
                                const junkSelectors = [
                                    'job-card',
                                    'snag-job-card',
                                    'app-job-card',
                                    'aside',
                                    'footer',
                                    'nav',
                                    'app-similar-jobs',
                                    'app-recommended-jobs',
                                    'snag-similar-jobs',
                                    'snag-recommendations',
                                    '[data-snagtag="job-card"]',
                                    '[data-snagtag*="recommend"]',
                                    '[data-snagtag*="similar"]',
                                    '[data-snagtag*="carousel"]',
                                    '[class*="similar"]',
                                    '[class*="recommended"]',
                                    '[class*="related"]',
                                    '[class*="sponsored"]',
                                    '[class*="advertisement"]',
                                    '[class*="ad-container"]',
                                    '[class*="carousel"]',
                                    '[class*="promo"]',
                                    '[id*="similar"]',
                                    '[id*="recommended"]',
                                    '[id*="sponsored"]',
                                    '[id*="carousel"]'
                                ];
                                junkSelectors.forEach(sel => {
                                    document.querySelectorAll(sel).forEach(el => el.remove());
                                });
                            """)
                        except Exception:
                            pass

                        # Expand any collapsed description sections
                        try:
                            expand_buttons = main_content.find_elements(By.XPATH, ".//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'read more') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view more')]")
                            for btn in expand_buttons:
                                if btn.is_displayed():
                                    self.driver.execute_script("arguments[0].click();", btn)
                                    time.sleep(0.3)
                        except:
                            pass

                        full_desc = ""
                        desc_parts = []
                        # 1. Try dedicated container selectors first (avoids parent container bleed)
                        try:
                            desc_containers = main_content.find_elements(By.CSS_SELECTOR, "[data-snagtag='job-description'], [data-snagtag='job-details'], #job-description, .job-description, section.job-description, div[itemprop='description'], div[class*='jobDescription'], div[class*='JobDescription']")
                            for dc in desc_containers:
                                t = dc.text.strip()
                                if t and len(t) > 50 and t not in desc_parts:
                                    desc_parts.append(t)
                        except Exception:
                            pass

                        # 2. Try heading-based container extraction
                        if not desc_parts:
                            try:
                                desc_headings = main_content.find_elements(By.XPATH, ".//h2[contains(text(), 'Job Description') or contains(text(), 'About this job') or contains(text(), 'Requirements') or contains(text(), 'Qualifications') or contains(text(), 'Responsibilities')] | .//h3[contains(text(), 'Job Description') or contains(text(), 'About this job') or contains(text(), 'Requirements') or contains(text(), 'Qualifications') or contains(text(), 'Responsibilities')]")
                                seen_parents = set()
                                for dh in desc_headings:
                                    try:
                                        sibs = dh.find_elements(By.XPATH, "./following-sibling::div | ./following-sibling::p | ./following-sibling::ul")
                                        sib_texts = [s.text.strip() for s in sibs if s.text.strip() and len(s.text.strip()) > 15]
                                        if sib_texts:
                                            desc_parts.append("\n\n".join(sib_texts))
                                        else:
                                            parent_box = dh.find_element(By.XPATH, "..")
                                            if parent_box not in seen_parents:
                                                seen_parents.add(parent_box)
                                                d_text = parent_box.text.strip()
                                                d_text = re.sub(r'^(?:About this job\s*|Job Description\s*)+', '', d_text, flags=re.IGNORECASE).strip()
                                                if d_text and len(d_text) > 20 and d_text not in desc_parts:
                                                    desc_parts.append(d_text)
                                    except:
                                        continue
                            except:
                                pass

                        if desc_parts:
                            full_desc = "\n\n".join(desc_parts)

                        # 3. Try Snagajob data-snagtag selectors fallback
                        if not full_desc or len(full_desc.strip()) < 100:
                            snag_tags = ["job-details", "job-description", "job-requirements", "job-body", "job-content"]
                            tag_parts = []
                            for tag in snag_tags:
                                try:
                                    elems = main_content.find_elements(By.CSS_SELECTOR, f"[data-snagtag='{tag}']")
                                    for el in elems:
                                        t = el.text.strip()
                                        if t and len(t) > 30 and t not in tag_parts:
                                            tag_parts.append(t)
                                except:
                                    continue
                            if tag_parts:
                                full_desc = "\n\n".join(tag_parts)

                        if not full_desc:
                            desc_selectors = [
                                "[data-snagtag='job-description']",
                                "#job-description",
                                ".job-description",
                                "div[itemprop='description']",
                                "section.job-description",
                                ".snag-job-description",
                                "div[class*='JobDescription']",
                                "div[class*='job-description']",
                                "div[class*='description']",
                                "section[class*='description']"
                            ]
                            for d_sel in desc_selectors:
                                try:
                                    desc_elem = main_content.find_element(By.CSS_SELECTOR, d_sel)
                                    d_text = desc_elem.text.strip()
                                    if d_text and len(d_text) > 30:
                                        full_desc = d_text
                                        break
                                except:
                                    continue

                        if not full_desc:
                            try:
                                paras = main_content.find_elements(By.TAG_NAME, "p")
                                p_texts = [p.text.strip() for p in paras if len(p.text.strip()) > 30]
                                if p_texts:
                                    full_desc = "\n\n".join(p_texts)
                            except:
                                pass

                        # 4. Check if description truncated before list items or requirements
                        if full_desc and (full_desc.strip().endswith("Requirements:") or full_desc.strip().endswith("Requirements") or "What Were Looking For" in full_desc[-60:] or "What We're Looking For" in full_desc[-60:]):
                            try:
                                uls = main_content.find_elements(By.XPATH, ".//ul | .//ol")
                                for ul in uls:
                                    ul_text = ul.text.strip()
                                    if ul_text and len(ul_text) > 15 and ul_text not in full_desc:
                                        full_desc += "\n" + ul_text
                            except:
                                pass

                        if full_desc:
                            # Prune any trailing similar jobs or recommendations text
                            for split_pat in [
                                r'(?i)\n+\s*(?:similar\s+jobs|recommended\s+jobs|people\s+also\s+viewed|jobs\s+you\s+might\s+like|other\s+jobs\s+at|browse\s+more\s+jobs|explore\s+more\s+jobs)\b',
                                r'(?i)\n+\s*(?:become\s+a\s+surrogate|earn\s+up\s+to\s+\$?\d+[\d,]*\s+as\s+a\s+surrogate|surrogacy\s+opportunity)\b',
                                r'(?i)\n+\s*(?:travel\s+radiologic\s+technologist|travel\s+physical\s+therapist|travel\s+ct\s+tech)\b',
                            ]:
                                full_desc = re.split(split_pat, full_desc)[0].strip()

                            # Scrub inline ad banners / surrogate text / DoorDash banners
                            full_desc = re.sub(r'(?i)(?:become\s+a\s+surrogate|earn\s+up\s+to\s+\$?(?:100,000|112,000|115,000|60k|75k|85k)|surrogate\s+mothers?|gestational\s+carrier|miracle\s+of\s+life|healthy\s+pregnancy\?\s+learn\s+about)[^\.\n]*[\.\n]?', ' ', full_desc)
                            full_desc = re.sub(r'(?i)(?:doordash\s+shopper|drive\s+with\s+doordash|deliver\s+with\s+uber|looking\s+for\s+part-time\s+jobs\?\s*-\s*deliver)[^\.\n]*[\.\n]?', ' ', full_desc)
                            full_desc = re.sub(r'(?i)(?:paid\s+focus\s+group|paid\s+research\s+panelist|online\s+survey\s+taker|research\s+study\s+panelist)[^\.\n]*[\.\n]?', ' ', full_desc)
                            full_desc = re.sub(r'(?i)(?:travel\s+radiologic\s+technologist|travel\s+ct\s+tech|travel\s+occupational\s+therapist|travel\s+physical\s+therapist)[^\.\n]*[\.\n]?', ' ', full_desc)
                            full_desc = re.sub(r'\s{2,}', ' ', full_desc).strip()

                            if is_expired_job_content(full_desc):
                                print(f"    [SKIP] Description indicates expired: {url}")
                                continue
                            job_data["description"] = full_desc

                        # Prioritize verified employer wage from Snagajob badge, else description pay
                        if verified_pay:
                            job_data["pay"] = verified_pay
                        elif full_desc:
                            desc_pay = extract_pay(full_desc)
                            if desc_pay and not any(art in desc_pay.lower() for art in ["53.85", "112,000", "115,000", "100,000", "48.08", "55.29"]):
                                job_data["pay"] = desc_pay
                            else:
                                job_data["pay"] = "Unstated"
                        else:
                            job_data["pay"] = "Unstated"

                        gemini_res = None
                        if full_desc and len(full_desc.strip()) > 30:
                            try:
                                from gemini_parser import analyze_job_with_gemini
                                gemini_res = analyze_job_with_gemini(
                                    title=job_data["job_title"],
                                    company=job_data["company"],
                                    location=job_data["location"],
                                    description_text=full_desc,
                                    raw_pay=job_data.get("pay", "N/A"),
                                    raw_type=job_data.get("job_type_extracted", "N/A"),
                                    raw_schedule=job_data.get("shift_schedule", "N/A")
                                )
                            except Exception:
                                gemini_res = None

                        if gemini_res:
                            if not gemini_res.is_entry_level:
                                print(f"    [SKIP] Filtered non-entry-level / rejected via Gemini: {job_data['job_title']} ({gemini_res.rejection_reason})")
                                continue
                            job_data["industry"] = gemini_res.sector
                            if gemini_res.pay_rate and gemini_res.pay_rate not in ["N/A"]:
                                job_data["pay"] = gemini_res.pay_rate
                            job_data["experience"] = extract_key_requirements(
                                text=full_desc,
                                existing_exp=gemini_res.experience_requirements,
                                job_dict=job_data
                            )
                            job_data["requirements"] = job_data["experience"]
                        else:
                            job_data["industry"] = self.determine_industry(job_data["job_title"], job_data["company"], job_data.get("description", ""))

                            # Extract structured key requirements for Column I
                            job_data["experience"] = extract_key_requirements(
                                text=full_desc,
                                existing_exp=job_data.get("experience"),
                                job_dict=job_data
                            )
                            job_data["requirements"] = job_data["experience"]

                        driver_lic_type = getattr(gemini_res, "driver_license_type", None) if gemini_res else None
                        job_data["experience"] = standardize_driver_license_requirement(
                            job_data.get("experience", ""),
                            text_context=f"{job_data.get('job_title', '')} {job_data.get('company', '')} {full_desc}",
                            gemini_license=driver_lic_type
                        )
                        job_data["requirements"] = job_data["experience"]

                        # Ensure Column J has key job description information
                        if not job_data.get("description") or job_data["description"] == "N/A":
                            job_data["description"] = generate_key_description(
                                title=job_data["job_title"],
                                company=job_data["company"],
                                location=job_data["location"],
                                sector=job_data["industry"],
                                job_type=job_data.get("job_type_extracted", "N/A"),
                                schedule=job_data.get("shift_schedule", "N/A"),
                                pay=job_data.get("pay", "N/A"),
                                requirements=job_data["experience"]
                            )

                        gemini_tf = getattr(gemini_res, "is_teen_friendly", None) if gemini_res else None
                        job_data["teen_friendly"] = is_teen_friendly(
                            title=job_data.get("job_title", ""),
                            company=job_data.get("company", ""),
                            text=full_desc,
                            requirements=job_data.get("experience", ""),
                            job_dict=job_data,
                            gemini_teen_friendly=gemini_tf
                        )

                        is_rej, rej_reason = is_rejected_job(job_data["job_title"], job_data["company"], job_data.get("description", ""), pay=job_data.get("pay", ""), location=job_data.get("location", ""))
                        if is_rej:
                            print(f"    [SKIP] Filtered non-entry-level / rejected: {job_data['job_title']} ({rej_reason})")
                            continue

                        if self.is_duplicate(job_data):
                            print(f"    [WARN] Duplicate job skipped: {job_data['job_title']} at {job_data['company']}")
                            continue
                        self.jobs_data.append(job_data)
                        self.seen_jobs.add(url)
                        print(f"    -> Extracted: {job_data['job_title']} at {job_data['company']}")
                        
                    except Exception as e:
                        print(f"Error processing job page {url}: {e}")
                        
                if max_pages > 1:
                     print("Pagination verified with one page for current run.")
                     break
                     
        except Exception as e:
            print(f"Snagajob scrape error: {e}")
            import traceback
            traceback.print_exc() 

    def extract_shift(self, text):
        return extract_shift(text)

    def is_duplicate(self, job_data, mark_seen=True):
        job_url = job_data.get('job_url', '')
        if job_url and 'jk=' in job_url:
            match = re.search(r'jk=([a-zA-Z0-9]+)', job_url)
            if match:
                jk_id = match.group(1)
                if jk_id in self.seen_jobs:
                    return True
                if mark_seen:
                    self.seen_jobs.add(jk_id)
                return False
                
        if not job_data.get('job_title') or not job_data.get('company'):
            return False
            
        loc = job_data.get('location', '')
        job_id = f"{job_data['job_title'].lower()}|{job_data['company'].lower()}|{loc.lower()}"
        
        if job_id in self.seen_jobs:
            return True
            
        if mark_seen:
            self.seen_jobs.add(job_id)
        return False
    
    def check_cloudflare(self):
        try:
            if "Security Check" not in self.driver.title and "Just a moment" not in self.driver.title:
                return

            print("    [!] Cloudflare Security Check detected! Attempting to bypass...")
            self.driver.switch_to.default_content()
            
            print("    [!] Waiting up to 30s for automatic Cloudflare redirect...")
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            
            for _ in range(30):
                if "Security Check" not in self.driver.title and "Just a moment" not in self.driver.title:
                    print(f"    [!] Cloudflare challenge passed! Title: {self.driver.title}")
                    self.random_delay(2, 4)
                    return
                
                try:
                    actions.move_by_offset(random.randint(-10, 10), random.randint(-10, 10)).perform()
                except:
                    pass
                
                print(f"    [!] Title: {self.driver.title}...", end='\r')
                time.sleep(1)
            print("")
            
            print("    [!] Page stuck on Cloudflare. Refreshing...")
            self.driver.refresh()
            self.random_delay(5, 8)
            
            if "Security Check" not in self.driver.title and "Just a moment" not in self.driver.title:
                 print("    [!] Refreshed and passed!")
                 return

            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            print(f"    [!] Found {len(iframes)} total iframes on page")
            
            iframe_found = False
            for i, frame in enumerate(iframes):
                try:
                    src = frame.get_attribute("src")
                    if src and ("cloudflare" in src or "turnstile" in src or "challenge" in src):
                        print(f"    [!] Found Cloudflare iframe (Index {i})! Switching...")
                        self.driver.switch_to.frame(frame)
                        
                        checkbox = self.short_wait.until(
                            EC.presence_of_element_located((By.XPATH, "//input[@type='checkbox'] | //div[@class='ctp-checkbox-label'] | //span[@class='mark']"))
                        )
                        
                        if checkbox:
                            print(f"    [!] Found checkbox in iframe {i}. Clicking...")
                            self.random_delay(0.5, 1.5)
                            checkbox.click()
                            print("    [!] Clicked! Waiting for reload...")
                            self.random_delay(5, 10)
                            self.driver.switch_to.default_content()
                            return 
                        
                        self.driver.switch_to.default_content()
                        iframe_found = True
                        
                except Exception:
                    self.driver.switch_to.default_content()
                    continue
            
            if not iframe_found:
                print("    [!] No Cloudflare iframe logic worked. Trying Shadow DOM traversal...")
                try:
                    res = self.driver.execute_script("""
                        function findAndClick() {
                            const all = document.querySelectorAll('*');
                            let shadowsFound = 0;
                            let dumped = "";
                            
                            for (const el of all) {
                                if (el.shadowRoot) {
                                    shadowsFound++;
                                    const input = el.shadowRoot.querySelector('input');
                                    if (input) {
                                        input.click();
                                        return {status: true, msg: "Clicked input in shadow root"};
                                    }
                                    const wrapper = el.shadowRoot.querySelector('div');
                                    if (wrapper) {
                                        dumped = el.shadowRoot.innerHTML;
                                    }
                                }
                            }
                            return {status: false, msg: "Found " + shadowsFound + " shadow roots", dump: dumped};
                        }
                        return findAndClick();
                    """)
                    
                    if isinstance(res, dict):
                        if res.get('status'):
                            print(f"    [!] Success: {res.get('msg')}")
                            self.random_delay(5, 10)
                            return
                        else:
                            print(f"    [!] Failed: {res.get('msg')}")
                            if res.get('dump'):
                                with open("debug_shadow.html", "w", encoding="utf-8") as f:
                                    f.write(res.get('dump'))
                                print("    [!] Dumped shadow root content to debug_shadow.html")
                            
                except Exception as js_e:
                    print(f"    [!] JS Shadow DOM error: {js_e}")

            print("    [!] No actionable element found. Waiting for implicit bypass...")
            
            if getattr(self, 'headless', False):
                print("    [!] Headless environment: Automated bypass unresolved. Gracefully skipping query.")
                return
            
            print("    [!] Waiting up to 45s before automatically continuing...")
            start_wait = time.time()
            while time.time() - start_wait < 45:
                if "Security Check" not in self.driver.title and "Just a moment" not in self.driver.title:
                    print(f"    [!] Cloudflare challenge passed! Resume scraping... (Title: {self.driver.title})")
                    self.random_delay(2, 4)
                    return
                time.sleep(1)
            
            print("    [!] Continuing scraper pipeline automatically...")            
            
        except Exception as e:
            print(f"    [WARN] Error in Cloudflare check: {e}")
            self.driver.switch_to.default_content()

    def close_popups(self):
        popup_selectors = [
            "button[aria-label='Close']",
            "button.modal_closeIcon",
            ".react-modal-close",
            "button[data-test='close-modal']",
            "svg[data-test='close-button']",
            ".modal-close-button",
            "button.CloseButton",
            "button[aria-label='close']",
            ".icl-CloseButton"
        ]
        
        for selector in popup_selectors:
            try:
                btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in btns:
                    if btn.is_displayed():
                        try:
                            btn.click()
                        except Exception:
                            self.driver.execute_script("arguments[0].click();", btn)
                        self.random_delay(0.3, 0.6)
                        print("    [OK] Closed popup")
                        break
            except Exception:
                continue

    def _get_indeed_cards(self):
        """Resiliently discover job card containers on Indeed results page."""
        # 1. Modern Indeed standard card container
        cards = self.driver.find_elements(By.CSS_SELECTOR, "div.cardOutline")
        if cards:
            return cards
            
        # 2. Beacon wrapper container
        cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")
        if cards:
            return cards
            
        # 3. List items inside results list that contain job titles or links
        potential_cards = self.driver.find_elements(By.CSS_SELECTOR, "#mosaic-provider-jobcards ul > li, .jobsearch-ResultsList > li")
        valid_cards = []
        for card in potential_cards:
            try:
                if card.find_elements(By.CSS_SELECTOR, "a.jcs-JobTitle, span[id^='jobTitle'], h2.jobTitle, h3.jobTitle, a[data-jk], h2 a, h3 a"):
                    valid_cards.append(card)
            except Exception:
                pass
        if valid_cards:
            return valid_cards
            
        # 4. Fallback selectors
        for sel in ["div[data-testid='job-card']", "article.job_card", "li.job_card", "div.slider_item"]:
            try:
                found = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if found:
                    return found
            except Exception:
                continue
                
        return []

    def scrape_indeed(self, job_title="Warehouse", location="Redding, CA 96002", radius=15, job_types=["fulltime"], days_ago=4, max_pages=3):
        print(f"\n{'='*60}")
        print(f"Starting Indeed scraping for: {job_title} in {location}")
        print(f"Filters: Radius={radius}m, Types={job_types}, Days={days_ago}")
        print(f"{'='*60}\n")
        
        try:
            base_url = "https://www.indeed.com/jobs"
            
            for jt in job_types:
                print(f"\n--- Searching for Job Type: {jt} ---")
                
                query_params = [
                    f"q={job_title.replace(' ', '+')}",
                    f"l={location.replace(' ', '+')}",
                    f"radius={radius}",
                    f"fromage={days_ago}",
                    f"jt={jt}"
                ]
                
                search_url = f"{base_url}?{'&'.join(query_params)}"
                
                # Network resilience: retry on temporary DNS / socket glitches
                loaded = False
                for attempt in range(2):
                    try:
                        self.driver.get(search_url)
                        loaded = True
                        break
                    except Exception as net_err:
                        err_str = str(net_err)
                        if "ERR_NAME_NOT_RESOLVED" in err_str or "net::" in err_str:
                            print(f"  [WARN] Indeed page load glitch on attempt {attempt + 1}: {err_str[:60]}, retrying in 3s...")
                            time.sleep(3)
                        else:
                            raise
                if not loaded:
                    print(f"  [ERROR] Skipping {jt} due to connection error on {search_url}")
                    continue

                print("[OK] Indeed page loaded - verifying verification...")
                self.random_delay(5, 8)
                self.check_cloudflare()
                
                self.close_popups()
                self.check_cloudflare()
                
                page_count = 0
                
                while page_count < max_pages:
                    print(f"\nScraping Indeed page {page_count + 1} (Type: {jt})...")
                    self.check_cloudflare()
                    
                    try:
                        # 1. Wait for the main results container
                        try:
                            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.cardOutline, div.job_seen_beacon, #mosaic-provider-jobcards ul, .jobsearch-ResultsList")))
                            print("  [OK] Main results container loaded")
                        except:
                            print("  [WARN] Main results container not found, falling back to card detection")

                        self.random_delay(1, 2)
                        cards = self._get_indeed_cards()
                        
                        if not cards:
                            print("  [X] Could not find job cards with any method")
                            with open("debug_failed_scrape.html", "w", encoding="utf-8") as f:
                                f.write(self.driver.page_source)
                            print("    [!] Dumped HTML to debug_failed_scrape.html")
                            break
                        
                        total_cards = len(cards)
                        print(f"  Found {total_cards} job listings on this page")
                        search_page_url = self.driver.current_url

                        # Extract rich structured mosaic metadata directly from Indeed's page state
                        mosaic_lookup = {}
                        try:
                            m_raw = self.driver.execute_script(
                                """
                                try {
                                    if (window.mosaic && window.mosaic.providerData && window.mosaic.providerData['mosaic-provider-jobcards']) {
                                        return window.mosaic.providerData['mosaic-provider-jobcards'].metaData.mosaicProviderJobCardsModel.results;
                                    }
                                } catch(e) {}
                                return null;
                                """
                            )
                            if m_raw and isinstance(m_raw, list):
                                for mr in m_raw:
                                    mjk = mr.get('jobkey')
                                    if mjk:
                                        mosaic_lookup[mjk] = mr
                        except Exception:
                            pass

                        for idx in range(total_cards):
                            navigated_away = False
                            try:
                                print(f"  Processing job {idx + 1}/{total_cards}...")

                                # Ensure browser is on the search results page (recover if navigated away previously)
                                cur_url = self.driver.current_url
                                if "/viewjob" in cur_url or (search_page_url and "/jobs" in search_page_url and "/jobs" not in cur_url):
                                    print("    [NAV] Navigating back to search results page...")
                                    try:
                                        self.driver.back()
                                        self.random_delay(1.5, 2.5)
                                    except Exception:
                                        pass

                                # REPAIR FAILURE MODE 2 (Stale Element Reference & Lazy Loading):
                                # Re-fetch fresh live DOM cards on every iteration
                                live_cards = self._get_indeed_cards()
                                if idx >= len(live_cards):
                                    try:
                                        self.driver.execute_script("window.scrollBy(0, 450);")
                                        self.random_delay(0.8, 1.2)
                                        live_cards = self._get_indeed_cards()
                                    except Exception:
                                        pass

                                if idx >= len(live_cards):
                                    print(f"    [INFO] Card {idx + 1} not found in DOM ({len(live_cards)} available), continuing...")
                                    continue
                                card = live_cards[idx]

                                # Extract unique job key (jk) directly from card element or child link
                                jk = card.get_attribute("data-jk")
                                if not jk:
                                    jk_elems = card.find_elements(By.CSS_SELECTOR, "[data-jk]")
                                    for je in jk_elems:
                                        val = je.get_attribute("data-jk")
                                        if val:
                                            jk = val
                                            break
                                if not jk:
                                    href_elems = card.find_elements(By.CSS_SELECTOR, "a[href*='jk='], a[id^='job_']")
                                    for he in href_elems:
                                        h_val = he.get_attribute("href")
                                        if h_val:
                                            m = re.search(r'jk=([a-zA-Z0-9]+)', h_val)
                                            if m:
                                                jk = m.group(1)
                                                break

                                # Extract baseline title, company, location, pay, and date from the card element
                                card_title = None
                                for t_sel in ["a.jcs-JobTitle", "span[id^='jobTitle']", "h2.jobTitle", "h3.jobTitle", "h2 a", "h3 a", "[data-testid='jobsearch-JobInfoHeader-title']"]:
                                    try:
                                        t_elems = card.find_elements(By.CSS_SELECTOR, t_sel)
                                        if t_elems and t_elems[0].text.strip():
                                            cleaned = clean_job_title(t_elems[0].text.strip())
                                            if cleaned and not is_bogus_title(cleaned):
                                                card_title = cleaned
                                                break
                                    except Exception:
                                        continue

                                card_company = None
                                for c_sel in ["[data-testid='company-name']", "span.companyName", "[data-company-name='true']", "span.css-63koeb", "span.css-1h7uxdj"]:
                                    try:
                                        c_elems = card.find_elements(By.CSS_SELECTOR, c_sel)
                                        if c_elems and c_elems[0].text.strip():
                                            card_company = c_elems[0].text.strip()
                                            break
                                    except Exception:
                                        continue

                                card_location = None
                                for l_sel in ["[data-testid='text-location']", "div.companyLocation", "span.companyLocation", "div.company_location"]:
                                    try:
                                        l_elems = card.find_elements(By.CSS_SELECTOR, l_sel)
                                        if l_elems and l_elems[0].text.strip():
                                            card_location = clean_location_str(l_elems[0].text.strip())
                                            break
                                    except Exception:
                                        continue

                                card_pay = None
                                for p_sel in ["div.metadata.salary-snippet-container", "div.salary-snippet-container", "div.estimated-salary", "[data-testid='attribute_snippet_testid']", "[data-testid*='salary']"]:
                                    try:
                                        p_elems = card.find_elements(By.CSS_SELECTOR, p_sel)
                                        if p_elems and p_elems[0].text.strip():
                                            card_pay = self.extract_pay(p_elems[0].text.strip())
                                            if card_pay:
                                                break
                                    except Exception:
                                        continue

                                card_date = None
                                for d_sel in ["[data-testid='myJobsStateDate']", "span.date", "span.css-10pe3me", "span.css-qs2091", "span[class*='date']"]:
                                    try:
                                        d_elems = card.find_elements(By.CSS_SELECTOR, d_sel)
                                        if d_elems and d_elems[0].text.strip():
                                            raw_d = d_elems[0].text.replace('Posted', '').strip()
                                            parsed_d = self.extract_date_posted(raw_d)
                                            if parsed_d:
                                                card_date = parsed_d
                                                break
                                    except Exception:
                                        continue

                                # Integrate mosaic model metadata if available for this job key
                                mosaic_item = mosaic_lookup.get(jk) if jk else None
                                mosaic_date = None
                                mosaic_pay = None
                                mosaic_jtypes = []
                                mosaic_shifts = []

                                if mosaic_item:
                                    if not card_title and mosaic_item.get('title'):
                                        card_title = clean_job_title(mosaic_item.get('title'))
                                    if not card_company and mosaic_item.get('company'):
                                        card_company = mosaic_item.get('company')
                                    if mosaic_item.get('pubDate'):
                                        try:
                                            mosaic_date = datetime.fromtimestamp(mosaic_item['pubDate'] / 1000.0).strftime('%Y-%m-%d')
                                        except Exception:
                                            pass
                                    if not mosaic_date and mosaic_item.get('formattedRelativeTime'):
                                        mosaic_date = self.extract_date_posted(mosaic_item['formattedRelativeTime'])
                                    if mosaic_item.get('salarySnippet', {}).get('text'):
                                        mosaic_pay = self.extract_pay(mosaic_item['salarySnippet']['text'])
                                    if mosaic_item.get('jobTypes'):
                                        mosaic_jtypes = mosaic_item.get('jobTypes', [])

                                    for ta in mosaic_item.get('taxonomyAttributes', []):
                                        t_lbl = ta.get('label', '')
                                        if t_lbl in ['shifts', 'schedules']:
                                            for a in ta.get('attributes', []):
                                                if a.get('label'):
                                                    mosaic_shifts.append(a.get('label'))
                                        elif t_lbl in ['job-types', 'job-types-cc'] and not mosaic_jtypes:
                                            for a in ta.get('attributes', []):
                                                if a.get('label'):
                                                    mosaic_jtypes.append(a.get('label'))

                                # EARLY PRE-CLICK FILTERING:
                                # 1. Detect non-job promotional banners, salary widgets, or search alert cards early
                                if not card_title and not card_company:
                                    print(f"    [INFO] Non-job promotional/widget card {idx + 1} skipped without clicking")
                                    continue

                                # 2. Save 2-4 seconds per duplicate/rejected job by checking card DOM metadata before clicking
                                if card_title and is_bogus_title(card_title):
                                    print(f"    [SKIP] Bogus card title: '{card_title}' for job {idx + 1}")
                                    continue

                                effective_pay = card_pay or mosaic_pay or ""
                                effective_loc = card_location or location

                                if card_title:
                                    is_rej, rej_reason = is_rejected_job(
                                        card_title, 
                                        card_company or "", 
                                        description="", 
                                        pay=effective_pay, 
                                        location=effective_loc
                                    )
                                    if is_rej:
                                        print(f"    [SKIP] Filtered non-entry-level / rejected: {card_title} ({rej_reason})")
                                        continue

                                    candidate_card_job = {
                                        'source': 'Indeed',
                                        'job_title': card_title,
                                        'company': card_company or "Unknown Company",
                                        'location': effective_loc,
                                        'pay': effective_pay,
                                        'job_url': f"https://www.indeed.com/viewjob?jk={jk}" if jk else ""
                                    }
                                    if self.is_duplicate(candidate_card_job, mark_seen=False):
                                        print(f"    [WARN] Duplicate job skipped: {card_title} at {card_company or 'Unknown Company'}")
                                        continue

                                # Target interactive anchor for clicking into the job preview pane
                                click_target = None
                                title_anchors = card.find_elements(By.CSS_SELECTOR, "a.jcs-JobTitle, a[data-jk], h2.jobTitle a, h3.jobTitle a, span[id^='jobTitle']")
                                if title_anchors:
                                    click_target = title_anchors[0]
                                else:
                                    beacons = card.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon, td.resultContent")
                                    click_target = beacons[0] if beacons else card

                                try:
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", click_target)
                                    self.random_delay(0.2, 0.4)
                                except Exception:
                                    pass

                                self.close_popups()

                                try:
                                    click_target.click()
                                except (ElementNotInteractableException, ElementClickInterceptedException, StaleElementReferenceException, WebDriverException):
                                    try:
                                        self.driver.execute_script("arguments[0].click();", click_target)
                                    except StaleElementReferenceException:
                                        live_cards = self._get_indeed_cards()
                                        if idx < len(live_cards):
                                            card = live_cards[idx]
                                            c_anchors = card.find_elements(By.CSS_SELECTOR, "a.jcs-JobTitle, a[data-jk]")
                                            tgt = c_anchors[0] if c_anchors else card
                                            self.driver.execute_script("arguments[0].click();", tgt)

                                # Wait for detail pane to update for this job
                                start_pane_wait = time.time()
                                while time.time() - start_pane_wait < 3.0:
                                    pane_elems = self.driver.find_elements(By.CSS_SELECTOR, "#jobDescriptionText, div.jobsearch-jobDescriptionText")
                                    if pane_elems and pane_elems[0].text.strip():
                                        if jk and jk in self.driver.current_url:
                                            break
                                        p_heads = self.driver.find_elements(By.CSS_SELECTOR, "h2[data-testid='jobsearch-JobInfoHeader-title'], h1[data-testid='jobsearch-JobInfoHeader-title']")
                                        if p_heads and card_title and card_title.lower()[:12] in p_heads[0].text.strip().lower():
                                            break
                                    time.sleep(0.3)

                                # Check if click triggered navigation to /viewjob or external page
                                cur_url = self.driver.current_url
                                if "/viewjob" in cur_url or (search_page_url and "/jobs" in search_page_url and "/jobs" not in cur_url):
                                    navigated_away = True

                                if not jk:
                                    vjk_match = re.search(r'[v]jk=([a-zA-Z0-9]+)', self.driver.current_url)
                                    if vjk_match:
                                        jk = vjk_match.group(1)

                                job_url = f"https://www.indeed.com/viewjob?jk={jk}" if jk else self.driver.current_url

                                job_data = {
                                    'source': 'Indeed',
                                    'job_title': card_title,
                                    'company': card_company or "Unknown Company",
                                    'location': effective_loc,
                                    'pay': card_pay or mosaic_pay,
                                    'job_type_extracted': ", ".join(mosaic_jtypes) if mosaic_jtypes else None,
                                    'shift_schedule': "; ".join(mosaic_shifts) if mosaic_shifts else None,
                                    'experience': None,
                                    'description': None,
                                    'date_posted': mosaic_date or card_date,
                                    'job_url': job_url,
                                    'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }

                                # Scope detail search: use pane if on search page, or full driver if navigated to viewjob
                                pane_containers = self.driver.find_elements(
                                    By.CSS_SELECTOR, 
                                    "#jobsearch-ViewjobPaneWrapper, div.jobsearch-JobComponent, #viewJobSSRRoot, div.jobsearch-RightPane"
                                )
                                search_scope = pane_containers[0] if (pane_containers and not navigated_away) else self.driver

                                # Extract title from pane with fallback to card_title
                                pane_title = None
                                title_selectors = [
                                    "h2[data-testid='jobsearch-JobInfoHeader-title']",
                                    "h1[data-testid='jobsearch-JobInfoHeader-title']",
                                    "h2.jobsearch-JobInfoHeader-title",
                                    "h1.jobsearch-JobInfoHeader-title",
                                    "span.jobsearch-JobInfoHeader-title-container"
                                ]
                                for selector in title_selectors:
                                    try:
                                        t_elems = search_scope.find_elements(By.CSS_SELECTOR, selector)
                                        if t_elems and t_elems[0].text.strip():
                                            raw_title = t_elems[0].text.strip()
                                            if len(raw_title) > 2 and "job post details" not in raw_title.lower() and not is_bogus_title(raw_title):
                                                pane_title = clean_job_title(raw_title)
                                                if pane_title:
                                                    break
                                    except Exception:
                                        continue

                                candidate_title = pane_title or card_title
                                if not candidate_title or is_bogus_title(candidate_title):
                                    print(f"    [SKIP] Could not extract valid non-bogus job title for job {idx + 1}")
                                    continue
                                job_data['job_title'] = candidate_title

                                # Extract company from pane with fallback
                                for c_sel in ["[data-testid='inlineHeader-companyName']", "[data-company-name='true']", "div[data-testid='company-name']", "a[data-testid='company-name']", "span.companyName"]:
                                    try:
                                        c_elems = search_scope.find_elements(By.CSS_SELECTOR, c_sel)
                                        if c_elems and c_elems[0].text.strip():
                                            job_data['company'] = c_elems[0].text.strip()
                                            break
                                    except Exception:
                                        continue

                                # Extract location from pane with fallback
                                for l_sel in ["[data-testid='inlineHeader-companyLocation']", "[data-testid='text-location']", "div.companyLocation"]:
                                    try:
                                        l_elems = search_scope.find_elements(By.CSS_SELECTOR, l_sel)
                                        if l_elems and l_elems[0].text.strip():
                                            spec_loc = clean_location_str(l_elems[0].text.strip())
                                            if spec_loc:
                                                job_data['location'] = spec_loc
                                                break
                                    except Exception:
                                        continue

                                # Extract date posted from pane if not already captured
                                if not job_data['date_posted']:
                                    for d_sel in ["span.date", "div.jobsearch-JobMetadataFooter", "[data-testid='myJobsStateDate']", "span.css-10pe3me", "span.css-qs2091"]:
                                        try:
                                            d_elems = search_scope.find_elements(By.CSS_SELECTOR, d_sel)
                                            if d_elems and d_elems[0].text.strip():
                                                raw_date = d_elems[0].text.replace('Posted', '').strip()
                                                parsed_d = self.extract_date_posted(raw_date)
                                                if parsed_d:
                                                    job_data['date_posted'] = parsed_d
                                                    break
                                        except Exception:
                                            continue

                                # Extract FULL description text from Indeed pane
                                desc_selectors = [
                                    "#jobDescriptionText",
                                    "div.jobsearch-jobDescriptionText",
                                    "[data-testid='job-description']",
                                    "div.jobsearch-JobComponent-description"
                                ]
                                description = ""
                                for selector in desc_selectors:
                                    try:
                                        desc_elems = search_scope.find_elements(By.CSS_SELECTOR, selector)
                                        if desc_elems and desc_elems[0].text.strip():
                                            description = desc_elems[0].text.strip()
                                            break
                                    except Exception:
                                        continue

                                # Fallback 1: Search top-level driver document
                                if not description and search_scope != self.driver:
                                    for selector in desc_selectors:
                                        try:
                                            desc_elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                            if desc_elems and desc_elems[0].text.strip():
                                                description = desc_elems[0].text.strip()
                                                break
                                        except Exception:
                                            continue

                                # Fallback 2: Check embedded detail iframe (vjs-container)
                                if not description:
                                    try:
                                        vjs_frames = self.driver.find_elements(By.CSS_SELECTOR, "iframe#vjs-container-iframe, iframe[title*='Job'], iframe[id*='vjs']")
                                        for frame in vjs_frames:
                                            try:
                                                self.driver.switch_to.frame(frame)
                                                f_elems = self.driver.find_elements(By.CSS_SELECTOR, "#jobDescriptionText, div.jobsearch-jobDescriptionText, [data-testid='job-description'], body")
                                                if f_elems and f_elems[0].text.strip():
                                                    f_txt = f_elems[0].text.strip()
                                                    if len(f_txt) > 50:
                                                        description = f_txt
                                                        self.driver.switch_to.default_content()
                                                        break
                                                self.driver.switch_to.default_content()
                                            except Exception:
                                                self.driver.switch_to.default_content()
                                    except Exception:
                                        pass

                                # Async fallback fetch via browser session if pane was empty
                                if not description and jk:
                                    try:
                                        fetched_html = self.driver.execute_async_script(
                                            """
                                            var jk = arguments[0];
                                            var callback = arguments[arguments.length - 1];
                                            fetch('/viewjob?jk=' + jk)
                                                .then(function(res) { return res.text(); })
                                                .then(function(html) { callback(html); })
                                                .catch(function(err) { callback(''); });
                                            """,
                                            jk
                                        )
                                        if fetched_html and len(fetched_html) > 200:
                                            from bs4 import BeautifulSoup as BS
                                            f_soup = BS(fetched_html, "html.parser")
                                            f_desc = f_soup.select("#jobDescriptionText, div.jobsearch-jobDescriptionText")
                                            if f_desc:
                                                description = f_desc[0].get_text(separator="\n").strip()
                                            f_scripts = f_soup.find_all("script", {"type": "application/ld+json"})
                                            for fs in f_scripts:
                                                try:
                                                    f_json = json.loads(fs.string)
                                                    if isinstance(f_json, dict) and f_json.get("@type") == "JobPosting":
                                                        if not description and f_json.get("description"):
                                                            description = BS(f_json.get("description"), "html.parser").get_text(separator="\n").strip()
                                                        if not job_data.get('date_posted') and f_json.get("datePosted"):
                                                            job_data['date_posted'] = f_json.get("datePosted")[:10]
                                                except Exception:
                                                    pass
                                    except Exception:
                                        pass

                                # Check for expired job banner in pane wrapper or description
                                pane_text = ""
                                for pane_sel in ["#jobsearch-ViewjobPaneWrapper", "div.jobsearch-JobComponent", "#viewJobSSRRoot"]:
                                    try:
                                        p_elems = search_scope.find_elements(By.CSS_SELECTOR, pane_sel)
                                        if p_elems and p_elems[0].text.strip():
                                            pane_text = p_elems[0].text.strip()
                                            break
                                    except Exception:
                                        pass

                                if is_expired_job_content(pane_text) or is_expired_job_content(description):
                                    print(f"    [SKIP] Expired job on Indeed: {job_data['job_title']} ({job_data['job_url']})")
                                    continue

                                # Extract pay and schedule pills from #salaryInfoAndJobType
                                try:
                                    metadata_elems = search_scope.find_elements(By.CSS_SELECTOR, "div#salaryInfoAndJobType, [data-testid='jobsearch-JobInfoHeader-salaryInfo']")
                                    if metadata_elems and metadata_elems[0].text.strip():
                                        metadata_text = metadata_elems[0].text.strip()
                                        if not job_data['pay']:
                                            job_data['pay'] = self.extract_pay(metadata_text)
                                        if not job_data['job_type_extracted']:
                                            job_data['job_type_extracted'] = self.extract_job_type(metadata_text)
                                        if not job_data['shift_schedule']:
                                            job_data['shift_schedule'] = self.extract_shift(metadata_text)
                                except Exception:
                                    pass

                                qual_text = ""
                                try:
                                    qual_elems = search_scope.find_elements(By.CSS_SELECTOR, "div#qualificationsSection li, div[data-testid='qualifications'] li")
                                    if qual_elems:
                                        qual_text = "; ".join(q.text.strip() for q in qual_elems if q.text.strip())
                                except Exception:
                                    pass

                                full_context = f"{description} {qual_text}".strip()
                                if description:
                                    job_data['description'] = description
                                    if not job_data['pay']:
                                        job_data['pay'] = self.extract_pay(description)
                                    if not job_data['job_type_extracted']:
                                        job_data['job_type_extracted'] = self.extract_job_type(description)
                                    if not job_data['shift_schedule']:
                                        job_data['shift_schedule'] = self.extract_shift(description)

                                # Gemini flash extraction for classification, requirements, pay, and address
                                gemini_res = None
                                if description and len(description.strip()) > 30:
                                    try:
                                        from gemini_parser import analyze_job_with_gemini
                                        gemini_res = analyze_job_with_gemini(
                                            title=job_data["job_title"],
                                            company=job_data["company"],
                                            location=job_data["location"],
                                            description_text=description,
                                            raw_pay=job_data.get("pay") or "Unstated",
                                            raw_type=job_data.get("job_type_extracted") or "Unstated",
                                            raw_schedule=job_data.get("shift_schedule") or "Unstated"
                                        )
                                    except Exception:
                                        gemini_res = None

                                if gemini_res:
                                    if not gemini_res.is_entry_level:
                                        print(f"    [SKIP] Filtered non-entry-level / rejected via Gemini: {job_data['job_title']} ({gemini_res.rejection_reason})")
                                        continue
                                    job_data['industry'] = gemini_res.sector
                                    if gemini_res.pay_rate and gemini_res.pay_rate not in ["N/A", "Unstated"]:
                                        job_data['pay'] = gemini_res.pay_rate
                                    if gemini_res.job_type and gemini_res.job_type not in ["N/A", "Unstated"]:
                                        job_data['job_type_extracted'] = gemini_res.job_type
                                    if gemini_res.schedule and gemini_res.schedule not in ["N/A", "Unstated"]:
                                        job_data['shift_schedule'] = gemini_res.schedule
                                    job_data['experience'] = extract_key_requirements(
                                        text=full_context,
                                        existing_exp=gemini_res.experience_requirements,
                                        job_dict=job_data
                                    )
                                    job_data['requirements'] = job_data['experience']
                                else:
                                    job_data['industry'] = self.determine_industry(job_data['job_title'], job_data['company'], job_data.get('description', ''))
                                    job_data['experience'] = extract_key_requirements(
                                        text=full_context,
                                        existing_exp=qual_text,
                                        job_dict=job_data
                                    )
                                    job_data['requirements'] = job_data['experience']

                                driver_lic_type = getattr(gemini_res, "driver_license_type", None) if gemini_res else None
                                job_data['experience'] = standardize_driver_license_requirement(
                                    job_data.get('experience', ''),
                                    text_context=f"{job_data.get('job_title', '')} {job_data.get('company', '')} {full_context}",
                                    gemini_license=driver_lic_type
                                )
                                job_data['requirements'] = job_data['experience']

                                # Ensure pay rate is never left empty
                                if not job_data.get('pay') or job_data['pay'] in ["N/A", "None", ""]:
                                    job_data['pay'] = "Unstated"

                                # Ensure job type (Full / Part Time) is captured
                                if not job_data.get('job_type_extracted') or job_data['job_type_extracted'] in ["N/A", "None", ""]:
                                    job_data['job_type_extracted'] = "Part-time" if jt == "parttime" else "Full-time" if jt == "fulltime" else "Unstated"

                                # Ensure schedule / shift is never left empty
                                if not job_data.get('shift_schedule') or job_data['shift_schedule'] in ["N/A", "None", ""]:
                                    job_data['shift_schedule'] = "Unstated"

                                # Ensure Date Posted is never left empty
                                if not job_data.get('date_posted') or job_data['date_posted'] in ["N/A", "None", ""]:
                                    job_data['date_posted'] = datetime.now().strftime('%Y-%m-%d')

                                # Resolve physical business address for RABA bus line feasibility
                                job_data['location'] = resolve_business_address(
                                    company=job_data['company'],
                                    location=job_data.get('location', 'Redding, CA 96002'),
                                    description=description,
                                    gemini_address=gemini_res.business_address if gemini_res else None
                                )

                                # Preserve actual job description
                                if not job_data.get('description') or job_data['description'] in ['N/A', '']:
                                    job_data['description'] = generate_key_description(
                                        title=job_data['job_title'],
                                        company=job_data['company'],
                                        location=job_data['location'],
                                        sector=job_data['industry'],
                                        job_type=job_data.get('job_type_extracted', 'Unstated'),
                                        schedule=job_data.get('shift_schedule', 'Unstated'),
                                        pay=job_data.get('pay', 'Unstated'),
                                        requirements=job_data['experience']
                                    )

                                gemini_tf = getattr(gemini_res, "is_teen_friendly", None) if gemini_res else None
                                job_data['teen_friendly'] = is_teen_friendly(
                                    title=job_data.get('job_title', ''),
                                    company=job_data.get('company', ''),
                                    text=full_context,
                                    requirements=job_data.get('experience', ''),
                                    job_dict=job_data,
                                    gemini_teen_friendly=gemini_tf
                                )

                                is_rej, rej_reason = is_rejected_job(job_data['job_title'], job_data['company'], job_data.get('description', ''), pay=job_data.get('pay', ''), location=job_data.get('location', ''))
                                if is_rej:
                                    print(f"    [SKIP] Filtered non-entry-level / rejected: {job_data['job_title']} ({rej_reason})")
                                    continue

                                if self.is_duplicate(job_data, mark_seen=True):
                                    print(f"    [WARN] Duplicate job skipped: {job_data['job_title']} at {job_data['company']}")
                                    continue

                                self.jobs_data.append(job_data)
                                print(f"    [OK] Extracted: {job_data['job_title']} at {job_data['company']}")
                                if job_data['pay']: print(f"      (Pay) Pay: {job_data['pay']}")
                                if job_data['job_type_extracted']: print(f"      (Type) Type: {job_data['job_type_extracted']}")
                                if job_data['shift_schedule']: print(f"      (Shift) Shift: {job_data['shift_schedule']}")
                                if job_data['date_posted']: print(f"      (Date) Date: {job_data['date_posted']}")
                                if job_data['location']: print(f"      (Address) Address: {job_data['location']}")

                            except Exception as e:
                                print(f"    [X] Error processing job: {str(e)}")
                                continue
                            finally:
                                if navigated_away:
                                    try:
                                        self.driver.back()
                                        self.random_delay(1.2, 2.0)
                                    except Exception:
                                        pass

                        try:
                            next_selectors = [
                                "[data-testid='pagination-page-next']",
                                "a[aria-label='Next Page']",
                                "a[data-testid='pagination-page-next']",
                                "a.np"
                            ]
                            for selector in next_selectors:
                                try:
                                    next_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                    if next_buttons:
                                        next_button = next_buttons[0]
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                                        self.random_delay(1, 2)
                                        try:
                                            next_button.click()
                                        except Exception:
                                            self.driver.execute_script("arguments[0].click();", next_button)
                                        self.random_delay(5, 10)
                                        self.check_cloudflare()
                                        page_count += 1
                                        break
                                except Exception:
                                    continue
                            else:
                                print("  No more pages available")
                                break
                        except Exception as e:
                            print(f"  Pagination error: {str(e)}")
                            break

                    except TimeoutException:
                        print("  Timeout waiting for job listings")
                        break

        except Exception as e:
            print(f"[ERROR] Error during Indeed scraping: {str(e)}")

    def save_to_excel(self, filename="job_listings.xlsx", rejected_titles=None, rejected_employers=None):
        """Save collected data to Excel with professional formatting and auto-sized columns."""
        if not self.jobs_data:
            print("\n[WARN] No data to save!")
            return
            
        if rejected_titles is None:
            rejected_titles = ["surrogate"]
        if rejected_employers is None:
            rejected_employers = ["navy", "doordash"]
            
        rej_titles_lower = [t.lower() for t in rejected_titles]
        rej_emp_lower = [e.lower() for e in rejected_employers]

        processed_data = []
        unique_hashes = set()
        
        cutoff_date = datetime.now() - timedelta(days=7)
        cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        print(f"\nProcessing {len(self.jobs_data)} collected jobs...")
        
        for job in self.jobs_data:
            # Check expired content
            if is_expired_job_content(job.get('description', '')) or is_expired_job_content(job.get('job_title', '')):
                continue

            # Check rejection criteria (titles, employers, degree/qualification requirements, pay ceiling, Shasta County location)
            is_rej, _ = is_rejected_job(job.get('job_title', ''), job.get('company', ''), job.get('description', ''), pay=job.get('pay', ''), location=job.get('location', ''))
            if is_rej:
                continue

            t_lower = str(job.get('job_title', '')).lower().strip()
            c_lower = str(job.get('company', '')).lower().strip()
            
            skip = False
            for rej in rej_titles_lower:
                if re.search(r'\b' + re.escape(rej) + r'\b', t_lower):
                    skip = True
                    break
            if skip:
                continue

            for rej in rej_emp_lower:
                if re.search(r'\b' + re.escape(rej) + r'\b', c_lower):
                    skip = True
                    break
            if skip:
                continue

            d_str = job.get('date_posted', 'N/A')
            if d_str and d_str != 'N/A':
                try:
                    d_date = datetime.strptime(d_str, "%Y-%m-%d")
                    if d_date < cutoff_date:
                        continue
                except:
                    pass
            
            job['location'] = resolve_business_address(
                company=job.get('company', ''),
                location=job.get('location', 'Redding, CA'),
                description=job.get('description', '')
            )
            if not job.get('industry') or job['industry'] in ['Other', 'N/A', '']:
                job['industry'] = self.determine_industry(job.get('job_title'), job.get('company'), job.get('description', ''))
            
            if not job.get('experience') or job['experience'] in ['N/A', 'None', '', 'Entry-level / No prior experience required']:
                job['experience'] = extract_key_requirements(
                    text=job.get('description', ''),
                    existing_exp='',
                    job_dict=job
                )

            if not job.get('pay') or job['pay'] in ['N/A', 'None', '']:
                job['pay'] = 'Unstated'

            if not job.get('job_type_extracted') or job['job_type_extracted'] in ['N/A', 'None', '']:
                job['job_type_extracted'] = 'Unstated'

            if not job.get('shift_schedule') or job['shift_schedule'] in ['N/A', 'None', '']:
                job['shift_schedule'] = 'Unstated'

            if not job.get('date_posted') or job['date_posted'] in ['N/A', 'None', '']:
                job['date_posted'] = datetime.now().strftime('%Y-%m-%d')

            if not job.get('description') or job['description'] in ['N/A', '']:
                job['description'] = generate_key_description(
                    title=job.get('job_title', ''),
                    company=job.get('company', ''),
                    location=job.get('location', 'Redding, CA'),
                    sector=job['industry'],
                    job_type=job.get('job_type_extracted', 'Unstated'),
                    schedule=job.get('shift_schedule', 'Unstated'),
                    pay=job.get('pay', 'Unstated'),
                    requirements=job['experience']
                )
            
            job['teen_friendly'] = is_teen_friendly(
                title=job.get('job_title', ''),
                company=job.get('company', ''),
                text=job.get('description', ''),
                requirements=job.get('experience', ''),
                job_dict=job,
                gemini_teen_friendly=job.get('teen_friendly')
            )
            
            t = str(job.get('job_title', '')).lower().strip()
            c = str(job.get('company', '')).lower().strip()
            l = str(job.get('location', '')).lower().strip()
            
            job_hash = (t, c, l)
            if job_hash in unique_hashes:
                continue
            unique_hashes.add(job_hash)
            
            processed_data.append(job)
            
        print(f"Refined job count: {len(processed_data)} (after filtering and deduplication)")
        self.jobs_data = processed_data
        
        if not processed_data:
            print("[WARN] No jobs remained after filtering.")
            return

        df = pd.DataFrame(processed_data)
        
        # Report date for "Last Updated"
        report_date = datetime.now().strftime("%Y-%m-%d")
        df['last_updated'] = report_date

        column_order = [
            'source', 'job_title', 'company', 'location', 'pay', 
            'job_type_extracted', 'shift_schedule', 'experience', 
            'teen_friendly', 'description', 'date_posted', 'job_url', 
            'industry', 'last_updated'
        ]
        for col in column_order:
            if col not in df.columns:
                df[col] = "N/A"
            
        df = df[column_order]
        df.sort_values(by="date_posted", ascending=False, inplace=True)
        
        display_headers = {
            'source': 'Source',
            'job_title': 'Job Title',
            'company': 'Company',
            'location': 'Location',
            'pay': 'Pay Rate',
            'job_type_extracted': 'Full / Part Time',
            'shift_schedule': 'Schedule / Shift',
            'experience': 'Experience / Requirements',
            'teen_friendly': 'Teen Friendly',
            'description': 'Job Description Summary',
            'date_posted': 'Date Posted',
            'job_url': 'Job Posting',
            'industry': 'Industry Sector',
            'last_updated': 'Last Updated'
        }
        df.rename(columns=display_headers, inplace=True)

        try:
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Active Job Openings')
                ws = writer.sheets['Active Job Openings']

                ws.freeze_panes = 'A2'

                header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
                header_fill = PatternFill(start_color='1E293B', end_color='1E293B', fill_type='solid')
                thin_border = Border(
                    left=Side(style='thin', color='CBD5E1'),
                    right=Side(style='thin', color='CBD5E1'),
                    top=Side(style='thin', color='CBD5E1'),
                    bottom=Side(style='thin', color='CBD5E1')
                )

                for col_num in range(1, len(df.columns) + 1):
                    cell = ws.cell(row=1, column=col_num)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=False)
                    cell.border = thin_border
                    ws.row_dimensions[1].height = 26

                for col_idx, col in enumerate(df.columns, start=1):
                    max_len = len(str(col))
                    col_letter = get_column_letter(col_idx)

                    for row_idx in range(2, len(df) + 2):
                        cell = ws.cell(row=row_idx, column=col_idx)
                        val_str = str(cell.value or '')
                        
                        if col == 'Job Posting' and val_str.startswith(('http://', 'https://')):
                            cell.hyperlink = val_str
                            cell.font = Font(name='Calibri', size=10, color='2563EB', underline='single')
                        elif col == 'Teen Friendly':
                            cell.font = Font(name='Calibri', size=10)
                            cell.alignment = Alignment(horizontal='center', vertical='center')
                        else:
                            cell.font = Font(name='Calibri', size=10)

                        cell.border = thin_border
                        if col != 'Teen Friendly':
                            cell.alignment = Alignment(vertical='center')

                        if len(val_str) > max_len:
                            max_len = len(val_str)

                    if col == 'Teen Friendly':
                        ws.column_dimensions[col_letter].width = 15
                    else:
                        ws.column_dimensions[col_letter].width = max(12, min(max_len + 3, 45))

            # Export CSV alongside Excel with matching columns
            csv_path = os.path.splitext(filename)[0] + ".csv"
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"\n{'='*60}")
            print(f"  [OK] Excel saved: {filename}")
            print(f"  [OK] CSV exported: {csv_path}")
            print(f"  Total jobs saved: {len(df)}")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"[ERROR] Could not save styled Excel: {e}")
            df.to_excel(filename, index=False)
            csv_path = os.path.splitext(filename)[0] + ".csv"
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"  [OK] CSV fallback exported: {csv_path}")

    def close(self):
        self.driver.quit()

def run_pdf_scrape(pdf_path=None):
    return run_scraping_job(run_pdf=True, run_online=False, filename_prefix="pdf_only", pdf_path=pdf_path, days_ago=14)

def run_redding_scrape(keywords=None, channels=None):
    return run_scraping_job(keywords=keywords, location=["Redding, CA 96002"], channels=channels, run_pdf=False, filename_prefix="redding_only")

def run_burney_scrape(keywords=None, channels=None):
    return run_scraping_job(keywords=keywords, location=["Burney, CA 96013"], channels=channels, run_pdf=False, filename_prefix="burney_only")

def run_scraping_job(keywords=None, location=None, radius=None, job_types=None, days_ago=None, max_pages=None, rejected_titles=None, rejected_employers=None, channels=None, run_pdf=True, run_online=True, filename_prefix="job_results", pdf_path=None):
    config = load_search_config()
    
    if keywords is None: keywords = config.get("keywords")
    if location is None: location = config.get("location")
    if radius is None: radius = config.get("radius", 15)
    if job_types is None: job_types = config.get("job_types", ["parttime", "fulltime"])
    if days_ago is None: days_ago = config.get("days_ago", 4)
    if max_pages is None: max_pages = config.get("max_pages", 3)
    if rejected_titles is None: rejected_titles = config.get("rejected_titles")
    if rejected_employers is None: rejected_employers = config.get("rejected_employers")
    if channels is None: channels = config.get("channels", ["Indeed", "Snagajob"])
    if isinstance(channels, str):
        channels = [c.strip() for c in channels.split(",") if c.strip()]
    if not channels:
        channels = ["Indeed", "Snagajob"]
    
    scraper = None
    output_file = None
    
    print("\n" + "="*60)
    print(f"JOB SCRAPER - {filename_prefix.upper()} MODE")
    print(f"Channels: {', '.join(channels)}")
    print("="*60 + "\n")
    
    try:
        if isinstance(keywords, str): keywords = [keywords]
        if isinstance(location, str): location = [location]
        
        scraper = JobScraper()
        
        print("Waiting 5 seconds for initial checks...")
        scraper.random_delay(5, 8)
        
        last_synced_count = 0

        if run_pdf:
            scraper.scrape_local_pdf(days_ago=days_ago, pdf_path=pdf_path)
            if len(scraper.jobs_data) > last_synced_count:
                new_jobs = scraper.jobs_data[last_synced_count:]
                try:
                    from firestore_sync import sync_jobs_to_firestore
                    sync_jobs_to_firestore(new_jobs)
                    last_synced_count = len(scraper.jobs_data)
                except Exception as fs_err:
                    print(f"[WARN] Incremental Firestore sync failed: {fs_err}")
        
        if run_online:
            active_channels_lower = [c.lower() for c in channels]
            for keyword in keywords:
                for loc in location:
                    print(f"Processing Keyword: {keyword} in {loc} (Channels: {', '.join(channels)})")
                    
                    if any("indeed" in c for c in active_channels_lower):
                        scraper.scrape_indeed(
                            job_title=keyword, 
                            location=loc, 
                            radius=radius,
                            job_types=job_types,
                            days_ago=days_ago,
                            max_pages=max_pages
                        )
                        scraper.random_delay(3, 5)
                    
                    if any("snagajob" in c or "snag" in c for c in active_channels_lower):
                        scraper.scrape_snagajob(
                            job_title=keyword,
                            location=loc,
                            max_pages=min(2, max_pages)
                        )
                        scraper.random_delay(3, 5)

                    for ch in channels:
                        ch_low = ch.lower()
                        if not any(k in ch_low for k in ["indeed", "snag"]):
                            print(f"[CHANNEL] '{ch}' selected (integration pending/beta).")

                    # Incremental sync to Firestore so jobs appear live in CMS while scraping
                    if len(scraper.jobs_data) > last_synced_count:
                        new_jobs = scraper.jobs_data[last_synced_count:]
                        try:
                            from firestore_sync import sync_jobs_to_firestore
                            sync_jobs_to_firestore(new_jobs)
                            last_synced_count = len(scraper.jobs_data)
                        except Exception as fs_err:
                            print(f"[WARN] Incremental Firestore sync failed: {fs_err}")
            
        if scraper.jobs_data:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            output_folder = os.path.join(base_dir, "output")
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")    
            output_file = os.path.join(output_folder, f"{filename_prefix}_{timestamp}.xlsx")
            
            scraper.save_to_excel(output_file, rejected_titles=rejected_titles, rejected_employers=rejected_employers)
            
            # Synchronize remaining new jobs directly to Firestore
            if len(scraper.jobs_data) > last_synced_count:
                new_jobs = scraper.jobs_data[last_synced_count:]
                try:
                    from firestore_sync import sync_jobs_to_firestore
                    sync_jobs_to_firestore(new_jobs)
                    last_synced_count = len(scraper.jobs_data)
                except Exception as fs_err:
                    print(f"[WARN] Firestore sync failed: {fs_err}")

            # Synchronize directly to Google Sheets
            try:
                from sheets_sync import update_google_sheet
                update_google_sheet(scraper.jobs_data)
            except Exception as gs_err:
                print(f"[WARN] Google Sheets sync failed: {gs_err}")

            return output_file
        else:
            print("[INFO] No data found to save.")
            return None
        
    except Exception as e:
        print(f"Error during scraping process: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if scraper and scraper.jobs_data:
            print("[INFO] Attempting to save partial results before exit...")
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                output_folder = os.path.join(base_dir, "output")
                if not os.path.exists(output_folder): 
                    os.makedirs(output_folder)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(output_folder, f"partial_{filename_prefix}_{timestamp}.xlsx")
                scraper.save_to_excel(output_file, rejected_titles=rejected_titles, rejected_employers=rejected_employers)
                return output_file
            except:
                pass
        return None
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    run_scraping_job()