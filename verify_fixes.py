import sys
import os
from scrapper import JobScraper, is_rejected_job, is_expired_job_content, clean_job_title

def test_unit_logic():
    print("=== Testing Unit Filtering Logic ===")
    
    # Test title cleaning
    raw_title = "Warehouse Associate\n- job post"
    cleaned = clean_job_title(raw_title)
    print(f"clean_job_title: '{raw_title}' -> '{cleaned}'")
    assert cleaned == "Warehouse Associate", f"Expected 'Warehouse Associate', got '{cleaned}'"

    # Test rejection filter: Non-entry-level titles
    test_cases = [
        ("Chief Financial Officer", "Acme", "Job description", True),
        ("Board Certified Behavior Analyst (BCBA)", "Clinic", "Job description", True),
        ("Licensed Clinical Social Worker", "Health", "Job description", True),
        ("Retail Warehouse Associate", "Best Buy", "Warehouse duties", False),
        ("Dishwasher", "Local Diner", "Washing dishes", False),
        ("Registered Nurse - ICU", "Hospital", "Nursing care", True),
        ("Driver", "Logistics Co", "Requires Master's Degree in Business", True),
        ("Cashier", "Target", "Requires Bachelor's Degree required for consideration", True),
        ("Stock Associate", "Walmart", "Requires 7+ years of experience in retail", True),
        ("Food Service Worker", "School", "No prior experience required. 18+ years old.", False),
        # User reported examples:
        ("Certified Prosthetist Orthotist", "Spectrum Orthotics & Prosthetics", "Duties", True, "$85,000 - $100,000"),
        ("Registered Dietitian - Eastern Michigan \"thumb\"", "Concert Consulting", "Duties", True, "$40 - $45"),
        ("Licensed Professional Counselor (LPC)", "Rula Health", "Duties", True, "$90 - $105"),
        ("Principal Enterprise Applications SAP Basis Consultant", "Infosys", "Duties", True, "$116,700 - $150,000"),
        ("Commercial Construction Superintendent", "Rick Shipman Construction", "Duties", True, "$90,000 - $112,000"),
        ("NOC Medical Assistant (Full-Time)", "New Dawn Treatment Centers", "Duties", True, "$21 - $24"),
        ("Vetco Relief Veterinarian", "Vetco Clinics", "Duties", True, "$17.90"),
        ("LVN (JRF)-(7am-4pm, including Saturday & Sunday)", "Shasta Community Health Center", "Duties", True, "$17.90"),
        # OTR Trucking cases:
        ("OTR Team Truck Driver", "Swift", "Long haul driving across the country", True, "$25/hr"),
        ("Over the road Class A Driver", "CRST", "Duties", True, "$30/hr"),
        ("Local Route Driver", "Local Supply Co", "Local Redding deliveries only. Home daily.", False, "$20/hr"),
        # Reported travel / remote / research panel jobs:
        ("Travel CT Tech - $2,616 per week in Redding, CA - Now Hiring", "AlliedTravelCareers", "Travel contract in Redding", True, "$2,616 per week"),
        ("Remote Out of Office Position / Data Entry (Hiring Immediately)", "Maxion Research", "Remote data entry position", True, "17.9"),
        ("Travel CT Tech - $2,679 to $2,879 per week in Redding, CA", "AlliedTravelCareers", "Travel contract in Redding", True, "$2,679 to $2,879 per week"),
        ("Travel CT Tech - $2,893 per week in Redding, CA", "AlliedTravelCareers", "Travel contract in Redding", True, "$2,893 per week"),
        ("Cashier / Retail Worker - Paid Research Panelist (Remote)", "Maxion Research", "Paid research study panelist", True, "17.9"),
        ("Travel CT Technologist - $2,879 per week", "Jackson HealthPros", "Travel imaging technologist", True, "17.9"),
        ("Cashier / Retail Worker - Paid Focus Group Participant (Remote)", "Focus Group Panel", "Focus group panelist", True, "17.9"),
        ("Customer Service Rep - Remote Paid Research Panelist", "Focus Group Panel", "Remote panelist", True, "17.9"),
        ("Customer Service Rep - Remote Paid Research Study Panelist", "Maxion Research", "Remote study", True, "17.9"),
        # Reported non-entry-level / specialized requirements:
        ("On-Call IT Field Technician - Redding, CA- Hiring NOW", "Geeks on Site", "1099 independent contractor field tech", True, "$35 per hour"),
        ("carpenter foreman", "Biddlecome Construction Inc", "Supervise construction site", True, "17.9"),
        ("Acrylic Bath Installer", "Bath Concepts Independent Dealers", "Install acrylic baths", True, "17.9"),
        ("HVAC Technician", "Pearce Services", "Service commercial HVAC systems", True, "17.9"),
        ("Forklift Operator - (ONTB)", "Accurate Personnel LLC", "Forklift operator warehouse", True, "17.9"),
        ("Library - Associate III", "Library Systems & Services LLC", "Provides library services", True, "Unstated"),
        ("Municipal Planner", "GoodwinRecruiting", "Municipal city planning", True, "17.9"),
        ("Experienced Carpenter", "CRBR", "Looking for experienced carpenter", True, "$33.80 - $38.00"),
        # Snagajob user reported cases:
        ("Field Mechanic - Redding, CA", "Wilson Construction Co.", "Minimum 5 years heavy mechanic experience. Must have tools and be willing to travel.", True, "$35.00"),
        ("Construction Equipment Lead Mechanic - experience only", "Express Employment Professionals", "Supervise shop and lead field mechanics. Experience only.", True, "$38.00"),
        ("CDL Driver", "Blach Beverage", "Delivery Driver to join our team. Starting $22.00 Hourly. Must have valid Class A Driver's License. Must be 18 years old.", False, "$22.00 Hourly"),
        # Regressions from October 2026 run:
        ("Retail Warehouse Associate", "Best Buy", "Warehouse duties. Similar jobs: Travel Physical Therapist (PT)", False, "$17.50"),
        ("Dishwasher", "Local Diner", "Washing dishes and sanitizing equipment. Clean physical therapist sidebar ignored.", False, "$16.50"),
        ("Cook", "Woody's", "Line cook duties. Food prep and grilling.", False, "$53.85/hr"),
        ("Team Member", "Target", "Guest service, cashiering, and stocking.", False, "$53.85/hr"),
        ("Caregiver / Personal Assistant- Redding", "Homecare Agency", "In-home personal care for seniors. Ad: Become a surrogate mother and earn up to $115,000.", False, "$18.00"),
        ("Babysitter Needed for my Children", "Private Family", "Care for 2 children after school. Ad: earn up to $115,000 as a surrogate.", False, "$17.00"),
        ("Home Care Aide", "Visiting Angels", "Serving Shasta County seniors with over 25 years of caregiving experience.", False, "$18.00"),
        ("Patient Services Representative", "Health Clinic", "Schedule patient appointments. Work alongside medical assistants and nurses.", False, "$19.00"),
        ("Traffic Control Flagger", "Construction Co", "Direct traffic on job sites. Must have valid driver's license for 3 years.", False, "$20.00"),
        # New regression test cases for Radiologic Technologist sidebar bleed:
        ("Retail Associates", "Burlington", "Customer service and merchandise displays. Trending nearby: Travel Radiologic Technologist", False, "$17.00"),
        ("Sandwich maker , Cashier", "Subway", "Making sandwiches and taking orders. Nearby: Radiologic Technologist", False, "$16.50"),
        ("Popeyes Cook - PT", "Popeyes", "Prep and fry station. Recommended: Radiologic Technologist", False, "$17.00"),
        ("Server", "Market Street Steakhouse", "Food and beverage service. Similar jobs: Radiologic Technologist", False, "$16.50"),
        ("Housekeeper (Part Time)", "Oxford Suites", "Clean guest rooms and replace linens. Sidebar: Radiologic Technologist", False, "$17.00"),
        ("General Labor", "Shasta Precast", "Clean equipment and move materials. Sidebar: Radiologic Technologist", False, "$18.00"),
        # New regression test cases for promo wage ceiling artifacts ($100k, $115k, $48.08, $55.29, $53.85):
        ("Seasonal Retail Sales Associate-MT SHASTA MALL - Now Hiring", "Aeropostale", "Retail store associate. Ad: Earn up to $100,000 as surrogate", False, "$100,000"),
        ("Part Time Product Demonstrator in Costco", "Club Demonstration Services", "Sample product demonstrations in warehouse. Ad banner: $100,000", False, "$100,000"),
        ("Nanny needed for one toddler with car, pet-friendly, weekdays", "Private Family", "Afternoon care for toddler.", False, "$53.85/hr"),
        ("Caregiver", "Visiting Angels", "Senior in-home companionship and daily support.", False, "$48.08/hr"),
        ("Caregiver / Personal Assistant- Redding", "Homecare Professionals", "Assist clients with personal care and meal prep.", False, "$55.29/hr"),
        # Ensure actual Radiologic Technologist / Imaging roles ARE rejected:
        ("Radiologic Technologist", "Mercy Medical Center", "Diagnostic X-ray and fluoroscopy procedures.", True, "$45.00/hr"),
        ("Travel Radiologic Technologist", "AlliedTravelCareers", "13-week travel contract.", True, "$2,600 per week"),
    ]

    for item in test_cases:
        title = item[0]
        comp = item[1]
        desc = item[2]
        expected_rej = item[3]
        pay = item[4] if len(item) > 4 else ""
        rej, reason = is_rejected_job(title, comp, desc, pay=pay)
        status = "REJECTED" if rej else "ACCEPTED"
        print(f"  [{status}] {title} ({pay if pay else 'No pay'}) -> {reason}")
        assert rej == expected_rej, f"Failed for {title}: expected {expected_rej}, got {rej}"

    # Test expired content detection
    expired_texts = [
        "This job has expired on Indeed. Reasons could include: the employer is not accepting applications...",
        "The job below is no longer available. Check out other jobs nearby.",
        "We are currently hiring full-time warehouse associates for our Redding fulfillment center.",
    ]
    assert is_expired_job_content(expired_texts[0]) == True
    assert is_expired_job_content(expired_texts[1]) == True
    assert is_expired_job_content(expired_texts[2]) == False
    
    # Test CDL-A requirement extraction and standardization
    from scrapper import extract_key_requirements, standardize_driver_license_requirement
    blach_desc = "Must have valid Class A Driver's License. Must be able to carry up to 50 lbs. and lift up to 170 lbs. Must be 18 years old."
    blach_reqs = extract_key_requirements(blach_desc, job_dict={"job_title": "CDL Driver", "company": "Blach Beverage"})
    print(f"Extracted requirements for Blach Beverage CDL Driver: '{blach_reqs}'")
    assert "Commercial Driver's License (CDL-A) required" in blach_reqs, f"Expected CDL-A in requirements, got: {blach_reqs}"
    assert "Class C" not in blach_reqs, f"Should not have Class C when CDL-A is required, got: {blach_reqs}"
    
    # Test standardization helper directly
    std_reqs = standardize_driver_license_requirement("No experience required", text_context="Must have valid Class A Driver's License")
    assert "Commercial Driver's License (CDL-A) required" in std_reqs, f"Expected CDL-A inserted, got: {std_reqs}"

    # Test Ewing Outdoor Supply: Customer Service Warehouse Associate
    ewing_desc = "Clean DMV record, valid driver license. Ability to lift 50-75 lbs. Forklift certification preferred. High school diploma or GED."
    ewing_reqs = extract_key_requirements(ewing_desc, job_dict={"job_title": "Customer Service Warehouse Associate", "company": "Ewing Outdoor Supply"})
    print(f"Extracted requirements for Ewing: '{ewing_reqs}'")
    assert "clean dmv record" in ewing_reqs.lower(), f"Expected clean DMV in Ewing, got: {ewing_reqs}"
    assert "50-75 lbs" in ewing_reqs, f"Expected 50-75 lbs lifting in Ewing, got: {ewing_reqs}"
    assert "forklift" in ewing_reqs.lower(), f"Expected forklift in Ewing, got: {ewing_reqs}"
    assert "high school diploma" in ewing_reqs.lower(), f"Expected HS diploma in Ewing, got: {ewing_reqs}"

    # Test Bristol Hospice: CHHA Home Health Aide - Trinity County
    bristol_desc = "Current California CHHA or CNA. Valid driver license, reliable vehicle, auto insurance. CPR / BLS. Criminal background check Live Scan. 18+ years old."
    bristol_reqs = extract_key_requirements(bristol_desc, job_dict={"job_title": "CHHA Home Health Aide - Trinity County", "company": "Bristol Hospice"})
    print(f"Extracted requirements for Bristol Hospice: '{bristol_reqs}'")
    assert "chha" in bristol_reqs.lower(), f"Expected CHHA in Bristol Hospice, got: {bristol_reqs}"
    assert "reliable vehicle" in bristol_reqs.lower(), f"Expected reliable vehicle in Bristol Hospice, got: {bristol_reqs}"
    assert "cpr" in bristol_reqs.lower(), f"Expected CPR in Bristol Hospice, got: {bristol_reqs}"
    assert "live scan" in bristol_reqs.lower() or "background check" in bristol_reqs.lower(), f"Expected background check in Bristol Hospice, got: {bristol_reqs}"

    # Test LeafHome: Event Marketer California
    leaf_desc = "Ability to work weekends (Friday, Saturday, Sunday). Reliable vehicle and valid driver’s license required. Event set up and tear down (ability to lift to 50 pounds). Must have a smartphone to use the Company timekeeping application. Standing for extended periods of time."
    leaf_reqs = extract_key_requirements(leaf_desc, job_dict={"job_title": "Event Marketer California", "company": "LeafHome"})
    print(f"Extracted requirements for LeafHome: '{leaf_reqs}'")
    assert "reliable vehicle" in leaf_reqs.lower(), f"Expected reliable vehicle in LeafHome, got: {leaf_reqs}"
    assert "lift up to 50 lbs" in leaf_reqs.lower(), f"Expected lift up to 50 lbs in LeafHome, got: {leaf_reqs}"
    assert "weekend" in leaf_reqs.lower(), f"Expected weekend availability in LeafHome, got: {leaf_reqs}"
    assert "smartphone" in leaf_reqs.lower(), f"Expected smartphone in LeafHome, got: {leaf_reqs}"
    assert "stand" in leaf_reqs.lower(), f"Expected standing in LeafHome, got: {leaf_reqs}"

    # Test Spectrum Center Schools: Special Education Paraprofessional
    spectrum_desc = "Must meet ESSA paraprofessional standards (48 college units or Paraprofessional Exam). LiveScan background clearance and TB test. High School Diploma or GED. Valid driver license."
    spectrum_reqs = extract_key_requirements(spectrum_desc, job_dict={"job_title": "Special Education Paraprofessional", "company": "Spectrum Center Schools"})
    print(f"Extracted requirements for Spectrum Center Schools: '{spectrum_reqs}'")
    assert "paraprofessional" in spectrum_reqs.lower(), f"Expected paraprofessional in Spectrum, got: {spectrum_reqs}"
    assert "tb" in spectrum_reqs.lower(), f"Expected TB clearance in Spectrum, got: {spectrum_reqs}"
    assert "live scan" in spectrum_reqs.lower() or "background check" in spectrum_reqs.lower(), f"Expected background check in Spectrum, got: {spectrum_reqs}"
    assert "high school diploma" in spectrum_reqs.lower(), f"Expected HS diploma in Spectrum, got: {spectrum_reqs}"

    print("Unit filtering and requirement extraction tests passed successfully!\n")

