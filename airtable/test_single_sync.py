import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

def test_sync():
    # Test record
    fields = {
        "catalog_id": "test:sync-v3",
        "product_id": "test:sync-v3",
        "supplier": "Comfort Gifts",
        "title": "Agent Sync Test V3",
        "status": "Inactive"
    }
    
    payload = {
        "performUpsert": {
            "fieldsToMergeOn": ["catalog_id"]
        },
        "records": [{"fields": fields}]
    }
    
    print("Sending test record...")
    r = requests.patch(API_URL, headers=HEADERS, json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")

if __name__ == "__main__":
    test_sync()
