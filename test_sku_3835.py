#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/edwardzev/crawler')

from crawler.fetcher import HTMLFetcher
from crawler.parser import HTMLParser
import yaml

# Load Zeus config
with open('config/zeus.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Test a product that was just crawled (SKU 3835)
test_url = "https://www.zeus.co.il/product/%D7%A2%D7%9C%D7%94-%D7%96%D7%99%D7%AA-%D7%9E%D7%92%D7%9F-%D7%94%D7%95%D7%A7%D7%A8%D7%94-%D7%9E%D7%96%D7%9B%D7%95%D7%9B%D7%99%D7%AA-%D7%A7%D7%A8%D7%99%D7%A1%D7%98%D7%9C-%D7%91%D7%A1%D7%99%D7%A1-%D7%9E%D7%95%D7%91%D7%A0%D7%94-3835"

print(f"Testing SKU 3835 (just crawled, has empty images in DB)")
print(f"URL: {test_url}")
print(f"Selector: {config['selectors']['images']}\n")

# Fetch the page (static, like the crawler does)
fetcher = HTMLFetcher()
html = fetcher.fetch(test_url)

# Parse
parser = HTMLParser(html)
data = parser.parse_product(config['selectors'])

print(f"Title: {data.get('title')}")
print(f"SKU: {data.get('sku')}")
print(f"Images extracted: {data.get('images')}")
print(f"Number of images: {len(data.get('images', []))}")

if data.get('images'):
    print("\n✅ Selector works correctly")
else:
    print("\n❌ Selector failed - no images extracted")
    
    # Debug
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    lightbox_links = soup.select(".lightbox a.lightbox_group")
    print(f"\nDebug: Found {len(lightbox_links)} .lightbox a.lightbox_group elements")
    for i, link in enumerate(lightbox_links[:3]):
        print(f"  [{i}] href: {link.get('href')}")

fetcher.close()
