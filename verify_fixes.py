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
        ("Regional delivery driver", "Local Bakery", "Over-the-road travel required 100% of time", True, "$20/hr"),
        ("Local Route Driver", "Local Supply Co", "Local Redding deliveries only. Home daily.", False, "$20/hr"),
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
    print("Unit filtering tests passed successfully!\n")

if __name__ == "__main__":
    test_unit_logic()
