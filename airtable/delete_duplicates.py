import os
import requests
import json
import time

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

def delete_duplicates():
    print("Fetching Comfort records...")
    
    records = []
    offset = None
    while True:
        params = [
            ("pageSize", "100"),
            ("fields[]", "sku"),
            ("fields[]", "supplier"),
            ("fields[]", "source_url"),
            ("fields[]", "category_major"),
            ("fields[]", "category_sub"),
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

    print(f"\nTotal: {len(records)}")
    
    # Identify duplicates
    sku_groups = {}
    for rec in records:
        sku = rec.get("fields", {}).get("sku")
        if sku:
            if sku not in sku_groups: sku_groups[sku] = []
            sku_groups[sku].append(rec)
            
    ids_to_delete = []
    
    for sku, group in sku_groups.items():
        if len(group) > 1:
            # Sort winner to top
            sorted_group = sorted(group, key=lambda r: (
                1 if r.get('fields',{}).get('category_major') else 0,
                1 if r.get('fields',{}).get('category_sub') else 0,
                len(r.get('fields',{}).get('source_url', ''))
            ), reverse=True)
            
            # Everyone else is deleted
            losers = sorted_group[1:]
            for l in losers:
                ids_to_delete.append(l['id'])
                
    print(f"Found {len(ids_to_delete)} records to delete.")
    
    if not ids_to_delete:
        print("No duplicates found.")
        return

    # Delete in batches of 10
    print("Deleting...")
    batch_size = 10
    for i in range(0, len(ids_to_delete), batch_size):
        batch = ids_to_delete[i:i+batch_size]
        try:
            # ?records[]=rec1&records[]=rec2
            delete_params = [("records[]", rid) for rid in batch]
            r = requests.delete(API_URL, headers=HEADERS, params=delete_params)
            r.raise_for_status()
            print(f"Deleted batch {i//batch_size + 1}/{(len(ids_to_delete)//batch_size)+1} ({len(batch)} recs)")
            time.sleep(0.5) # rate limit
        except Exception as e:
            print(f"Failed to delete batch: {e}")
            
    print("Done.")

if __name__ == "__main__":
    delete_duplicates()
