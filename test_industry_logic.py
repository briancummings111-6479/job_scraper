import pandas as pd
from datetime import datetime, timedelta

def determine_industry(row):
    """
    Determine industry based on Job Title and Company.
    """
    # Normalize text
    title = str(row.get('job_title', '')).lower()
    company = str(row.get('company', '')).lower()
    text = f"{title} {company}"
    
    # Industry Guidelines
    # Restaurant: restaurant, food, cook, chef, server, dining, kitchen, bar, pizza, burger, taco, cafe
    # Retail: retail, store, cashier, shop, mart, sales associate
    # Sales: sales, representative
    # Office: office, admin, clerk, receptionist, assistant, secretary, data entry
    # Construction: construction, laborer, carpenter, builder, site
    # Health Care: health, medical, nurse, patient, care, rn, cna, clinic, hospital
    # Driver: driver, delivery, transport, truck, courier
    # Technical: technician, engineer, software, developer, support, it
    # Trades: mechanic, welder, electrician, plumber, maintenance, hvac
    # Management: management, manager, supervisor, director, executive, lead
    
    keywords = {
        'Restaurant': ['restaurant', 'food', 'cook', 'chef', 'server', 'dining', 'kitchen', 'bar', 'pizza', 'burger', 'taco', 'cafe'],
        'Retail': ['retail', 'store', 'cashier', 'shop', 'mart', 'sales associate'],
        'Sales': ['sales', 'representative'],
        'Office': ['office', 'admin', 'clerk', 'receptionist', 'assistant', 'secretary', 'data entry'],
        'Construction': ['construction', 'laborer', 'carpenter', 'builder', 'site'],
        'Health Care': ['health', 'medical', 'nurse', 'patient', 'care', 'caregiver', 'rn', 'cna', 'clinic', 'hospital'],
        'Driver': ['driver', 'delivery', 'transport', 'truck', 'courier'],
        'Technical': ['technician', 'engineer', 'software', 'developer', 'support', 'it'],
        'Trades': ['mechanic', 'welder', 'electrician', 'plumber', 'maintenance', 'hvac'],
        'Management': ['management', 'manager', 'supervisor', 'director', 'executive', 'lead', 'team lead']
    }
    
    # Priority? Maybe check specific ones first or just first match?
    # Let's iterate and return first match for now.
    
    for industry, tags in keywords.items():
        for tag in tags:
            # Check entire word match to avoid partials like 'it' in 'waiter'?
            # 'it' is very short. 'it' might match 'waiter'.
            # Better to use word boundaries or carefully check.
            # Special case for 'it':
            if tag == 'it':
                 if f" {tag} " in f" {text} " or text.startswith(tag + " ") or text.endswith(" " + tag):
                     return industry
            elif tag in text:
                return industry
                
    return "Other"

# Test Data
test_data = [
    {"job_title": "Server", "company": "Olive Garden"},
    {"job_title": "Software Engineer", "company": "Google"},
    {"job_title": "Store Manager", "company": "Walmart"}, # Should match Management (matches manager) or Retail?
    # "Store Manager" has "Store" (Retail) and "Manager" (Management).
    # Order of checking matters. User added Management later.
    # Usually Management implies level, but Industry might be Retail.
    # User's request: "Determine the industry type". 
    # "Store Manager" is Retail industry, Management role.
    # But user listed industries: "Restaurant, Retail, ..., Management".
    # If I check Management last, "Store Manager" might hit "Store" -> Retail.
    # If I check Management first, it hits "Manager" -> Management.
    # I will stick to the iteration order.
    # Let's see what happens.
    
    {"job_title": "Construction Laborer", "company": "Bob's Builders"},
    {"job_title": "Registered Nurse", "company": "General Hospital"},
    {"job_title": "Truck Driver", "company": "FedEx"},
    {"job_title": "Sales Representative", "company": "Comcast"},
    {"job_title": "Admin Assistant", "company": "Office Depot"},
    {"job_title": "HVAC Technician", "company": "Cool Air"},
    {"job_title": "Head Chef", "company": "La Trattoria"}
]

print("--- Industry Classification Test ---")
for job in test_data:
    ind = determine_industry(job)
    print(f"Job: {job['job_title']} @ {job['company']} -> {ind}")

print("\n--- Date Filter Test ---")
today = datetime.now()
dates = [
    (today - timedelta(days=2)).strftime("%Y-%m-%d"),
    (today - timedelta(days=7)).strftime("%Y-%m-%d"), # Boundary
    (today - timedelta(days=8)).strftime("%Y-%m-%d"), # Should filter
    "N/A",
    "Yesterday" # Scraper converts this, but let's test if raw
]
# Scraper converts all to YYYY-MM-DD or N/A
print(f"Today: {today.strftime('%Y-%m-%d')}")
cutoff = today - timedelta(days=7)
print(f"Cutoff: {cutoff.strftime('%Y-%m-%d')} (Any date BEFORE this is excluded)")

for d_str in dates:
    exclude = False
    if d_str == "N/A":
        # Keep or exclude? User said "Do not include posts over 7 days old".
        # If unknown, we can't be sure.
        # But for safety in a scraper, usually keep unless known old.
        pass
    else:
        try:
            d_date = datetime.strptime(d_str, "%Y-%m-%d")
            if d_date < cutoff.replace(hour=0, minute=0, second=0, microsecond=0):
                exclude = True
        except:
             pass
    print(f"Date: {d_str} -> Exclude? {exclude}")
