import os
import sqlite3
import requests
import json
import time

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
DB_PATH = "products.db"
SUPPLIER = "Comfort Gifts"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

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
            ("filterByFormula", "{supplier}='Comfort'")
        ]
        if offset:
            params.append(("offset", offset))
            
        try:
            r = requests.get(API_URL, headers=HEADERS, params=params)
            r.raise_for_status()
            data = r.json()
            at_records.extend(data.get("records", []))
            offset = data.get("offset")
            print(f"Fetched {len(at_records)}...", end="\r")
            if not offset: break
        except Exception as e:
            print(f"Error fetching Airtable: {e}")
            return

    print(f"\nFetched {len(at_records)} Airtable records.")
    
    # 3. Match and Update
    updates = []
    
    for rec in at_records:
        at_id = rec['id']
        at_sku = rec['fields'].get('sku')
        
        if at_sku in db_map:
            local = db_map[at_sku]
            
            # Prepare fields to update
            # We want to sync: Title, Description, Images, URL (just in case), Status?
            
            # Images need format conversion: JSON list string -> list of objects with 'url'
            img_list = []
            if local['images']:
                try:
                    urls = json.loads(local['images'])
                    if isinstance(urls, list):
                        img_list = [{"url": u} for u in urls if u.startswith("http")]
                except: pass
            
            fields = {
                "title": local['title'], 
                "description": local['description'][:10000] if local['description'] else "", # limit length
                "source_url": local['url'],
                "images": img_list,
                # "status": "Published" if local else "Draft" ? User said ignore status.
            }
            
            updates.append({
                "id": at_id,
                "fields": fields
            })
            
    print(f"Prepared updates for {len(updates)} records.")
    
    # 4. Batch Update
    batch_size = 10
    total_batches = (len(updates) // batch_size) + 1
    
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        payload = {"records": batch, "typecast": True}
        try:
            r = requests.patch(API_URL, headers=HEADERS, json=payload)
            r.raise_for_status()
            print(f"Updated batch {i//batch_size + 1}/{total_batches}")
            time.sleep(0.5)
        except Exception as e:
            print(f"Error updating batch {i}: {e}")
            if 'r' in locals():
                print(r.text)
            break # Stop on first error to debug

    print("Sync complete.")

if __name__ == "__main__":
    sync_to_airtable()
