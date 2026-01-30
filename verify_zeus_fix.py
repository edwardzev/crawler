#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/edwardzev/crawler')

from crawler.fetcher import HTMLFetcher
from crawler.parser import HTMLParser
import yaml

# Load Zeus config
with open('config/zeus.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Test URL from database (product without images)
test_url = "https://www.zeus.co.il/product/%D7%9E%D7%A2%D7%9E%D7%93-%D7%97%D7%99%D7%99%D7%9C-%D7%A2%D7%9D-%D7%9B%D7%95%D7%A1-%D7%9C%D7%A2%D7%98%D7%99%D7%9D"

print(f"Testing UPDATED selector: {config['selectors']['images']}")
print(f"URL: {test_url}\n")

# Fetch the page
fetcher = HTMLFetcher()
html = fetcher.fetch(test_url)

# Parse with updated selector
parser = HTMLParser(html)
data = parser.parse_product(config['selectors'])

print(f"✓ Title: {data.get('title')}")
print(f"✓ SKU: {data.get('sku')}")
print(f"✓ Images: {data.get('images')}")
print(f"✓ Number of images: {len(data.get('images', []))}")

if data.get('images'):
    print("\n✅ SUCCESS! Images are now being extracted correctly.")
else:
    print("\n❌ FAILED! Still no images found.")

fetcher.close()
