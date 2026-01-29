from scrapper import JobScraper
import time

def dump_snagajob_job():
    scraper = JobScraper(headless=False)
    # Using a real link found in the previous dump
    url = "https://www.snagajob.com/jobs/1214962506" 
    
    print(f"Navigating to {url}")
    scraper.driver.get(url)
    
    print("Waiting for page load...")
    time.sleep(10)
    
    scraper.check_cloudflare()
    
    print("Dumping HTML...")
    with open("debug_snagajob_job.html", "w", encoding="utf-8") as f:
        f.write(scraper.driver.page_source)
        
    print("Done! HTML saved to debug_snagajob_job.html")
    scraper.driver.quit()

if __name__ == "__main__":
    dump_snagajob_job()
