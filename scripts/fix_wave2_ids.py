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

def fix_wave2_ids():
    print("Fetching Wave2 records with hash-based IDs...")
    
    records = []
    offset = None
    while True:
        # Filter for Wave2 records where product_id looks like a hash (40 chars)
        # OR just filter all Wave2 and we'll check in Python.
        params = [
            ("pageSize", "100"),
            ("fields[]", "sku"),
            ("fields[]", "supplier"),
            ("fields[]", "product_id"),
            ("filterByFormula", "{supplier}='Wave2'")
        ]
        if offset:
            params.append(("offset", offset))
            
        try:
            r = requests.get(API_URL, headers=HEADERS, params=params)
            r.raise_for_status()
            data = r.json()
            records.extend(data.get("records", []))
            offset = data.get("offset")
            print(f"Fetched {len(records)}...", end="\r")
            if not offset: break
        except Exception as e:
            print(f"Error: {e}")
            return

    print(f"\nTotal Wave2 records: {len(records)}")
    
    to_update = []
    for rec in records:
        f = rec.get("fields", {})
        pid = f.get("product_id", "")
        sku = f.get("sku")
        supplier = f.get("supplier", "Wave2")
        rid = rec.get("id")
        
        # Check if ID is a hash (hex, 40 chars)
        if len(pid) == 40 and all(c in "0123456789abcdefABCDEF" for c in pid):
            # Generate new standardized ID
            new_pid = f"{supplier.lower()}:{sku}"
            to_update.append({
                "id": rid,
                "fields": {
                    "product_id": new_pid,
                    "catalog_id": new_pid
                }
            })
            
    print(f"Found {len(to_update)} records to fix.")
    
    if not to_update:
        return

    # Update in batches
    batch_size = 10
    total_batches = (len(to_update) + batch_size - 1) // batch_size
    for i in range(0, len(to_update), batch_size):
        batch = to_update[i:i+batch_size]
        payload = {"records": batch}
        try:
            r = requests.patch(API_URL, headers=HEADERS, json=payload)
            r.raise_for_status()
            print(f"Updated batch {i//batch_size + 1}/{total_batches}")
            time.sleep(0.5)
        except Exception as e:
            print(f"Error updating batch: {e}")
            if 'r' in locals():
                 print(r.text)

if __name__ == "__main__":
    fix_wave2_ids()
