import sqlite3
import logging
import sys
from crawler.utils import clean_sku, slugify_supplier, generate_catalog_id, generate_content_hash, normalize_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DB_PATH = "products.db"

def migrate_db():
    logger.info(f"Starting Identity Migration for {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 1. Read all existing data
    try:
        c.execute("SELECT * FROM products")
        rows = c.fetchall()
    except sqlite3.OperationalError:
        logger.error("Could not read products table. Is DB initialized?")
        return

    logger.info(f"Loaded {len(rows)} raw rows.")
    
    # 2. Process rows into new ID map
    # catalog_id -> product_data
    # Handling duplicates by keeping the one with most recent last_seen_at
    
    catalog_map = {}
    duplicates_count = 0
    missing_sku_count = 0
    
    for row in rows:
        data = dict(row)
        
        supplier = data.get('supplier') or 'Unknown'
        sku = data.get('sku')
        
        if not sku:
            # Try to extract SKU from URL or other means if critical
            # For this strict migration, we might drop them or auto-generate fallback
            # But requirements said "Fail ingestion if SKU missing", for migration we flag them.
            missing_sku_count += 1
            logger.warning(f"Row missing SKU: {data.get('url')} (ID: {data.get('product_id')})")
            continue
            
        try:
            cat_id = generate_catalog_id(supplier, sku)
        except Exception as e:
            logger.error(f"Error generating ID: {e}")
            continue
            
        # Compute new fields
        data['catalog_id'] = cat_id
        data['sku_clean'] = clean_sku(sku)
        data['supplier_slug'] = slugify_supplier(supplier)
        
        # Ensure previous field consistency
        if 'url_clean' not in data or not data['url_clean']:
            data['url_clean'] = normalize_url(data.get('url'))
            
        # Deduplication Logic
        if cat_id in catalog_map:
            duplicates_count += 1
            existing = catalog_map[cat_id]
            
            # Compare dates
            new_ts = data.get('last_seen_at') or ''
            old_ts = existing.get('last_seen_at') or ''
            
            if new_ts > old_ts:
                # Replace with newer
                catalog_map[cat_id] = data
            else:
                # Keep existing
                pass
        else:
            catalog_map[cat_id] = data

    logger.info(f"Processed {len(rows)} -> {len(catalog_map)} unique catalog items.")
    logger.info(f"Duplicates resolved: {duplicates_count}")
    logger.info(f"Skipped (No SKU): {missing_sku_count}")
    
    # 3. recreate table with new schema
    # Rename old table
    c.execute("DROP TABLE IF EXISTS products_backup_v2")
    c.execute("ALTER TABLE products RENAME TO products_backup_v2")
    
    # Create new table (Schema matches Pipeline._init_db)
    # Note: 'images' is TEXT (json string)
    c.execute('''CREATE TABLE products
                 (catalog_id TEXT PRIMARY KEY,
                  product_id TEXT,
                  supplier_slug TEXT,
                  sku_clean TEXT,
                  supplier TEXT,
                  url TEXT,
                  url_clean TEXT,
                  title TEXT,
                  sku TEXT,
                  category_path TEXT,
                  description TEXT,
                  properties TEXT,
                  images TEXT,
                  price REAL,
                  currency TEXT,
                  availability TEXT,
                  variants TEXT,
                  raw TEXT,
                  content_hash TEXT,
                  first_seen_at TIMESTAMP,
                  last_seen_at TIMESTAMP)''')
                  
    # 4. Insert data
    items = list(catalog_map.values())
    if items:
        # Sort items by catalog_id for clean index
        items.sort(key=lambda x: x['catalog_id'])
        
        # Determine columns dynamically from first item
        # But we must ensure they match the table schema columns
        # Let's map explicitly to be safe
        
        schema_cols = [
            'catalog_id', 'product_id', 'supplier_slug', 'sku_clean',
            'supplier', 'url', 'url_clean', 'title', 'sku',
            'category_path', 'description', 'properties', 'images',
            'price', 'currency', 'availability', 'variants', 'raw',
            'content_hash', 'first_seen_at', 'last_seen_at'
        ]
        
        insert_sql = f"INSERT INTO products ({','.join(schema_cols)}) VALUES ({','.join(['?']*len(schema_cols))})"
        
        batch_data = []
        for item in items:
            row_vals = []
            for col in schema_cols:
                row_vals.append(item.get(col))
            batch_data.append(row_vals)
            
        c.executemany(insert_sql, batch_data)
        logger.info(f"Inserted {len(batch_data)} rows into new table.")
        
    # Indices
    c.execute("CREATE INDEX IF NOT EXISTS idx_url_clean ON products(url_clean)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_supplier ON products(supplier)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_catalog_lookup ON products(supplier_slug, sku_clean)")
    
    conn.commit()
    conn.close()
    logger.info("Migration Complete. Backup stored in 'products_backup_v2'.")

if __name__ == "__main__":
    migrate_db()
