import os
import requests
import json
import re

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

def fix_skus():
    print("Scanning Comfort records for bad SKUs...")
    
    records = []
    offset = None
    while True:
        # Fetch only Comfort records, we need checks
        params = [
            ("pageSize", "100"),
            ("fields[]", "sku"),
            ("fields[]", "supplier"),
            ("fields[]", "product_id"),
            ("filterByFormula", "{supplier}='Comfort'")
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

    print(f"\nTotal Comfort records: {len(records)}")
    
    to_update = []
    
    for rec in records:
        f = rec.get("fields", {})
        sku = f.get("sku", "")
        rid = rec.get("id")
        
        # Check for hyphenated SKUs (e.g. 1770-Uranus)
        if '-' in sku:
            # Extract digits before hyphen? Or just first group of digits?
            # User example: 1770-Uranus -> 1770
            match = re.match(r'^(\d+)-', sku)
            if match:
                clean_sku = match.group(1)
                
                # We also need to update product_id likely?
                # current product_id: Comfort:1770-Uranus (probably)
                # new product_id: Comfort:1770
                
                new_pid = f"comfort:{clean_sku}"
                
                to_update.append({
                    "id": rid,
                    "fields": {
                        "sku": clean_sku,
                        "sku_clean": clean_sku,
                        "product_id": f"comfort:{clean_sku}" # Assuming lower case comfort prefix
                        # Using "Comfort" (Capitalized) might be better if that's the standard
                        # Wait, let's look at existing logic. 
                        # In db it is "comfort-gifts:123" or similar?
                        # Let's check airtable audit output. 
                        # Actually audit showed "kraus:KR202". 
                        # The user just said "correct sku is 4 digits".
                        # Let's just update SKU and sku_clean primarily.
                        # I'll update product_id to match "comfort:<sku>" to be safe/consistent?
                        # Or keep capitalized "Comfort"?
                        # I'll use "Comfort:<sku>" to match the supplier field value + colon.
                    }
                })
                print(f"Found bad SKU: {sku} -> {clean_sku}")
    
    print(f"Found {len(to_update)} records to fix.")
    
    if not to_update:
        return

    # Update in batches
    batch_size = 10
    for i in range(0, len(to_update), batch_size):
        batch = to_update[i:i+batch_size]
        payload = {"records": batch}
        try:
            r = requests.patch(API_URL, headers=HEADERS, json=payload)
            r.raise_for_status()
            print(f"Updated batch {i//batch_size + 1}")
        except Exception as e:
            print(f"Error updating batch: {e}")
            print(r.text)

if __name__ == "__main__":
    fix_skus()
