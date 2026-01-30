#!/usr/bin/env python3
"""
Fix Comfort product IDs in Airtable by removing '-gifts' suffix.
Changes 'comfort-gifts:XXXX' to 'comfort:XXXX'
"""
import os
import requests
import time
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

def airtable_request(method: str, url: str, params: list = None, json_data: dict = None) -> dict:
    max_retries = 5
    for attempt in range(max_retries):
        try:
            r = requests.request(method, url, headers=HEADERS, params=params, json=json_data)
            if r.status_code == 429:
                wait = (2 ** attempt) + 1
                print(f"Rate limit hit. Retrying in {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Permanent error: {e}")
                raise e
            time.sleep(1)
    return {}

def fix_comfort_ids():
    print("Fetching Comfort records from Airtable...")
    
    # Fetch all Comfort records
    records = []
    offset = None
    
    while True:
        params = [
            ("pageSize", "100"),
            ("filterByFormula", "{supplier}='Comfort'"),
            ("fields[]", "product_id"),
            ("fields[]", "catalog_id")
        ]
        if offset:
            params.append(("offset", offset))
        
        data = airtable_request("GET", API_URL, params=params)
        records.extend(data.get("records", []))
        offset = data.get("offset")
        print(f"Fetched {len(records)} records...", end="\r")
        if not offset:
            break
    
    print(f"\nFound {len(records)} Comfort records")
    
    # Prepare updates
    updates = []
    for rec in records:
        rec_id = rec['id']
        fields = rec.get('fields', {})
        product_id = fields.get('product_id', '')
        catalog_id = fields.get('catalog_id', '')
        
        # Check if update is needed
        if 'comfort-gifts:' in product_id or 'comfort-gifts:' in catalog_id:
            new_product_id = product_id.replace('comfort-gifts:', 'comfort:')
            new_catalog_id = catalog_id.replace('comfort-gifts:', 'comfort:')
            
            updates.append({
                "id": rec_id,
                "fields": {
                    "product_id": new_product_id,
                    "catalog_id": new_catalog_id
                }
            })
    
    print(f"Prepared {len(updates)} updates")
    
    if not updates:
        print("No updates needed!")
        return
    
    # Batch update
    print("Starting batch updates...")
    batch_size = 10
    total_batches = (len(updates) // batch_size) + 1
    
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        try:
            airtable_request("PATCH", API_URL, json_data={"records": batch})
            print(f"Updated batch {i//batch_size + 1}/{total_batches}")
            time.sleep(0.5)
        except Exception as e:
            print(f"Error updating batch: {e}")
    
    print("✅ All Comfort IDs updated successfully!")

if __name__ == "__main__":
    fix_comfort_ids()
