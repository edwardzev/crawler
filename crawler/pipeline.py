import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, Any
import logging
from crawler.models import Product
from crawler.utils import normalize_url, generate_legacy_hash_id, generate_content_hash

logger = logging.getLogger(__name__)

class DataPipeline:
    def __init__(self, db_path: str):
        self.db_path = db_path
        logger.info(f"Initialized DataPipeline with DB: {self.db_path}")
        self._init_db()
        
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if not c.fetchone():
            # Initial create with new schema
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
                          color TEXT,
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
            c.execute("CREATE INDEX IF NOT EXISTS idx_url_clean ON products(url_clean)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_supplier ON products(supplier)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_catalog_lookup ON products(supplier_slug, sku_clean)")
        else:
            # Check for column updates
            c.execute("PRAGMA table_info(products)")
            columns = [row[1] for row in c.fetchall()]
            
            new_cols = {
                'catalog_id': 'TEXT',
                'sku_clean': 'TEXT',
                'supplier_slug': 'TEXT',
                'color': 'TEXT'
            }
            
            for col, dtype in new_cols.items():
                if col not in columns:
                    logger.info(f"Migrating DB: Adding {col} column")
                    c.execute(f"ALTER TABLE products ADD COLUMN {col} {dtype}")
            
            # Note: Changing PRIMARY KEY requires full migration (Done in migrate_identity.py)
                
        conn.commit()
        conn.close()
        
    def process_item(self, item_data: Dict[str, Any]):
        try:
            # Add system fields if missing
            now = datetime.now(timezone.utc)
            item_data['first_seen_at'] = now
            item_data['last_seen_at'] = now
            
            # 1. URL Normalization
            raw_url = item_data.get('url', '')
            clean_url = normalize_url(raw_url)
            item_data['url_clean'] = clean_url
            
            # 2. Identity Generation
            supplier = item_data.get('supplier', 'Unknown')
            sku = item_data.get('sku')
            
            if not sku:
                logger.error(f"SKU Missing for {clean_url}. Skipping ingestion.")
                return

            from crawler.utils import clean_sku, slugify_supplier, generate_catalog_id
            
            item_data['sku_clean'] = clean_sku(sku)
            item_data['supplier_slug'] = slugify_supplier(supplier)
            item_data['catalog_id'] = generate_catalog_id(supplier, sku)
            
            # Legacy ID (Keep for DB backward compatibility, but system uses catalog_id)
            item_data['product_id'] = item_data['catalog_id']
            item_data['legacy_hash_id'] = generate_legacy_hash_id(supplier, sku, clean_url)
            
            # Specific cleanup for Comfort (remove HTML)
            if supplier == 'Comfort' and item_data.get('description'):
                try:
                    soup = BeautifulSoup(item_data['description'], 'html.parser')
                    # Get text with separator to avoid merging lines
                    text = soup.get_text(separator=' ', strip=True)
                    item_data['description'] = text
                except Exception as e:
                    logger.warning(f"Failed to clean description for {sku}: {e}")

            # 3. Stable Content Hash (Excluding timestamps)
            item_data['content_hash'] = generate_content_hash(item_data)
            
            # 4. Derive Color from Variants if available
            # Variants often contain color names. We want to extract them into a string.
            if item_data.get('variants'):
                 # We expect variants to be a list of dicts like [{"name": "Red"}, {"name": "Blue"}] or strings (if parser logic changed)
                 # Based on core.py it's normalized to [{"name": "..."}]
                 colors = []
                 for v in item_data['variants']:
                     if isinstance(v, dict) and 'name' in v:
                         name = v['name']
                         # Filter out generic labels often found in Hebrew sites
                         if name not in ["צבע", "בחר צבע", "בחר", "Color", "Select Color"]:
                             colors.append(name)
                 
                 if colors:
                     item_data['color'] = ", ".join(sorted(list(set(colors))))

            
            # Validate with Pydantic
            product = Product(**item_data)
            
            self._save_to_db(product)
            logger.info(f"Saved product: {product.title} ({product.catalog_id})")
            
        except Exception as e:
            logger.error(f"Validation or Storage error: {e}")

    def _save_to_db(self, product: Product):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Serialize complex types
        data = product.model_dump()
        data['category_path'] = json.dumps(data['category_path'], ensure_ascii=False)
        data['properties'] = json.dumps(data['properties'], ensure_ascii=False)
        data['images'] = json.dumps([str(u) for u in data['images']], ensure_ascii=False)
        data['variants'] = json.dumps(data['variants'], ensure_ascii=False)
        data['raw'] = json.dumps(data['raw'], ensure_ascii=False)
        data['url'] = str(data['url'])
        if data.get('url_clean'):
             data['url_clean'] = str(data['url_clean'])
        
        # Remove legacy_hash_id - column doesn't exist in DB schema
        if 'legacy_hash_id' in data:
            del data['legacy_hash_id']
        
        # Upsert using catalog_id
        keys = list(data.keys())
        placeholders = ",".join(["?"] * len(keys))
        columns = ",".join(keys)
        
        # Check if we assume catalog_id is PRIMARY KEY or UNIQUE
        # If running on old DB before migration, this might fail unless we migrated schema.
        # But this code is for FUTURE ingestion.
        
        query = f"""INSERT INTO products ({columns}) VALUES ({placeholders})
                    ON CONFLICT(catalog_id) DO UPDATE SET
                    last_seen_at=excluded.last_seen_at,
                    content_hash=excluded.content_hash,
                    price=excluded.price,
                    availability=excluded.availability,
                    properties=excluded.properties,
                    category_path=excluded.category_path,
                    title=excluded.title,
                    sku=excluded.sku,
                    description=excluded.description,
                    color=excluded.color,
                    images=excluded.images,
                    url_clean=excluded.url_clean,
                    product_id=excluded.product_id
                    """
        
        try:
            c.execute(query, list(data.values()))
            conn.commit()
        except sqlite3.OperationalError as e:
            logger.error(f"DB Error (Schema Mismatch?): {e}")
            # Fallback for during-migration state or if conflict target missing
        finally:
            conn.close()
        
    def run_migration(self):
        """
        One-time migration to:
        1. Backfill url_clean
        2. Recalculate all product_ids
        3. Deduplicate based on new IDs
        """
        logger.info("Starting Database Migration & Deduplication...")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Load all existing rows
        c.execute("SELECT * FROM products")
        rows = c.fetchall()
        logger.info(f"Loaded {len(rows)} rows for processing.")
        
        # In-memory deduplication: {new_product_id: row_data}
        deduped_map = {}
        
        for row in rows:
            data = dict(row)
            
            # Recalculate key fields
            raw_url = data.get('url', '')
            clean_url = normalize_url(raw_url)
            supplier = data.get('supplier', 'Unknown')
            sku = data.get('sku')
            
            new_id = generate_catalog_id(supplier, sku)
            legacy_hash = generate_legacy_hash_id(supplier, sku, clean_url)
            
            # Check conflict
            if new_id in deduped_map:
                existing = deduped_map[new_id]
                # Compare timestamps (ISO strings)
                new_ts = data.get('last_seen_at') or ''
                old_ts = existing.get('last_seen_at') or ''
                if new_ts > old_ts:
                    # Replace with newer
                    data['product_id'] = new_id
                    data['url_clean'] = clean_url
                    deduped_map[new_id] = data
            else:
                data['product_id'] = new_id
                data['url_clean'] = clean_url
                deduped_map[new_id] = data
                
        logger.info(f"Deduplication complete. Retaining {len(deduped_map)} unique records.")
        
        # Create temp table
        c.execute("DROP TABLE IF EXISTS products_new")
        c.execute('''CREATE TABLE products_new
                     (product_id TEXT PRIMARY KEY,
                      supplier TEXT,
                      url TEXT,
                      url_clean TEXT,
                      title TEXT,
                      sku TEXT,
                      category_path TEXT,
                      description TEXT,
                      color TEXT,
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
                      
        # Insert deduped data
        items = list(deduped_map.values())
        if items:
            keys = list(items[0].keys())
            columns = ",".join(keys)
            placeholders = ",".join(["?"] * len(keys))
            query = f"INSERT INTO products_new ({columns}) VALUES ({placeholders})"
            
            batch = [list(item.values()) for item in items]
            c.executemany(query, batch)
            
        # Swap tables
        c.execute("DROP TABLE products")
        c.execute("ALTER TABLE products_new RENAME TO products")
        c.execute("CREATE INDEX IF NOT EXISTS idx_url_clean ON products(url_clean)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_supplier ON products(supplier)")
        
        conn.commit()
        conn.close()
        logger.info("Migration successful.")

    def export_data(self, output_path: str, fmt: str = "csv"):
        import pandas as pd
        
        conn = sqlite3.connect(self.db_path)
        
        # Debug DB content
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        logger.info(f"DB Tables: {tables}")
        
        if tables:
            cursor.execute(f"SELECT count(*) FROM {tables[0][0]}")
            count = cursor.fetchone()[0]
            logger.info(f"Row count in {tables[0][0]}: {count}")
        
        try:
            df = pd.read_sql_query("SELECT * FROM products", conn)
        except Exception as e:
            logger.error(f"Pandas read error: {e}")
            conn.close()
            return

        conn.close()
        
        if df.empty:
            logger.warning("No data to export.")
            return

        # Deserialize JSON fields for better usability if needed, 
        # but for flat CSV/Excel, string representation might be safer.
        # For true JSON export, we should deserialize.
        json_cols = ["category_path", "properties", "images", "variants", "raw"]
        
        # Clean up JSON fields for export
        for col in json_cols:
            if col in df.columns:
                def clean_json(val):
                    if not val: return ""
                    try:
                        parsed = json.loads(val)
                        if isinstance(parsed, list):
                            return " > ".join(parsed) if col == "category_path" else ", ".join(parsed)
                        return val
                    except:
                        return val
                df[col] = df[col].apply(clean_json)

        # Ensure order includes url_clean if present
        if 'url_clean' in df.columns:
             # Reorder to put url_clean near url
             cols = df.columns.tolist()
             if 'url' in cols and 'url_clean' in cols:
                 cols.remove('url_clean')
                 url_idx = cols.index('url')
                 cols.insert(url_idx + 1, 'url_clean')
                 df = df[cols]

        if fmt == "json":
            df.to_json(output_path, orient="records", indent=2, date_format="iso")
            
        elif fmt == "csv":
            df.to_csv(output_path, index=False)
            
        elif fmt == "xlsx":
            df.to_excel(output_path, index=False)
            
        logger.info(f"Exported {len(df)} records to {output_path}")

