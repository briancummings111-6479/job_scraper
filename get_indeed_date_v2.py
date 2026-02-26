from scrapper import JobScraper
import time
import json
from selenium.webdriver.common.by import By

def main():
    print("Initializing JobScraper...")
    scraper = JobScraper(headless=False)
    try:
        url = "https://www.indeed.com/viewjob?jk=73066fc0d2344900&from=shareddesktop_copy"
        print(f"Navigating to {url}")
        scraper.driver.get(url)
        
        print("Checking Cloudflare...")
        scraper.check_cloudflare()
        
        print("Page title:", scraper.driver.title)
        
        # 1. Look for meta itemprop="datePosted"
        try:
            meta = scraper.driver.find_elements(By.CSS_SELECTOR, "meta[itemprop='datePosted']")
            for m in meta:
                print(f"FOUND meta datePosted: {m.get_attribute('content')}")
        except Exception as e:
            print(f"Meta datePosted error: {e}")

        # 2. Look for JSON-LD
        try:
            print("Checking JSON-LD...")
            scripts = scraper.driver.find_elements(By.XPATH, "//script[@type='application/ld+json']")
            for i, script in enumerate(scripts):
                try:
                    content = script.get_attribute("innerHTML")
                    data = json.loads(content)
                    # Check if it's the job posting schema
                    if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                        print(f"FOUND JobPosting JSON-LD:")
                        print(f"datePosted: {data.get('datePosted')}")
                        print(f"validThrough: {data.get('validThrough')}")
                    elif 'datePosted' in str(data):
                        print(f"FOUND datePosted in JSON-LD {i} (other type):")
                        print(json.dumps(data, indent=2))
                except:
                    pass
        except Exception as e:
            print(f"Error checking JSON-LD: {e}")

        # 3. Look for visible text
        print("Checking visual elements...")
        try:
            selectors = [
                "span.date",
                "span.myJobsStateDate", 
                "[data-testid='myJobsStateDate']",
                "span.css-qs2091",
                "span.css-10pe3me",
                "div.jobsearch-JobMetadataFooter"
            ]
            for sel in selectors:
                try:
                    elems = scraper.driver.find_elements(By.CSS_SELECTOR, sel)
                    for el in elems:
                        print(f"Found visual element ({sel}): '{el.text}'")
                except:
                    pass
        except:
            pass
            
        # Dump source
        with open("indeed_v2_source.html", "w", encoding="utf-8") as f:
            f.write(scraper.driver.page_source)
        print("Saved source to indeed_v2_source.html")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Closing driver...")
        scraper.driver.quit()

if __name__ == "__main__":
    main()
