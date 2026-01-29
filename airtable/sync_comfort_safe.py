import sqlite3
import os
import sys
import json
import time
import requests
from typing import Dict, Any, List, Set, Tuple
from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), ".env"))

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"

API_BASE = "https://api.airtable.com/v0"
API_URL = f"{API_BASE}/{BASE_ID}/{TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

BATCH_SIZE = 10
MAX_RETRIES = 5
SLEEP_BETWEEN_BATCHES_SEC = 0.5

# NEVER OVERWRITE THESE FIELDS IF THEY HAVE DATA IN AIRTABLE
PROTECTED_FIELDS = {
    "status", 
    "tags", 
    "featured_rank", 
    "slug_override", 
    "description", 
    "whatsapp_text_override",
    "image_main_url", 
    "seo_title",
    "seo_description",
    "whatsapp_text_final",
    "whatsapp_link",
    "title", # Added title to protection just in case user renamed it
    "properties" # Added properties to protection 
}

def airtable_get_existing_comfort_records() -> Dict[str, Dict[str, Any]]:
    """Fetch all existing Comfort Gifts records to compare fields."""
    print("Fetching existing Comfort Gifts records from Airtable for safety mapping...")
    records_map = {}
    offset = None
    
    # Filter only Comfort Gifts to be efficient
    formula = "OR({supplier}='Comfort Gifts', {supplier}='Comfort')"
    
    while True:
        params = {
            "pageSize": 100,
            "filterByFormula": formula
        }
        if offset:
            params["offset"] = offset
            
        r = requests.get(API_URL, headers=HEADERS, params=params)
        if not r.ok:
            print(f"Error fetching existing records: {r.status_code} - {r.text}")
            break
            
        data = r.json()
        for rec in data.get("records", []):
            fields = rec.get("fields", {})
            cid = fields.get("catalog_id")
            if cid:
                records_map[cid] = fields
                
        offset = data.get("offset")
        if not offset:
            break
            
    print(f"Mapped {len(records_map)} existing Comfort Gift records.")
    return records_map

def category_from_path(category_path: Any) -> Tuple[str, str, str]:
    if not category_path: return ("", "", "")
    if isinstance(category_path, str):
        s = category_path.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                arr = json.loads(s)
                parts = [str(x).strip() for x in arr if str(x).strip()]
            except: parts = [s]
        else:
            for sep in (">", "/", "|", "»"):
                if sep in s:
                    parts = [p.strip() for p in s.split(sep) if p.strip()]
                    break
            else: parts = [s]
    elif isinstance(category_path, list):
        parts = [str(x).strip() for x in category_path if str(x).strip()]
    else: parts = [str(category_path).strip()]
    
    major = parts[0] if len(parts) > 0 else ""
    sub = parts[1] if len(parts) > 1 else ""
    sub2 = parts[2] if len(parts) > 2 else ""
    return (major, sub, sub2)

def get_sqlite_comfort_products(db_path: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        # ABSOLUTE FILTER: ONLY COMFORT GIFTS
        c.execute("SELECT * FROM products WHERE supplier = 'Comfort Gifts'")
    except Exception as e:
        print(f"DB Error: {e}")
        sys.exit(1)
        
    rows = c.fetchall()
    products = []
    for r in rows:
        d = dict(r)
        for field in ['images', 'properties', 'cloudinary_images', 'variants']:
            if d.get(field):
                try: d[field] = json.loads(d[field])
                except: d[field] = [] if field != 'properties' else {}
            elif field != 'properties': d[field] = []
            else: d[field] = {}
        products.append(d)
    conn.close()
    return products

def airtable_upsert(records: List[Dict[str, Any]]):
    payload = {
        "performUpsert": {
            "fieldsToMergeOn": ["catalog_id"]
        },
        "records": [{"fields": r} for r in records]
    }
    r = requests.patch(API_URL, headers=HEADERS, json=payload, timeout=45)
    return r

def main():
    if not AIRTABLE_PAT:
        print("ERROR: AIRTABLE_PAT not set.")
        return

    db_path = "products.db"
    
    # Check for --once flag
    run_once = "--once" in sys.argv

    while True:
        if not os.path.exists(db_path):
            print("products.db not found. Waiting...")
            time.sleep(60)
            continue

        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Safe Sync cycle...")
        
        # 1. Fetch from SQLite
        products = get_sqlite_comfort_products(db_path)
        print(f"Loaded {len(products)} Comfort Gifts products from SQLite.")

        # 2. Fetch from Airtable for safety
        existing_map = airtable_get_existing_comfort_records()

        # 3. Prepare sanitized batches
        batch_records = []
        protected_count = 0

        for p in products:
            cid = p.get('catalog_id')
            if not cid: continue
            
            major, sub, sub2 = category_from_path(p.get('category_path'))
            final_images = p.get('cloudinary_images') if p.get('cloudinary_images') else p.get('images', [])
            img_objs = [{"url": url} for url in final_images if url][:10]
            # Initial field set from crawler
            fields = {
                "catalog_id": cid,
                "product_id": f"comfort:{p.get('sku')}", # Standardized ID
                "sku": p.get('sku'),
                "sku_clean": p.get('sku_clean'),
                "supplier": "Comfort", # Match Airtable choice
                "supplier_slug": "comfort",
                "title": p.get('title'),
                "price": p.get('price'),
                "currency": p.get('currency'),
                "source_url": p.get('url_clean') or p.get('url'),
                "image_urls": "\n".join(final_images),
                "category_major": major,
                "category_sub": sub,
                "category_sub2": sub2,
                "description": p.get('description'),
                "properties": json.dumps(p.get('properties'), ensure_ascii=False) if p.get('properties') else "",
                "last_seen_in_crawl": p.get('last_seen_at'),
                "content_hash": p.get('content_hash')
            }
            if img_objs: fields["images"] = img_objs

            if cid in existing_map:
                airtable_fields = existing_map[cid]
                for prot in PROTECTED_FIELDS:
                    if airtable_fields.get(prot):
                        if fields.get(prot) != airtable_fields.get(prot):
                            del fields[prot]
                            protected_count += 1
            batch_records.append(fields)

        if not batch_records:
            print("No Comfort products found to sync.")
        else:
            print(f"Sanitization complete: {protected_count} protected fields preserved.")
            print(f"Syncing {len(batch_records)} products...")
            
            # Categories are the main cause of 422 errors
            category_fields = ["category_major", "category_sub", "category_sub2"]
            
            for i in range(0, len(batch_records), BATCH_SIZE):
                chunk = batch_records[i:i+BATCH_SIZE]
                
                try:
                    # Attempt 1: Sync WITHOUT categories first to ensure core data is there
                    core_chunk = [{k: v for k, v in r.items() if k not in category_fields} for r in chunk]
                    resp = airtable_upsert(core_chunk)
                    
                    if resp.ok:
                        cat_updates = [{"catalog_id": r["catalog_id"], "category_major": r.get("category_major"), "category_sub": r.get("category_sub"), "category_sub2": r.get("category_sub2")} for r in chunk]
                        airtable_upsert(cat_updates)
                    else:
                        print(f"  Batch {i}: Core failure: {resp.status_code}")
                except Exception as e:
                    print(f"  Batch {i}: ERROR: {e}")
                
                time.sleep(SLEEP_BETWEEN_BATCHES_SEC)
            print("Cycle Complete.")

        if run_once:
            break
            
        print("Sleeping for 10 minutes before next sync...")
        time.sleep(600)

if __name__ == "__main__":
    main()
