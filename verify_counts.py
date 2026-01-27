
from scrapper import JobScraper
import time

def verify_counts():
    print("Starting verification...", flush=True)
    scraper = JobScraper(headless=False)
    
    try:
        # Run standard scrape
        scraper.scrape_indeed(
            job_title="warehouse",
            location="Redding, CA 96002",
            radius=25,
            job_types=["fulltime"],
            days_ago=7,
            max_pages=2
        )
        
        count = len(scraper.jobs_data)
        print(f"Total jobs collected: {count}", flush=True)
        
    except Exception as e:
        print(f"Error: {e}", flush=True)
    finally:
        scraper.close()

if __name__ == "__main__":
    verify_counts()
