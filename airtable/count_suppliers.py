import os
import requests
import json
from collections import Counter


AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

def fetch_and_count():
    offset = None
    supplier_counts = Counter()
    total_records = 0
    
    print("Fetching records from Airtable...")
    
    while True:
        params = [
            ("pageSize", "100"),
            ("fields[]", "supplier")
        ]
        if offset:
            params.append(("offset", offset))
            
        try:
            r = requests.get(API_URL, headers=HEADERS, params=params)
            r.raise_for_status()
            data = r.json()
            records = data.get("records", [])
            total_records += len(records)
            
            for rec in records:
                s = rec.get("fields", {}).get("supplier", "Unknown")
                supplier_counts[str(s)] += 1
            
            offset = data.get("offset")
            print(f"Fetched {total_records} records...", end="\r")
            
            if not offset:
                break
        except Exception as e:
            print(f"\nError: {e}")
            break
            
    print(f"\n\nTotal Records: {total_records}")
    print("Supplier Breakdown:")
    for supplier, count in supplier_counts.most_common():
        print(f"- {supplier}: {count}")

if __name__ == "__main__":
    fetch_and_count()
