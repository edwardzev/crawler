import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from crawler.sitemap import SitemapCrawler

def main():
    base_url = "https://www.zeus.co.il/"
    print(f"Starting SitemapCrawler for {base_url}...")
    
    # SitemapCrawler uses base_url to find robots.txt or sitemap.xml
    # zeus.yaml has sitemap_url: "http://www.zeus.co.il/sitemap.xml"
    # The SitemapCrawler might need strict sitemap URL if auto-discovery fails.
    # Let's check crawler/sitemap.py logic briefly if needed, but usually it tries robots.txt.
    
    crawler = SitemapCrawler(base_url)
    # Force sitemap URL if not auto-discovered (Zeus robots.txt has it)
    crawler.sitemap_url = "http://www.zeus.co.il/sitemap.xml" 
    
    urls = crawler.get_product_urls()
    
    print(f"Total Unique URLs found in sitemap: {len(urls)}")
    
    # Print sample
    print("\nSample URLs:")
    for u in urls[:5]:
        print(f" - {u}")

if __name__ == "__main__":
    main()
