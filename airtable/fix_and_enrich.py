import os
import requests
import json
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

def fetch_kraus_description(url):
    if not url: return None
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            desc_div = soup.select_one('.woocommerce-product-details__short-description')
            if desc_div:
                return desc_div.get_text(strip=True)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def update_airtable_batch(updates):
    if not updates: return
    payload = {"records": updates}
    try:
        r = requests.patch(API_URL, headers=HEADERS, json=payload)
        if not r.ok:
            print(f"Airtable Update Error: {r.status_code} - {r.text}")
        else:
            print(f"Successfully updated batch of {len(updates)}")
    except Exception as e:
        print(f"Request error: {e}")

def main():
    if not os.path.exists("airtable_audit.json"):
        print("Audit file not found. Run audit_records.py first.")
        return

    with open("airtable_audit.json", "r") as f:
        audit = json.load(f)

    incorrect_ids = audit.get("incorrect_ids", [])
    missing_desc = audit.get("kraus_missing_desc", [])

    print(f"Starting correction of {len(incorrect_ids)} IDs and enrichment of {len(missing_desc)} Kraus descriptions.")

    # 1. Prepare ID updates
    id_updates = []
    for item in incorrect_ids:
        id_updates.append({
            "id": item["record_id"],
            "fields": {
                "product_id": item["expected_id"]
            }
        })

    # 2. Prepare Description updates (in-memory first, then batch)
    print("Fetching Kraus descriptions (this may take a while)...")
    desc_updates = []
    
    # Using ThreadPool to speed up fetching
    def process_kraus(item):
        desc = fetch_kraus_description(item["url"])
        if desc:
            return {
                "id": item["record_id"],
                "fields": {
                    "description": desc
                }
            }
        return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_kraus, missing_desc))
    
    desc_updates = [r for r in results if r]
    print(f"Found descriptions for {len(desc_updates)} out of {len(missing_desc)} products.")

    # 3. Combine updates
    # Combine updates for same record if both ID and Desc are changing
    final_updates_map = {}
    
    for u in id_updates:
        final_updates_map[u["id"]] = u["fields"]
        
    for u in desc_updates:
        if u["id"] in final_updates_map:
            final_updates_map[u["id"]].update(u["fields"])
        else:
            final_updates_map[u["id"]] = u["fields"]

    # 4. Push updates to Airtable in batches of 10
    all_update_items = [{"id": rid, "fields": fields} for rid, fields in final_updates_map.items()]
    print(f"Total records to update in Airtable: {len(all_update_items)}")

    for i in range(0, len(all_update_items), 10):
        batch = all_update_items[i:i+10]
        update_airtable_batch(batch)
        time.sleep(0.25) # Rate limit respect

    print("\n✅ Airtable Correction & Enrichment Complete.")

if __name__ == "__main__":
    main()
