
from scrapper import JobScraper
import os

def verify_fix():
    print("Starting verification of scrapper.py fix...", flush=True)
    scraper = JobScraper(headless=False)
    
    try:
        # Standard scrape call - should handle CF internally now
        scraper.scrape_indeed(
            job_title="warehouse",
            location="Redding, CA 96002",
            radius=25,
            job_types=["fulltime"],
            days_ago=7,
            max_pages=1
        )
        
        count = len(scraper.jobs_data)
        print(f"Jobs found: {count}", flush=True)
        
        if count > 0:
            print("SUCCESS: Scraper bypassed Cloudflare and found jobs!", flush=True)
        else:
            print("FAILURE: Scraper found 0 jobs.", flush=True)
            
    except Exception as e:
        print(f"Error during verification: {e}", flush=True)
    finally:
        scraper.close()

if __name__ == "__main__":
    verify_fix()
