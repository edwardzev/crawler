import requests
import xml.etree.ElementTree as ET
from typing import List, Set
import logging

logger = logging.getLogger(__name__)

class SitemapCrawler:
    """Fast crawler that uses sitemap.xml to get direct product URLs"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
    def get_product_urls(self) -> List[str]:
        """Fetch all product URLs from sitemap"""
        product_urls = []
        
        # Step 1: Get sitemap index
        try:
            index_url = f"{self.base_url}/sitemap.xml"
            logger.info(f"Fetching sitemap index: {index_url}")
            response = requests.get(index_url, timeout=10)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            ns = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # Get all sitemap URLs
            sitemap_locs = root.findall('.//sitemap:loc', ns)
            sitemap_urls = [loc.text for loc in sitemap_locs if loc.text]
            
            # Filter for main sitemaps (not image sitemaps)
            main_sitemaps = [url for url in sitemap_urls if 'image-sitemap' not in url]
            logger.info(f"Found {len(main_sitemaps)} main sitemaps")
            
            # Step 2: Fetch each sitemap and extract product URLs
            for sitemap_url in main_sitemaps:
                logger.info(f"Fetching: {sitemap_url}")
                try:
                    resp = requests.get(sitemap_url, timeout=10)
                    resp.raise_for_status()
                    
                    # Check if it's a sitemap index or urlset
                    sitemap_root = ET.fromstring(resp.content)
                    
                    # Try urlset format first
                    url_locs = sitemap_root.findall('.//sitemap:loc', ns)
                    
                    # If it's another index, recurse
                    if url_locs and 'sitemap-' in url_locs[0].text:
                        for sub_url in url_locs:
                            sub_resp = requests.get(sub_url.text, timeout=10)
                            sub_root = ET.fromstring(sub_resp.content)
                            urls = sub_root.findall('.//sitemap:loc', ns)
                            product_urls.extend([u.text for u in urls if u.text and '/product/' in u.text])
                    else:
                        # Direct urlset
                        urls = sitemap_root.findall('.//sitemap:loc', ns)
                        product_urls.extend([u.text for u in urls if u.text and '/product/' in u.text])
                        
                except Exception as e:
                    logger.error(f"Failed to fetch {sitemap_url}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to fetch sitemap index: {e}")
            return []
        
        # Deduplicate
        unique_urls = list(set(product_urls))
        logger.info(f"Found {len(unique_urls)} unique product URLs")
        return unique_urls
