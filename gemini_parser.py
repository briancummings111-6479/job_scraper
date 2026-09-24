import os
import json
import re
from typing import Optional
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

VALID_SECTORS = [
    "Retail & Merchandising",
    "Food & Restaurant",
    "Trades & Labor Helpers",
    "Healthcare & Caregiving",
    "Customer Service & Hospitality",
    "Janitorial & Facilities",
    "Office & Clerical",
    "Warehouse & Logistics",
    "Transportation & Delivery",
    "Personal Care & Services",
    "Childcare & Education Support",
    "Other"
]

class JobAnalysisResult(BaseModel):
    is_entry_level: bool = Field(description="True if the position is entry-level suitable for job seekers with 0-2 years experience. False if it requires advanced degrees, senior management, OTR over-the-road trucking, or 5+ years experience.")
    rejection_reason: Optional[str] = Field(default=None, description="If is_entry_level is False, provide the specific disqualifying reason (e.g. 'Requires Bachelor's Degree', 'OTR over-the-road trucking', 'Requires 5+ years experience').")
    clean_title: str = Field(description="Clean, concise job title without scraper artifacts, emojis, or marketing noise.")
    sector: str = Field(description=f"Best matching industry sector from: {', '.join(VALID_SECTORS)}")
    pay_rate: str = Field(description="Employer-stated compensation rate (e.g., '$18.00 - $22.00 / hr', '$20.00 per hour', '$55,000 / yr') or 'N/A' if not stated in the posting text. Never include algorithmic estimated wages.")
    job_type: str = Field(description="Full-time, Part-time, Contract, Temporary, or N/A.")
    schedule: str = Field(description="Shift or schedule (e.g. Day shift, Night shift, Weekend availability, Monday to Friday) or N/A.")
    experience_requirements: str = Field(description="Concise, semicolon-separated list of candidate qualifications for Column I: experience level, age if specified, driver's license/CDL class, education if specified, and role certifications.")
    job_description_summary: str = Field(description="Crisp 2-3 sentence overview of the role's essential responsibilities, daily tasks, and duties for Column J. Do not duplicate metadata like pay or sector.")
    min_age: Optional[int] = Field(default=18, description="Minimum age requirement if explicitly specified (e.g. 16, 18, 21), or 18 as default.")
    is_youth_friendly: bool = Field(default=False, description="True if the job is explicitly marked 16+, youth-friendly, or suitable for minors/students.")
    requires_driver_license: bool = Field(default=False, description="True if a driver's license or driving duties are required.")
    driver_license_type: str = Field(default="None", description="One of: 'None', 'Class C (Standard)', 'Commercial Class A (CDL-A)', 'Commercial Class B (CDL-B)'.")
    requires_hs_ged: bool = Field(default=False, description="True if high school diploma or GED is explicitly required.")
    requires_drug_test: bool = Field(default=False, description="True if drug screening is explicitly stated as required.")
    requires_background_check: bool = Field(default=False, description="True if background check is explicitly stated as required.")

def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"[GEMINI] Error initializing google.genai Client: {e}")
        return None

def analyze_job_with_gemini(
    title: str,
    company: str,
    location: str,
    description_text: str,
    raw_pay: str = "N/A",
    raw_type: str = "N/A",
    raw_schedule: str = "N/A"
) -> Optional[JobAnalysisResult]:
    """
    Parses, understands, and structures job posting data using Gemini Flash with structured schema output.
    Returns None if GEMINI_API_KEY is not configured or if an unrecoverable API error occurs.
    """
    client = get_gemini_client()
    if not client:
        return None

    prompt = f"""
You are an expert workforce development analyst for Shasta County, California (Redding, Anderson, Shasta Lake area).
Analyze the following job posting and extract structured, verified data.

JOB CONTEXT:
- Scraped Title: {title}
- Company / Employer: {company}
- Location: {location}
- Scraped Pay: {raw_pay}
- Scraped Job Type: {raw_type}
- Scraped Schedule: {raw_schedule}

FULL ON-PAGE JOB POSTING TEXT:
\"\"\"
{description_text}
\"\"\"

CRITICAL EVALUATION RULES:
1. ENTRY-LEVEL FILTERING:
   - Reject (is_entry_level=False) if the job requires:
     * Advanced professional degree (Bachelor's, Master's, PhD, MD, JD).
     * Professional licenses (LCSW, LMFT, LPCC, RN, DVM, Architect, Commercial Superintendent).
     * OTR (Over-the-road / nationwide) trucking.
     * 5+ years of mandatory prior experience.
     * Annual compensation exceeding entry-level ceiling ($75k+) or hourly exceeding $38/hr.
   - Accept (is_entry_level=True) entry-level, apprentice, helper, or 0-2 year experience positions.

2. ACCURATE COLUMN DATA:
   - Sector: Must be one of: {', '.join(VALID_SECTORS)}.
   - Pay Rate (Column F): Extract the true employer-provided pay rate from text. If no wage is given by the employer, use "N/A". Never use algorithmic estimates.
   - Experience / Requirements (Column I): Semicolon-separated list: Experience level; Age if stated; Driver license / CDL class; Education if stated; Certifications (e.g. Food Handler, CNA, CPR). Never include conflicting statements.
   - Job Description (Column J): Crisp 2-3 sentence summary describing daily duties and responsibilities. Do NOT repeat metadata like sector, pay, or requirements list.
"""

    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": JobAnalysisResult,
                    "temperature": 0.1,
                }
            )
            if response and response.text:
                data = json.loads(response.text)
                return JobAnalysisResult(**data)
        except Exception as e:
            # Try next model fallback
            continue

    return None
