import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, Any
import logging
from crawler.models import Product
from crawler.utils import generate_id

logger = logging.getLogger(__name__)

class DataPipeline:
    def __init__(self, db_path: str):
        self.db_path = db_path
        logger.info(f"Initialized DataPipeline with DB: {self.db_path}")
        self._init_db()
        
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Schema matching Product model
        c.execute('''CREATE TABLE IF NOT EXISTS products
                     (product_id TEXT PRIMARY KEY,
                      supplier TEXT,
                      url TEXT,
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
        conn.commit()
        conn.close()
        
    def process_item(self, item_data: Dict[str, Any]):
        try:
            # Add system fields if missing
            now = datetime.now(timezone.utc)
            item_data['first_seen_at'] = now
            item_data['last_seen_at'] = now
            
            # Generate ID based on URL or SKU+Supplier
            # Using URL hash for simplicity as primary key for now
            url = item_data.get('url', '')
            item_data['product_id'] = generate_id(url)
            
            # Content hash to check changes
            content_str = json.dumps(item_data, sort_keys=True, default=str)
            item_data['content_hash'] = generate_id(content_str)
            
            # Validate with Pydantic
            product = Product(**item_data)
            
            self._save_to_db(product)
            logger.info(f"Saved product: {product.title} ({product.product_id})")
            
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
        
        # Upsert
        keys = list(data.keys())
        placeholders = ",".join(["?"] * len(keys))
        columns = ",".join(keys)
        
        query = f"""INSERT INTO products ({columns}) VALUES ({placeholders})
                    ON CONFLICT(product_id) DO UPDATE SET
                    last_seen_at=excluded.last_seen_at,
                    content_hash=excluded.content_hash,
                    price=excluded.price,
                    availability=excluded.availability,
                    properties=excluded.properties,
                    category_path=excluded.category_path,
                    title=excluded.title,
                    sku=excluded.sku,
                    description=excluded.description,
                    images=excluded.images
                    """
        
        c.execute(query, list(data.values()))
        conn.commit()
        conn.close()
        
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

        if fmt == "json":
            df.to_json(output_path, orient="records", indent=2, date_format="iso")
            
        elif fmt == "csv":
            df.to_csv(output_path, index=False)
            
        elif fmt == "xlsx":
            df.to_excel(output_path, index=False)
            
        logger.info(f"Exported {len(df)} records to {output_path}")

