#!/usr/bin/env python3
"""
Re-crawl only Zeus products that are missing images.
This is more efficient than re-crawling all 1,118 products.
"""
import sqlite3
import sys
sys.path.insert(0, '/Users/edwardzev/crawler')

from crawler.core import CrawlerEngine
import yaml

# Load Zeus config
with open('config/zeus.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Get products with missing images
conn = sqlite3.connect('products.db')
cursor = conn.cursor()
cursor.execute("""
    SELECT url 
    FROM products 
    WHERE supplier = 'Zeus' 
    AND (images IS NULL OR images = '' OR images = '[]')
""")
urls_to_recrawl = [row[0] for row in cursor.fetchall()]
conn.close()

print(f"Found {len(urls_to_recrawl)} Zeus products with missing images")
print(f"Starting targeted re-crawl...\n")

# Initialize crawler
crawler = CrawlerEngine(config)

# Seed queue with only the URLs that need images
crawler.seed_queue(urls_to_recrawl)

# Run the crawl
crawler.run()

print(f"\n✅ Re-crawl complete!")
