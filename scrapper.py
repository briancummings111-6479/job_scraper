"""
Job Scraper for Indeed and Glassdoor - 2025 UC Version
Uses undetected-chromedriver to bypass Cloudflare
Educational purposes only - Review ToS before use
"""

import time
import random
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
import re
from datetime import datetime, timedelta
import os

class JobScraper:
    def __init__(self, headless=False):
        """Initialize the scraper with undetected Chrome driver"""
        
        # ChromeDriver path - Let uc handle it or use local drivers folder
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Chrome profile path (local folder)
        chrome_profile_path = os.path.join(self.base_dir, "chrome_profile")
        if not os.path.exists(chrome_profile_path):
            os.makedirs(chrome_profile_path)
        
        print(f"[OK] Using Chrome profile: {chrome_profile_path}")
        
        # UC Options
        options = uc.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-notifications')
        
        if headless:
            options.add_argument('--headless=new')
        
        # Initialize undetected Chrome with profile
        # Fix for version mismatch (Browser 144 vs Driver 145)
        self.driver = uc.Chrome(options=options, user_data_dir=chrome_profile_path, version_main=144)
        self.wait = WebDriverWait(self.driver, 20)
        self.short_wait = WebDriverWait(self.driver, 5)
        
        self.jobs_data = []
        self.seen_jobs = set()
        
        # Random delays to mimic human behavior
        min_seconds = 2
        max_seconds = 5
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def random_delay(self, min_s=2, max_s=5):
        """Add random delay"""
        time.sleep(random.uniform(min_s, max_s))

    def extract_email(self, text):
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return ', '.join(set(emails)) if emails else None
    
    def extract_phone(self, text):
        """Extract phone numbers from text"""
        phone_patterns = [
            r'\+92[\s-]?\d{3}[\s-]?\d{7}',
            r'0\d{3}[\s-]?\d{7}',
            r'\d{4}[\s-]?\d{7}',
            r'\(\d{3}\)\s*\d{3}[-\s]?\d{4}'
        ]
        phones = []
        for pattern in phone_patterns:
            found = re.findall(pattern, text)
            phones.extend(found)
        return ', '.join(set(phones)) if phones else None

    def extract_pay(self, text):
        """Extract pay/salary information"""
        # Look for patterns like $15.00/hr, $50k-$70k, etc.
        pay_patterns = [
            r'\$\d+(?:,\d+)?(?:\.\d+)?\s*(?:-|to)\s*\$\d+(?:,\d+)?(?:\.\d+)?\s*(?:per\s+hour|per\s+year|yr|hr|annually)?',
            r'\$\d+(?:,\d+)?(?:\.\d+)?\s*(?:per\s+hour|per\s+year|yr|hr|annually)',
            r'\d+k\s*(?:-|to)\s*\d+k'
        ]
        for pattern in pay_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def extract_job_type(self, text):
        """Extract job type (Full-time, Part-time, etc.)"""
        types = ["Full-time", "Part-time", "Contract", "Temporary", "Internship"]
        found_types = []
        for t in types:
            if re.search(r'\b' + re.escape(t) + r'\b', text, re.IGNORECASE):
                found_types.append(t)
        return ', '.join(found_types) if found_types else None

    def extract_min_age(self, text):
        """Extract minimum age from text"""
        # Patterns like "16 years or older", "Must be 18", "Minimum age 21"
        age_patterns = [
            r'(\d{2})\s*years\s*(?:or)?\s*older',
            r'must\s*be\s*(\d{2})',
            r'minimum\s*age\s*(\d{2})',
            r'(\d{2})\+',
            r'at\s*least\s*(\d{2})'
        ]
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def extract_date_posted(self, text):
        """Calculate date posted from relative text"""
        if not text: return None
        
        today = datetime.now()
        text = text.lower().strip()
        
        if "today" in text:
            return today.strftime("%Y-%m-%d")
        if "yesterday" in text:
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")
            
        # "30+ days ago", "5 days ago", "1d ago"
        try:
            days_match = re.search(r'(\d+)\+?\s*d', text)
            if days_match:
                days = int(days_match.group(1))
                return (today - timedelta(days=days)).strftime("%Y-%m-%d")
        except: pass
            
        return "N/A"

    def scrape_snagajob(self, job_title="full time", location="96001", max_pages=3):
        """Scrape Snagajob listings with keyword and location"""
        search_url = f"https://www.snagajob.com/search?q={job_title.replace(' ', '+')}&w={location.replace(' ', '+')}"
        print(f"Starting Snagajob scrape: {search_url}")
        
        try:
            self.driver.get(search_url)
            self.check_cloudflare()
            
            for page in range(max_pages):
                print(f"Scraping page {page + 1}")
                self.random_delay()
                
                # Scroll to load dynamic content
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay(2, 4)
                
                # Find all job cards
                try:
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "job-card")))
                    job_cards = self.driver.find_elements(By.TAG_NAME, "job-card")
                except TimeoutException:
                    print("No job cards found on this page.")
                    break
                
                print(f"Found {len(job_cards)} job cards. Processing...")
                
                # Extract links first to avoid stale elements when navigating back/forth
                job_links = []
                for card in job_cards:
                    try:
                        # Extract basic info from card for fallback
                        link_elem = card.find_element(By.TAG_NAME, "a")
                        url = link_elem.get_attribute("href")
                        if url:
                            job_links.append(url)
                    except Exception as e:
                        print(f"Error extracting link from card: {e}")
                        continue
                        
                # Visit each job page
                for url in job_links:
                    if url in self.seen_jobs:
                        continue
                    
                    try:
                        print(f"  Visiting: {url}")
                        self.driver.get(url)
                        self.random_delay(2, 4)
                        self.check_cloudflare() 
                        
                        # Extract Fields
                        job_data = {
                            "source": "Snagajob",
                            "job_title": "N/A",
                            "company": "N/A",
                            "location": "N/A",
                            "pay": "N/A",
                            "job_type_extracted": "N/A",
                            "shift_schedule": "N/A",
                            "experience": "N/A", # Will store Min Age or extracted experience
                            "date_posted": "N/A",
                            "job_url": url,
                            "scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Scope to main content if possible
                        try:
                            main_content = self.driver.find_element(By.ID, "main-content")
                        except:
                            main_content = self.driver

                        # Job Title - Prefer H1 or ID
                        try:
                            # Try id="jobTitle" first (most specific from dump)
                            job_data["job_title"] = main_content.find_element(By.ID, "jobTitle").text.strip()
                        except:
                            try:
                                job_data["job_title"] = main_content.find_element(By.TAG_NAME, "h1").text.strip()
                            except: 
                                try:
                                    job_data["job_title"] = main_content.find_element(By.CSS_SELECTOR, "[data-snagtag='job-title']").text.strip()
                                except: pass

                        # Company
                        try:
                            job_data["company"] = main_content.find_element(By.CSS_SELECTOR, "[data-snagtag='company-name']").text.strip()
                        except: pass
                        
                        # Location
                        try:
                            job_data["location"] = main_content.find_element(By.CSS_SELECTOR, "[data-snagtag='location']").text.strip()
                        except: pass
                        
                        # Pay
                        try:
                            job_data["pay"] = main_content.find_element(By.CSS_SELECTOR, "[data-snagtag='job-est-wage']").text.strip()
                        except:
                            try:
                                job_data["pay"] = main_content.find_element(By.CSS_SELECTOR, "[data-snagtag='job-verified-wage']").text.strip()
                            except: pass
                            
                        # Type/Shift
                        try:
                            job_data["job_type_extracted"] = main_content.find_element(By.CSS_SELECTOR, "[data-snagtag='job-categories']").text.strip()
                        except: pass
                        
                        # Date Posted (Look for bullet separator near company or generic text)
                        try:
                            # Strategy: Find the company element, then look for the next sibling div or text
                            # From structure: Company -> div -> div with bullet
                            # XPath: //a[@data-snagtag='company-name']/../../following-sibling::div[contains(text(), 'ago') or contains(text(), 'Today')]
                            # Simplified: Look for any element containing "days ago" or "Today" inside the header area
                            
                            # Let's try to find text relative to Company Name which we have
                             # The dump shows: <div ...><span ...>•</span>14 days ago </div>
                             # It's a div.text-gray-700.body-lg...
                             
                             # Try XPath relative to company name link
                            company_elem = main_content.find_element(By.CSS_SELECTOR, "[data-snagtag='company-name']")
                            # Parent is div, Parent is div. Next Sibling is the Date div.
                            date_elem = company_elem.find_element(By.XPATH, "./../../following-sibling::div[contains(@class, 'text-gray-700')]")
                            date_text = date_elem.text.replace("•", "").strip()
                            job_data["date_posted"] = self.extract_date_posted(date_text)
                        except: 
                            # Fallback: Search for any element with "days ago"
                            try:
                                # This might be risky if there are similar jobs, but we scoped to main_content
                                potential_date = main_content.find_element(By.XPATH, ".//div[contains(text(), 'days ago') or contains(text(), 'Today') or contains(text(), 'Yesterday')]")
                                job_data["date_posted"] = self.extract_date_posted(potential_date.text.replace("•", "").strip())
                            except: pass

                        # Description (for Min Age/Exp/Email/Phone)
                        try:
                            desc_elem = main_content.find_element(By.CSS_SELECTOR, "[data-snagtag='job-description']")
                            full_desc = desc_elem.text
                            # job_data["description"] = full_desc # Not in target excel but useful? Leaving out to match requested format strictly
                            
                            # Extract Min Age -> Experience
                            age = self.extract_min_age(full_desc)
                            if age:
                                job_data["experience"] = f"{age}+ years old"
                            else:
                                # Try standard experience extraction if age fails or in addition?
                                # Simple regex for now similar to age or just leave as N/A
                                pass
                                
                        except: pass
                        
                        # Add to results
                        self.jobs_data.append(job_data)
                        self.seen_jobs.add(url)
                        print(f"    -> Extracted: {job_data['job_title']} at {job_data['company']}")
                        
                    except Exception as e:
                        print(f"Error processing job page {url}: {e}")
                        
                # Pagination - Check for 'Next' button
                # Selector for next button: button with aria-label="Next page" or similar
                # From dump search page, pagination seems complex or infinite scroll.
                # Let's try to find a next button. If not found, break.
                # Snagajob often uses numbering. Let's assume passed search_url handles it or just do 1 page for now if pagination is hard.
                # The URL includes page params sometimes.
                # For safety, let's just break for now unless we see an obvious next button provided by new request details from user.
                # User URL had no 'page' param explicitly visible (maybe implicit).
                # Implementation Note: We will stick to the provided URL for now. 
                # If pagination is needed, we'd look for pagination controls.
                # Since we extracted links from search, let's assume we proceed.
                
                # If we want to support pagination, we might need to click "Next".
                # But to start simple and safer:
                if max_pages > 1:
                     print("Pagination not fully implemented for Snagajob yet, verifying with one page.")
                     break
                     
        except Exception as e:
            print(f"Snagajob scrape error: {e}")
            import traceback
            traceback.print_exc() 


    def extract_shift(self, text):
        """Extract shift/schedule information"""
        shifts = ["Day shift", "Night shift", "Overnight shift", "Monday to Friday", "Weekend availability", "8 hour shift", "10 hour shift", "12 hour shift"]
        found_shifts = []
        for s in shifts:
            if re.search(r'\b' + re.escape(s) + r'\b', text, re.IGNORECASE):
                found_shifts.append(s)
        return ', '.join(found_shifts) if found_shifts else None

    def is_duplicate(self, job_data):
        """Check if job is a duplicate based on ID or details"""
        # 1. Try to get ID from URL (jk parameter)
        job_url = job_data.get('job_url', '')
        if job_url and 'jk=' in job_url:
            match = re.search(r'jk=([a-zA-Z0-9]+)', job_url)
            if match:
                jk_id = match.group(1)
                if jk_id in self.seen_jobs:
                    return True
                self.seen_jobs.add(jk_id)
                return False
                
        # 2. Fallback to Title + Company + Location
        if not job_data['job_title'] or not job_data['company']:
            return False
            
        # Create a unique identifier
        loc = job_data.get('location', '')
        job_id = f"{job_data['job_title'].lower()}|{job_data['company'].lower()}|{loc.lower()}"
        
        if job_id in self.seen_jobs:
            return True
            
        self.seen_jobs.add(job_id)
        return False
    
    def check_cloudflare(self):
        """Check for Cloudflare security check and try to bypass it"""
        try:
            # Quick check of title first
            if "Security Check" not in self.driver.title and "Just a moment" not in self.driver.title:
                return

            print("    [!] Cloudflare Security Check detected! Attempting to bypass...")
            
            # Switch to default content first
            self.driver.switch_to.default_content()
            
            # 1. Wait for redirect (Just a moment... -> Jobs)
            print("    [!] Waiting up to 30s for automatic Cloudflare redirect...")
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            
            for _ in range(30):
                if "Security Check" not in self.driver.title and "Just a moment" not in self.driver.title:
                    print(f"    [!] Cloudflare challenge passed! Title: {self.driver.title}")
                    self.random_delay(2, 4)
                    return
                
                try:
                    actions.move_by_offset(random.randint(-10, 10), random.randint(-10, 10)).perform()
                except:
                    pass
                
                print(f"    [!] Title: {self.driver.title}...", end='\r')
                time.sleep(1)
            print("")
            
            # Refresh if stuck
            print("    [!] Page stuck on Cloudflare. Refreshing...")
            self.driver.refresh()
            self.random_delay(5, 8)
            
            if "Security Check" not in self.driver.title and "Just a moment" not in self.driver.title:
                 print("    [!] Refreshed and passed!")
                 return
            # Look for ANY iframe
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            print(f"    [!] Found {len(iframes)} total iframes on page")
            
            iframe_found = False
            for i, frame in enumerate(iframes):
                try:
                    # Log src for debugging
                    src = frame.get_attribute("src")
                    # print(f"      Frame {i} src: {src}")
                    
                    if src and ("cloudflare" in src or "turnstile" in src or "challenge" in src):
                        print(f"    [!] Found Cloudflare iframe (Index {i})! Switching...")
                        self.driver.switch_to.frame(frame)
                        
                        # Try to find the input/checkbox
                        checkbox = self.short_wait.until(
                            EC.presence_of_element_located((By.XPATH, "//input[@type='checkbox'] | //div[@class='ctp-checkbox-label'] | //span[@class='mark']"))
                        )
                        
                        if checkbox:
                            print(f"    [!] Found checkbox in iframe {i}. Clicking...")
                            self.random_delay(0.5, 1.5)
                            checkbox.click()
                            print("    [!] Clicked! Waiting for reload...")
                            self.random_delay(5, 10)
                            self.driver.switch_to.default_content()
                            return 
                        
                        self.driver.switch_to.default_content()
                        iframe_found = True
                        
                except Exception as frame_e:
                    # print(f"      Error in frame {i}: {frame_e}")
                    self.driver.switch_to.default_content()
                    continue
            
            if not iframe_found:
                print("    [!] No Cloudflare iframe logic worked. Trying Shadow DOM traversal...")
                # Try JS injection to find Shadow DOM elements
                try:
                    res = self.driver.execute_script("""
                        function findAndClick() {
                            const all = document.querySelectorAll('*');
                            let shadowsFound = 0;
                            let dumped = "";
                            
                            for (const el of all) {
                                if (el.shadowRoot) {
                                    shadowsFound++;
                                    // Try to click any input
                                    const input = el.shadowRoot.querySelector('input');
                                    if (input) {
                                        input.click();
                                        return {status: true, msg: "Clicked input in shadow root"};
                                    }
                                    
                                    // Try to click the wrapper if no input
                                    const wrapper = el.shadowRoot.querySelector('div');
                                    if (wrapper) {
                                        // wrapper.click(); // Risky, might not be the right one
                                        // Just dump the content
                                        dumped = el.shadowRoot.innerHTML;
                                    }
                                }
                            }
                            return {status: false, msg: "Found " + shadowsFound + " shadow roots", dump: dumped};
                        }
                        return findAndClick();
                    """)
                    
                    if isinstance(res, dict):
                        if res.get('status'):
                            print(f"    [!] Success: {res.get('msg')}")
                            self.random_delay(5, 10)
                            return
                        else:
                            print(f"    [!] Failed: {res.get('msg')}")
                            if res.get('dump'):
                                with open("debug_shadow.html", "w", encoding="utf-8") as f:
                                    f.write(res.get('dump'))
                                print("    [!] Dumped shadow root content to debug_shadow.html")
                            
                except Exception as js_e:
                    print(f"    [!] JS Shadow DOM error: {js_e}")

            # If no iframe logic worked, just wait a bit and hope
            print("    [!] No actionable element found. Waiting for implicit bypass...")
            
            # Manual Fallback: Explicitly ask user to solve it
            print("    [!] AUTOMATED BYPASS FAILED/INCOMPLETE.")
            print("    [!] ACTION REQUIRED: Please solve the Cloudflare check manually in the browser window.")
            print("    [!] The scraper will wait until the page title changes from 'Just a moment...'")
            
            # Wait up to 5 minutes for manual solve
            start_wait = time.time()
            while time.time() - start_wait < 300:
                if "Security Check" not in self.driver.title and "Just a moment" not in self.driver.title:
                    print(f"    [!] Cloudflare challenge passed! Resume scraping... (Title: {self.driver.title})")
                    self.random_delay(2, 4)
                    return
                time.sleep(1)
            
            print("    [!] Timed out waiting 5 minutes for manual solution.")            
            
        except Exception as e:
            # Don't let check_cloudflare crash the whole scraper
            print(f"    [WARN] Error in Cloudflare check: {e}")
            self.driver.switch_to.default_content()

    def close_popups(self):
        """Close common popups and modals"""
        popup_selectors = [
            "button[aria-label='Close']",
            "button.modal_closeIcon",
            ".react-modal-close",
            "button[data-test='close-modal']",
            "svg[data-test='close-button']",
            ".modal-close-button",
            "button.CloseButton",
            "button[aria-label='close']",
            ".icl-CloseButton"
        ]
        
        for selector in popup_selectors:
            try:
                close_btn = self.short_wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                close_btn.click()
                self.random_delay(0.5, 1)
                print("    [OK] Closed popup")
            except:
                continue
    
    def scrape_indeed(self, job_title="Flutter Developer", location="Lahore", radius=25, job_types=["fulltime"], days_ago=7, max_pages=3):
        """Scrape jobs from Indeed - UC Version"""
        print(f"\n{'='*60}")
        print(f"Starting Indeed scraping for: {job_title} in {location}")
        print(f"Filters: Radius={radius}m, Types={job_types}, Days={days_ago}")
        print(f"{'='*60}\n")
        
        try:
            base_url = "https://www.indeed.com/jobs"
            
            for jt in job_types:
                print(f"\n--- Searching for Job Type: {jt} ---")
                
                query_params = [
                    f"q={job_title.replace(' ', '+')}",
                    f"l={location.replace(' ', '+')}",
                    f"radius={radius}",
                    f"fromage={days_ago}",
                    f"jt={jt}"
                ]
                
                search_url = f"{base_url}?{'&'.join(query_params)}"
                
                self.driver.get(search_url)
                print("[OK] Indeed page loaded - bypassing Cloudflare...")
                self.random_delay(5, 8)
                self.check_cloudflare() # Check immediately after load
                
                self.close_popups()
                
                # Double check
                self.check_cloudflare()
                
                page_count = 0
                
                while page_count < max_pages:
                    print(f"\nScraping Indeed page {page_count + 1} (Type: {jt})...")
                    self.check_cloudflare() # Check before scraping page
                    
                    try:
                        # 1. Wait for the main results container
                        try:
                            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#mosaic-provider-jobcards ul, .jobsearch-ResultsList")))
                            print("  [OK] Main results container loaded")
                        except:
                            print("  [WARN] Main results container not found, falling back to card detection")

                        # 2. Find all potential job card containers (li elements)
                        # Indeed usually puts cards in <li> inside the results list
                        potential_cards = self.driver.find_elements(By.CSS_SELECTOR, "#mosaic-provider-jobcards ul > li, .jobsearch-ResultsList > li")
                        
                        job_cards = []
                        if potential_cards:
                            print(f"  Found {len(potential_cards)} list items. Filtering for validity...")
                            for card in potential_cards:
                                # Check if it's a real job card (has title or company)
                                # Exclude ads/mosaics that aren't jobs
                                try:
                                    if card.find_elements(By.CSS_SELECTOR, "h2.jobsearch-JobInfoHeader-title, h2 a, span[id^='jobTitle']"):
                                        job_cards.append(card)
                                except:
                                    pass
                        
                        if not job_cards:
                            print("  [INFO] No cards found via list items. Trying strict selectors...")
                            job_cards_selectors = [
                                "div.job_seen_beacon",
                                "div.cardOutline",
                                "article.job_card",
                                "div[data-testid='job-card']",
                                "li.job_card",
                                "div.slider_item"
                            ]
                            
                            for selector in job_cards_selectors:
                                try:
                                    found = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                    if found:
                                        print(f"  [OK] Using selector: {selector} (Found {len(found)})")
                                        job_cards = found
                                        break
                                except:
                                    continue
                        
                        if not job_cards:
                            print("  [X] Could not find job cards with any method")
                            # Debug dump
                            with open("debug_failed_scrape.html", "w", encoding="utf-8") as f:
                                f.write(self.driver.page_source)
                            print("    [!] Dumped HTML to debug_failed_scrape.html")
                            break
                        
                        print(f"  Found {len(job_cards)} job listings on this page")
                        
                        # DEBUG: Dump the page to see what we might be missing
                        try:
                            debug_filename = f"debug_scraped_page_{page_count+1}.html"
                            with open(debug_filename, "w", encoding="utf-8") as f:
                                f.write(self.driver.page_source)
                            print(f"    [!] Dumped page HTML to {debug_filename} for analysis")
                        except:
                            pass
                        
                        for idx, card in enumerate(job_cards, 1):
                            try:
                                print(f"  Processing job {idx}/{len(job_cards)}...")
                                
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                                self.random_delay(0.5, 1)
                                
                                card.click()
                                self.random_delay(2, 3)
                                
                                job_data = {
                                    'source': 'Indeed',
                                    'job_title': None,
                                    'company': None,
                                    'location': location,
                                    'pay': None,
                                    'job_type_extracted': None,
                                    'shift_schedule': None,
                                    'experience': None,
                                    'date_posted': None,
                                    'job_url': self.driver.current_url, # Default
                                    'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }

                                try:
                                    # Target specifically the "Link" button seen in the screenshot (usually chain icon)
                                    # This button typically copies the link or is an anchor.
                                    # If it's a Copy Link button, we might need to get the "canonical" link instead.
                                    # However, let's try to find the button and see if it wraps an href first.
                                    link_btn = self.driver.find_element(By.CSS_SELECTOR, "div.jobsearch-JobInfoHeader-actions button[aria-label='Copy link'], button.jobsearch-JobInfoHeader-share-button")
                                    # If found, we can try to get the canonical URL because "Copy link" implies the canonical one.
                                    # Or we can check if it's an anchor.
                                    
                                    # A safer bet that matches "Link from the icon" without risking the copy-paste action
                                    # is to get the canonical link from the page head, which is what that button usually shares.
                                    canonical = self.driver.find_element(By.CSS_SELECTOR, "link[rel='canonical']")
                                    if canonical:
                                        href = canonical.get_attribute("href")
                                        if href:
                                            job_data['job_url'] = href
                                except:
                                    # If any of this fails, we just keep the default current_url
                                    pass
                                
                                # Extract job title
                                title_selectors = [
                                    "h2.jobsearch-JobInfoHeader-title",
                                    "h1.jobsearch-JobInfoHeader-title",
                                    "h2[data-testid='jobsearch-JobInfoHeader-title']",
                                    "span.jobsearch-JobInfoHeader-title-container",
                                    "h1.icl-u-xs-mb--xs"
                                ]
                                for selector in title_selectors:
                                    try:
                                        title_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                                        job_data['job_title'] = title_elem.text.strip()
                                        break
                                    except:
                                        continue
                                
                                # Extract company name
                                company_selectors = [
                                    "[data-testid='inlineHeader-companyName']",
                                    "[data-company-name='true']",
                                    "div[data-testid='company-name']",
                                    "a[data-testid='company-name']",
                                    "span.companyName",
                                    "div.icl-u-lg-mr--sm"
                                ]
                                for selector in company_selectors:
                                    try:
                                        company_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                                        job_data['company'] = company_elem.text.strip()
                                        break
                                    except:
                                        continue
                                
                                # Extract specific location
                                location_selectors = [
                                    "[data-testid='text-location']",
                                    ".companyLocation",
                                    "div[data-testid='text-location']",
                                    "div.companyLocation",
                                    "span.companyLocation",
                                    "div[data-testid='inlineHeader-companyLocation']"
                                ]
                                for selector in location_selectors:
                                    try:
                                        loc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                                        specific_location = loc_elem.text.strip()
                                        if specific_location:
                                            job_data['location'] = specific_location
                                            break
                                    except:
                                        continue

                                # Extract Date Posted
                                date_selectors = [
                                    "span.date",
                                    "span.myJobsStateDate",
                                    "[data-testid='myJobsStateDate']",
                                    "span.css-qs2091",
                                    "span.css-10pe3me",
                                    "span.css-10pe3me.eu4oa1w0"
                                ]
                                for selector in date_selectors:
                                    try:
                                        date_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                                        raw_date = date_elem.text.replace('Posted', '').strip()
                                        job_data['date_posted'] = self.extract_date_posted(raw_date)
                                        break
                                    except:
                                        continue

                                # Extract full job description
                                desc_selectors = [
                                    "#jobDescriptionText",
                                    "div.jobsearch-jobDescriptionText",
                                    "[data-testid='job-description']",
                                    "div.jobsearch-JobComponent-description"
                                ]
                                description = ""
                                for selector in desc_selectors:
                                    try:
                                        desc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                                        description = desc_elem.text
                                        break
                                    except:
                                        continue
                                
                                # Extract metadata (Pay, Job Type, Shift) from header/metadata section
                                try:
                                    metadata_elem = self.driver.find_element(By.CSS_SELECTOR, "div#salaryInfoAndJobType")
                                    metadata_text = metadata_elem.text
                                    job_data['pay'] = self.extract_pay(metadata_text)
                                    job_data['job_type_extracted'] = self.extract_job_type(metadata_text)
                                    job_data['shift_schedule'] = self.extract_shift(metadata_text)
                                except:
                                    pass

                                if description:
                                    
                                    # Fallback extraction from description
                                    if not job_data['pay']:
                                        job_data['pay'] = self.extract_pay(description)
                                    if not job_data['job_type_extracted']:
                                        job_data['job_type_extracted'] = self.extract_job_type(description)
                                    if not job_data['shift_schedule']:
                                        job_data['shift_schedule'] = self.extract_shift(description)

                                    # Extract experience
                                    exp_patterns = [
                                        r'(\d+[\+]?\s*(?:-\s*\d+)?\s*years?)',
                                        r'(\d+[\+]?\s*(?:to\s+\d+)?\s*years?)',
                                        r'experience:\s*(\d+[\+]?\s*(?:-\s*\d+)?\s*years?)'
                                    ]
                                    for pattern in exp_patterns:
                                        exp_match = re.search(pattern, description, re.IGNORECASE)
                                        if exp_match:
                                            job_data['experience'] = exp_match.group(1).strip()
                                            break
                                
                                # Check for duplicates
                                if self.is_duplicate(job_data):
                                    print(f"    [WARN] Duplicate job skipped: {job_data['job_title']} at {job_data['company']}")
                                    continue

                                self.jobs_data.append(job_data)
                                print(f"    [OK] Extracted: {job_data['job_title']} at {job_data['company']}")
                                if job_data['pay']: print(f"      (Pay) Pay: {job_data['pay']}")
                                if job_data['job_type_extracted']: print(f"      (Type) Type: {job_data['job_type_extracted']}")
                                
                            except Exception as e:
                                print(f"    [X] Error processing job: {str(e)}")
                                continue
                        
                        try:
                            next_selectors = [
                                "[data-testid='pagination-page-next']",
                                "a[aria-label='Next Page']",
                                "a[data-testid='pagination-page-next']",
                                "a.np"
                            ]
                            for selector in next_selectors:
                                try:
                                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                    self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
                                    self.random_delay(1, 2)
                                    next_button.click()
                                    self.random_delay(5, 10) # Increased delay between pages
                                    self.check_cloudflare() # Check after navigation
                                    page_count += 1
                                    break
                                except:
                                    continue
                            else:
                                print("  No more pages available")
                                # Dump to see why
                                with open(f"debug_pagination_end_page_{page_count}.html", "w", encoding="utf-8") as f:
                                    f.write(self.driver.page_source)
                                break
                        except Exception as e:
                            print(f"  Pagination error: {str(e)}")
                            break
                            
                    except TimeoutException:
                        print("  Timeout waiting for job listings")
                        break
                    
        except Exception as e:
            print(f"[ERROR] Error during Indeed scraping: {str(e)}")
    

    
    def save_to_excel(self, filename="job_listings.xlsx"):
        """Save collected data to Excel file"""
        if not self.jobs_data:
            print("\n[WARN] No data to save!")
            return
        
        df = pd.DataFrame(self.jobs_data)
        
        # Reorder columns
        column_order = [
            'source', 'job_title', 'company', 'location', 
            'pay', 'job_type_extracted', 'shift_schedule',
            'experience', 'date_posted', 
            'job_url', 'scraped_date'
        ]
        # Ensure all columns exist
        for col in column_order:
            if col not in df.columns:
                df[col] = None
            
        df = df[column_order]
        
        # Save to Excel
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\n{'='*60}")
        print(f"  [OK] Data saved to {filename}")
        print(f"  Total jobs scraped: {len(self.jobs_data)}")
        print(f"  Indeed jobs: {len([j for j in self.jobs_data if j['source'] == 'Indeed'])}")
        print(f"  Snagajob jobs: {len([j for j in self.jobs_data if j['source'] == 'Snagajob'])}")
        print(f"{'='*60}\n")

    def close(self):
        """Close the browser"""
        self.driver.quit()

def run_scraping_job(keywords=None, location=None, radius=None, job_types=None, days_ago=None, max_pages=None):
    """Run the scraping job and return the path to the generated Excel file"""
    
    # Defaults
    if keywords is None: keywords = ["warehouse", "store", "restaurant", "fast food", "retail", "laborer", "clerk", "security guard", "crew", "cashier", "delivery"]
    if location is None: location = "Redding, CA 96002"
    if radius is None: radius = 15
    if job_types is None: job_types = ["parttime", "fulltime"]
    if days_ago is None: days_ago = 3
    if max_pages is None: max_pages = 5
    
    scraper = None
    output_file = None
    
    print("\n" + "="*60)
    print("JOB SCRAPER - APP MODE")
    print("="*60 + "\n")
    
    try:
        scraper = JobScraper(headless=False) # Keep visible for now as per original script
        
        # Initial delay
        print("Waiting 5 seconds for initial checks...")
        scraper.random_delay(5, 8)
        
        for keyword in keywords:
            print(f"Processing Keyword: {keyword}")
            scraper.scrape_indeed(
                job_title=keyword, 
                location=location, 
                radius=radius,
                job_types=job_types,
                days_ago=days_ago,
                max_pages=max_pages
            )
            scraper.random_delay(3, 5)
            
            scraper.scrape_snagajob(
                job_title=keyword,
                location=location,
                max_pages=min(2, max_pages) # Lower max pages for Snagajob safety
            )
            scraper.random_delay(3, 5)
            
        # Save results
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_folder = os.path.join(base_dir, "output")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")    
        output_file = os.path.join(output_folder, f"redding_jobs_{timestamp}.xlsx")
        
        scraper.save_to_excel(output_file)
        return output_file
        
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    run_scraping_job()