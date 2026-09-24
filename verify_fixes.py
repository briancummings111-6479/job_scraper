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
    ]

    for title, comp, desc, expected_rej in test_cases:
        rej, reason = is_rejected_job(title, comp, desc)
        status = "REJECTED" if rej else "ACCEPTED"
        print(f"  [{status}] {title} (Expected: {'REJECT' if expected_rej else 'ACCEPT'}) - Reason: {reason}")
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
