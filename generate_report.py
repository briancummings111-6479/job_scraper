import sys
import re
import pandas as pd
import os
import glob
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime

def get_latest_excel_file(output_dir):
    """Find the most recent Excel file in the output directory"""
    list_of_files = glob.glob(os.path.join(output_dir, '*.xlsx'))
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getctime)

def generate_pdf_report(excel_file, output_pdf):
    """Generate a PDF report from the Excel file"""
    print(f"Reading data from: {excel_file}")
    
    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # Required columns
    columns_to_include = [
        'job_title', 'company', 'location', 'pay', 
        'job_type_extracted', 'shift_schedule', 'job_url', 'scraped_date'
    ]
    
    # Filter and clean data
    for col in columns_to_include:
        if col not in df.columns:
            df[col] = "N/A"
    
    # Create PDF
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=letter,
        rightMargin=36, leftMargin=36, # Reduced margins for 2 columns
        topMargin=72, bottomMargin=18
    )
    
    styles = getSampleStyleSheet()
    
    # Increase font sizes by 2 points
    for style_name in ['Normal', 'Title', 'Heading2']:
        if style_name in styles:
            styles[style_name].fontSize += 2
            styles[style_name].leading += 2

    styles.add(ParagraphStyle(name='JobTitle', parent=styles['Heading2'], spaceAfter=6))
    styles.add(ParagraphStyle(name='Label', parent=styles['Normal'], fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='Value', parent=styles['Normal'], spaceAfter=6))
    styles.add(ParagraphStyle(name='Link', parent=styles['Normal'], textColor=colors.blue))
    
    story = []
    

    
    for index, row in df.iterrows():
        job_elements = []
        
        # Company (Header)
        company = str(row.get('company', 'N/A'))
        job_elements.append(Paragraph(company, styles['JobTitle']))
        
        # Job Title (Details)
        job_title_raw = str(row.get('job_title', 'N/A'))
        job_title = re.sub(r'\s*-\s*job\s*post\s*', '', job_title_raw, flags=re.IGNORECASE).strip()
        
        # Details
        details = [
            ("Job Title", job_title),
            ("Location", row.get('location', 'N/A')),
            ("Pay", row.get('pay', 'N/A')),
            ("Type", row.get('job_type_extracted', 'N/A')),
            ("Shift", row.get('shift_schedule', 'N/A')),
        ]
        
        for label, value in details:
            if pd.isna(value): value = "N/A"
            text = f"<b>{label}:</b> {value}"
            job_elements.append(Paragraph(text, styles['Normal']))
            
        # Date
        date_val = row.get('scraped_date', '')
        if pd.notna(date_val):
            try:
                date_str = str(date_val).split(' ')[0]
                job_elements.append(Paragraph(f"<b>Date Added:</b> {date_str}", styles['Normal']))
            except:
                job_elements.append(Paragraph(f"<b>Date Added:</b> {date_val}", styles['Normal']))
        
        job_elements.append(Spacer(1, 12))
        job_elements.append(Paragraph("_" * 60, styles['Normal'])) # Separator line
        job_elements.append(Spacer(1, 12))
        
        story.append(KeepTogether(job_elements))
        
    try:
        doc.build(story)
        print(f"PDF Report generated successfully: {output_pdf}")
    except Exception as e:
        print(f"Error generating PDF: {e}")

def run_report_generation(base_dir=None):
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    
    # Use argument if provided, otherwise latest
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    else:
        target_file = get_latest_excel_file(output_dir)
        
    if target_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_pdf = os.path.join(output_dir, f"job_report_{timestamp}.pdf")
        generate_pdf_report(target_file, output_pdf)
        return output_pdf
    else:
        print("No Excel files found in output directory.")
        return None

if __name__ == "__main__":
    run_report_generation()
