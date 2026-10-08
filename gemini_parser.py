import os
import json
import re
from typing import Optional
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

WORKFORCE_TAXONOMY = {
    "Animal Care & Veterinary Services": {
        "scope": "Domestic/livestock care, grooming, boarding, veterinary support",
        "common_titles": "Kennel Assistant, Pet Bather, Veterinary Aide, Shelter Caretaker"
    },
    "Agriculture & Groundskeeping": {
        "scope": "Farming, nurseries, landscaping, commercial grounds maintenance",
        "common_titles": "Farm Hand, Nursery Worker, Landscaper, Grounds Maintenance Aide"
    },
    "Childcare & Education Support": {
        "scope": "Early childhood facilities, schools, youth development",
        "common_titles": "Daycare Aide, Preschool Assistant, After-School Tutor, Instructional Aide"
    },
    "Construction & Laborers": {
        "scope": "Job site building, structural renovation, general utility labor",
        "common_titles": "Construction Laborer, Carpenter Helper, Drywall Apprentice, Site Cleanup, Other Laborers"
    },
    "Customer Service & Hospitality": {
        "scope": "Front-of-house service, lodging, ticketing, contact centers",
        "common_titles": "Front Desk Clerk, Guest Services Agent, Call Center Rep, Concierge"
    },
    "Food & Restaurant": {
        "scope": "Food prep, commercial kitchen operations, dining service",
        "common_titles": "Dishwasher, Line Cook, Prep Cook, Host/Hostess, Barista, Server"
    },
    "Healthcare & Caregiving": {
        "scope": "Non-acute patient assistance, in-home care, facility support",
        "common_titles": "Caregiver, Home Health Aide, Direct Support Professional (DSP), CNA"
    },
    "Janitorial & Facilities": {
        "scope": "Building sanitation, custodial upkeep, commercial cleaning",
        "common_titles": "Custodian, Janitor, Housekeeper, Floor Tech, EVS Specialist"
    },
    "Manufacturing & Production": {
        "scope": "Assembly plants, factory fabrication, industrial processing",
        "common_titles": "Assembly Line Worker, Packaging Operator, Production Helper, QA Sorter"
    },
    "Office & Clerical": {
        "scope": "Administrative support, record keeping, front office reception",
        "common_titles": "Receptionist, File Clerk, Data Entry Operator, Office Assistant, Bank Teller"
    },
    "Personal Care & Services": {
        "scope": "Salons, barbershops, personal styling, wellness support",
        "common_titles": "Salon Assistant, Barber Apprentice, Spa Attendant"
    },
    "Retail & Sales": {
        "scope": "Storefront retail, field canvassing & direct sales, phone appointment setting, cashiering, merchandising",
        "common_titles": "Sales Associate, Canvasser, Appointment Setter, Cashier, Stock Associate, Merchandiser"
    },
    "Security & Public Safety": {
        "scope": "Facility protection, access control, event monitoring",
        "common_titles": "Unarmed Security Guard, Gate Attendant, Loss Prevention Associate"
    },
    "Social & Human Services": {
        "scope": "Community support, non-profits, transitional shelter aid",
        "common_titles": "Community Outreach Aide, Food Bank Sorter, Shelter Support Worker"
    },
    "Technology & IT Support": {
        "scope": "Hardware diagnostics, cable pulling, helpdesk support",
        "common_titles": "Helpdesk Technician, PC Repair Assistant, Cable/Telecom Installer Helper"
    },
    "Trades & Mechanics": {
        "scope": "Mechanical & automotive, appliance repair, electrical, HVAC, plumbing, trades apprenticeship",
        "common_titles": "Mechanic Helper, Lube & Oil Tech, Tire Technician, Appliance Repair Assistant, HVAC Helper, Plumber Assistant, Electrician Helper, Trade Apprentice"
    },
    "Transportation & Delivery": {
        "scope": "Local delivery, route driving, courier dispatch",
        "common_titles": "Route Driver, Van Delivery Courier, Non-CDL Delivery Helper"
    },
    "Warehouse & Logistics": {
        "scope": "Material handling, shipping & receiving, inventory staging",
        "common_titles": "Package Handler, Order Picker, Forklift Operator, Staging Associate"
    },
    "Other": {
        "scope": "Specialized roles outside standard workforce sectors",
        "common_titles": "General Service Worker, Event Staff"
    }
}

