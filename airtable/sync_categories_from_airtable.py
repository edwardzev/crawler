import os
import requests
import sqlite3
import json
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
DB_FILE = "products.db"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

def sync_categories():
    print("Fetching categories from Airtable...")
    records = []
    offset = None
    
    while True:
        params = [("pageSize", "100"), ("fields[]", "sku"), ("fields[]", "category_major"), ("fields[]", "category_sub")]
        if offset:
            params.append(("offset", offset))
            
        try:
            r = requests.get(API_URL, headers=HEADERS, params=params)
            r.raise_for_status()
            data = r.json()
            records.extend(data.get("records", []))
            offset = data.get("offset")
            print(f"Fetched {len(records)} records...", end="\r")
            if not offset: break
        except Exception as e:
            print(f"Error fetching Airtable: {e}")
            return

    print(f"\nSyncing {len(records)} records to DB...")
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    updates = 0
    
    for rec in records:
        f = rec.get('fields', {})
        sku = f.get('sku')
        if not sku: continue
        
        cat_path = []
        if f.get('category_major'): cat_path.append(f.get('category_major'))
        if f.get('category_sub'): cat_path.append(f.get('category_sub'))
        
        if not cat_path: continue
        
        json_path = json.dumps(cat_path, ensure_ascii=False)
        
        # We update existing products matching the SKU
        c.execute("UPDATE products SET category_path = ? WHERE sku = ?", (json_path, sku))
        if c.rowcount > 0:
            updates += 1
            
    conn.commit()
    conn.close()
    print(f"Updated categories for {updates} products in local DB.")

if __name__ == "__main__":
    sync_categories()
