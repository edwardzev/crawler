import os
import requests
import json
import random

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

def get_samples():
    params = [
        ("pageSize", "50"),
        ("fields[]", "sku"), 
        ("fields[]", "description"),
        ("fields[]", "short_description")
    ]
    # Note: Checking common field names. 'Name' is usually primary. 'description' was seen in schema.
    
    try:
        r = requests.get(API_URL, headers=HEADERS, params=params)
        r.raise_for_status()
        data = r.json()
        records = data.get("records", [])
        
        print(f"Fetched {len(records)} records. Showing 10 random samples:\n")
        
        sample = random.sample(records, min(len(records), 10))
        
        for i, rec in enumerate(sample, 1):
            fields = rec.get("fields", {})
            name = fields.get("Name", "N/A")
            desc = fields.get("description", "N/A")[:200] # Truncate for readability
            print(f"{i}. NAME: {name}")
            print(f"   DESC: {desc}...")
            print("-" * 40)
            
    except Exception as e:
        print(f"Error: {e}")
        try:
            print(f"Response: {r.text}")
        except:
            pass

if __name__ == "__main__":
    get_samples()
