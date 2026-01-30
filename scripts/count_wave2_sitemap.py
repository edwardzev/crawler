
import requests
import xml.etree.ElementTree as ET

def count_sitemap_urls(sitemap_url):
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        # Namespace is usually http://www.sitemaps.org/schemas/sitemap/0.9
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = root.findall('ns:url/ns:loc', namespace)
        return len(urls), [u.text for u in urls]
    except Exception as e:
        print(f"Error fetching {sitemap_url}: {e}")
        return 0, []

def main():
    sitemaps = [
        "https://www.wave2.co.il/product-sitemap.xml",
        "https://www.wave2.co.il/product-sitemap2.xml"
    ]
    
    total_count = 0
    all_urls = set()
    
    for sm in sitemaps:
        print(f"Checking {sm}...")
        count, urls = count_sitemap_urls(sm)
        print(f"Found {count} URLs in {sm}")
        total_count += count
        all_urls.update(urls)
        
    print(f"\nTotal URLs found: {total_count}")
    print(f"Unique URLs: {len(all_urls)}")

if __name__ == "__main__":
    main()
