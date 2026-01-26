import sqlite3
import os
import sys
import json
import time
import requests
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict
from dotenv import load_dotenv

# Load env (explicitly from current dir)
load_dotenv(os.path.join(os.getcwd(), ".env"))

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"

API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

PROTECTED_FIELDS = [
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
]

def get_sqlite_products(db_path: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    # Check if cloudinary_images column exists
    try:
        c.execute("SELECT * FROM products")
    except Exception as e:
        print(f"DB Error: {e}")
        sys.exit(1)
        
    rows = c.fetchall()
    products = []
    
    # Check columns to see if cloudinary_images exists
    cols = [description[0] for description in c.description]
    has_cloud_imgs = "cloudinary_images" in cols
    
    for r in rows:
        d = dict(r)
        
        # Parse JSON
        if d.get('images'): 
            try: d['images'] = json.loads(d['images']) 
            except: d['images'] = []
            
        if d.get('properties'):
            try: d['properties'] = json.loads(d['properties'])
            except: d['properties'] = {}
            
        if has_cloud_imgs and d.get('cloudinary_images'):
            try: d['cloudinary_images'] = json.loads(d['cloudinary_images'])
            except: d['cloudinary_images'] = []
        else:
            d['cloudinary_images'] = []
            
        products.append(d)
    conn.close()
    return products

def fetch_airtable_records() -> Dict[str, Any]:
    records_map = {}
    duplicates = defaultdict(list)
    offset = None
    print("Fetching existing Airtable records...")
    
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset   
        try:
            r = requests.get(API_URL, headers=HEADERS, params=params)
            r.raise_for_status()
            data = r.json()
            for rec in data.get("records", []):
                fields = rec.get("fields", {})
                rid = rec["id"]
                cid = fields.get("catalog_id")
                if cid:
                    if cid in records_map:
                        duplicates[cid].append(rid)
                    else:
                        records_map[cid] = {"id": rid, "fields": fields}
            offset = data.get("offset")
            if not offset: break
        except Exception as e:
            print(f"Error fetching airtable: {e}")
            sys.exit(1)
            
    print(f"Fetched {len(records_map)} unique catalog_id records.")
    return records_map, duplicates

def sync_batch(batch_payload: List[Dict[str, Any]], method: str = "PATCH"):
    for i in range(0, len(batch_payload), 10):
        chunk = batch_payload[i:i+10]
        payload = {"records": chunk}
        try:
            if method == "POST":
                r = requests.post(API_URL, headers=HEADERS, json=payload)
            else:
                r = requests.patch(API_URL, headers=HEADERS, json=payload)
            r.raise_for_status()
            time.sleep(0.25)
        except Exception as e:
            print(f"Error syncing batch {i}: {e}")
            if hasattr(e, 'response') and e.response: print(e.response.text)

def main():
    db_path = "products.db"
    if not os.path.exists(db_path):
        print("products.db not found.")
        return

    products = get_sqlite_products(db_path)
    airtable_map, airtable_dupes = fetch_airtable_records()
    
    to_create = []
    to_update = []
    
    print(f"Processing {len(products)} local products...")
    
    for p in products:
        cid = p['catalog_id']
        if not cid: continue
        
        # PREPARE URLS
        # Priorities: 1. Cloudinary Images, 2. Original Images
        final_images = p['cloudinary_images'] if p['cloudinary_images'] else p['images']
        
        # Format for Airtable Attachments
        img_objs = [{"url": url} for url in final_images if url]
        
        # Format for 'image_urls' text field (newline separated)
        img_urls_text = "\n".join(final_images) if final_images else ""

        fields = {
            "catalog_id": cid,
            "product_id": p['product_id'],
            "sku": p['sku'],
            "sku_clean": p.get('sku_clean'),
            "supplier": p['supplier'],
            "supplier_slug": p.get('supplier_slug'),
            "title": p['title'],
            "price": p['price'],
            "currency": p['currency'],
            "source_url": p['url_clean'] or p['url'],
            "image_urls": img_urls_text,
            # "images": img_objs  <-- Uncomment if we want to sync attachments too
        }
        
        # Update Attachment field 'images'
        if img_objs:
             fields["images"] = img_objs

        if cid in airtable_dupes:
            continue # specific processing later if needed

        if cid in airtable_map:
            # UPDATE
            existing = airtable_map[cid]
            rid = existing['id']
            existing_fields = existing['fields']
            
            # Default Description from DB if not protected
            if p.get('description'):
                fields['description'] = p['description']
            
            # Remove protected if exists in Airtable
            for prot in PROTECTED_FIELDS:
                if existing_fields.get(prot): 
                    if prot in fields: del fields[prot]
            
            to_update.append({"id": rid, "fields": fields})
        else:
            # CREATE
            if p.get('description'):
                fields['description'] = p['description']
            to_create.append({"fields": fields})
            
    print(f"Plan: Create {len(to_create)}, Update {len(to_update)}")
    
    if to_create:
        print("Executing Creates...")
        sync_batch(to_create, "POST")
        
    if to_update:
        print("Executing Updates...")
        sync_batch(to_update, "PATCH")
        
    print("Sync Complete.")

if __name__ == "__main__":
    main()
