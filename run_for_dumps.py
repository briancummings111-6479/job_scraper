
from scrapper import JobScraper
import os

def run_and_dump():
    print("Starting run to capture page dumps...", flush=True)
    scraper = JobScraper(headless=False)
    try:
        scraper.scrape_indeed(
            job_title="warehouse",
            location="Redding, CA 96002",
            radius=25,
            job_types=["fulltime"],
            days_ago=7,
            max_pages=2
        )
        print(f"Total jobs: {len(scraper.jobs_data)}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
    finally:
        scraper.close()

if __name__ == "__main__":
    run_and_dump()
