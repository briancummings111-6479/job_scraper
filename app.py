from flask import Flask, render_template, jsonify, request
import os
import sys
import setuptools # Required for Python 3.12+ (distutils support)
from generate_report import run_report_generation
from scrapper import run_scraping_job, run_pdf_scrape, run_redding_scrape, run_burney_scrape

# Ensure we can find the generate_report module if it's in the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search-config', methods=['GET'])
def get_search_config():
    try:
        from scrapper import load_search_config
        config = load_search_config()
        return jsonify({"status": "success", "config": config})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/search-config', methods=['POST'])
def save_search_config():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided."})
        
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "search_config.json")
        import json
        
        def clean_list(val):
            if isinstance(val, str):
                delimiter = ';' if ';' in val else ','
                return [x.strip() for x in val.split(delimiter) if x.strip()]
            elif isinstance(val, list):
                return [str(x).strip() for x in val if str(x).strip()]
            return []

        from scrapper import load_search_config
        current_config = load_search_config()
        
        if 'keywords' in data:
            current_config['keywords'] = clean_list(data['keywords'])
        if 'standard_keywords' in data:
            current_config['standard_keywords'] = clean_list(data['standard_keywords'])
        if 'all_keywords' in data:
            current_config['all_keywords'] = clean_list(data['all_keywords'])
        if 'location' in data:
            current_config['location'] = clean_list(data['location'])
        if 'radius' in data:
            current_config['radius'] = int(data['radius'])
        if 'job_types' in data:
            current_config['job_types'] = clean_list(data['job_types'])
        if 'days_ago' in data:
            current_config['days_ago'] = int(data['days_ago'])
        if 'max_pages' in data:
            current_config['max_pages'] = int(data['max_pages'])
        if 'rejected_titles' in data:
            current_config['rejected_titles'] = clean_list(data['rejected_titles'])
        if 'rejected_employers' in data:
            current_config['rejected_employers'] = clean_list(data['rejected_employers'])
        if 'industry_keywords' in data and isinstance(data['industry_keywords'], dict):
            current_config['industry_keywords'] = data['industry_keywords']
        if 'keyword_groups' in data and isinstance(data['keyword_groups'], dict):
            current_config['keyword_groups'] = data['keyword_groups']

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(current_config, f, indent=2)
            
        return jsonify({"status": "success", "message": "Search configuration saved successfully!", "config": current_config})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/generate', methods=['POST'])
