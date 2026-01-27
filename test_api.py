import requests
import json

try:
    print("Sending POST request to /generate...")
    response = requests.post('http://127.0.0.1:5000/generate', timeout=300)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
