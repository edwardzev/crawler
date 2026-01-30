#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/edwardzev/crawler')

from crawler.fetcher import HTMLFetcher
from crawler.parser import HTMLParser
import yaml

# Load Zeus config
with open('config/zeus.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Test SKU 4287 that was just crawled
test_url = "https://www.zeus.co.il/product/TEA-TIME-%D7%9E%D7%90%D7%A8%D7%96-%D7%A2%D7%A5-%D7%98%D7%91%D7%A2%D7%99-%D7%9C%D7%AA%D7%94-6-%D7%AA%D7%90%D7%99%D7%9D"

print(f"Testing SKU 4287 (just saved with empty images)")
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
    print("\n✅ Selector works - images extracted")
else:
    print("\n❌ Selector failed - no images")
    
    # Debug
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check if this product even has images
    all_imgs = soup.select("img")
    product_imgs = [img for img in all_imgs if 'catalog' in img.get('src', '').lower() or 'product' in img.get('src', '').lower()]
    print(f"\nFound {len(product_imgs)} product-related img tags")
    for img in product_imgs[:3]:
        print(f"  src: {img.get('src')}")
    
    lightbox_links = soup.select(".lightbox a.lightbox_group")
    print(f"\nFound {len(lightbox_links)} .lightbox a.lightbox_group elements")
    for link in lightbox_links[:3]:
        print(f"  href: {link.get('href')}")

fetcher.close()
