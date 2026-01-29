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

def fetch_all_records():
    all_records = []
    offset = None
    print("Fetching records from Airtable...")
    
    while True:
        params = {
            "pageSize": 100,
            "fields": ["product_id", "supplier", "sku", "description", "source_url"]
        }
        if offset:
            params["offset"] = offset
            
        r = requests.get(API_URL, headers=HEADERS, params=params)
        if not r.ok:
            print(f"Error: {r.status_code} - {r.text}")
            break
            
        data = r.json()
        records = data.get("records", [])
        all_records.extend(records)
        
        offset = data.get("offset")
        if not offset:
            break
            
    print(f"Total records fetched: {len(all_records)}")
    return all_records

def main():
    records = fetch_all_records()
    
    kraus_missing_desc = []
    incorrect_ids = []
    
    for rec in records:
        f = rec.get("fields", {})
        rid = rec.get("id")
        pid = f.get("product_id", "")
        supplier = f.get("supplier", "")
        sku = f.get("sku", "")
        desc = f.get("description", "")
        url = f.get("source_url", "")
        
        # Check ID structure: <supplier>:<sku>
        expected_id = f"{supplier.lower()}:{sku}"
        if pid != expected_id:
            incorrect_ids.append({
                "record_id": rid,
                "current_id": pid,
                "expected_id": expected_id,
                "supplier": supplier,
                "sku": sku
            })
            
        # Check Kraus missing description
        if supplier.lower() == "kraus" and not desc.strip():
            kraus_missing_desc.append({
                "record_id": rid,
                "title": f.get("title", "No Title"),
                "sku": sku,
                "url": url
            })
            
    print(f"\nCorrection Summary:")
    print(f"- Incorrect IDs: {len(incorrect_ids)}")
    print(f"- Kraus missing descriptions: {len(kraus_missing_desc)}")
    
    # Save to a temporary file for the next step
    report = {
        "incorrect_ids": incorrect_ids,
        "kraus_missing_desc": kraus_missing_desc
    }
    with open("airtable_audit.json", "w") as f:
        json.dump(report, f, indent=2)
    print("\nAudit saved to airtable_audit.json")

if __name__ == "__main__":
    main()
