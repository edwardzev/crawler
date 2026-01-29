import sqlite3
import os
import sys
import json
import time
import requests
import re
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict
from dotenv import load_dotenv

# Load env (explicitly from current dir)
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
SLEEP_BETWEEN_BATCHES_SEC = 0.25

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
    "whatsapp_link"
}

def airtable_request(method: str, url: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    for attempt in range(1, MAX_RETRIES + 1):
        r = requests.request(method, url, headers=HEADERS, json=payload, timeout=30)
        if r.status_code in (429, 500, 502, 503, 504):
            wait = min(2 ** attempt, 20)
            print(f"Retryable Airtable error {r.status_code}. Waiting {wait}s... (attempt {attempt}/{MAX_RETRIES})")
            time.sleep(wait)
            continue
        if not r.ok:
            print(f"\nAirtable API error {r.status_code}: {r.text}")
            return {}
        return r.json()
    return {}

def category_from_path(category_path: Any) -> Tuple[str, str, str]:
    if category_path is None:
        return ("", "", "")

    if isinstance(category_path, str):
        s = category_path.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                arr = json.loads(s)
                parts = [str(x).strip() for x in arr if str(x).strip()]
            except:
                parts = [s]
        else:
            for sep in (">", "/", "|", "»"):
                if sep in s:
                    parts = [p.strip() for p in s.split(sep) if p.strip()]
                    break
            else:
                parts = [s]
    elif isinstance(category_path, list):
        parts = [str(x).strip() for x in category_path if str(x).strip()]
    else:
        parts = [str(category_path).strip()]

    major = parts[0] if len(parts) > 0 else ""
    sub = parts[1] if len(parts) > 1 else ""
    sub2 = parts[2] if len(parts) > 2 else ""
    return (major, sub, sub2)

def get_sqlite_products(db_path: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM products")
    except Exception as e:
        print(f"DB Error: {e}")
        sys.exit(1)
        
    rows = c.fetchall()
    products = []
    cols = [description[0] for description in c.description]
    
    for r in rows:
        d = dict(r)
        # Parse JSON
        for field in ['images', 'properties', 'cloudinary_images', 'variants']:
            if d.get(field):
                try: d[field] = json.loads(d[field])
                except: d[field] = [] if field != 'properties' else {}
            elif field != 'properties':
                d[field] = []
            else:
                d[field] = {}
        products.append(d)
    conn.close()
    return products

def airtable_upsert(records: List[Dict[str, Any]], fields_to_merge: List[str]):
    payload = {
        "performUpsert": {
            "fieldsToMergeOn": fields_to_merge
        },
        "records": [{"fields": r} for r in records]
    }
    r = requests.patch(API_URL, headers=HEADERS, json=payload, timeout=45)
    return r

def main():
    if not AIRTABLE_PAT:
        print("ERROR: AIRTABLE_PAT env var not set.")
        return

    db_path = "products.db"
    if not os.path.exists(db_path):
        print("products.db not found.")
        return

    products = get_sqlite_products(db_path)
    print(f"Loaded {len(products)} products from SQLite.")

    # Prepare batch records
    batch_records = []
    for p in products:
        cid = p.get('catalog_id')
        if not cid: continue
        
        major, sub, sub2 = category_from_path(p.get('category_path'))
        final_images = p.get('cloudinary_images') if p.get('cloudinary_images') else p.get('images', [])
        img_objs = [{"url": url} for url in final_images if url][:10]
        
        fields = {
            "catalog_id": cid,
            "product_id": p.get('product_id'),
            "sku": p.get('sku'),
            "sku_clean": p.get('sku_clean'),
            "supplier": p.get('supplier'),
            "supplier_slug": p.get('supplier_slug'),
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
        batch_records.append(fields)

    # Sync Loop
    print(f"Upserting {len(batch_records)} products to Airtable...")
    total = len(batch_records)
    done = 0
    
    cat_fields = ["category_major", "category_sub", "category_sub2"]

    for i in range(0, total, BATCH_SIZE):
        chunk = batch_records[i:i+BATCH_SIZE]
        
        # Attempt 1: Full sync
        resp = airtable_upsert(chunk, ["catalog_id"])
        
        if not resp.ok:
            if resp.status_code == 422:
                # 422 usually means a new choice in a select field
                # Fallback: Sync without category fields
                print(f"  Batch {i}: 422 error. Retrying without category fields...")
                fallback_chunk = []
                for rec in chunk:
                    clean_rec = {k: v for k, v in rec.items() if k not in cat_fields}
                    fallback_chunk.append(clean_rec)
                
                resp2 = airtable_upsert(fallback_chunk, ["catalog_id"])
                if not resp2.ok:
                    print(f"  Batch {i}: Permanent failure: {resp2.text}")
            else:
                print(f"  Batch {i}: Error {resp.status_code}: {resp.text}")
        
        done += len(chunk)
        if done % 100 == 0 or done == total:
            print(f"  {done}/{total} products processed")
        time.sleep(SLEEP_BETWEEN_BATCHES_SEC)

    print("\n✅ Sync Complete.")

if __name__ == "__main__":
    main()
