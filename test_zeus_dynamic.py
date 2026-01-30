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
print("=" * 80)

# Test with DYNAMIC fetching (Playwright)
print("\n### TESTING WITH DYNAMIC FETCHING (Playwright) ###\n")
fetcher = HTMLFetcher()
html_dynamic = fetcher.fetch_dynamic(test_url)

if html_dynamic:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_dynamic, 'html.parser')
    
    print("1. Current selector: #thumbGalleryDetail a.lightbox_group")
    thumbs = soup.select("#thumbGalleryDetail a.lightbox_group")
    print(f"   Found {len(thumbs)} elements")
    for i, thumb in enumerate(thumbs[:5]):
        print(f"   [{i}] href: {thumb.get('href')}")
    
    print("\n2. Looking for img tags in #thumbGalleryDetail")
    imgs = soup.select("#thumbGalleryDetail img")
    print(f"   Found {len(imgs)} img elements")
    for i, img in enumerate(imgs[:5]):
        print(f"   [{i}] src: {img.get('src')}")
    
    print("\n3. Looking for main product image area")
    main_area = soup.select("#mainImage, .main-image, .product-image-container")
    print(f"   Found {len(main_area)} main image containers")
    for i, area in enumerate(main_area[:3]):
        print(f"   [{i}] {area.name} - id: {area.get('id')} class: {area.get('class')}")
        imgs_in_area = area.select("img")
        for j, img in enumerate(imgs_in_area[:3]):
            print(f"       img src: {img.get('src')}")
    
    print("\n4. All img tags on page (first 10)")
    all_imgs = soup.select("img")
    print(f"   Total img tags: {len(all_imgs)}")
    for i, img in enumerate(all_imgs[:10]):
        src = img.get('src', '')
        if 'product' in src.lower() or 'upload' in src.lower():
            print(f"   [{i}] src: {src}")
    
    print("\n5. Looking for gallery/slider elements")
    galleries = soup.select("[class*='gallery'], [class*='slider'], [class*='carousel'], [id*='gallery']")
    print(f"   Found {len(galleries)} gallery-like elements")
    for i, gal in enumerate(galleries[:5]):
        print(f"   [{i}] {gal.name} - id: {gal.get('id')} class: {gal.get('class')}")

fetcher.close()
