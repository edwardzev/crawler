import os
import requests
import json
import re
from datetime import datetime

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
OUTPUT_FILE = "frontend/public/data/products.frontend.json"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

def slugify(text):
    if not text: return ""
    # Simple slugify: lowercase, replace non-alphanumeric with -, strip
    # Also handle hebrew? The example used dashes between hebrew words.
    # "gb110-•-גלובל-תיק-אל-בד-gb110" -> seems to just replace spaces with dashes?
    # Let's keep it simple.
    text = str(text).lower().strip()
    text = re.sub(r'[\s\.]+', '-', text)
    text = re.sub(r'[^\w\u0590-\u05FF\-]', '', text) # Keep alphanumeric + hebrew + dash
    return text

def export_frontend():
    print("Fetching ALL records from Airtable...")
    records = []
    offset = None
    
    while True:
        params = [
            ("pageSize", "100"),
            ("view", "Grid view") 
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
        
        # ID Mapping
        pid = f.get('product_id', f.get('catalog_id', f"unknown:{f.get('sku')}"))
        
        # Images
        # Airtable 'images' is list of attachment objects {url, ...}
        img_objs = f.get('images', [])
        image_urls = []
        if isinstance(img_objs, list):
            for img in img_objs:
                if isinstance(img, dict) and 'url' in img:
                    image_urls.append(img['url'])
                elif isinstance(img, str): # Legacy/Error handling
                    image_urls.append(img)
                    
        image_main = image_urls[0] if image_urls else None
        
        # Categories
        cat_path = []
        if f.get('category_major'): cat_path.append(f.get('category_major'))
        if f.get('category_sub'): cat_path.append(f.get('category_sub'))
        
        # Slug
        # Start with SKU
        sku = f.get('sku', '')
        title = f.get('title', '')
        raw_slug = f"{sku}-{title}"
        slug = slugify(raw_slug)
        
        # Search blob
        blob = f"{sku} {title} {' '.join(cat_path)}"
        
        item = {
            "id": pid,
            "catalog_id": pid,
            "sku_clean": f.get('sku_clean', sku),
            "supplier_slug": f.get('supplier_slug', f.get('supplier', 'unknown').lower()),
            "supplier": f.get('supplier', 'Unknown'),
            "url": f.get('source_url', ''),
            "url_clean": f.get('source_url', ''), # Don't have cleaner logic handy, use source
            "slug": slug,
            "title": title,
            "sku": sku,
            "category_path": cat_path,
            "category_slug_path": [slugify(c) for c in cat_path],
            "description": f.get('description', ''),
            "properties": {}, # Not really populated in Airtable
            "images": image_urls,
            "image_main": image_main,
            "price": f.get('price'),
            "currency": f.get('currency'),
            "availability": f.get('availability'),
            "variants": [], # Not synced yet
            "content_hash": f.get('content_hash', ''),
            "first_seen_at": f.get('first_seen_at', datetime.now().isoformat()),
            "last_seen_at": datetime.now().isoformat(),
            "search_blob": blob
        }
        
        frontend_products.append(item)
        
    # Validation/Dupe check?
    # JSON output
    print(f"Exporting {len(frontend_products)} products to {OUTPUT_FILE}...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(frontend_products, f, indent=2, ensure_ascii=False)
        
    print("Done.")

if __name__ == "__main__":
    export_frontend()
