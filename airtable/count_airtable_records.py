#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
}

def count_records(supplier):
    """Count records in Airtable for a given supplier"""
    count = 0
    offset = None
    
    while True:
        params = [
            ("pageSize", "100"),
            ("filterByFormula", "{supplier}='" + supplier + "'"),
            ("fields[]", "sku")
        ]
        if offset:
            params.append(("offset", offset))
        
        r = requests.get(API_URL, headers=HEADERS, params=params)
        r.raise_for_status()
        data = r.json()
        
        count += len(data.get("records", []))
        offset = data.get("offset")
        
        if not offset:
            break
    
    return count

if __name__ == "__main__":
    suppliers = ["Comfort", "Zeus", "Wave2", "Kraus", "polo"]
    
    print("Airtable Record Counts:")
    print("-" * 40)
    for supplier in suppliers:
        count = count_records(supplier)
        print(f"{supplier:20} {count:5} records")
