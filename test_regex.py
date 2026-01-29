import re

def test_age_regex():
    text = """
    Do you love to smile and provide great guest service?   As a team member you will be an ambassador by providing friendly and courteous service by greeting each guest with a smile and making them feel welcome. Responsibilities include:
    Thinking in a Food Safety mindset
    Cashiering at Front Counter and Drive Thru
    Food prep, cooking, and assembly of produce, lunch, and dinner products
    Preparing our World Famous Chili
    Serving guests in the dining room and patio
    General cleaning (All interior and exterior areas of restaurant)
    General opening and closing duties
    Collaborate with team members and fulfill our mission: Serving Food to Serve Others
    You will enjoy a fast-paced team environment whether you’re working in the drive thru, kitchen, or crafting our delicious desserts. Either way, your job will be to ensure great guest service 100% of the time!
    This restaurant is independently owned and operated.
    Required qualifications:
    Legally authorized to work in the United States
    Preferred qualifications:
    16 years or older
    """
    
    age_patterns = [
        r'(\d{2})\s*years\s*(?:or)?\s*older',
        r'must\s*be\s*(\d{2})',
        r'minimum\s*age\s*(\d{2})',
        r'(\d{2})\+',
        r'at\s*least\s*(\d{2})'
    ]
    
    print("Testing Regex on Text:")
    for pattern in age_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            print(f"Matched pattern '{pattern}': {match.group(1)}")
            return
            
    print("No match found.")

if __name__ == "__main__":
    test_age_regex()
