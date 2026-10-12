"""
generate_knowledge_base.py

Builds the complete Shasta County employer profiles database for all 262 employers
found in the user's Google Sheet 'Redding Area Employers'.
"""

import os
import json
import re

OUTPUT_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "shasta_employers_enriched.json")

# 19 Standard Workforce Taxonomy Sectors
VALID_SECTORS = [
    "Animal Care & Veterinary Services",
    "Agriculture & Groundskeeping",
    "Childcare & Education Support",
    "Construction & Laborers",
    "Customer Service & Hospitality",
    "Food & Restaurant",
    "Healthcare & Caregiving",
    "Janitorial & Facilities",
    "Manufacturing & Production",
    "Office & Clerical",
    "Personal Care & Services",
    "Retail & Sales",
    "Security & Public Safety",
    "Social & Human Services",
    "Technology & IT Support",
    "Trades & Mechanics",
    "Transportation & Delivery",
    "Warehouse & Logistics",
    "Other"
]

print("Script template ready.")
