import sys
import os
import sqlite3
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
DB_PATH = "products.db"

# Allow CLI arg for supplier, default to Comfort for backward compat
if len(sys.argv) > 1:
    SUPPLIER = sys.argv[1]
else:
    SUPPLIER = "Comfort"

# Mapping for Airtable 'supplier' field if needed (e.g. database has 'Zeus', Airtable has 'Zeus' or 'Zeus Gifts')
# Assuming 1:1 for now, but good to note.


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

def sync_to_airtable():
    print(f"Syncing {SUPPLIER} from DB to Airtable...")
    
    # 1. Load Local DB
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE supplier = ?", (SUPPLIER,))
    db_rows = cursor.fetchall()
    conn.close()
    
    db_map = {row['sku']: row for row in db_rows}
    print(f"Loaded {len(db_map)} local products.")

    # 2. Load Airtable Records
    print("Fetching Airtable records...")
    at_records = []
    offset = None
    while True:
        params = [
            ("pageSize", "100"),
            ("fields[]", "sku"),
            ("fields[]", "product_id"),
            ("filterByFormula", "{supplier}='" + SUPPLIER + "'")
        ]
        if offset:
            params.append(("offset", offset))
            
        try:
            data = airtable_request("GET", API_URL, params=params)
            at_records.extend(data.get("records", []))
            offset = data.get("offset")
            print(f"Fetched {len(at_records)}...", end="\r")
            if not offset: break
        except Exception as e:
            print(f"Error fetching Airtable after retries: {e}")
            return

    print(f"\nFetched {len(at_records)} Airtable records.")
    
    # 3. Match and Update
    updates = []
    at_skus = set()
    
    for rec in at_records:
        at_id = rec['id']
        at_sku = rec['fields'].get('sku')
        at_skus.add(at_sku)
        
        if at_sku in db_map:
            local = db_map[at_sku]
            
            img_list = []
            if local['images']:
                try:
                    urls = json.loads(local['images'])
                    if isinstance(urls, list):
                        img_list = [{"url": u} for u in urls if u.startswith("http")]
                except: pass
            
            fields = {
                "catalog_id": local['catalog_id'],
                "product_id": local['catalog_id'], # Convention: supplier:sku
                "title": local['title'], 
                "description": local['description'][:10000] if local['description'] else "", 
                "color": local['color'] if local['color'] else "",
                "source_url": local['url'],
                "images": img_list,
                "image_urls": ""
            }
            try:
                if local['images']:
                    urls = json.loads(local['images'])
                    fields["image_urls"] = "\n".join(urls)
            except: pass
            
            updates.append({"id": at_id, "fields": fields})
            if len(updates) == 1:
                print(f"DEBUG: First update fields: {json.dumps(fields, indent=2, ensure_ascii=False)}")


    # 3.1 Identify Creates
    creates = []
    for sku, local in db_map.items():
        if sku not in at_skus:
            img_list = []
            if local['images']:
                try:
                    urls = json.loads(local['images'])
                    if isinstance(urls, list):
                        img_list = [{"url": u} for u in urls if u.startswith("http")]
                except: pass
            
            fields = {
                "catalog_id": local['catalog_id'],
                "product_id": local['catalog_id'], # Convention: supplier:sku
                "sku": sku,
                "supplier": SUPPLIER,
                "title": local['title'],
                "description": local['description'][:10000] if local['description'] else "",
                "color": local['color'] if local['color'] else "",
                "source_url": local['url'],
                "images": img_list,
                "image_urls": ""
            }
            try:
                if local['images']:
                    urls = json.loads(local['images'])
                    fields["image_urls"] = "\n".join(urls)
            except: pass
            
            creates.append({"fields": fields})
            
    print(f"Prepared creation for {len(creates)} new records.")

    # 4. Batch Update (PATCH)
    if updates:
        print("Starting batch updates...")
        batch_size = 10
        total_batches = (len(updates) // batch_size) + 1
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i+batch_size]
            try:
                airtable_request("PATCH", API_URL, json_data={"records": batch, "typecast": True})
                print(f"Updated batch {i//batch_size + 1}/{total_batches}")
                time.sleep(0.5)
            except: pass

    # 5. Batch Create (POST)
    if creates:
        print("Starting batch creation...")
        batch_size = 10
        total_batches = (len(creates) // batch_size) + 1
        for i in range(0, len(creates), batch_size):
            batch = creates[i:i+batch_size]
            try:
                airtable_request("POST", API_URL, json_data={"records": batch, "typecast": True})
                print(f"Created batch {i//batch_size + 1}/{total_batches}")
                time.sleep(0.5)
            except: pass

    print("Sync complete.")



    print("Sync complete.")

if __name__ == "__main__":
    sync_to_airtable()
