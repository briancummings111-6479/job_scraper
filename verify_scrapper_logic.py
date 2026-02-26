from scrapper import JobScraper
from datetime import datetime, timedelta
import os

print("--- Verifying Scraper Logic ---")

# Initialize Scraper (headless doesn't matter as we won't scrape)
scraper = JobScraper(headless=True)

# Create Dummy Data
today = datetime.now()
old_date = (today - timedelta(days=10)).strftime("%Y-%m-%d")
recent_date = (today - timedelta(days=2)).strftime("%Y-%m-%d")

scraper.jobs_data = [
    # 1. Valid Job - Manager
    {
        "source": "Test", "job_title": "Store Manager", "company": "Walmart", "location": "Redding, CA",
        "date_posted": recent_date, "job_url": "http://example.com/1"
    },
    # 2. Duplicate of 1 (should be removed)
    {
        "source": "Test", "job_title": "Store Manager", "company": "Walmart", "location": "Redding, CA",
        "date_posted": recent_date, "job_url": "http://example.com/1-dup"
    },
    # 3. Old Job (should be removed)
    {
        "source": "Test", "job_title": "Old Clerk", "company": "Old Co", "location": "Redding, CA",
        "date_posted": old_date, "job_url": "http://example.com/old"
    },
    # 4. Valid Job - Nurse (Health Care)
    {
        "source": "Test", "job_title": "Registered Nurse", "company": "Mercy Hospital", "location": "Redding, CA",
        "date_posted": recent_date, "job_url": "http://example.com/2"
    },
    # 5. Valid Job - Driver (Driver)
    {
        "source": "Test", "job_title": "Truck Driver", "company": "FedEx", "location": "Redding, CA",
        "date_posted": "N/A", "job_url": "http://example.com/3"
    }
]

output_file = "verify_output.xlsx"
if os.path.exists(output_file):
    os.remove(output_file)

# Run save_to_excel which contains the logic
scraper.save_to_excel(output_file)

# Check if file exists
if os.path.exists(output_file):
    print(f"[SUCCESS] Output file created: {output_file}")
    # Verify content using pandas?
    import pandas as pd
    df = pd.read_excel(output_file)
    print("\nDataFrame Content:")
    print(df[['job_title', 'company', 'date_posted', 'industry']])
    
    # Assertions
    assert len(df) == 3, f"Expected 3 jobs, got {len(df)}"
    
    # Check Industry
    row1 = df[df['job_title'] == 'Store Manager'].iloc[0]
    # "Store Manager" hits "Retail" (Store) or "Management" (Manager).
    # In my logic, "Retail" comes before "Management" in iteration?
    # Dictionary order is insertion order in Python 3.7+.
    # My dict definition: Restaurant, Retail, ..., Management.
    # So "Retail" is checked before "Management".
    # "Store Manager" has "Store" -> Retail.
    # Let's see what it extracted.
    
    row2 = df[df['job_title'] == 'Registered Nurse'].iloc[0]
    assert row2['industry'] == 'Health Care', f"Nurse should be Health Care, got {row2['industry']}"
    
    print("\n[SUCCESS] Verification passed!")
    
else:
    print("[ERROR] Output file not created")

scraper.close()