VALID_SECTORS = list(WORKFORCE_TAXONOMY.keys())

class JobAnalysisResult(BaseModel):
    is_entry_level: bool = Field(description="True if the position is an in-person, local entry-level role suitable for Shasta County job seekers with 0-2 years experience. False if the job is remote/work-from-home, an online survey/research panel/focus group, a travel healthcare contract, supervisory (Foreman, Lead), senior tier (Associate II/III+), journeyman trade (Experienced Carpenter, HVAC Tech without helper/apprentice), professional planner, 1099 contractor, or exceeds pay ceilings ($38/hr, $1,520/wk, $75k/yr).")
    rejection_reason: Optional[str] = Field(default=None, description="If is_entry_level is False, provide the specific disqualifying reason (e.g. 'Remote / Survey panel position', 'Travel healthcare contract', 'Supervisory role (Foreman)', 'Senior tier (Associate III)', 'Journeyman trade / requires trade certification', 'Exceeds compensation ceiling').")
    clean_title: str = Field(description="Clean, concise job title without scraper artifacts, emojis, or marketing noise.")
    sector: str = Field(description=f"Best matching industry sector from: {', '.join(VALID_SECTORS)}")
    business_address: str = Field(description="The actual physical street address of the business/worksite in the Redding / Shasta County, CA area (e.g. '1030 Dana Dr, Redding, CA 96002', '1070 E Cypress Ave, Redding, CA 96002', '3737 Mountain Lakes Blvd, Redding, CA 96003'). Extract from the job description if present; otherwise resolve the physical facility/branch street address for this company in Redding, CA. If a private home/confidential employer without a commercial storefront, provide the nearest street/crossroads and city/zip (e.g. 'Redding, CA 96002').")
    pay_rate: str = Field(description="Employer-stated compensation rate (e.g., '$18.00 - $22.00 / hr', '$20.00 per hour', '$55,000 / yr') or 'Unstated' if not stated in the posting text. Never include algorithmic estimated wages.")
    job_type: str = Field(description="Full-time, Part-time, Contract, Temporary, Apprenticeship, or Unstated.")
    schedule: str = Field(description="Shift or schedule (e.g. Day shift, Night shift, Swing shift, Weekend availability, 8 hour shift, Monday to Friday) or Unstated.")
    experience_requirements: str = Field(description="Structured, semicolon-separated list of candidate prerequisites for Column I. NEVER omit concrete prerequisites stated in the posting: Driver's license & vehicle (e.g. 'Commercial Driver\\'s License (CDL-A) required' if Class A, 'Commercial Driver\\'s License (CDL-B) required' if Class B, 'Valid CA Driver License (Class C) and reliable vehicle required' or 'Valid CA Driver License (Class C) and clean DMV record required'); role certifications (e.g. 'Active Home Health Aide (CHHA) certification required', 'Paraprofessional assessment / 48 college units / Paraeducator credential required/preferred', 'Active CNA certification required', 'Forklift certification preferred / training provided', 'CPR / BLS certification required/preferred'); minimum age (e.g. 'Must be 18+ years old'); education (e.g. 'High School Diploma or GED required'); clearances (e.g. 'Background check / Live Scan required', 'TB (Tuberculosis) clearance required', 'Drug screening required'); physical demands (e.g. 'Ability to lift 50-75 lbs', 'Ability to lift up to 50 lbs', 'Ability to stand for extended periods'); operational specifics (e.g. 'Smartphone required for timekeeping/apps', 'Weekend availability required'); and training ('On-the-job training provided' or 'No experience required (On-the-job training provided)').")
    job_description_summary: str = Field(description="Crisp 2-3 sentence overview of the role's essential responsibilities, daily tasks, and duties. Do not duplicate metadata like pay or sector.")
    min_age: Optional[int] = Field(default=18, description="Minimum age requirement if explicitly specified (e.g. 16, 18, 21), or 18 as default.")
    is_youth_friendly: bool = Field(default=False, description="True if the job is explicitly marked 16+, youth-friendly, or suitable for minors/students.")
    is_teen_friendly: bool = Field(default=False, description="True ONLY IF the position is available to youth under 18 years of age (14-17). Set True ONLY if the employer is specifically known to hire under age 18 (e.g. McDonald's, Taco Bell, Chick-fil-A, In-N-Out, Dutch Bros, Wendy's, Target, Cinemark) or if clearly stated in the job description (e.g. 16+, youth-friendly, minor, student). If the job description explicitly requires 18+ or 21+ or requires commercial driving/supervisory duties, set False.")
    requires_driver_license: bool = Field(default=False, description="True if a driver's license or driving duties are required.")
    driver_license_type: str = Field(default="None", description="One of: 'None', 'Class C (Standard)', 'Commercial Class A (CDL-A)', 'Commercial Class B (CDL-B)'. If the job requires Class A / CDL-A, set 'Commercial Class A (CDL-A)' and include 'Commercial Driver\\'s License (CDL-A) required' in experience_requirements.")
    requires_hs_ged: bool = Field(default=False, description="True if high school diploma or GED is explicitly required.")
    requires_drug_test: bool = Field(default=False, description="True if drug screening is explicitly stated as required.")
    requires_background_check: bool = Field(default=False, description="True if background check is explicitly stated as required.")

