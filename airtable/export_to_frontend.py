import os
import requests
import sqlite3
import json
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
OUTPUT_FILE = "frontend/public/data/products.frontend.json"
DB_FILE = "products.db"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

def slugify(text):
    if not text: return ""
    text = str(text).lower().strip()
    text = re.sub(r'[\s\.]+', '-', text)
    text = re.sub(r'[^\w\u0590-\u05FF\-]', '', text) 
    return text

def load_db_images():
    """Load persistent Cloudinary images from local DB."""
    if not os.path.exists(DB_FILE):
        return {}
        
    print("Loading persistent images from DB...")
    sku_map = {}
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT sku, cloudinary_images FROM products")
        for row in cursor.fetchall():
            sku, images_json = row
            if images_json:
                try:
                    imgs = json.loads(images_json)
                    if imgs and isinstance(imgs, list):
                         sku_map[sku] = imgs
                except:
                    pass
        conn.close()
    except Exception as e:
        print(f"Error loading DB images: {e}")
        
    return sku_map

def export_frontend():
    # 1. Load persistent images
    db_images = load_db_images()
    
    print("Fetching ALL records from Airtable...")
    records = []
    offset = None
    
    while True:
        params = [
            ("pageSize", "100")
        ]
        if offset:
            params.append(("offset", offset))
            
        try:
            r = requests.get(API_URL, headers=HEADERS, params=params)
            r.raise_for_status()
            data = r.json()
            records.extend(data.get("records", []))
            offset = data.get("offset")
            print(f"Fetched {len(records)}...", end="\r")
            if not offset: break
        except Exception as e:
            print(f"Error fetching Airtable: {e}")
            return

    print(f"\nProcessing {len(records)} records...")
    
    frontend_products = []
    
    for rec in records:
        f = rec.get('fields', {})
        
        # Basic Validation
        if not f.get('sku'): continue
        
        sku = f.get('sku', '')
        
        # ID Mapping
        pid = f.get('product_id', f.get('catalog_id', f"unknown:{sku}"))
        
        # Images Logic: Prefer DB (Persistent) -> Airtable (Expiring)
        image_urls = []
        
        # Check DB first
        if sku in db_images:
            image_urls = db_images[sku]
        else:
            # Fallback to Airtable
            img_objs = f.get('images', [])
            if isinstance(img_objs, list):
                for img in img_objs:
                    if isinstance(img, dict) and 'url' in img:
                        image_urls.append(img['url'])
                    elif isinstance(img, str): 
                        image_urls.append(img)
                    
        image_main = image_urls[0] if image_urls else None
        
        # Categories
        cat_path = []
        if f.get('category_major'): cat_path.append(f.get('category_major'))
        if f.get('category_sub'): cat_path.append(f.get('category_sub'))
        
        # Slug
        title = f.get('title', '')
        raw_slug = f"{sku}-{title}"
        slug = slugify(raw_slug)
        
        # Search blob
        blob = f"{sku} {title} {' '.join(cat_path)}"
        
        # Clean URL check
        src_url = f.get('source_url', '')
        
        item = {
            "id": pid,
            "catalog_id": pid,
            "sku_clean": f.get('sku_clean', sku),
            "supplier_slug": f.get('supplier_slug', f.get('supplier', 'unknown').lower()),
            "supplier": f.get('supplier', 'Unknown'),
            "url": src_url,
            "url_clean": src_url,
            "slug": slug,
            "title": title,
            "sku": sku,
            "category_path": cat_path,
            "category_slug_path": [slugify(c) for c in cat_path],
            "description": f.get('description', ''),
            "properties": {}, 
            "images": image_urls,
            "image_main": image_main,
            "price": f.get('price'),
            "currency": f.get('currency'),
            "availability": f.get('availability'),
            "variants": [], 
            "content_hash": f.get('content_hash', ''),
            "first_seen_at": f.get('first_seen_at', datetime.now().isoformat()),
            "last_seen_at": datetime.now().isoformat(),
            "search_blob": blob
        }
        
        frontend_products.append(item)
        
    print(f"Exporting {len(frontend_products)} products to {OUTPUT_FILE}...")
    
    # Ensure dir exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(frontend_products, f, indent=2, ensure_ascii=False)
        
    print("Done.")

if __name__ == "__main__":
    export_frontend()
