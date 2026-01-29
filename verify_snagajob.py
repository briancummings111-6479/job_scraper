from scrapper import JobScraper
import pandas as pd
import os

def verify_snagajob():
    print("Initializing scraper...")
    scraper = JobScraper(headless=False)
    
    url = "https://www.snagajob.com/search?w=96001&combined=&categories=full+time&categories=part+time&categories=seasonal+full+time&categories=seasonal+part+time&lmax=2&industries=administration+office+support&industries=agriculture+environment&industries=construction&industries=customer+service&industries=food+restaurant&industries=healthcare&industries=installation+repair&industries=law+enforcement+security&industries=maintenance+janitorial&industries=personal+care+services&industries=retail&industries=transportation&industries=warehouse+production&promotedonly=false"
    
    print(f"Testing URL: {url}")
    scraper.scrape_snagajob(url, max_pages=1)
    
    print("\n--- Scraping Results ---")
    print(f"Total Jobs Found: {len(scraper.jobs_data)}")
    
    if scraper.jobs_data:
        df = pd.DataFrame(scraper.jobs_data)
        print(df.head())
        
        # Save to Excel
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_file = os.path.join(output_dir, f"snagajob_jobs_{timestamp}.xlsx")
        df.to_excel(output_file, index=False)
        print(f"\n[SUCCESS] Results saved to {output_file}")
        
        # Check for important fields
        sample = scraper.jobs_data[0]
        print("\nSample Data:")
        for k, v in sample.items():
            if k == "Description":
                print(f"{k}: {v[:100]}...")
            else:
                print(f"{k}: {v}")
                
        # Verify min age and date posted extraction
        print("\nChecking Extractions:")
        with_age = [j for j in scraper.jobs_data if j['experience'] != 'N/A']
        print(f"Jobs with Experience/Age extracted: {len(with_age)}")
        
        with_date = [j for j in scraper.jobs_data if j['date_posted'] != 'N/A']
        print(f"Jobs with Date Posted extracted: {len(with_date)}")
        if with_date:
            print(f"Sample Date Posted: {with_date[0]['date_posted']} (from '{with_date[0].get('job_url', '')}')")
            
    else:
        print("No data extracted.")
        
    scraper.driver.quit()

if __name__ == "__main__":
    verify_snagajob()
