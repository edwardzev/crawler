import os
import sys
import sqlite3
import json
import argparse
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

load_dotenv()

# Cloudinary Config
url = os.getenv("CLOUDINARY_URL")
if not url:
    print("WARNING: CLOUDINARY_URL not found in env.")
else:
    # Manual Configuration to ensure reliability
    try:
        # Expected: cloudinary://api_key:api_secret@cloud_name
        # Remove 'cloudinary://' prefix
        clean_url = url.replace("cloudinary://", "")
        creds, cloud_name = clean_url.split("@")
        api_key, api_secret = creds.split(":")
        
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        print(f"Configured Cloudinary: {cloud_name}")
    except Exception as e:
        print(f"Error parsing CLOUDINARY_URL: {e}")

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE products ADD COLUMN cloudinary_images TEXT")
    except sqlite3.OperationalError:
        pass 
    conn.commit()
    conn.close()

def get_products(db_path: str, suppliers: list[str]):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    placeholders = ",".join(["?"] * len(suppliers))
    query = f"SELECT catalog_id, supplier_slug, sku_clean, images, cloudinary_images FROM products WHERE supplier_slug IN ({placeholders})"
    c.execute(query, suppliers)
    rows = c.fetchall()
    conn.close()
    return rows

def update_product_images(db_path: str, catalog_id: str, cloud_urls: list):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE products SET cloudinary_images = ? WHERE catalog_id = ?", 
              (json.dumps(cloud_urls), catalog_id))
    conn.commit()
    conn.close()

def upload_images(db_path: str, suppliers: list[str], supplier_aliases: dict[str, str]):
    init_db(db_path)
    rows = get_products(db_path, suppliers)
    
    total = len(rows)
    print(f"Found {total} products to process.")
    
    for i, row in enumerate(rows, 1):
        cid = row['catalog_id']
        supplier = row['supplier_slug']
        sku = row['sku_clean']
        
        if row['cloudinary_images']:
            try:
                existing = json.loads(row['cloudinary_images'])
                if existing and len(existing) > 0:
                    if i % 100 == 0: print(f"[{i}/{total}] Skipping {cid} (Already uploaded)")
                    continue
            except:
                pass
        
        if not (supplier and sku):
            # print(f"Skipping {cid}: Missing identity fields")
            continue
            
        images_json = row['images']
        if not images_json:
            continue
            
        try:
            images = json.loads(images_json)
        except:
            continue
            
        cloud_urls = []
        uploaded_any = False
        
        for idx, img_url in enumerate(images, 1):
            if not img_url: continue
            
            idx_str = f"{idx:02d}"
            folder_supplier = supplier_aliases.get(supplier, supplier)
            public_id = f"catalog/products/{folder_supplier}/{sku}/{idx_str}"
            
            try:
                res = cloudinary.uploader.upload(
                    img_url,
                    public_id=public_id,
                    overwrite=False,
                    unique_filename=False,
                    resource_type="image"
                )
                url = res.get('secure_url')
                cloud_urls.append(url)
                uploaded_any = True
                
            except Exception as e:
                print(f"  Error uploading {public_id}: {e}")
                pass
                
        if uploaded_any:
            update_product_images(db_path, cid, cloud_urls)
            print(f"[{i}/{total}] Uploaded {len(cloud_urls)} images for {cid}")
        else:
            if i % 100 == 0: print(f"[{i}/{total}] No images uploaded for {cid}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload product images to Cloudinary")
    parser.add_argument("--db", default="products.db", help="Path to SQLite DB")
    parser.add_argument(
        "--suppliers",
        default="comfort",
        help="Comma-separated supplier slugs to process"
    )
    parser.add_argument(
        "--supplier-alias",
        action="append",
        default=[],
        help="Optional mapping in the form from:to (e.g., wave2:wave)"
    )
    args = parser.parse_args()

    suppliers = [s.strip() for s in args.suppliers.split(",") if s.strip()]
    aliases = {}
    for item in args.supplier_alias:
        if ":" in item:
            src, dest = item.split(":", 1)
            aliases[src.strip()] = dest.strip()

    upload_images(args.db, suppliers, aliases)
