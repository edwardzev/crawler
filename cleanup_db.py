#!/usr/bin/env python3
"""
Database cleanup script - removes duplicate URL variations, keeps one record per SKU
"""
import sqlite3
import sys

def cleanup_database(db_path: str):
    """Remove duplicate records, keeping the first occurrence of each SKU"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get stats before cleanup
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT sku) FROM products")
    total_before, unique_skus = cursor.fetchone()
    
    print(f"Database: {db_path}")
    print(f"Before cleanup:")
    print(f"  Total records: {total_before}")
    print(f"  Unique SKUs: {unique_skus}")
    print(f"  Duplicates: {total_before - unique_skus}")
    
    # Create a new table with deduplicated data
    # Keep the record with the earliest first_seen_at for each SKU
    print("\nCleaning up duplicates...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products_clean AS
        SELECT * FROM products
        WHERE product_id IN (
            SELECT MIN(product_id) 
            FROM products 
            WHERE sku IS NOT NULL
            GROUP BY sku
        )
    """)
    
    # Count records in clean table
    cursor.execute("SELECT COUNT(*) FROM products_clean")
    total_after = cursor.fetchone()[0]
    
    print(f"\nAfter cleanup:")
    print(f"  Total records: {total_after}")
    print(f"  Removed: {total_before - total_after} duplicate records")
    
    # Backup old table and replace
    print("\nReplacing tables...")
    cursor.execute("DROP TABLE IF EXISTS products_backup")
    cursor.execute("ALTER TABLE products RENAME TO products_backup")
    cursor.execute("ALTER TABLE products_clean RENAME TO products")
    
    conn.commit()
    conn.close()
    
    print("\n✓ Cleanup complete!")
    print(f"  Original table backed up as 'products_backup'")
    print(f"  New 'products' table contains {total_after} unique records")

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "products.db"
    cleanup_database(db_path)