def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"[GEMINI] Error initializing google.genai Client: {e}")
        return None

def analyze_job_with_gemini(
    title: str,
    company: str,
    location: str,
    description_text: str,
    raw_pay: str = "N/A",
    raw_type: str = "N/A",
    raw_schedule: str = "N/A"
) -> Optional[JobAnalysisResult]:
    """
    Parses, understands, and structures job posting data using Gemini Flash with structured schema output.
    Returns None if GEMINI_API_KEY is not configured or if an unrecoverable API error occurs.
    """
    client = get_gemini_client()
    if not client:
        return None

    taxonomy_guide = "\n".join([
        f"     * {sec}: Scope: {info['scope']} | Common Entry-Level Titles: {info['common_titles']}"
        for sec, info in WORKFORCE_TAXONOMY.items()
    ])

    prompt = f"""
You are an expert workforce development analyst for Shasta County, California (Redding, Anderson, Shasta Lake area).
Analyze the following job posting and extract structured, verified data for workforce program participants.

JOB CONTEXT:
- Scraped Title: {title}
- Company / Employer: {company}
- Location: {location}
- Scraped Pay: {raw_pay}
- Scraped Job Type: {raw_type}
- Scraped Schedule: {raw_schedule}

FULL ON-PAGE JOB POSTING TEXT:
\"\"\"
{description_text}
\"\"\"

CRITICAL EVALUATION RULES:
1. MANDATORY REJECTIONS (Set is_entry_level=False and provide rejection_reason):
   - REMOTE / WORK-FROM-HOME / SURVEY / FOCUS GROUP:
     Reject ANY job that is Remote, Work-from-Home, Out-of-Office, Telecommute, or is a paid research panelist, paid focus group participant, survey panelist, or online study participant (e.g. Maxion Research, Focus Group Panel). All jobs must be local, in-person positions in Shasta County, CA.
   - TRAVEL HEALTHCARE & CONTRACT ASSIGNMENTS:
     Reject ANY job that is a travel healthcare contract, travel assignment, or traveling role (e.g., 'Travel CT Tech', 'Travel CT Technologist', 'Travel Nurse', AlliedTravelCareers, Jackson HealthPros).
   - SUPERVISORY & SENIOR ROLES:
     Reject Foreman (e.g. 'carpenter foreman'), Supervisor, Superintendent, Manager, Lead (e.g. 'Lead Mechanic'), or Team Lead positions.
   - SENIOR PROMOTIONAL TIERS:
     Reject positions designated with Roman numerals or senior levels: Associate II, Associate III, Level II, Level III, Tier II, Tier III (e.g. 'Library - Associate III').
   - PROFESSIONAL PLANNING & ADVANCED DEGREE ROLES:
     Reject professional planner positions (e.g. 'Municipal Planner', 'Urban Planner', 'City Planner') or roles requiring Bachelor's, Master's, PhD, MD, or JD degrees.
   - JOURNEYMAN TRADES & SKILLED MECHANICS / INSTALLERS:
     Reject skilled trade installers, lead mechanics, field mechanics, master mechanics, and journeyman roles (e.g. 'Field Mechanic', 'Lead Mechanic', 'Acrylic Bath Installer', 'Experienced Carpenter', or 'HVAC Technician') UNLESS explicitly titled Helper, Assistant, Apprentice, or Trainee.
   - EXPERIENCE ONLY:
     Reject any position titled or explicitly stating 'experience only' or 'experienced only'.
   - 1099 CONTRACTOR & ON-CALL TECH:
     Reject 1099 independent contractor roles, on-call field technicians requiring their own tools, vehicle, and diagnostic gear (e.g. 'On-Call IT Field Technician', Geeks on Site).
   - SPECIALIZED LICENSES & HEAVY CERTIFICATIONS:
     Reject positions requiring ARRT, EPA Section 608 Universal, LCSW, LMFT, LPCC, RN, DVM, or mandatory forklift certification / 2+ years heavy equipment experience (e.g. 'Forklift Operator - (ONTB)').
   - SURROGACY / EGG DONOR / MEDICAL SUBJECTS:
     Reject paid surrogate mother, egg donor, sperm donor, plasma donation, or clinical trial subject opportunities (e.g. Legend Family Surrogacy). These are medical procedures, not employment.
   - COMPENSATION CEILINGS:
     Reject if compensation exceeds entry-level ceilings: $38.00/hour, $1,520/week, or $75,000/year.
   - EXPERIENCE CEILING:
     Reject if requiring 3+ years of mandatory prior experience (e.g. 'Minimum 5 years heavy mechanic experience').

2. ACCEPTABLE ENTRY-LEVEL POSITIONS (Set is_entry_level=True):
   - Accept genuine local, in-person entry-level, helper, apprentice, trainee, or 0-2 year experience positions (e.g. Dishwasher, Cashier, Retail Associate, Caregiver, Warehouse Material Handler, Construction Laborer, Trades Helper/Apprentice, Local Route Driver).
   - Local route delivery drivers (e.g. Blach Beverage CDL Driver) that provide route training and local distribution are accepted, but accurately capture their CDL requirement.

3. ACCURATE COLUMN DATA:
   - Sector: Must be selected strictly from the standard 19-sector workforce taxonomy based on occupational scope and titles:
{taxonomy_guide}
     * Retail Store Rule: Storefront associates, task associates, cashiers, stockers, and beauty advisors at retail stores (e.g. Ulta, Target, Burlington, Pacsun, Walmart) belong to 'Retail & Sales' (or 'Customer Service & Hospitality'), NOT 'Security & Public Safety' even if the posting mentions adhering to loss prevention policies or protecting store assets.
   - Business Address: Physical street address of the employer/worksite in the Redding / Shasta County, CA area (e.g. '1030 Dana Dr, Redding, CA 96002', '1070 E Cypress Ave, Redding, CA 96002', '3737 Mountain Lakes Blvd, Redding, CA 96003'). Essential for participants who rely on Redding Area Bus Authority (RABA) public transit. Extract from text if present; if not stated in text, provide the known physical street address for {company} in Redding, CA. If private residence or unlisted, provide nearest crossroads / city and zip (e.g. 'Redding, CA 96002').
   - Pay Rate (Column F): Extract the true employer-provided pay rate from text or metadata. If a wage range is given (e.g. '$21 - $25/hr', '$16.90 - $21.45/hr'), extract the FULL range (both minimum and maximum), never just a single boundary. If no wage is given by the employer, use "Unstated". Never use algorithmic estimates.
   - Full / Part Time (Column G): Full-time, Part-time, Apprenticeship, Temporary, or Unstated.
   - Schedule / Shift (Column H): Shift or schedule (e.g. Day shift, Night shift, Swing shift, Weekend availability, 8 hour shift, Monday to Friday). Carefully scan for explicit shift hours (e.g. 'Day Shift: 6:00 AM–6:30 PM; Night Shift: 6:00 PM–6:30 AM', '30.0 - 40.0 hours per week; Flexible schedule', 'School hours / Monday to Friday'). NEVER output 'Unstated' if shift windows or hours are explicitly stated in the posting.
   - Driver's License Requirement (Column I):
     Carefully check if the role requires a Commercial Driver License.
     * If the posting mentions Class A, CDL-A, or CDL Class A, you MUST include 'Commercial Driver\\'s License (CDL-A) required' in the Experience / Requirements text and set driver_license_type='Commercial Class A (CDL-A)'. Do NOT downgrade or omit Class A.
     * If Class B or CDL-B is mentioned, include 'Commercial Driver\\'s License (CDL-B) required' and set driver_license_type='Commercial Class B (CDL-B)'.
     * If standard driving duties are mentioned, include 'Valid CA Driver License (Class C) required'.
     * If no driving duties, state 'No driver license required'.
   - Experience / Requirements (Column I): Semicolon-separated list of candidate prerequisites. Never omit concrete requirements stated in the posting:
     * Driver's license & vehicle: 'Commercial Driver\'s License (CDL-A) required' if Class A; 'Commercial Driver\'s License (CDL-B) required' if Class B; 'Valid CA Driver License (Class C) and reliable vehicle required' if vehicle/insurance required; 'Valid CA Driver License (Class C) and clean DMV record required' if clean DMV stated; 'Valid CA Driver License (Class C) required'; or 'No driver license required'.
     * Specific role certifications: 'Active Home Health Aide (CHHA) certification required', 'Paraprofessional assessment / 48 college units / Paraeducator credential required/preferred', 'Active CNA certification required', 'Forklift certification preferred / training provided', 'CPR / BLS certification required/preferred'.
     * Culinary & Kitchen specifics: For cook, prep cook, or line cook positions, do NOT replace stated food prep experience or knife skills with 'On-the-job training provided' simply because the employer offers 'paid training' as a company benefit. Include both (e.g. 'Prior food prep / line cook experience required; Knife skills required; On-the-job training provided').
     * Physical demands: Exact lifting demands (e.g. 'Ability to lift 50-75 lbs', 'Ability to lift up to 50 lbs'), 'Ability to stand for extended periods'.
     * Clearances & testing: 'Background check / Live Scan required', 'TB (Tuberculosis) clearance required', 'Drug screening required'.
     * Operational prerequisites: 'Smartphone required for timekeeping/apps', 'Weekend availability required'.
     * Education & Age: 'Must be 18+ years old', 'High School Diploma or GED required'.
     * Training / Experience: 'On-the-job training provided' or 'No experience required (On-the-job training provided)'. Never output a vague 'Entry level'.
   - Job Description Summary (Column J): Crisp 2-3 sentence summary describing daily duties and responsibilities. Do NOT repeat metadata like sector, pay, or requirements list.
   - Teen Friendly (Checkbox Column):
     * Set is_teen_friendly to True ONLY IF the job is available to youth under 18 years old (ages 14-17).
     * Do NOT set True unless the employer is specifically known to hire under age 18 (such as McDonald's, Taco Bell, Chick-fil-A, In-N-Out, Dutch Bros, Wendy's, Burger King, Carl's Jr, Target, Cinemark, Best Buy, Home Depot) OR it is clearly stated in the job description (e.g., 14+, 15+, 16+, youth-friendly, minors welcome, high school student).
     * If the job explicitly requires 18+ or 21+, requires a Commercial Driver License (CDL), or is a supervisory/managerial role (General Manager, Assistant Manager, Shift Supervisor, Lead), set is_teen_friendly=False.
"""

    models_to_try = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-3.8-flash", "gemini-3.5-flash"]
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": JobAnalysisResult,
                    "temperature": 0.1,
                }
            )
            if response and response.text:
                data = json.loads(response.text)
                return JobAnalysisResult(**data)
        except Exception as e:
            # Try next model fallback
            continue

    return None
