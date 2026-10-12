import os
import unittest
import tempfile
import json
import sqlite3
import shutil

from employer_db import (
    init_db,
    upsert_employer,
    upsert_location,
    get_employer,
    get_all_employers,
    export_to_json,
    load_fast_cache,
    match_employer,
    resolve_branch_location,
    normalize_name,
    log_unregistered_employer,
    get_unregistered_employers
)

class TestEmployerDB(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_employers.db")
        self.cache_path = os.path.join(self.test_dir, "test_cache.json")
        init_db(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_normalize_name(self):
        self.assertEqual(normalize_name("McDonald's, LLC"), "mcdonalds")
        self.assertEqual(normalize_name("Ace Hardware Corp."), "ace hardware")
        self.assertEqual(normalize_name("In-N-Out Burger Inc"), "in-n-out burger")
        self.assertEqual(normalize_name("Blach Beverage LLC"), "blach beverage")

    def test_upsert_employer_and_locations(self):
        emp_data = {
            "name": "Ace Hardware",
            "aliases": ["Ace", "Redding Ace Hardware"],
            "industry_sector": "Retail & Sales",
            "min_age_baseline": 16,
            "hs_ged_baseline": "No",
            "felon_friendly": "Case-by-Case",
            "drug_testing": "None",
            "background_check": "None"
        }
        emp_id = upsert_employer(emp_data, db_path=self.db_path)
        self.assertIsInstance(emp_id, int)

        # Add Branch 1 (Hartnell)
        loc1 = {
            "location_name": "Hartnell Store",
            "street_address": "1350 Hartnell Ave, Redding, CA 96002",
            "city": "Redding",
            "zip_code": "96002",
            "phone": "530-221-1234",
            "manager_name": "Dave Miller",
            "is_primary": True
        }
        loc1_id = upsert_location(emp_id, loc1, db_path=self.db_path)
        self.assertIsInstance(loc1_id, int)

        # Add Branch 2 (Westside)
        loc2 = {
            "location_name": "Westside Store",
            "street_address": "4490 Westside Rd, Redding, CA 96001",
            "city": "Redding",
            "zip_code": "96001",
            "phone": "530-241-5678",
            "manager_name": "Sarah Connor",
            "is_primary": False
        }
        loc2_id = upsert_location(emp_id, loc2, db_path=self.db_path)
        self.assertIsInstance(loc2_id, int)

        # Retrieve and verify
        emp = get_employer(emp_id, db_path=self.db_path)
        self.assertEqual(emp["name"], "Ace Hardware")
        self.assertEqual(len(emp["locations"]), 2)
        self.assertEqual(emp["industry_sector"], "Retail & Sales")

    def test_export_and_matching(self):
        # Insert Ace Hardware with 2 locations
        emp1_id = upsert_employer({
            "name": "Ace Hardware",
            "aliases": ["Ace"],
            "industry_sector": "Retail & Sales",
            "min_age_baseline": 16
        }, db_path=self.db_path)

        upsert_location(emp1_id, {
            "location_name": "Hartnell Store",
            "street_address": "1350 Hartnell Ave, Redding, CA 96002",
            "phone": "530-221-1234",
            "manager_name": "Dave Miller",
            "is_primary": True
        }, db_path=self.db_path)

        upsert_location(emp1_id, {
            "location_name": "Westside Store",
            "street_address": "4490 Westside Rd, Redding, CA 96001",
            "phone": "530-241-5678",
            "manager_name": "Sarah Connor",
            "is_primary": False
        }, db_path=self.db_path)

        # Insert In-N-Out Burger
        emp2_id = upsert_employer({
            "name": "In-N-Out Burger",
            "aliases": ["In-N-Out", "In N Out"],
            "industry_sector": "Food & Restaurant",
            "min_age_baseline": 16,
            "felon_friendly": "Yes"
        }, db_path=self.db_path)

        upsert_location(emp2_id, {
            "street_address": "1275 Dana Dr, Redding, CA 96002",
            "phone": "800-786-1000",
            "is_primary": True
        }, db_path=self.db_path)

        # Export to JSON cache
        export_to_json(json_path=self.cache_path, db_path=self.db_path)
        load_fast_cache(json_path=self.cache_path, force_reload=True)

        # Test exact match
        emp, loc = match_employer("Ace Hardware", json_path=self.cache_path)
        self.assertIsNotNone(emp)
        self.assertEqual(emp["name"], "Ace Hardware")
        self.assertEqual(loc["phone"], "530-221-1234")

        # Test corporate suffix stripping match
        emp, loc = match_employer("In-N-Out Burger, LLC", json_path=self.cache_path)
        self.assertIsNotNone(emp)
        self.assertEqual(emp["name"], "In-N-Out Burger")

        # Test alias match
        emp, loc = match_employer("In N Out", json_path=self.cache_path)
        self.assertIsNotNone(emp)
        self.assertEqual(emp["name"], "In-N-Out Burger")

        # Test multi-location resolution based on address hint
        emp, loc = match_employer("Ace Hardware", location_hint="4490 Westside Rd", json_path=self.cache_path)
        self.assertEqual(loc["manager_name"], "Sarah Connor")
        self.assertEqual(loc["street_address"], "4490 Westside Rd, Redding, CA 96001")

        # Test unregistered employer logging
        emp, loc = match_employer("Unknown Mysterious Employer LLC", json_path=self.cache_path)
        self.assertIsNone(emp)

        log_unregistered_employer("Unknown Mysterious Employer LLC", "Warehouse Sorter", "Redding, CA", db_path=self.db_path)
        unreg = get_unregistered_employers(db_path=self.db_path)
        self.assertEqual(len(unreg), 1)
        self.assertEqual(unreg[0]["name"], "Unknown Mysterious Employer LLC")

if __name__ == "__main__":
    unittest.main()
