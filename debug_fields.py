import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Orders"
ORDER_ID = "rectSFt7YtVxsHiYS" # valid ID from previous step
URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/{ORDER_ID}"

headers = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

fields_to_test = {
    "Graphic 1": [{"url": "https://via.placeholder.com/150"}],
    "Width 1 cm": 15,
    "Number 1": 10,
    "Notes to Design": "Test Note",
    "Width 1": 15, # alternative
    "Quantity 1": 10, # alternative
    "Logo 1": [{"url": "https://via.placeholder.com/150"}] # alternative
}

for field_name, value in fields_to_test.items():
    print(f"Testing field: {field_name}...")
    payload = {"fields": {field_name: value}}
    try:
        r = requests.patch(URL, headers=headers, json=payload)
        if r.status_code == 200:
            print(f"SUCCESS: {field_name}")
        else:
            print(f"FAILED: {field_name} -> {r.status_code} {r.text}")
    except Exception as e:
        print(f"ERROR: {field_name} -> {e}")
