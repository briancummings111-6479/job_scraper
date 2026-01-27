
from scrapper import JobScraper
import time

def dump_html():
    print("Starting fast dump...", flush=True)
    scraper = JobScraper(headless=False)
    try:
        url = "https://www.indeed.com/jobs?q=warehouse&l=Redding,+CA+96002"
        scraper.driver.get(url)
        print("Page requested. Waiting 10s...", flush=True)
        time.sleep(10)
        
        with open("debug_fast_dump.html", "w", encoding="utf-8") as f:
            f.write(scraper.driver.page_source)
        print("HTML dumped to debug_fast_dump.html", flush=True)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    dump_html()
