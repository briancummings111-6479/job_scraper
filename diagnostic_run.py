
from scrapper import JobScraper
import time

def run_diagnostic():
    print("Starting diagnostic scrape...", flush=True)
    print("Please solve any Cloudflare challenges in the browser window.", flush=True)
    
    scraper = JobScraper(headless=False)
    
    try:
        scraper.scrape_indeed(
            job_title="warehouse",
            location="Redding, CA 96002",
            radius=25,
            job_types=["fulltime"],
            days_ago=7,
            max_pages=1
        )
        print(f"Total extracted: {len(scraper.jobs_data)}", flush=True)
        
    except Exception as e:
        print(f"Error: {e}", flush=True)
    finally:
        print("Closing in 5 seconds...", flush=True)
        time.sleep(5)
        scraper.close()

if __name__ == "__main__":
    run_diagnostic()
