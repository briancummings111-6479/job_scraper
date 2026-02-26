from flask import Flask, render_template, jsonify
import os
import sys
import setuptools # Required for Python 3.12+ (distutils support)
from generate_report import run_report_generation
from scrapper import run_scraping_job

# Ensure we can find the generate_report module if it's in the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True)
