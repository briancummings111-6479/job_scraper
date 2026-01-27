
from scrapper import JobScraper
import time
import os

def manual_dump():
    print("Starting manual dump...", flush=True)
    scraper = JobScraper(headless=False)
    try:
        url = "https://www.indeed.com/jobs?q=warehouse&l=Redding,+CA+96002"
        scraper.driver.get(url)
        
        print("\n" + "="*50)
        print("PLEASE SOLVE CLOUDFLARE CHECK IN THE BROWSER NOW.")
        print("Once the job listing page is visible, press ENTER here.")
        print("="*50 + "\n")
        
        try:
            input()
        except EOFError:
            print("Running in non-interactive mode. Waiting 45s...")
            time.sleep(45)
            
        print("Dumping HTML...", flush=True)
        timestamp = int(time.time())
        filename = f"debug_manual_{timestamp}.html"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(scraper.driver.page_source)
            
        print(f"HTML dumped to {filename}", flush=True)
        
        # Quick analysis
        from selenium.webdriver.common.by import By
        cards = scraper.driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")
        print(f"Quick check - Found {len(cards)} 'div.job_seen_beacon' elements.")
        
        cards_li = scraper.driver.find_elements(By.CSS_SELECTOR, "td.resultContent")
        print(f"Quick check - Found {len(cards_li)} 'td.resultContent' elements.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    manual_dump()
