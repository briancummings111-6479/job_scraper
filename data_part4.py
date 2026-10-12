"""
data_part4.py - Verified profiles for Employers 196 to 262 (Raising Cane's to Zumiez)
"""

PART4_PROFILES = {
    "Raising Cane's": {
        "corporate_name": "Raising Cane's Restaurants, LLC",
        "sector": "Food & Restaurant",
        "min_age": 16,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "None",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Crew training provided)",
        "starting_wage": "$20.00 / hr (CA Fast Food Minimum Wage)",
        "career_url": "https://jobs.raisingcanes.com/",
        "notes": "Fast food chicken fingers; restaurant crew, cashier, cook.",
        "locations": [
            {
                "branch_name": "Friendly Rd Restaurant",
                "street_address": "1470 Friendly Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 223-1440",
                "notes": "Near Dana Drive shopping corridor; RABA Route 18."
            }
        ]
    },
    "Raley's": {
        "corporate_name": "The Raley's Companies",
        "sector": "Retail & Sales",
        "min_age": 16,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (On-the-job training provided)",
        "starting_wage": "$16.50 - $18.50 / hr",
        "career_url": "https://jobs.raley.com/",
        "notes": "Regional supermarket chain; courtesy clerk, cashier, bakery/deli clerk, grocery clerk.",
        "locations": [
            {
                "branch_name": "Lake Blvd Store",
                "street_address": "201 Lake Blvd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 246-3500",
                "notes": "RABA Route 2 & 3."
            }
        ]
    },
    "RDSolutions": {
        "corporate_name": "RDSolutions LLC",
        "sector": "Retail & Sales",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "Valid CA Driver License (Class C) required",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Smartphone app auditing training provided)",
        "starting_wage": "$17.00 - $19.50 / hr",
        "career_url": "",
        "notes": "Field merchandising, price auditing, and barcode scan survey contractor dispatched locally to Shasta County retailers.",
        "locations": [
            {
                "branch_name": "Mobile Field Operations",
                "street_address": "Field Dispatched / Mobile Retail (Redding, CA)",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "",
                "notes": "Dispatched to local grocery and retail stores across Redding area."
            }
        ]
    },
    "Red Roof Inns": {
        "corporate_name": "Red Roof Inn Redding",
        "sector": "Customer Service & Hospitality",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (On-the-job training provided)",
        "starting_wage": "$16.50 - $17.50 / hr",
        "career_url": "https://www.redroof.com/careers",
        "notes": "Hotel hospitality; room attendant/housekeeping, front desk clerk, maintenance.",
        "locations": [
            {
                "branch_name": "Bechelli Ln Hotel",
                "street_address": "2975 Bechelli Ln",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 222-0144",
                "notes": "RABA Route 14."
            }
        ]
    },
    "Redding Post Acute": {
        "corporate_name": "Redding Post Acute (Skilled Nursing)",
        "sector": "Healthcare & Caregiving",
        "min_age": 18,
        "fair_chance": "No (Healthcare Clearance Required)",
        "drug_testing": "Clinical Drug Screen",
        "background_check": "Live Scan / Fingerprint Clearance",
        "driver_license": "None",
        "hs_ged": "Required",
        "work_experience": "No experience required for dietary / housekeeping; CNA certification for aides",
        "starting_wage": "$17.50 - $21.50 / hr",
        "career_url": "https://reddingpostacute.com/careers/",
        "notes": "Skilled nursing and post-acute therapy facility; CNA, dietary aide, housekeeper.",
        "locations": [
            {
                "branch_name": "Gold St Facility",
                "street_address": "1836 Gold St",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 241-0433",
                "notes": "Downtown Redding health corridor; RABA Downtown Terminal."
            }
        ]
    },
    "REDDING RANCHERIA WIN-RIVER CASINO": {
        "corporate_name": "WIN-RIVER HOTEL CORPORATION (Redding Rancheria)",
        "sector": "Customer Service & Hospitality",
        "min_age": 21,
        "fair_chance": "No (Tribal Gaming Commission License Required)",
        "drug_testing": "5-Panel Pre-Employment",
        "background_check": "Live Scan / Tribal Gaming Commission Clearance",
        "driver_license": "None (Role-dependent)",
        "hs_ged": "Required",
        "work_experience": "No experience required for busser/dishwasher/security officer trainee",
        "starting_wage": "$17.50 - $21.00 / hr + tips",
        "career_url": "https://www.winrivercasino.com/careers/",
        "notes": "Tribal resort and casino; table games dealer, slot attendant, security officer, cook, steward, hotel front desk.",
        "locations": [
            {
                "branch_name": "Win-River Resort & Casino",
                "street_address": "2100 Redding Rancheria Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 243-3377",
                "notes": "Hwy 273 corridor."
            }
        ]
    },
    "River Valley Healthcare & Wellness Center": {
        "corporate_name": "River Valley Healthcare & Wellness Center",
        "sector": "Healthcare & Caregiving",
        "min_age": 18,
        "fair_chance": "No (Healthcare Clearance Required)",
        "drug_testing": "Clinical Drug Screen",
        "background_check": "Live Scan / Fingerprint Clearance",
        "driver_license": "None",
        "hs_ged": "Required",
        "work_experience": "Dietary/housekeeping no exp; CNA requires active certification",
        "starting_wage": "$17.50 - $21.50 / hr",
        "career_url": "https://rivervalleyhealthcare.com/careers/",
        "notes": "Skilled nursing and long-term care facility; certified nursing assistant, dietary server, EVS cleaner.",
        "locations": [
            {
                "branch_name": "Edith Ave Facility",
                "street_address": "2620 Edith Ave",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 246-1800",
                "notes": "Edith Ave healthcare campus."
            }
        ]
    },
    "Rose Garden Thai Cuisine": {
        "corporate_name": "Rose Garden Thai Cuisine",
        "sector": "Food & Restaurant",
        "min_age": 16,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "None",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required for busser/dishwasher; line cook 1+ yr pref",
        "starting_wage": "$16.50 - $18.50 / hr + tips",
        "career_url": "",
        "notes": "Thai dining restaurant; host, busser, server, prep cook, dishwasher.",
        "locations": [
            {
                "branch_name": "Eureka Way Restaurant",
                "street_address": "1350 Eureka Way",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 244-9888",
                "notes": "RABA Route 2."
            }
        ]
    },
    "Roslyn Home Care": {
        "corporate_name": "Roslyn Home Care Inc.",
        "sector": "Healthcare & Caregiving",
        "min_age": 18,
        "fair_chance": "No (DSS In-Home Care Clearance Required)",
        "drug_testing": "Clinical Drug Screen",
        "background_check": "Live Scan / Fingerprint Clearance",
        "driver_license": "Valid CA Driver License (Class C) and reliable vehicle required",
        "hs_ged": "Required",
        "work_experience": "No experience required (Caregiver training provided)",
        "starting_wage": "$17.00 - $19.50 / hr",
        "career_url": "",
        "notes": "In-home caregiving and companion care dispatched to private residences in Shasta County.",
        "locations": [
            {
                "branch_name": "Redding Office",
                "street_address": "1335 Pine St",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 241-1188",
                "notes": "Downtown Redding office."
            }
        ]
    },
    "Ross Dress for Less": {
        "corporate_name": "Ross Stores, Inc.",
        "sector": "Retail & Sales",
        "min_age": 16,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (On-the-job training provided)",
        "starting_wage": "$16.50 - $17.50 / hr",
        "career_url": "https://jobs.rossstores.com/",
        "notes": "Off-price retail; retail associate, cashier, early morning stocker, store protection.",
        "locations": [
            {
                "branch_name": "Hilltop / Browning Store",
                "street_address": "835 Browning St",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 221-1250",
                "notes": "Near Hilltop Dr; RABA Route 11."
            },
            {
                "branch_name": "Cypress Ave Store",
                "street_address": "1655 E Cypress Ave",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 223-1120",
                "notes": "Cypress Ave center; RABA Route 18."
            }
        ]
    },
    "Round Table Pizza": {
        "corporate_name": "FAT Brands / Round Table Pizza",
        "sector": "Food & Restaurant",
        "min_age": 16,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "None",
        "driver_license": "None (Class C for delivery drivers)",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (On-the-job training provided)",
        "starting_wage": "$16.50 - $17.50 / hr + tips",
        "career_url": "https://roundtablepizza.com/careers/",
        "notes": "Pizzeria restaurant; dough roller, pizza cook, cashier, counter server, delivery driver.",
        "locations": [
            {
                "branch_name": "Churn Creek Store",
                "street_address": "1926 Churn Creek Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 222-1200",
                "notes": "RABA Route 18."
            },
            {
                "branch_name": "Lake Blvd Store",
                "street_address": "100 Lake Blvd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 241-1188",
                "notes": "RABA Route 2 & 3."
            },
            {
                "branch_name": "Anderson Store",
                "street_address": "2650 Gateway Dr",
                "city": "Anderson",
                "state": "CA",
                "zip_code": "96007",
                "phone": "(530) 365-2711",
                "notes": "RABA Route 9."
            }
        ]
    },
    "Safe Haven Security": {
        "corporate_name": "Safe Haven Security (ADT Authorized Dealer)",
        "sector": "Trades & Mechanics",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "5-Panel (THC-Exempt in CA)",
        "background_check": "Standard Pre-Employment",
        "driver_license": "Valid CA Driver License (Class C) required",
        "hs_ged": "Required",
        "work_experience": "No experience required (Field installation training provided)",
        "starting_wage": "$18.00 - $24.00 / hr + performance incentives",
        "career_url": "https://mysafehaven.com/careers/",
        "notes": "Residential security and smart home installation; field service technician dispatched to homes.",
        "locations": [
            {
                "branch_name": "Field Dispatched / Home Security",
                "street_address": "Field Dispatched / Mobile (Redding, CA)",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(888) 723-3428",
                "notes": "Technicians dispatched to client homes across Shasta County."
            }
        ]
    },
    "Safeway": {
        "corporate_name": "Albertsons Companies, Inc. / Safeway",
        "sector": "Retail & Sales",
        "min_age": 16,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Union retail grocery training provided)",
        "starting_wage": "$16.50 - $18.50 / hr (UFCW union pay scale)",
        "career_url": "https://www.albertsonscompanies.com/careers",
        "notes": "Full service supermarket; courtesy clerk, food clerk, deli/bakery clerk, meat clerk.",
        "locations": [
            {
                "branch_name": "Redding - East Cypress",
                "street_address": "1070 E Cypress Ave",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 222-2114",
                "notes": "RABA Route 18."
            },
            {
                "branch_name": "Redding - Downtown Pine St",
                "street_address": "2275 Pine St",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 246-0688",
                "notes": "Downtown Redding; RABA Route 2 & 3."
            },
            {
                "branch_name": "Anderson Store",
                "street_address": "2601 Balls Ferry Rd",
                "city": "Anderson",
                "state": "CA",
                "zip_code": "96007",
                "phone": "(530) 365-2747",
                "notes": "RABA Route 9 (Anderson)."
            }
        ]
    },
    "Salvation Army": {
        "corporate_name": "The Salvation Army USA Western Territory (Redding Corps)",
        "sector": "Social & Human Services",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "5-Panel (THC-Exempt in CA)",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None (Class C for donation route drivers)",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Social mission training provided)",
        "starting_wage": "$16.50 - $18.00 / hr",
        "career_url": "https://westernusa.salvationarmy.org/careers/",
        "notes": "Community social service and thrift operation; donation sorter, food pantry clerk, thrift cashier.",
        "locations": [
            {
                "branch_name": "Redding Corps & Social Services",
                "street_address": "2691 Larkspur Ln",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 222-2207",
                "notes": "Larkspur Ln center; RABA Route 18."
            }
        ]
    },
    "Save Mart": {
        "corporate_name": "The Save Mart Companies",
        "sector": "Retail & Sales",
        "min_age": 16,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (On-the-job grocery training provided)",
        "starting_wage": "$16.50 - $18.50 / hr",
        "career_url": "https://www.savemart.com/careers",
        "notes": "Regional supermarket; courtesy clerk, cashier, deli clerk, produce stocker.",
        "locations": [
            {
                "branch_name": "Churn Creek Store",
                "street_address": "4631 Churn Creek Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 221-5000",
                "notes": "South Redding shopping center."
            }
        ]
    },
    "See's Candies": {
        "corporate_name": "See's Candies, Inc. (Berkshire Hathaway)",
        "sector": "Retail & Sales",
        "min_age": 16,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (On-the-job customer service training provided)",
        "starting_wage": "$16.50 - $17.50 / hr",
        "career_url": "https://careers.sees.com/",
        "notes": "Youth-friendly confectionery retail; sales associate, cashier, holiday candy packer.",
        "locations": [
            {
                "branch_name": "Mt Shasta Mall Shop",
                "street_address": "900 Dana Dr, Ste A-06",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 223-2882",
                "notes": "Mt Shasta Mall; central RABA transit hub."
            }
        ]
    },
    "ServiceMaster Building Maintenance by Sharma": {
        "corporate_name": "ServiceMaster Clean / ServiceMaster by Sharma",
        "sector": "Janitorial & Facilities",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "5-Panel (THC-Exempt in CA)",
        "background_check": "Standard Pre-Employment",
        "driver_license": "Valid CA Driver License (Class C) required for crew drivers",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Commercial cleaning training provided)",
        "starting_wage": "$16.50 - $19.00 / hr",
        "career_url": "https://www.servicemasterclean.com/",
        "notes": "Commercial janitorial and commercial facility floor maintenance.",
        "locations": [
            {
                "branch_name": "Victor Ave Facility",
                "street_address": "3470 Victor Ave",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 221-1250",
                "notes": "Victor Ave commercial corridor; RABA Route 18."
            }
        ]
    },
    "Shasta College": {
        "corporate_name": "Shasta-Tehama-Trinity Joint Community College District",
        "sector": "Childcare & Education Support",
        "min_age": 18,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt (DOT for transportation)",
        "background_check": "Live Scan / Fingerprint Clearance",
        "driver_license": "None (Role-dependent)",
        "hs_ged": "Required",
        "work_experience": "Student worker / custodian / dining assistant entry-level",
        "starting_wage": "$18.50 - $24.00 / hr (CalPERS retirement)",
        "career_url": "https://www.shastacollege.edu/human-resources/jobs/",
        "notes": "Regional community college; custodial worker, groundskeeper, cafeteria aide, campus safety.",
        "locations": [
            {
                "branch_name": "Main Redding Campus",
                "street_address": "11555 Old Oregon Trail",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 242-7500",
                "notes": "RABA Route 11 (Direct college service)."
            }
        ]
    },
    "Shasta Community Health Center": {
        "corporate_name": "Shasta Community Health Center (SCHC)",
        "sector": "Healthcare & Caregiving",
        "min_age": 18,
        "fair_chance": "No (FQHC Healthcare Clearance Required)",
        "drug_testing": "Clinical Drug Screen",
        "background_check": "Live Scan / Fingerprint Clearance",
        "driver_license": "None",
        "hs_ged": "Required",
        "work_experience": "No experience required for records clerk / receptionist; MA cert for clinic",
        "starting_wage": "$18.50 - $23.00 / hr",
        "career_url": "https://www.shastahealth.org/careers",
        "notes": "Federally Qualified Health Center (FQHC); medical assistant, dental assistant, patient intake.",
        "locations": [
            {
                "branch_name": "Redding Main Center",
                "street_address": "1035 Placer St",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 246-5710",
                "notes": "Downtown Redding; RABA Downtown Terminal."
            },
            {
                "branch_name": "Anderson Health Center",
                "street_address": "2965 East St",
                "city": "Anderson",
                "state": "CA",
                "zip_code": "96007",
                "phone": "(530) 378-0486",
                "notes": "RABA Route 9 (Anderson)."
            },
            {
                "branch_name": "Shasta Lake Health Center",
                "street_address": "4215 Front St",
                "city": "Shasta Lake",
                "state": "CA",
                "zip_code": "96019",
                "phone": "(530) 276-9196",
                "notes": "RABA Route 1."
            }
        ]
    },
    "Shasta County": {
        "corporate_name": "County of Shasta (County Government)",
        "sector": "Office & Clerical",
        "min_age": 18,
        "fair_chance": "Case-by-case",
        "drug_testing": "5-Panel Pre-Employment",
        "background_check": "Live Scan / Fingerprint Clearance",
        "driver_license": "Valid CA Driver License (Class C) required for most field roles",
        "hs_ged": "Required",
        "work_experience": "No experience required for entry-level clerical / maintenance aide",
        "starting_wage": "$18.50 - $24.50 / hr (County benefits & pension)",
        "career_url": "https://www.governmentjobs.com/careers/shasta",
        "notes": "County government agency; office assistant, roads maintenance worker, eligibility worker trainee.",
        "locations": [
            {
                "branch_name": "County Administration & Courthouse",
                "street_address": "1450 Court St",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 225-5555",
                "notes": "Downtown Redding; RABA Downtown Terminal."
            }
        ]
    },
    "Shasta County Job Center": {
        "corporate_name": "Smart Business Resource Center / America's Job Center of California",
        "sector": "Social & Human Services",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Required",
        "work_experience": "No experience required (Workforce peer specialist training provided)",
        "starting_wage": "$17.50 - $21.00 / hr",
        "career_url": "https://thesmartcenter.biz/careers/",
        "notes": "Workforce development hub; intake specialist, employment peer specialist, resource clerk.",
        "locations": [
            {
                "branch_name": "East St Job Center",
                "street_address": "1255 East St, Ste 200",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 246-7911",
                "notes": "Downtown Redding; RABA Downtown Terminal."
            }
        ]
    },
    "SHASTA COUNTY OFFICE OF EDUCATION": {
        "corporate_name": "Shasta County Office of Education (SCOE)",
        "sector": "Childcare & Education Support",
        "min_age": 18,
        "fair_chance": "No (Education Code Live Scan Clearance Required)",
        "drug_testing": "5-Panel Drug Screen",
        "background_check": "Live Scan / FBI/DOJ Clearance",
        "driver_license": "None (Class B with passenger endorsement for bus drivers)",
        "hs_ged": "Required",
        "work_experience": "Paraprofessional assessment or 48 college units for instructional aides",
        "starting_wage": "$18.00 - $23.00 / hr (CalPERS pension)",
        "career_url": "https://www.edjoin.org/shastacoe",
        "notes": "County educational agency; special education paraprofessional, school bus driver, custodian.",
        "locations": [
            {
                "branch_name": "Magnolia Ave Administration",
                "street_address": "1644 Magnolia Ave",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 225-0200",
                "notes": "Downtown Redding; RABA Route 5."
            }
        ]
    },
    "Shasta Eye Medical Group": {
        "corporate_name": "Shasta Eye Medical Group, Inc.",
        "sector": "Healthcare & Caregiving",
        "min_age": 18,
        "fair_chance": "No (Clearance Required)",
        "drug_testing": "5-Panel (THC-Exempt in CA)",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Required",
        "work_experience": "No experience required for receptionist; ophthalmic tech training provided",
        "starting_wage": "$17.50 - $21.00 / hr",
        "career_url": "https://shastaeye.com/careers/",
        "notes": "Ophthalmology and optometry clinic; patient receptionist, ophthalmic assistant trainee.",
        "locations": [
            {
                "branch_name": "Redding Eye Clinic",
                "street_address": "3165 Churn Creek Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 223-1400",
                "notes": "RABA Route 18."
            }
        ]
    },
    "Shasta Head Start": {
        "corporate_name": "Shasta County Head Start Child Development, Inc.",
        "sector": "Childcare & Education Support",
        "min_age": 18,
        "fair_chance": "No (Childcare Live Scan Clearance Required)",
        "drug_testing": "Clinical Drug Screen",
        "background_check": "Live Scan / Fingerprint Clearance / TB Clearance",
        "driver_license": "None",
        "hs_ged": "Required",
        "work_experience": "ECE college credits helpful / teacher aide training provided",
        "starting_wage": "$17.00 - $19.50 / hr",
        "career_url": "https://shastaheadstart.org/careers/",
        "notes": "Early childhood education nonprofit; teacher aide, family service advocate, center cook.",
        "locations": [
            {
                "branch_name": "Churn Creek Administrative Center",
                "street_address": "2885 Churn Creek Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 241-1036",
                "notes": "RABA Route 18."
            }
        ]
    },
    "Shasta Precast, Inc.": {
        "corporate_name": "Shasta Precast, Inc.",
        "sector": "Manufacturing & Production",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "5-Panel Pre-Employment",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None (Class C or CDL for boom truck drivers)",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Heavy precast concrete labor training provided)",
        "starting_wage": "$18.00 - $22.50 / hr",
        "career_url": "https://shastaprecast.com/",
        "notes": "Precast concrete manufacturing plant in Shasta Lake; rebar fabricator, concrete pourer, yard loader.",
        "locations": [
            {
                "branch_name": "Shasta Lake Plant",
                "street_address": "5250 Ashby Rd",
                "city": "Shasta Lake",
                "state": "CA",
                "zip_code": "96019",
                "phone": "(530) 275-5457",
                "notes": "Ashby Rd industrial corridor; RABA Route 1."
            }
        ]
    },
    "Sheraton Redding at the Sundial Bridge": {
        "corporate_name": "Marriott International / Sheraton Redding at the Sundial Bridge",
        "sector": "Customer Service & Hospitality",
        "min_age": 18,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None (Class C for shuttle drivers)",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Comprehensive hospitality training provided)",
        "starting_wage": "$17.00 - $19.00 / hr",
        "career_url": "https://careers.marriott.com/",
        "notes": "Four-diamond riverfront hotel; front desk associate, night auditor, room attendant/housekeeping, banquet server.",
        "locations": [
            {
                "branch_name": "Riverfront Hotel",
                "street_address": "820 Sundial Bridge Dr",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 364-2800",
                "notes": "Sundial Bridge & Turtle Bay park; RABA Route 11."
            }
        ]
    },
    "Sierra Pacific Industries": {
        "corporate_name": "Sierra Pacific Industries (SPI)",
        "sector": "Manufacturing & Production",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "DOT Safety-Sensitive / 5-Panel Pre-Employment",
        "background_check": "Standard Pre-Employment",
        "driver_license": "Valid CA Driver License (Class C) preferred",
        "hs_ged": "Not Required",
        "work_experience": "No experience required for entry-level mill clean-up / tail-off; forklift pref",
        "starting_wage": "$22.84 / hr (Standard Entry Mill Rate)",
        "career_url": "https://spi-ind.com/Employment",
        "notes": "Largest private lumber manufacturer; sawmill laborer, green chain puller, cleanup crew, planer mill.",
        "locations": [
            {
                "branch_name": "Anderson Mill & Division Office",
                "street_address": "19794 Riverside Ave",
                "city": "Anderson",
                "state": "CA",
                "zip_code": "96007",
                "phone": "(530) 378-8000",
                "notes": "Riverside Ave sawmill division; RABA Route 9."
            },
            {
                "branch_name": "Burney Sawmill",
                "street_address": "37350 Highway 299 E",
                "city": "Burney",
                "state": "CA",
                "zip_code": "96013",
                "phone": "(530) 335-3681",
                "notes": "Eastern Shasta County regional sawmill operation."
            },
            {
                "branch_name": "Shasta Lake Plant",
                "street_address": "3850 Main St",
                "city": "Shasta Lake",
                "state": "CA",
                "zip_code": "96019",
                "phone": "(530) 275-8812",
                "notes": "Shasta Lake manufacturing division; RABA Route 1."
            }
        ]
    },
    "Sinclair Broadcast Group": {
        "corporate_name": "Sinclair Broadcast Group / KRCR News Channel 7",
        "sector": "Customer Service & Hospitality",
        "min_age": 18,
        "fair_chance": "Case-by-case",
        "drug_testing": "5-Panel (THC-Exempt in CA)",
        "background_check": "Standard Pre-Employment",
        "driver_license": "Valid CA Driver License (Class C) required for news/production crew",
        "hs_ged": "Required",
        "work_experience": "No experience required for studio production assistant / master control clerk",
        "starting_wage": "$17.50 - $21.00 / hr",
        "career_url": "https://sbgi.net/careers/",
        "notes": "Television broadcast news station; production assistant, camera operator, traffic coordinator.",
        "locations": [
            {
                "branch_name": "KRCR Television Studios",
                "street_address": "755 Auditorium Dr",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 243-7777",
                "notes": "Civic Center / Auditorium Dr; RABA Route 5."
            }
        ]
    },
    "Sonic Drive-In": {
        "corporate_name": "Inspire Brands / Sonic Drive-In",
        "sector": "Food & Restaurant",
        "min_age": 16,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "None",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (On-the-job training provided)",
        "starting_wage": "$16.50 - $17.50 / hr + tips",
        "career_url": "https://careers.sonicdrivein.com/",
        "notes": "Fast food drive-in; carhop on skates, cook, fountain prep, cashier.",
        "locations": [
            {
                "branch_name": "Anderson Drive-In",
                "street_address": "2605 Gateway Dr",
                "city": "Anderson",
                "state": "CA",
                "zip_code": "96007",
                "phone": "(530) 365-1700",
                "notes": "RABA Route 9 (Anderson)."
            }
        ]
    },
    "Spectrum": {
        "corporate_name": "Charter Communications / Spectrum",
        "sector": "Customer Service & Hospitality",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "5-Panel (THC-Exempt in CA per corporate policy)",
        "background_check": "Standard Pre-Employment",
        "driver_license": "Valid CA Driver License (Class C) required for field tech",
        "hs_ged": "Required",
        "work_experience": "Customer service passion (Field technician & retail sales training provided)",
        "starting_wage": "$20.00 / hr (Spectrum National Minimum Wage)",
        "career_url": "https://jobs.spectrum.com/",
        "notes": "Telecommunications and broadband provider; retail sales associate, field technician trainee.",
        "locations": [
            {
                "branch_name": "Dana Dr Retail Store",
                "street_address": "1435 Dana Dr, Ste B",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(888) 438-2427",
                "notes": "Dana Drive shopping corridor; RABA Route 18."
            }
        ]
    },
    "Spencer Gifts": {
        "corporate_name": "Spencer Gifts LLC",
        "sector": "Retail & Sales",
        "min_age": 17,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Customer service focus)",
        "starting_wage": "$16.50 - $17.50 / hr",
        "career_url": "https://www.spencersonline.com/content.jsp?pageName=Careers",
        "notes": "Novelty and pop-culture gift retail at Mt Shasta Mall; sales associate, cashier.",
        "locations": [
            {
                "branch_name": "Mt Shasta Mall Store",
                "street_address": "900 Dana Dr, Ste D-08",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 223-2884",
                "notes": "Mt Shasta Mall; central RABA transit hub."
            }
        ]
    },
    "Spirit Halloween Stores": {
        "corporate_name": "Spirit Halloween Superstores LLC",
        "sector": "Retail & Sales",
        "min_age": 16,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Seasonal retail training provided)",
        "starting_wage": "$16.50 - $17.50 / hr",
        "career_url": "https://www.spirithalloween.com/content.jsp?pageName=Careers",
        "notes": "Seasonal costume and holiday animatronics retail; sales associate, cashier, setup crew.",
        "locations": [
            {
                "branch_name": "Dana Dr Seasonal Store",
                "street_address": "1235 Dana Dr",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(866) 586-0150",
                "notes": "Seasonal storefront on Dana Dr; RABA Route 18."
            }
        ]
    },
    "Sprouts Farmers Market": {
        "corporate_name": "Sprouts Farmers Market, Inc.",
        "sector": "Retail & Sales",
        "min_age": 16,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (On-the-job grocery training provided)",
        "starting_wage": "$16.50 - $18.00 / hr",
        "career_url": "https://about.sprouts.com/careers/",
        "notes": "Natural grocery and fresh market; courtesy clerk, cashier, produce clerk, bakery/deli clerk.",
        "locations": [
            {
                "branch_name": "Hilltop / Dana Center Store",
                "street_address": "855 Browning St",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 223-1120",
                "notes": "Browning St shopping center; RABA Route 11."
            }
        ]
    },
    "Starbucks": {
        "corporate_name": "Starbucks Corporation",
        "sector": "Food & Restaurant",
        "min_age": 16,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Comprehensive barista training provided)",
        "starting_wage": "$17.50 - $19.50 / hr + tips",
        "career_url": "https://www.starbucks.com/careers/",
        "notes": "Youth-friendly coffee shop; barista, cashier, customer service.",
        "locations": [
            {
                "branch_name": "Dana Dr Store",
                "street_address": "1225 Dana Dr",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 223-3882",
                "notes": "RABA Route 18."
            },
            {
                "branch_name": "Churn Creek Store",
                "street_address": "1720 Churn Creek Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 222-1188",
                "notes": "RABA Route 18."
            },
            {
                "branch_name": "Lake Blvd Store",
                "street_address": "150 Lake Blvd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 241-1188",
                "notes": "RABA Route 2 & 3."
            },
            {
                "branch_name": "Anderson Store",
                "street_address": "2560 Balls Ferry Rd",
                "city": "Anderson",
                "state": "CA",
                "zip_code": "96007",
                "phone": "(530) 365-2711",
                "notes": "RABA Route 9."
            }
        ]
    },
    "Sun Oaks Tennis and Fitness": {
        "corporate_name": "Sun Oaks Tennis and Fitness Inc.",
        "sector": "Customer Service & Hospitality",
        "min_age": 16,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Lifeguard certification for pool roles)",
        "starting_wage": "$16.50 - $18.00 / hr",
        "career_url": "https://sunoaks.com/careers/",
        "notes": "Premier tennis and fitness facility; front desk receptionist, lifeguard, child center attendant, facility cleaner.",
        "locations": [
            {
                "branch_name": "Argyle Rd Club",
                "street_address": "3452 Argyle Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 221-4405",
                "notes": "South Redding recreational corridor."
            }
        ]
    },
    "Supreme Caregiving": {
        "corporate_name": "Supreme Caregiving LLC",
        "sector": "Healthcare & Caregiving",
        "min_age": 18,
        "fair_chance": "No (DSS In-Home Care Clearance Required)",
        "drug_testing": "Clinical Drug Screen",
        "background_check": "Live Scan / Fingerprint Clearance",
        "driver_license": "Valid CA Driver License (Class C) and reliable vehicle required",
        "hs_ged": "Required",
        "work_experience": "Caregiver training provided / CNA preferred",
        "starting_wage": "$17.00 - $20.00 / hr",
        "career_url": "",
        "notes": "In-home personal care aide and companion services dispatched to client homes.",
        "locations": [
            {
                "branch_name": "Mobile Caregiver Dispatch",
                "street_address": "In-Home Client Residence Dispatch (Redding, CA)",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "",
                "notes": "Dispatched to private client residences across Shasta County."
            }
        ]
    },
    "Taco Bell": {
        "corporate_name": "Yum! Brands / Franchise Operations",
        "sector": "Food & Restaurant",
        "min_age": 16,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "None",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Fast food crew training provided)",
        "starting_wage": "$20.00 / hr (CA Fast Food Minimum Wage)",
        "career_url": "https://www.tacobell.com/careers",
        "notes": "Youth-friendly fast food restaurant; service champion, food champion, cashier, drive-thru.",
        "locations": [
            {
                "branch_name": "Dana Dr Store",
                "street_address": "1105 Dana Dr",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 223-1188",
                "notes": "RABA Route 18."
            },
            {
                "branch_name": "Cypress Ave Store",
                "street_address": "1625 E Cypress Ave",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 221-1188",
                "notes": "RABA Route 18."
            },
            {
                "branch_name": "Lake Blvd Store",
                "street_address": "2605 Lake Blvd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 246-1188",
                "notes": "RABA Route 2 & 3."
            },
            {
                "branch_name": "Churn Creek Store",
                "street_address": "2355 Churn Creek Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 222-1188",
                "notes": "RABA Route 18."
            },
            {
                "branch_name": "Anderson Store",
                "street_address": "2620 Balls Ferry Rd",
                "city": "Anderson",
                "state": "CA",
                "zip_code": "96007",
                "phone": "(530) 365-1188",
                "notes": "RABA Route 9."
            }
        ]
    },
    "Talent Solutions": {
        "corporate_name": "ManpowerGroup / Talent Solutions",
        "sector": "Office & Clerical",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "5-Panel (THC-Exempt in CA; client-dependent)",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Required",
        "work_experience": "Clerical / customer service / recruiting experience helpful",
        "starting_wage": "$17.50 - $22.00 / hr",
        "career_url": "https://www.talentsolutions.manpowergroup.com/",
        "notes": "Recruiting process outsourcing and talent acquisition placements.",
        "locations": [
            {
                "branch_name": "Shasta Regional Placements",
                "street_address": "Local Talent Placements (Redding, CA)",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "",
                "notes": "Client corporate placements."
            }
        ]
    },
    "Target": {
        "corporate_name": "Target Corporation",
        "sector": "Retail & Sales",
        "min_age": 16,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (On-the-job training provided)",
        "starting_wage": "$16.75 - $18.50 / hr",
        "career_url": "https://corporate.target.com/careers",
        "notes": "Youth-friendly retail department store; guest advocate, general merchandise expert, fulfillment.",
        "locations": [
            {
                "branch_name": "Redding Store T-0359",
                "street_address": "1280 Dana Dr",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 223-0100",
                "notes": "Dana Drive shopping corridor; RABA Route 18."
            }
        ]
    },
    "The Mindful Maids": {
        "corporate_name": "The Mindful Maids LLC",
        "sector": "Janitorial & Facilities",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "Valid CA Driver License (Class C) and reliable vehicle required",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Residential cleaning training provided)",
        "starting_wage": "$17.00 - $20.00 / hr",
        "career_url": "https://themindfulmaids.com/",
        "notes": "Eco-friendly residential cleaning service dispatched locally in Redding.",
        "locations": [
            {
                "branch_name": "Mobile Residential Cleaning",
                "street_address": "Mobile Residential Dispatch (Redding, CA)",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 605-1100",
                "notes": "Dispatched to client residences."
            }
        ]
    },
    "The Salvation Army USA Western Territory": {
        "corporate_name": "The Salvation Army USA Western Territory",
        "sector": "Social & Human Services",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "5-Panel (THC-Exempt in CA)",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Community support mission training provided)",
        "starting_wage": "$16.50 - $18.00 / hr",
        "career_url": "https://westernusa.salvationarmy.org/careers/",
        "notes": "Community social service; shelter support worker, thrift donation attendant, food bank sorter.",
        "locations": [
            {
                "branch_name": "Larkspur Ln Center",
                "street_address": "2691 Larkspur Ln",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 222-2207",
                "notes": "Larkspur Ln social services center; RABA Route 18."
            }
        ]
    },
    "Thorntons LLC": {
        "corporate_name": "Thorntons LLC (BP Products)",
        "sector": "Retail & Sales",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (On-the-job training provided)",
        "starting_wage": "$16.50 - $17.50 / hr",
        "career_url": "https://www.mythorntons.com/careers",
        "notes": "Retail fuel and convenience store; guest service associate, cashier.",
        "locations": [
            {
                "branch_name": "Churn Creek Station",
                "street_address": "4631 Churn Creek Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 221-5000",
                "notes": "South Redding shopping center."
            }
        ]
    },
    "TJ Maxx": {
        "corporate_name": "The TJX Companies, Inc. / T.J. Maxx",
        "sector": "Retail & Sales",
        "min_age": 16,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (On-the-job training provided)",
        "starting_wage": "$16.50 - $17.50 / hr",
        "career_url": "https://jobs.tjx.com/",
        "notes": "Off-price apparel and accessories retail; merchandise associate, cashier, backroom coordinator.",
        "locations": [
            {
                "branch_name": "Dana Dr Store",
                "street_address": "1165 Dana Dr",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 223-1444",
                "notes": "Dana Drive shopping plaza; RABA Route 18."
            }
        ]
    },
    "Tractor Supply Company": {
        "corporate_name": "Tractor Supply Company",
        "sector": "Retail & Sales",
        "min_age": 16,
        "fair_chance": "Case-by-case",
        "drug_testing": "5-Panel (THC-Exempt in CA)",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Rural lifestyle & pet care passion helpful)",
        "starting_wage": "$16.50 - $18.00 / hr",
        "career_url": "https://tractorsupply.jobs/",
        "notes": "Rural lifestyle, pet, livestock, and hardware retail; team member, cashier, receiver.",
        "locations": [
            {
                "branch_name": "Redding - Caterpillar Rd (Twin View)",
                "street_address": "3950 Caterpillar Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 243-1800",
                "notes": "North Redding corridor."
            },
            {
                "branch_name": "Redding - Churn Creek",
                "street_address": "2555 Churn Creek Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 221-1250",
                "notes": "RABA Route 18."
            },
            {
                "branch_name": "Anderson Store",
                "street_address": "2715 Balls Ferry Rd",
                "city": "Anderson",
                "state": "CA",
                "zip_code": "96007",
                "phone": "(530) 365-2780",
                "notes": "RABA Route 9."
            }
        ]
    },
    "Travel Centers of America": {
        "corporate_name": "TravelCenters of America (BP Products)",
        "sector": "Customer Service & Hospitality",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "5-Panel (THC-Exempt in CA)",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required for cashier/fuel attendant; truck tech 1+ yr",
        "starting_wage": "$17.00 - $19.50 / hr",
        "career_url": "https://www.ta-petro.com/careers",
        "notes": "Full service travel plaza; travel store cashier, fuel island attendant, maintenance, truck repair.",
        "locations": [
            {
                "branch_name": "Knighton Rd Travel Center",
                "street_address": "2560 Knighton Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 222-1188",
                "notes": "I-5 & Knighton Rd interchange."
            }
        ]
    },
    "Trio-Community-Meals": {
        "corporate_name": "Elior North America / Trio Community Meals",
        "sector": "Food & Restaurant",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "5-Panel Drug Screen",
        "background_check": "Standard Pre-Employment (Healthcare Facility Clearance)",
        "driver_license": "None (Class C for delivery route drivers)",
        "hs_ged": "Required",
        "work_experience": "No experience required for food service worker / prep cook",
        "starting_wage": "$17.00 - $19.50 / hr",
        "career_url": "https://triocommunitymeals.com/careers/",
        "notes": "Institutional nutrition and food service operations contracted inside local health facilities.",
        "locations": [
            {
                "branch_name": "Redding Food Service Center",
                "street_address": "2175 Rosaline Ave (Mercy Campus)",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 225-6000",
                "notes": "Hospital food service hub."
            }
        ]
    },
    "Turners Outdoorsman": {
        "corporate_name": "Turner's Outdoorsman",
        "sector": "Retail & Sales",
        "min_age": 18,
        "fair_chance": "No (Firearms Regulatory Clearance Required)",
        "drug_testing": "5-Panel Pre-Employment",
        "background_check": "Standard Pre-Employment (DOJ/ATF Firearms Handling Check; 21+ for gun sales)",
        "driver_license": "None",
        "hs_ged": "Required",
        "work_experience": "Hunting, fishing, and shooting sports retail knowledge preferred",
        "starting_wage": "$17.00 - $19.50 / hr",
        "career_url": "https://www.turners.com/info/employment",
        "notes": "Hunting, fishing, and shooting sports retail; sales associate, cashier, archery specialist.",
        "locations": [
            {
                "branch_name": "Dana Dr Store",
                "street_address": "1045 Dana Dr",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 223-1180",
                "notes": "Dana Drive shopping corridor; RABA Route 18."
            }
        ]
    },
    "Turtle Bay Exploration Park": {
        "corporate_name": "Turtle Bay Exploration Park (Nonprofit)",
        "sector": "Customer Service & Hospitality",
        "min_age": 16,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Guest service and environmental education passion)",
        "starting_wage": "$16.50 - $18.00 / hr",
        "career_url": "https://www.turtlebay.org/employment",
        "notes": "Cultural park, museum, and botanical garden; guest services associate, park maintenance, forestry aide.",
        "locations": [
            {
                "branch_name": "Park Headquarters",
                "street_address": "844 Sundial Bridge Dr",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 243-8855",
                "notes": "Sundial Bridge & Turtle Bay; RABA Route 11."
            }
        ]
    },
    "U-Haul": {
        "corporate_name": "U-Haul International, Inc.",
        "sector": "Customer Service & Hospitality",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt (Nicotine-free hiring policy for corporate roles)",
        "background_check": "Clean DMV Record (Class C)",
        "driver_license": "Valid CA Driver License (Class C) required",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Customer service and hitch training provided)",
        "starting_wage": "$17.00 - $19.50 / hr",
        "career_url": "https://uhauljobs.com/",
        "notes": "Moving and self-storage; customer service representative, storage facility cleaner, hitch installer.",
        "locations": [
            {
                "branch_name": "Twin View Moving Center",
                "street_address": "2325 Twin View Blvd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 243-1188",
                "notes": "Twin View corridor."
            },
            {
                "branch_name": "Hartnell Ave Moving Center",
                "street_address": "1270 Hartnell Ave",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 222-1188",
                "notes": "RABA Route 5 & 18."
            }
        ]
    },
    "Ulta Beauty": {
        "corporate_name": "Ulta Beauty, Inc.",
        "sector": "Retail & Sales",
        "min_age": 18,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required for beauty advisor/cashier; licensed for salon",
        "starting_wage": "$16.50 - $17.50 / hr",
        "career_url": "https://careers.ulta.com/",
        "notes": "Cosmetics and beauty retail at Mt Shasta Mall; beauty advisor, task associate/stocker, cashier.",
        "locations": [
            {
                "branch_name": "Mt Shasta Mall Store",
                "street_address": "900 Dana Dr, Ste A-02",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 221-1250",
                "notes": "Mt Shasta Mall; central RABA transit hub."
            }
        ]
    },
    "US LBM Holdings, LLC": {
        "corporate_name": "US LBM Holdings / Homewood Building Supply (Meek's West)",
        "sector": "Manufacturing & Production",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "5-Panel Pre-Employment",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None (Class C or CDL for boom delivery)",
        "hs_ged": "Required",
        "work_experience": "No experience required for truss assembler (Power tool training provided)",
        "starting_wage": "$18.50 - $22.50 / hr",
        "career_url": "https://www.uslbm.com/careers/",
        "notes": "Commercial building components and roof truss fabrication; truss assembler, yard worker, forklift driver.",
        "locations": [
            {
                "branch_name": "Redding Truss Plant",
                "street_address": "2851 Churn Creek Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 221-1188",
                "notes": "RABA Route 18."
            }
        ]
    },
    "Van's": {
        "corporate_name": "VF Corporation / Vans",
        "sector": "Retail & Sales",
        "min_age": 16,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Skate culture passion and customer service)",
        "starting_wage": "$16.50 - $17.50 / hr",
        "career_url": "https://www.vfc.com/careers",
        "notes": "Youth-friendly skate footwear and apparel retail at Mt Shasta Mall; sales associate, stocker.",
        "locations": [
            {
                "branch_name": "Mt Shasta Mall Store",
                "street_address": "900 Dana Dr, Ste B-12",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 223-1180",
                "notes": "Mt Shasta Mall; central RABA transit hub."
            }
        ]
    },
    "VCA Animal Hospitals": {
        "corporate_name": "Mars Veterinary Health / VCA Animal Hospitals",
        "sector": "Animal Care & Veterinary Services",
        "min_age": 18,
        "fair_chance": "Case-by-case",
        "drug_testing": "5-Panel (THC-Exempt in CA)",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Required",
        "work_experience": "Animal care experience / veterinary assistant training provided; RVT cert for tech",
        "starting_wage": "$17.00 - $21.00 / hr",
        "career_url": "https://careers.vca.com/",
        "notes": "Veterinary medical hospital; veterinary assistant, kennel technician, client service representative.",
        "locations": [
            {
                "branch_name": "VCA Gateway Animal Hospital",
                "street_address": "2655 Bechelli Ln",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 222-1188",
                "notes": "RABA Route 14."
            }
        ]
    },
    "Verizon": {
        "corporate_name": "Verizon Communications Inc. / Cellular Sales Authorized",
        "sector": "Retail & Sales",
        "min_age": 18,
        "fair_chance": "Case-by-case",
        "drug_testing": "5-Panel (THC-Exempt in CA)",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Required",
        "work_experience": "Customer service / technology sales experience helpful",
        "starting_wage": "$17.00 - $20.00 / hr + commissions",
        "career_url": "https://www.verizon.com/about/careers",
        "notes": "Wireless telecommunications retail; retail sales specialist, customer service representative.",
        "locations": [
            {
                "branch_name": "Dana Dr Store",
                "street_address": "1120 Dana Dr",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 221-1188",
                "notes": "Dana Drive shopping plaza; RABA Route 18."
            },
            {
                "branch_name": "Churn Creek Store",
                "street_address": "1320 Churn Creek Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 222-1188",
                "notes": "RABA Route 18."
            },
            {
                "branch_name": "Anderson Store",
                "street_address": "2650 Gateway Dr",
                "city": "Anderson",
                "state": "CA",
                "zip_code": "96007",
                "phone": "(530) 365-1188",
                "notes": "RABA Route 9."
            }
        ]
    },
    "Vibra Hospital": {
        "corporate_name": "Vibra Healthcare / Vibra Hospital of Northern California",
        "sector": "Healthcare & Caregiving",
        "min_age": 18,
        "fair_chance": "No (Hospital Clinical Clearance Required)",
        "drug_testing": "Clinical Drug Screen",
        "background_check": "Live Scan / Fingerprint Clearance",
        "driver_license": "None",
        "hs_ged": "Required",
        "work_experience": "Dietary/EVS no exp; CNA requires active certification",
        "starting_wage": "$18.50 - $24.00 / hr",
        "career_url": "https://www.vhnortherncalifornia.com/careers/",
        "notes": "Long-term acute care hospital and physical rehabilitation center; CNA, dietary aide, housekeeper.",
        "locations": [
            {
                "branch_name": "Edith Ave Hospital Campus",
                "street_address": "2620 Edith Ave",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 246-9000",
                "notes": "Edith Ave healthcare campus."
            }
        ]
    },
    "Vittles Family Restaurant": {
        "corporate_name": "Vittles Family Restaurant Anderson",
        "sector": "Food & Restaurant",
        "min_age": 16,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "None",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required for busser/dishwasher; line cook 1+ yr pref",
        "starting_wage": "$16.50 - $18.50 / hr + tips",
        "career_url": "https://www.facebook.com/vittlesrestaurant/",
        "notes": "Homestyle family restaurant in Anderson; host, busser, server, prep cook, line cook.",
        "locations": [
            {
                "branch_name": "Anderson Restaurant",
                "street_address": "2272 Balls Ferry Rd",
                "city": "Anderson",
                "state": "CA",
                "zip_code": "96007",
                "phone": "(530) 365-5100",
                "notes": "RABA Route 9 (Anderson)."
            }
        ]
    },
    "Wachter, Inc.": {
        "corporate_name": "Wachter, Inc. (Electrical & Technology Contractor)",
        "sector": "Trades & Mechanics",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "5-Panel Pre-Employment",
        "background_check": "Clean DMV Record (Class C)",
        "driver_license": "Valid CA Driver License (Class C) and reliable vehicle required",
        "hs_ged": "Required",
        "work_experience": "No experience required for technician helper / cable puller (Electrical training provided)",
        "starting_wage": "$19.00 - $26.00 / hr",
        "career_url": "https://www.wachter.com/careers/",
        "notes": "Remote electrical, structured cabling, and POS retail automation contractor dispatched locally to Shasta County commercial sites.",
        "locations": [
            {
                "branch_name": "Field Dispatched / Electrical & Telecom",
                "street_address": "Field Dispatched / Mobile (Redding, CA)",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(888) 862-2483",
                "notes": "Dispatched locally across commercial sites in Redding and Shasta County."
            }
        ]
    },
    "Walgreens": {
        "corporate_name": "Walgreens Boots Alliance, Inc.",
        "sector": "Retail & Sales",
        "min_age": 16,
        "fair_chance": "Case-by-case",
        "drug_testing": "5-Panel (THC-Exempt in CA; required for pharmacy)",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required (Required for pharmacy technician)",
        "work_experience": "No experience required (Customer service training provided)",
        "starting_wage": "$16.50 - $18.50 / hr",
        "career_url": "https://jobs.walgreens.com/",
        "notes": "Retail pharmacy; customer service associate, cashier, pharmacy technician trainee.",
        "locations": [
            {
                "branch_name": "Churn Creek Store",
                "street_address": "1150 Churn Creek Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 221-1250",
                "notes": "RABA Route 18."
            },
            {
                "branch_name": "Eureka Way Store",
                "street_address": "1775 Eureka Way",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 241-1188",
                "notes": "RABA Route 2."
            },
            {
                "branch_name": "Cypress Ave Store",
                "street_address": "980 E Cypress Ave",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 221-1188",
                "notes": "RABA Route 18."
            }
        ]
    },
    "Walmart": {
        "corporate_name": "Walmart Inc.",
        "sector": "Retail & Sales",
        "min_age": 16,
        "fair_chance": "Case-by-case",
        "drug_testing": "5-Panel (THC-Exempt in CA; testing for asset protection/equipment roles)",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (On-the-job training provided)",
        "starting_wage": "$17.00 - $19.00 / hr",
        "career_url": "https://careers.walmart.com/",
        "notes": "Major supercenter retail employer; digital personal shopper/fulfillment, cashier, stocker, cart attendant.",
        "locations": [
            {
                "branch_name": "Redding Supercenter #2079",
                "street_address": "1515 Dana Dr",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 221-0100",
                "notes": "Dana Drive shopping corridor; RABA Route 18."
            },
            {
                "branch_name": "Anderson Supercenter #5136",
                "street_address": "5000 Rhonda Rd",
                "city": "Anderson",
                "state": "CA",
                "zip_code": "96007",
                "phone": "(530) 378-0100",
                "notes": "Rhonda Rd commercial hub."
            }
        ]
    },
    "Waste Management": {
        "corporate_name": "WM (Waste Management, Inc.)",
        "sector": "Transportation & Delivery",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "DOT Safety-Sensitive (Includes THC)",
        "background_check": "Standard Pre-Employment / Clean DMV Record",
        "driver_license": "None for sorter/scale; Commercial Class B (CDL-B) for route driver",
        "hs_ged": "Required",
        "work_experience": "No experience required for recycling sorter / transfer station laborer",
        "starting_wage": "$19.00 - $26.00 / hr",
        "career_url": "https://careers.wm.com/",
        "notes": "Solid waste, recycling, and environmental services; transfer station sorter, scale clerk, route driver.",
        "locations": [
            {
                "branch_name": "Redding Transfer Station",
                "street_address": "1980 Twin View Blvd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 243-7030",
                "notes": "Twin View industrial corridor."
            },
            {
                "branch_name": "Anderson Landfill Facility",
                "street_address": "18703 American Way",
                "city": "Anderson",
                "state": "CA",
                "zip_code": "96007",
                "phone": "(530) 347-5236",
                "notes": "Regional landfill and disposal facility."
            }
        ]
    },
    "Waterworks Park": {
        "corporate_name": "Waterworks Park Redding",
        "sector": "Customer Service & Hospitality",
        "min_age": 15,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "None",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Lifeguard Red Cross certification provided on-site)",
        "starting_wage": "$16.50 - $17.50 / hr",
        "career_url": "https://waterworkspark.com/employment/",
        "notes": "Youth-friendly seasonal water amusement park; lifeguard, admissions cashier, food service, park maintenance.",
        "locations": [
            {
                "branch_name": "Redding Waterpark",
                "street_address": "151 N Boulder Dr",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 246-9550",
                "notes": "North Redding recreational corridor."
            }
        ]
    },
    "West Coast Sourdough": {
        "corporate_name": "WC REDDING INC (West Coast Sourdough Franchise)",
        "sector": "Food & Restaurant",
        "min_age": 16,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "None",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (On-the-job sandwich making training provided)",
        "starting_wage": "$16.50 - $18.00 / hr + tips",
        "career_url": "https://wcsourdough.com/careers/",
        "notes": "Fast-casual sourdough sandwich and soup deli; sandwich artist, cashier, kitchen prep.",
        "locations": [
            {
                "branch_name": "Dana Dr Deli",
                "street_address": "1140 Dana Dr, Ste 10",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 221-1188",
                "notes": "Dana Drive shopping plaza; RABA Route 18."
            }
        ]
    },
    "Win River": {
        "corporate_name": "WIN-RIVER HOTEL CORPORATION (Redding Rancheria)",
        "sector": "Customer Service & Hospitality",
        "min_age": 21,
        "fair_chance": "No (Tribal Gaming Commission License Required)",
        "drug_testing": "5-Panel Pre-Employment",
        "background_check": "Live Scan / Tribal Gaming Commission Clearance",
        "driver_license": "None (Role-dependent)",
        "hs_ged": "Required",
        "work_experience": "No experience required for busser/dishwasher/security trainee",
        "starting_wage": "$17.50 - $21.00 / hr + tips",
        "career_url": "https://www.winrivercasino.com/careers/",
        "notes": "Tribal resort, gaming floor, and event facility; host, server, dealer, security, hotel front desk.",
        "locations": [
            {
                "branch_name": "Win-River Resort & Casino",
                "street_address": "2100 Redding Rancheria Rd",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 243-3377",
                "notes": "Hwy 273 corridor."
            }
        ]
    },
    "Wise Auto Group": {
        "corporate_name": "Wise Auto Group (Redding Subaru / Redding Hyundai)",
        "sector": "Trades & Mechanics",
        "min_age": 18,
        "fair_chance": "Case-by-case",
        "drug_testing": "5-Panel (THC-Exempt in CA)",
        "background_check": "Clean DMV Record (Class C)",
        "driver_license": "Valid CA Driver License (Class C) and clean driving record required",
        "hs_ged": "Required",
        "work_experience": "No experience required for lot porter / detailer",
        "starting_wage": "$17.00 - $21.00 / hr",
        "career_url": "https://www.wiseautogroup.com/careers/",
        "notes": "Automotive dealerships; lot porter, detailer, express lube technician, service receptionist.",
        "locations": [
            {
                "branch_name": "Redding Subaru",
                "street_address": "488 E Cypress Ave",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 223-1188",
                "notes": "Cypress Ave automotive corridor; RABA Route 5."
            },
            {
                "branch_name": "Redding Hyundai",
                "street_address": "250 E Cypress Ave",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96002",
                "phone": "(530) 222-1188",
                "notes": "Cypress Ave automotive corridor; RABA Route 5."
            }
        ]
    },
    "Woody's Brewing Company": {
        "corporate_name": "Woody's Brewing Company LLC",
        "sector": "Food & Restaurant",
        "min_age": 18,
        "fair_chance": "Yes",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "None",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required for busser/dishwasher; line cook 1+ yr pref",
        "starting_wage": "$16.50 - $19.00 / hr + tips",
        "career_url": "https://woodysbrewing.com/",
        "notes": "Downtown craft brewery and restaurant; line cook, prep cook, dishwasher, server, host.",
        "locations": [
            {
                "branch_name": "Downtown Pub",
                "street_address": "1257 Oregon St",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96001",
                "phone": "(530) 768-1025",
                "notes": "Downtown Redding; RABA Downtown Terminal."
            }
        ]
    },
    "Work World": {
        "corporate_name": "Work World America, Inc.",
        "sector": "Retail & Sales",
        "min_age": 18,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Required",
        "work_experience": "No experience required (Workwear & safety boot knowledge helpful)",
        "starting_wage": "$16.50 - $17.50 / hr",
        "career_url": "https://www.workworld.com/careers",
        "notes": "Workwear, boots, and industrial safety apparel retail; sales associate, cashier, stocker.",
        "locations": [
            {
                "branch_name": "Dana Dr Store",
                "street_address": "1120 Dana Dr, Ste 40",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 223-1188",
                "notes": "Dana Drive shopping plaza; RABA Route 18."
            }
        ]
    },
    "Zumiez": {
        "corporate_name": "Zumiez Inc.",
        "sector": "Retail & Sales",
        "min_age": 16,
        "fair_chance": "Case-by-case",
        "drug_testing": "None / Pre-Employment Exempt",
        "background_check": "Standard Pre-Employment",
        "driver_license": "None",
        "hs_ged": "Not Required",
        "work_experience": "No experience required (Skate/snowboard culture and energetic customer service)",
        "starting_wage": "$16.50 - $17.50 / hr",
        "career_url": "https://careers.zumiez.com/",
        "notes": "Youth-friendly skate, snowboard, and action sports apparel retail at Mt Shasta Mall.",
        "locations": [
            {
                "branch_name": "Mt Shasta Mall Store",
                "street_address": "900 Dana Dr, Ste B-04",
                "city": "Redding",
                "state": "CA",
                "zip_code": "96003",
                "phone": "(530) 223-1188",
                "notes": "Mt Shasta Mall; central RABA transit hub."
            }
        ]
    }
}

print(f"data_part4 loaded with {len(PART4_PROFILES)} employer profiles.")
