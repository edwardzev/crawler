#!/usr/bin/env python3
"""
Script to add a test product with color variants to the database.
This demonstrates the new variant field support.
"""

import sqlite3
import json
import sys
from pathlib import Path

def add_test_product_with_variants():
    db_path = "products.db"
    
    # Test product data
    product = {
        "catalog_id": "test-supplier:tshirt-001",
        "product_id": "legacy-id-001",
        "supplier_slug": "test-supplier",
        "sku_clean": "tshirt-001",
        "supplier": "Test Supplier",
        "url": "https://example.com/tshirt-001",
        "url_clean": "https://example.com/tshirt-001",
        "title": "Premium Cotton T-Shirt",
        "sku": "TSHIRT-001",
        "category_path": json.dumps(["Clothing", "T-Shirts"]),
        "description": "High-quality cotton t-shirt available in multiple colors",
        "color": "Various",  # Legacy color field
        "properties": json.dumps({
            "Material": "100% Cotton",
            "Weight": "180 GSM",
            "Fit": "Regular"
        }),
        "images": json.dumps([
            "https://via.placeholder.com/400/000000/FFFFFF?text=Black",
            "https://via.placeholder.com/400/FFFFFF/000000?text=White",
            "https://via.placeholder.com/400/000080/FFFFFF?text=Navy"
        ]),
        "price": 49.90,
        "currency": "ILS",
        "availability": "In Stock",
        "variants": json.dumps([]),  # Legacy variants field (array)
        "variant": json.dumps({  # NEW: Structured variant field
            "type": "color",
            "options": [
                {"value": "black", "label": "שחור"},
                {"value": "white", "label": "לבן"},
                {"value": "navy", "label": "כחול נייבי"}
            ]
        }),
        "raw": json.dumps({}),
        "content_hash": "test-hash-001"
    }
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if not c.fetchone():
            print("❌ Database table 'products' does not exist.")
            print("   Run the crawler first to initialize the database.")
            return False
        
        # Check if variant column exists
        c.execute("PRAGMA table_info(products)")
        columns = [row[1] for row in c.fetchall()]
        
        if 'variant' not in columns:
            print("⚠️  Adding 'variant' column to database...")
            c.execute("ALTER TABLE products ADD COLUMN variant TEXT")
            conn.commit()
        
        # Insert or replace test product
        columns_list = list(product.keys())
        placeholders = ','.join(['?' for _ in columns_list])
        columns_str = ','.join(columns_list)
        
        query = f"""
            INSERT OR REPLACE INTO products ({columns_str})
            VALUES ({placeholders})
        """
        
        c.execute(query, list(product.values()))
        conn.commit()
        
        print("✅ Test product added successfully!")
        print(f"   Catalog ID: {product['catalog_id']}")
        print(f"   Title: {product['title']}")
        print(f"   SKU: {product['sku']}")
        print(f"   Variants: {len(json.loads(product['variant'])['options'])} colors")
        
        # Verify
        c.execute("SELECT catalog_id, title, variant FROM products WHERE catalog_id = ?", 
                  (product['catalog_id'],))
        row = c.fetchone()
        
        if row:
            variant_data = json.loads(row[2]) if row[2] else None
            print(f"\n✅ Verification successful!")
            print(f"   Product: {row[1]}")
            if variant_data:
                print(f"   Variant Type: {variant_data.get('type')}")
                print(f"   Options: {', '.join([opt['label'] for opt in variant_data['options']])}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Adding test product with color variants...\n")
    success = add_test_product_with_variants()
    sys.exit(0 if success else 1)