def generate():
    print("Received generation request...")
    try:
        # Step 1: Run Scraper
        print("Starting scraper...")
        excel_file = run_scraping_job(days_ago=3)
        if not excel_file:
             return jsonify({"status": "error", "message": "Scraping failed or produced no data."})
        
        print(f"Scraping complete: {excel_file}")
        
        # Step 2: Generate Report (it picks up the latest file, which is this one)
        output_pdf = run_report_generation()
        print(f"Generation result: {output_pdf}")
        if output_pdf:
            return jsonify({
                "status": "success", 
                "message": f"Report generated successfully!",
                "file_path": output_pdf,
                "file_name": os.path.basename(output_pdf)
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "No Excel files found to process in the output directory."
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/generate-redding', methods=['POST'])
def generate_redding():
    print("Received Redding-only scraping request...")
    try:
        excel_file = run_redding_scrape()
        if excel_file:
            output_pdf = run_report_generation()
            return jsonify({"status": "success", "message": "Redding report generated!", "file_name": os.path.basename(output_pdf)})
        return jsonify({"status": "error", "message": "Scraping failed."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/generate-burney', methods=['POST'])
def generate_burney():
    print("Received Burney-only scraping request...")
    try:
        excel_file = run_burney_scrape()
        if excel_file:
            output_pdf = run_report_generation()
            return jsonify({"status": "success", "message": "Burney report generated!", "file_name": os.path.basename(output_pdf)})
        return jsonify({"status": "error", "message": "Scraping failed."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/generate-pdf-scrape', methods=['POST'])
def generate_pdf_scrape():
    print("Received PDF-only scraping request...")
    try:
        pdf_path = None
        if 'pdf_file' in request.files:
            file = request.files['pdf_file']
            if file and file.filename:
                upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                from werkzeug.utils import secure_filename
                filename = secure_filename(file.filename)
                pdf_path = os.path.join(upload_dir, filename)
                file.save(pdf_path)
                print(f"Saved uploaded PDF to: {pdf_path}")
        
        if not pdf_path:
            return jsonify({"status": "error", "message": "No PDF file uploaded. Please select the Shasta County Area Job Listings PDF document."})

        excel_file = run_pdf_scrape(pdf_path=pdf_path)
        if excel_file:
            output_pdf = run_report_generation()
            return jsonify({
                "status": "success", 
                "message": "CSV report generated successfully!", 
                "file_name": os.path.basename(output_pdf),
                "download_url": f"/download/{os.path.basename(output_pdf)}"
            })
        return jsonify({"status": "error", "message": "Scraping failed."})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)})

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf_only():
    print("Received PDF-only generation request...")
    try:
        output_pdf = run_report_generation()
        print(f"Generation result: {output_pdf}")
        
        if output_pdf:
            return jsonify({
                "status": "success", 
                "message": f"Report generated successfully!",
                "file_path": output_pdf,
                "file_name": os.path.basename(output_pdf),
                "download_url": f"/download/{os.path.basename(output_pdf)}"
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "No Excel files found to process. Please run the full scraper first."
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

from flask import send_from_directory

@app.route('/download/<path:filename>')
def download_file(filename):
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    return send_from_directory(output_dir, filename, as_attachment=True)

@app.route('/api/send-email', methods=['POST'])
def send_email_report():
    """Optional simple emailing of scraped reports via standard SMTP"""
    try:
        data = request.get_json() or {}
        recipient = data.get('recipient_email', '').strip()
        filename = data.get('file_name', '').strip()
        
        if not recipient or '@' not in recipient:
            return jsonify({"status": "error", "message": "Please enter a valid recipient email address."})
        if not filename:
            return jsonify({"status": "error", "message": "No file specified to email."})
            
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        file_path = os.path.join(output_dir, filename)
        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": f"File '{filename}' not found on server."})
            
        smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", 587))
        smtp_user = os.environ.get("SMTP_USER", "")
        smtp_pass = os.environ.get("SMTP_PASSWORD", "")
        
        if not smtp_user or not smtp_pass:
            return jsonify({
                "status": "info",
                "message": "To enable direct emailing, configure SMTP_USER and SMTP_PASSWORD in your environment variables (e.g. using a free Gmail App Password)."
            })
            
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.text import MIMEText
        from email import encoders
        from datetime import datetime
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient
        msg['Subject'] = f"Career Miner Scraped Report - {datetime.now().strftime('%b %d, %Y')}"
        
        body = f"Hello,\n\nAttached is your latest scraped job report from Career Miner: {filename}.\n\nBest regards,\nCareer Miner Automated Hub"
        msg.attach(MIMEText(body, 'plain'))
        
        with open(file_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)
            
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        
        return jsonify({"status": "success", "message": f"Report successfully emailed to {recipient}!"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Email sending failed: {str(e)}"})

import json

@app.route('/refine')
def refine():
    return render_template('refine_pdf.html')

def analyze_parsed_jobs(jobs):
    warnings = []
    seen_hashes = set()
    seen_urls = {}
    
    for idx, job in enumerate(jobs):
        title = job.get("job_title", "")
        company = job.get("company", "")
        location = job.get("location", "")
        pay = job.get("pay", "")
        url = job.get("job_url", "")
        page = job.get("page", "?")
        
        # 1. Duplicate check
        hash_key = (title.lower().strip(), company.lower().strip(), location.lower().strip())
        if hash_key in seen_hashes:
            warnings.append({
                "level": "warn",
                "message": f"Page {page}: Duplicate listing detected for '{title}' at '{company}'."
            })
        seen_hashes.add(hash_key)
        
        # 2. Pay rate in title warning
        if any(char in title for char in ["$", "hour", "hr", "/hr", "salary"]):
            warnings.append({
                "level": "warn",
                "message": f"Page {page}: Pay rate details or '$' symbol detected in job title: '{title}'."
            })
            
        # 3. Short title warning
        if len(title.strip()) < 5:
            warnings.append({
                "level": "warn",
                "message": f"Page {page}: Job title '{title}' is extremely short. This might be a layout parsing error."
            })
            
        # 4. Long title warning
        if len(title.strip()) > 75:
            warnings.append({
                "level": "warn",
                "message": f"Page {page}: Job title '{title}' is very long ({len(title)} chars). This might be a run-together sentence."
            })
            
        # 5. Default/Placeholder URL warning
        if url and any(base in url.lower() for base in ["indeed.com", "caljobs.ca.gov", "edjoin.org", "calcareers.ca.gov", "governmentjobs.com"]):
            url_clean = url.lower().strip().rstrip('/')
            if url_clean in [
                "https://www.indeed.com", "https://www.caljobs.ca.gov", "https://www.edjoin.org", 
                "https://calcareers.ca.gov", "https://www.governmentjobs.com", "https://northstatejobs.com"
            ]:
                warnings.append({
                    "level": "warn",
                    "message": f"Page {page}: Job '{title}' is mapped to a generic portal URL: '{url}'."
                })
                
        # 6. Duplicate URL warning (excluding common search portals)
        if url and not any(base in url.lower() for base in ["indeed.com", "caljobs.ca.gov", "edjoin.org", "calcareers.ca.gov", "governmentjobs.com"]):
            if url in seen_urls:
                seen_urls[url].append((title, page))
            else:
                seen_urls[url] = [(title, page)]
                
    for url, items in seen_urls.items():
        if len(items) > 1:
            details = ", ".join([f"'{t}' (Pg {p})" for t, p in items])
            warnings.append({
                "level": "info" if "shastacounty.gov" in url else "warn",
                "message": f"Multiple jobs are mapped to the same company URL '{url}': {details}"
            })
            
    return warnings

def get_config_payload():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Loading config: {e}")
    return {
        "invalid_titles": [],
        "company_mappings": [],
        "overrides": [],
        "layout_overrides": {}
    }

@app.route('/refine-pdf/upload', methods=['POST'])
def refine_pdf_upload():
    print("Received refinement upload request...")
    try:
        if 'pdf_file' not in request.files:
            return jsonify({"status": "error", "message": "No PDF file uploaded."})
            
        file = request.files['pdf_file']
        if not file or not file.filename:
            return jsonify({"status": "error", "message": "Invalid file selected."})
            
        upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(upload_dir, filename)
        file.save(pdf_path)
        print(f"Saved uploaded PDF to: {pdf_path}")
        
        from scrapper import JobScraper
        scraper = JobScraper(headless=True)
        jobs = scraper.scrape_local_pdf(pdf_path=pdf_path, dry_run=True)
        
        warnings = analyze_parsed_jobs(jobs)
        config = get_config_payload()
        
        return jsonify({
            "status": "success",
            "jobs": jobs,
            "warnings": warnings,
            "config": config
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)})

@app.route('/refine-pdf/preview', methods=['POST'])
def refine_pdf_preview():
    print("Received preview scrape request...")
    try:
        if 'pdf_file' not in request.files:
            return jsonify({"status": "error", "message": "No PDF file uploaded."})
            
        file = request.files['pdf_file']
        config_str = request.form.get('config_data')
        
        if not config_str:
            return jsonify({"status": "error", "message": "No configurations provided."})
            
        config_data = json.loads(config_str)
        
        upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(upload_dir, filename)
        file.save(pdf_path)
        
        from scrapper import JobScraper
        scraper = JobScraper(headless=True)
        jobs = scraper.scrape_local_pdf(pdf_path=pdf_path, dry_run=True, config_dict=config_data)
        
        warnings = analyze_parsed_jobs(jobs)
        
        return jsonify({
            "status": "success",
            "jobs": jobs,
            "warnings": warnings,
            "config": config_data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)})

@app.route('/refine-pdf/approve', methods=['POST'])
def refine_pdf_approve():
    print("Received approval request...")
    try:
        if 'pdf_file' not in request.files:
            return jsonify({"status": "error", "message": "No PDF file uploaded."})
            
        file = request.files['pdf_file']
        config_str = request.form.get('config_data')
        
        if not config_str:
            return jsonify({"status": "error", "message": "No configurations provided."})
            
        config_data = json.loads(config_str)
        
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        print(f"[OK] Configuration updated successfully at {config_path}")
        
        upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(upload_dir, filename)
        file.save(pdf_path)
        
        from scrapper import run_pdf_scrape
        excel_file = run_pdf_scrape(pdf_path=pdf_path)
        print(f"[OK] Run scraper excel completed: {excel_file}")
        
        output_pdf = run_report_generation()
        print(f"[OK] Run report generation completed: {output_pdf}")
        
        if output_pdf:
            return jsonify({
                "status": "success",
                "message": "Approved and integrated successfully!",
                "file_name": os.path.basename(output_pdf)
            })
        else:
            return jsonify({"status": "error", "message": "Approved, but Excel/PDF generation failed."})
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)})

@app.route('/generate-targeted', methods=['POST'])
def generate_targeted():
    print("Received candidate-targeted scraping request...")
    try:
        data = request.get_json() or {}
        raw_keywords = data.get("keywords", [])
        raw_location = data.get("location", "Redding, CA 96002")
        radius = int(data.get("radius", 15))
        bypass_terms = [b.lower() for b in data.get("bypass_terms", [])]

        if not raw_keywords:
            return jsonify({"status": "error", "message": "No search keywords provided."})

        from scrapper import run_scraping_job, load_search_config
        config = load_search_config()

        formatted_keywords = [
            kw if kw.startswith("title:") else f"title:({kw})"
            for kw in raw_keywords
        ]

        standard_rejected = config.get("rejected_titles", [])
        active_rejections = [
            rej for rej in standard_rejected
            if not any(b in rej.lower() for b in bypass_terms)
        ]

        excel_file = run_scraping_job(
            keywords=formatted_keywords,
            location=[raw_location],
            radius=radius,
            rejected_titles=active_rejections,
            days_ago=7,
            max_pages=2,
            run_pdf=False,
            run_online=True,
            filename_prefix="targeted_search"
        )

        if excel_file:
            from generate_report import run_report_generation
            output_pdf = run_report_generation()
            filename = os.path.basename(output_pdf) if output_pdf else os.path.basename(excel_file)
            return jsonify({
                "status": "success",
                "message": f"Targeted search complete for {raw_location} ({radius}m radius).",
                "file_name": filename,
                "download_url": f"/download/{filename}"
            })

        return jsonify({"status": "error", "message": "Targeted search found no matching records."})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