def test_teen_friendly_logic():
    print("=== Testing Teen Friendly Column & Filter Logic ===")
    from scrapper import is_teen_friendly, is_known_teen_employer

    # 1. Test known employer recognition
    assert is_known_teen_employer("McDonald's") == True
    assert is_known_teen_employer("McDonalds") == True
    assert is_known_teen_employer("Taco Bell") == True
    assert is_known_teen_employer("Taco Bell #1234") == True
    assert is_known_teen_employer("In-N-Out Burger") == True
    assert is_known_teen_employer("Chick-fil-A") == True
    assert is_known_teen_employer("Bird Hospitality LLC (Chick-fil-A)") == True
    assert is_known_teen_employer("Dutch Bros Coffee") == True
    assert is_known_teen_employer("Target") == True
    assert is_known_teen_employer("Cinemark") == True
    assert is_known_teen_employer("Best Buy") == True
    assert is_known_teen_employer("AutoZone") == True
    assert is_known_teen_employer("Home Depot") == True
    assert is_known_teen_employer("Acme Logistics") == False
    assert is_known_teen_employer("Ewing Outdoor Supply") == False
    assert is_known_teen_employer("Bristol Hospice") == False

    # 2. Test positive known employer cases
    assert is_teen_friendly(title="Crew Member", company="McDonald's", text="Food prep, cashiering") == True
    assert is_teen_friendly(title="Team Member", company="Taco Bell", text="Take orders, make tacos") == True
    assert is_teen_friendly(title="Front of House Team Member", company="Chick-fil-A", text="Guest service") == True
    assert is_teen_friendly(title="Store Associate", company="In-N-Out Burger", text="Customer service, food prep") == True
    assert is_teen_friendly(title="Broista / Barista", company="Dutch Bros Coffee", text="Making coffee drinks") == True
    assert is_teen_friendly(title="Guest Advocate (Cashier)", company="Target", text="Scan items, cashiering") == True
    assert is_teen_friendly(title="Theater Team Member", company="Cinemark", text="Ticket taking, concessions") == True
    assert is_teen_friendly(title="Retail Sales Associate", company="Best Buy", text="Customer assistance") == True

    # 3. Test negative cases for known employers (supervisors, driving, explicit 18+)
    assert is_teen_friendly(title="Shift Manager", company="McDonald's", text="Supervise crew, cash handling") == False
    assert is_teen_friendly(title="General Manager", company="Taco Bell", text="Store operations") == False
    assert is_teen_friendly(title="Delivery Driver", company="Taco Bell", text="Deliver food with own car") == False
    assert is_teen_friendly(title="Crew Member", company="McDonald's", text="Must be 18+ years old to operate machinery.") == False
    assert is_teen_friendly(title="Team Member", company="Taco Bell", text="Must be at least 18 years of age.") == False
    assert is_teen_friendly(title="Operations Lead", company="Target", text="Lead team in logistics") == False

    # 4. Test explicit under-18 statement for unlisted employers
    assert is_teen_friendly(title="Dishwasher", company="Local Diner", text="Great position for students! Ages 16+ welcome. Work permit accepted.") == True
    assert is_teen_friendly(title="Camp Counselor Aide", company="Community Rec", text="Youth-friendly role for high school students 15 and older.") == True
    assert is_teen_friendly(title="Dishwasher", company="Local Diner", text="Wash dishes, mop floors. Entry-level, no experience required.") == False

    # 5. Test adult / professional / CDL exclusions
    assert is_teen_friendly(title="CDL Driver", company="Blach Beverage", text="Commercial Class A license required.") == False
    assert is_teen_friendly(title="Bartender", company="Downtown Lounge", text="Serve alcoholic beverages. 21+ required.") == False
    assert is_teen_friendly(title="Warehouse Associate", company="Amazon", text="Package handling. Must be 18+ years old.") == False
    assert is_teen_friendly(title="Customer Service Warehouse Associate", company="Ewing Outdoor Supply", text="Forklift and clean DMV.") == False
    assert is_teen_friendly(title="CHHA Home Health Aide", company="Bristol Hospice", text="In-home patient care.") == False
    assert is_teen_friendly(title="Event Marketer", company="LeafHome", text="Brand ambassador events.") == False

    # 6. Test Excel / CSV DataFrame generation with Teen Friendly column
    import pandas as pd
    from scrapper import JobScraper
    test_scraper = JobScraper.__new__(JobScraper)
    test_scraper.jobs_data = [{
        'source': 'Indeed',
        'job_title': 'Crew Member',
        'company': "McDonald's",
        'location': 'Redding, CA',
        'pay': '$17/hr',
        'job_type_extracted': 'Part-time',
        'shift_schedule': 'Day shift',
        'experience': 'No experience required',
        'description': 'Food prep and cashiering.',
        'date_posted': '2026-10-07',
        'job_url': 'https://indeed.com/viewjob?jk=123',
        'industry': 'Food & Restaurant'
    }]
    test_export_path = 'output/test_teen_verification.xlsx'
    test_scraper.save_to_excel(test_export_path)
    df_read = pd.read_excel(test_export_path)
    assert 'Teen Friendly' in df_read.columns, f"Expected 'Teen Friendly' in columns, got: {df_read.columns}"
    assert df_read.iloc[0]['Teen Friendly'] == True, "Expected McDonald's Crew Member to have Teen Friendly == True"
    print(f"Verified Excel output columns: {df_read.columns.tolist()}")

    print("All Teen Friendly unit and export tests passed successfully!\n")

if __name__ == "__main__":
    test_unit_logic()
    test_teen_friendly_logic()

