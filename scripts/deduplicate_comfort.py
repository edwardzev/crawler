import sqlite3
import json
import logging

DB_PATH = "products.db"
SUPPLIER = "Comfort Gifts"

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

def deduplicate():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Get all Comfort Gifts products
    cursor.execute("SELECT rowid, sku, category_path, url FROM products WHERE supplier = ?", (SUPPLIER,))
    rows = cursor.fetchall()

    logger.info(f"Total rows for {SUPPLIER}: {len(rows)}")

    # 2. Group by SKU
    sku_groups = {}
    for row in rows:
        sku = row['sku']
        if not sku:
            continue
        
        if sku not in sku_groups:
            sku_groups[sku] = []
        sku_groups[sku].append(row)

    logger.info(f"Unique SKUs: {len(sku_groups)}")

    ids_to_delete = []
    
    # 3. Pick winner for each group
    for sku, group in sku_groups.items():
        if len(group) == 1:
            continue
        
        # Sort by category path length (descending), then URL length (descending)
        # We assume richer data has longer category strings/lists
        def score(row):
            cat = row['category_path'] or ""
            return (len(cat), len(row['url'] or ""))

        sorted_group = sorted(group, key=score, reverse=True)
        winner = sorted_group[0]
        losers = sorted_group[1:]

        for loser in losers:
            ids_to_delete.append(loser['rowid'])
            
    logger.info(f"Found {len(ids_to_delete)} duplicate records to delete.")

    # 4. Delete
    if ids_to_delete:
        placeholders = ', '.join(['?'] * len(ids_to_delete))
        cursor.execute(f"DELETE FROM products WHERE rowid IN ({placeholders})", ids_to_delete)
        conn.commit()
        logger.info("Deletion complete.")
    else:
        logger.info("No duplicates found to delete.")

    # 5. Verify final count
    cursor.execute("SELECT count(*) FROM products WHERE supplier = ?", (SUPPLIER,))
    final_count = cursor.fetchone()[0]
    logger.info(f"Final count for {SUPPLIER}: {final_count}")

    conn.close()

if __name__ == "__main__":
    deduplicate()
