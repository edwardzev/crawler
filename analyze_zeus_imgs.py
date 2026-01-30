#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/edwardzev/crawler')

from crawler.fetcher import HTMLFetcher
from bs4 import BeautifulSoup

test_url = "https://www.zeus.co.il/product/%D7%9E%D7%A2%D7%9E%D7%93-%D7%97%D7%99%D7%99%D7%9C-%D7%A2%D7%9D-%D7%9B%D7%95%D7%A1-%D7%9C%D7%A2%D7%98%D7%99%D7%9D"

print(f"Analyzing: {test_url}\n")

fetcher = HTMLFetcher()
html = fetcher.fetch(test_url)  # Static first

if html:
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find ALL img tags and print their details
    all_imgs = soup.select("img")
    print(f"Total img tags found: {len(all_imgs)}\n")
    
    for i, img in enumerate(all_imgs):
        src = img.get('src', '')
        alt = img.get('alt', '')
        parent = img.parent
        parent_class = parent.get('class', []) if parent else []
        parent_id = parent.get('id', '') if parent else ''
        
        # Only show product-related images
        if any(keyword in src.lower() for keyword in ['upload', 'product', 'item', 'image']):
            print(f"[{i}] IMG:")
            print(f"    src: {src}")
            print(f"    alt: {alt}")
            print(f"    parent: <{parent.name if parent else 'none'}> id='{parent_id}' class={parent_class}")
            
            # Check grandparent
            if parent and parent.parent:
                gp = parent.parent
                print(f"    grandparent: <{gp.name}> id='{gp.get('id', '')}' class={gp.get('class', [])}")
            print()

fetcher.close()
