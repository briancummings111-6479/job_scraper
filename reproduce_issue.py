
import os
import sys
import time
import traceback
from scrapper import JobScraper

def run_debug_scrape():
    print("Starting debug scrape (v2)...", flush=True)
    scraper = None
    try:
        scraper = JobScraper(headless=False)
        
        # Open page manually first to handle CF
        url = "https://www.indeed.com/jobs?q=warehouse&l=Redding,+CA+96002"
        scraper.driver.get(url)
        print("Page requested. Checking title...", flush=True)
        
        # Wait for Cloudflare (Disabled, testing scrapper.py logic)
        # for i in range(12): # Wait up to 60s
        #     title = scraper.driver.title
        #     print(f"Current title: {title}", flush=True)
        #     if "Security Check" not in title and "Just a moment" not in title:
        #         print("Passed Cloudflare!", flush=True)
        #         break
        #     time.sleep(5)
        
        # Now run scraper logic (simplified)
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
        
        # Determine filename based on count
        filename = "debug_page_success.html" if count > 0 else "debug_page_fail.html"
        print(f"Dumping HTML to {filename}...", flush=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(scraper.driver.page_source)
        print("HTML dump complete.", flush=True)
            
    except Exception as e:
        print(f"Error: {e}", flush=True)
        traceback.print_exc()
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    run_debug_scrape()
