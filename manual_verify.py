
from scrapper import JobScraper
import time

def manual_verify():
    print("Starting manual verification...", flush=True)
    print("A Chrome browser window will open.", flush=True)
    print("If you see a Cloudflare 'Security Check' or 'Just a moment...', please solve it manually.", flush=True)
    
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
        
        print(f"\nTotal jobs collected: {len(scraper.jobs_data)}", flush=True)
        if len(scraper.jobs_data) > 0:
            print("SUCCESS: Jobs were scraped!", flush=True)
        else:
            print("FAILURE: No jobs found.", flush=True)
            
    except Exception as e:
        print(f"Error: {e}", flush=True)
    finally:
        print("Closing scraper...", flush=True)
        # Keep open for a moment to see result
        time.sleep(5)
        scraper.close()

if __name__ == "__main__":
    manual_verify()
