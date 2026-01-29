import os
import requests
import json
from collections import Counter

# We need to get the env vars
AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

def analyze():
    print("Fetching Comfort Gifts records from Airtable...")
    
    offset = None
    records = []
    
    # Filter for Comfort Gifts only to save time if possible, 
    # but filterByFormula is safer to ensure we get them all.
    # formula: {supplier} = 'Comfort Gifts'
    
    while True:
        params = [
            ("pageSize", "100"),
            ("fields[]", "sku"),
            ("fields[]", "supplier"),
            ("fields[]", "source_url"),
            ("fields[]", "category_major"),
            ("fields[]", "category_sub"),
            ("fields[]", "product_id"), # internal ID
            ("filterByFormula", "{supplier}='Comfort'")
        ]
        
        if offset:
            params.append(("offset", offset))
            
        try:
            r = requests.get(API_URL, headers=HEADERS, params=params)
            r.raise_for_status()
            data = r.json()
            batch = data.get("records", [])
            records.extend(batch)
            
            offset = data.get("offset")
            print(f"Fetched {len(records)} records...", end="\r")
            
            if not offset:
                break
        except Exception as e:
            print(f"\nError: {e}")
            return

    print(f"\nTotal Comfort Gifts Records: {len(records)}")
    
    # Group by SKU
    sku_groups = {}
    for rec in records:
        f = rec.get("fields", {})
        sku = f.get("sku")
        if not sku:
            continue # Should not happen for valid products
            
        if sku not in sku_groups:
            sku_groups[sku] = []
        sku_groups[sku].append(rec)
        
    # Analyze Duplicates
    dupes = {k:v for k,v in sku_groups.items() if len(v) > 1}
    print(f"SKUs with duplicates: {len(dupes)}")
    
    total_to_delete = 0
    
    print("\n--- SAMPLE DUPLICATES ---")
    count = 0
    for sku, group in dupes.items():
        total_to_delete += (len(group) - 1)
        
        # Only print first 5 examples
        if count < 5:
            print(f"\nSKU: {sku} ({len(group)} records)")
            
            # Score them to see who wins
            # Score = (Has Category Major?, Has Category Sub?, URL Length)
            for rec in group:
                f = rec.get("fields", {})
                rid = rec.get("id")
                has_maj = 1 if f.get("category_major") else 0
                has_sub = 1 if f.get("category_sub") else 0
                url_len = len(f.get("source_url", ""))
                
                score = (has_maj + has_sub) * 1000 + url_len
                print(f"  - [{rid}] Score={score} | Cats={has_maj},{has_sub} | URL={f.get('source_url','')[:50]}...")
            
            # Identify winner
            # Sort by score descending
            sorted_group = sorted(group, key=lambda r: (
                1 if r.get('fields',{}).get('category_major') else 0,
                1 if r.get('fields',{}).get('category_sub') else 0,
                len(r.get('fields',{}).get('source_url', ''))
            ), reverse=True)
            
            winner = sorted_group[0]
            print(f"  => WINNER: {winner.get('id')} (would keep)")
            
            count += 1
            
    print(f"\nTotal Duplicate Groups: {len(dupes)}")
    print(f"Total Records that would be deleted: {total_to_delete}")
    print(f"Final Count would be: {len(records) - total_to_delete}")

if __name__ == "__main__":
    analyze()
