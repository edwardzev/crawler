import sqlite3
import re
import sys

print("Step 1: Starting")
from crawler.sitemap import SitemapCrawler
sc = SitemapCrawler("https://www.comfort-gifts.com/")
print("Step 2: Fetching URLs")
urls = sc.get_product_urls()
print(f"Step 3: Found {len(urls)} URLs")

conn = sqlite3.connect('products.db')
cur = conn.cursor()
cur.execute("SELECT sku_clean FROM products WHERE supplier = 'Comfort Gifts'")
existing_skus = {row[0].upper() for row in cur.fetchall() if row[0]}
print(f"Step 4: DB has {len(existing_skus)} SKUs")

new_skus = []
for url in urls:
    match = re.search(r'(?:^|/)(\d+)[^/]*$', url)
    if match:
        sku = match.group(1).upper()
        if sku not in existing_skus:
            new_skus.append((sku, url))

print(f"Step 5: New SKUs: {len(new_skus)}")
for s, u in new_skus[:5]:
    print(f"  {s}: {u}")
