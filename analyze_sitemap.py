import sys
import os
import re

# Add current dir to path
sys.path.append(os.getcwd())

from crawler.sitemap import SitemapCrawler

def get_sku_from_url(url):
    match = re.search(r'(?:^|/)(\d+)[^/]*$', url)
    if match:
        return match.group(1)
    return None

def main():
    base_url = "https://www.comfort-gifts.com"
    print(f"Starting SitemapCrawler for {base_url}...")
    
    crawler = SitemapCrawler(base_url)
    urls = crawler.get_product_urls()
    
    print(f"Fetched {len(urls)} URLs from sitemap.")
    
    skus = {}
    for url in urls:
        sku = get_sku_from_url(url)
        if sku:
            if sku not in skus:
                skus[sku] = []
            skus[sku].append(url)
            
    print(f"\n--- Final Analysis ---")
    print(f"Total URLs: {len(urls)}")
    print(f"Unique SKUs: {len(skus)}")
    
    dupes = {k:v for k,v in skus.items() if len(v) > 1}
    print(f"SKUs with multiple URLs: {len(dupes)}")
    
    if dupes:
        print("\nTop 5 Duplicates:")
        for sku, urls in list(dupes.items())[:5]:
            print(f"SKU {sku}: {len(urls)} URLs")
            for u in urls:
                print(f"  - {u}")

if __name__ == "__main__":
    main()
