import os
import unittest
import json
from app import app
import employer_db
from gemini_parser import compare_job_with_employer_baseline, JobAnalysisResult
from scrapper import resolve_business_address

class TestEmployerIntegration(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_api_get_employers(self):
        """Verify GET /api/employers returns the 150+ seeded employers with branches."""
        res = self.client.get('/api/employers')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["total"], 100)
        
        # Test search filter for Ace Hardware
        res_ace = self.client.get('/api/employers?q=Ace')
        data_ace = res_ace.get_json()
        self.assertTrue(any(e["name"] == "Ace Hardware" for e in data_ace["employers"]))

    def test_api_employer_crud(self):
        """Verify POST /api/employers creates/updates and GET /api/employers/<id> retrieves."""
        new_emp = {
            "name": "Integration Test Cafe",
            "aliases": ["Test Cafe"],
            "industry_sector": "Food & Restaurant",
            "min_age_baseline": 16,
            "hs_ged_baseline": "No",
            "felon_friendly": "Yes",
            "drug_testing": "None",
            "background_check": "None",
            "locations": [
                {
                    "location_name": "Downtown Branch",
                    "street_address": "1500 Market St, Redding, CA 96001",
                    "city": "Redding",
                    "zip_code": "96001",
                    "phone": "530-222-9999",
                    "manager_name": "Bob Builder",
                    "is_primary": True
                }
            ]
        }
        res_post = self.client.post('/api/employers', json=new_emp)
        self.assertEqual(res_post.status_code, 200)
        post_data = res_post.get_json()
        self.assertEqual(post_data["status"], "success")
        emp_id = post_data["employer"]["id"]

        # Retrieve detail
        res_get = self.client.get(f'/api/employers/{emp_id}')
        self.assertEqual(res_get.status_code, 200)
        get_data = res_get.get_json()
        self.assertEqual(get_data["employer"]["name"], "Integration Test Cafe")
        self.assertEqual(len(get_data["employer"]["locations"]), 1)
        self.assertEqual(get_data["employer"]["locations"][0]["phone"], "530-222-9999")

    def test_compare_job_with_employer_baseline(self):
        """Verify baseline comparison reconciles baseline policies and posting specifics."""
        baseline = {
            "name": "Ace Hardware",
            "industry_sector": "Retail & Sales",
            "street_address": "1350 Hartnell Ave, Redding, CA 96002",
            "min_age_baseline": 16,
            "hs_ged_baseline": "No",
            "felon_friendly": "Case-by-Case",
            "background_check": "None",
            "drug_testing": "None",
            "drivers_license": "None"
        }
        res = compare_job_with_employer_baseline(
            title="Cashier / Customer Service",
            company="Ace Hardware",
            location="1350 Hartnell Ave, Redding, CA",
            description_text="Customer checkout, stocking shelves. No diploma required. Min age 16.",
            employer_baseline=baseline,
            raw_pay="$16.90 / hr"
        )
        self.assertIsNotNone(res)
        self.assertTrue(isinstance(res, JobAnalysisResult))
        self.assertTrue(res.is_entry_level)
        self.assertEqual(res.sector, "Retail & Sales")
        self.assertEqual(res.business_address, "1350 Hartnell Ave, Redding, CA 96002")

    def test_scrapper_address_resolution_integration(self):
        """Verify resolve_business_address matches through employer_db."""
        addr = resolve_business_address("Ace Hardware", location="Redding, CA", description="1350 Hartnell Ave store")
        self.assertIn("Hartnell", addr)

if __name__ == '__main__':
    unittest.main()
