import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import json

def main():
    try:
        options = uc.ChromeOptions()
        # options.add_argument('--headless=new') # Headless might trigger detection more easily, trying regular first or headless if needed. 
        # The user's scrapper uses headless=False by default. Let's try headless=True for my tool use, but if it fails I might need to ask user.
        # Actually, let's try headless=True first as I cannot see the UI.
        options.add_argument('--headless=new')
        options.add_argument('--start-maximized')
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        chrome_profile_path = os.path.join(base_dir, "chrome_profile")
        
        print(f"Starting ChromeDriver with profile: {chrome_profile_path}")
        driver = uc.Chrome(options=options, user_data_dir=chrome_profile_path, version_main=144)
        
        url = "https://www.indeed.com/viewjob?jk=73066fc0d2344900&from=shareddesktop_copy"
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for some content
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            print("Page loaded.")
        except:
            print("Timeout waiting for h1.")
            
        # Cloudflare check (simplified from user's script)
        title = driver.title
        print(f"Page Title: {title}")
        
        # Capture source
        with open("indeed_full_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Saved source to indeed_full_source.html")
        
        # Try to find JSON-LD
        try:
            scripts = driver.find_elements(By.XPATH, "//script[@type='application/ld+json']")
            for i, script in enumerate(scripts):
                try:
                    data = json.loads(script.get_attribute("innerHTML"))
                    print(f"\nJSON-LD {i}:")
                    print(json.dumps(data, indent=2))
                except:
                    pass
        except Exception as e:
            print(f"Error extracting JSON-LD: {e}")
            
        driver.quit()
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
