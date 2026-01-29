import sqlite3
import os
import json
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OLD_DB = "/Users/edwardzev/crawler/crawler1/products.db"
NEW_DB = "products.db"

def merge():
    if not os.path.exists(OLD_DB):
        logger.error(f"Source DB missing: {OLD_DB}")
        return

    logger.info(f"Connecting to source: {OLD_DB}")
    conn_old = sqlite3.connect(OLD_DB)
    conn_old.row_factory = sqlite3.Row
    rows_old = conn_old.execute("SELECT * FROM products").fetchall()
    logger.info(f"Loaded {len(rows_old)} products from legacy DB.")

    logger.info(f"Connecting to target: {NEW_DB}")
    conn_new = sqlite3.connect(NEW_DB)
    # Ensure current table has catalog_id
    try:
        conn_new.execute("ALTER TABLE products ADD COLUMN catalog_id TEXT")
    except:
        pass # Already exists
        
    try:
        conn_new.execute("ALTER TABLE products ADD COLUMN sku_clean TEXT")
    except:
        pass
        
    try:
        conn_new.execute("ALTER TABLE products ADD COLUMN supplier_slug TEXT")
    except:
        pass

    # Helper functions from utils (inlined for safety)
    import re
    def clean_sku(raw):
        if not raw: return ""
        s = str(raw).strip().upper()
        s = s.replace(" ", "_").replace("/", "-")
        s = re.sub(r"[^A-Z0-9_\-]", "", s)
        return re.sub(r"_+", "_", re.sub(r"-+", "-", s)).strip("_-")

    def slugify_supplier(raw):
        if not raw: return ""
        s = str(raw).strip().lower().replace(" ", "-")
        s = re.sub(r"[^a-z0-9\-]", "-", s)
        return re.sub(r"-+", "-", s).strip("-")

    def generate_catalog_id(supplier, sku):
        s_slug = slugify_supplier(supplier)
        s_clean = clean_sku(sku)
        if not s_clean: return ""
        return f"{s_slug}:{s_clean}"

    # Merge stats
    added = 0
    updated = 0
    skipped = 0

    for row in rows_old:
        data = dict(row)
        supplier = data.get('supplier', 'Unknown')
        sku = data.get('sku')
        
        if not sku:
            # Try to find SKU in raw or title if missing? 
            # In crawler1, products had SKU.
            skipped += 1
            continue

        cid = generate_catalog_id(supplier, sku)
        if not cid:
            skipped += 1
            continue
            
        data['catalog_id'] = cid
        data['sku_clean'] = clean_sku(sku)
        data['supplier_slug'] = slugify_supplier(supplier)

        # Upsert logic
        keys = list(data.keys())
        placeholders = ",".join(["?"] * len(keys))
        columns = ",".join(keys)
        
        # We use catalog_id as the merge key
        # Check if exists
        existing = conn_new.execute("SELECT first_seen_at FROM products WHERE catalog_id = ?", (cid,)).fetchone()
        
        if existing:
            # Update
            set_clause = ", ".join([f"{k}=excluded.{k}" for k in keys if k != 'catalog_id' and k != 'first_seen_at' and k != 'product_id'])
            query = f"""INSERT INTO products ({columns}) VALUES ({placeholders})
                        ON CONFLICT(catalog_id) DO UPDATE SET {set_clause}"""
            # Note: The above ON CONFLICT requires catalog_id to be UNIQUE or PK.
            # If not yet PK, we'll do a simple UPDATE.
            try:
                # Try INSERT/UPDATE
                conn_new.execute(query, list(data.values()))
                updated += 1
            except sqlite3.OperationalError:
                # Fallback to manual update if ON CONFLICT fails
                upd_keys = [k for k in keys if k != 'catalog_id']
                upd_placeholders = ", ".join([f"{k}=?" for k in upd_keys])
                conn_new.execute(f"UPDATE products SET {upd_placeholders} WHERE catalog_id=?", list(data[k] for k in upd_keys) + [cid])
                updated += 1
        else:
            # Insert
            try:
                conn_new.execute(f"INSERT INTO products ({columns}) VALUES ({placeholders})", list(data.values()))
                added += 1
            except sqlite3.IntegrityError:
                # Product ID conflict?
                updated += 1

    conn_new.commit()
    conn_new.close()
    conn_old.close()

    logger.info(f"Merge Summary: Added {added}, Updated {updated}, Skipped {skipped}")

if __name__ == "__main__":
    merge()
