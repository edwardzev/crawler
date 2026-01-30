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

print(f"Testing URL: {test_url}")
print(f"Current image selector: {config['selectors']['images']}")
print("-" * 80)

# Fetch the page
fetcher = HTMLFetcher()
html = fetcher.fetch(test_url)

if not html:
    print("Failed to fetch HTML")
    sys.exit(1)

# Parse with current selector
parser = HTMLParser(html)
data = parser.parse_product(config['selectors'])

print(f"\nExtracted data:")
print(f"Title: {data.get('title')}")
print(f"SKU: {data.get('sku')}")
print(f"Images: {data.get('images')}")
print(f"Number of images: {len(data.get('images', []))}")

# Now let's try alternative selectors
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

print("\n" + "=" * 80)
print("DEBUGGING: Looking for image elements...")
print("=" * 80)

# Check for the current selector
print("\n1. Current selector: #thumbGalleryDetail a.lightbox_group")
thumbs = soup.select("#thumbGalleryDetail a.lightbox_group")
print(f"   Found {len(thumbs)} elements")
for i, thumb in enumerate(thumbs[:3]):
    print(f"   [{i}] href: {thumb.get('href')}")

# Check for img tags in gallery
print("\n2. Looking for img tags in #thumbGalleryDetail")
imgs = soup.select("#thumbGalleryDetail img")
print(f"   Found {len(imgs)} img elements")
for i, img in enumerate(imgs[:3]):
    print(f"   [{i}] src: {img.get('src')}")

# Check for main product image
print("\n3. Looking for main product image")
main_imgs = soup.select(".product_image img, .main-image img, img.product-image")
print(f"   Found {len(main_imgs)} main image elements")
for i, img in enumerate(main_imgs[:3]):
    print(f"   [{i}] src: {img.get('src')}")

# Check for any lightbox links
print("\n4. Looking for any lightbox links")
lightbox = soup.select("a.lightbox, a[rel='lightbox'], a.fancybox")
print(f"   Found {len(lightbox)} lightbox elements")
for i, lb in enumerate(lightbox[:3]):
    print(f"   [{i}] href: {lb.get('href')}")

# Look for data attributes
print("\n5. Looking for data-image attributes")
data_imgs = soup.select("[data-image], [data-src], [data-zoom-image]")
print(f"   Found {len(data_imgs)} elements with data-image attributes")
for i, elem in enumerate(data_imgs[:3]):
    print(f"   [{i}] data-image: {elem.get('data-image')}")
    print(f"   [{i}] data-src: {elem.get('data-src')}")
    print(f"   [{i}] data-zoom-image: {elem.get('data-zoom-image')}")

fetcher.close()
