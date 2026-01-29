import requests
import xml.etree.ElementTree as ET
from typing import List, Set
import logging
import re
import time

logger = logging.getLogger(__name__)

class SitemapCrawler:
    """Fast crawler that uses sitemap.xml to get direct product URLs"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
    def get_product_urls(self) -> List[str]:
        """Fetch all product URLs from sitemap with fallback to browser for captchas"""
        product_urls = []
        index_url = self.base_url + "/sitemap.xml"
        if self.base_url.endswith("sitemap.xml"):
            index_url = self.base_url

        logger.info(f"Fetching sitemap via requests: {index_url}")
        content = ""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5"
            }
            resp = requests.get(index_url, headers=headers, timeout=30)
            if resp.status_code == 200:
                content = resp.text
        except Exception as e:
            logger.warning(f"Direct sitemap fetch failed: {e}")

        # Step 2: Fallback to browser
        if not content or ("sgcaptcha" in content and len(content) < 5000) or ("Robot Challenge" in content):
            from playwright.sync_api import sync_playwright
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    # Apply stealth for sitemap too
                    try:
                        from playwright_stealth import stealth
                        stealth(page)
                    except: pass
                    
                    logger.info(f"Fetching sitemap via browser: {index_url}")
                    content = self._fetch_with_page(page, index_url)
                    browser.close()
            except Exception as e:
                logger.error(f"Sitemap browser fetch failed: {e}")

        if not content: return []

        # Parsing logic
        def is_product(u):
            # Match numeric patterns: /123, /123-slug, /product/123
            return '/product/' in u or re.search(r'/\d+($|[/-])', u)

        all_locs = re.findall(r"<loc>(.*?)</loc>", content)
        all_locs = [l.replace('&amp;', '&') for l in all_locs]
        
        # Filter for products
        found_products = [u for u in all_locs if is_product(u)]
        product_urls.extend(found_products)
        
        # Check for sub-sitemaps (one level deep)
        sitemaps = [u for u in all_locs if 'sitemap' in u and 'image' not in u and u != index_url]
        if sitemaps:
            logger.info(f"Checking {len(sitemaps)} sub-sitemaps")
            for s_url in sitemaps:
                try:
                    # For sub-sitemaps, we try requests first, then browser if needed
                    s_resp = requests.get(s_url, timeout=15)
                    s_content = s_resp.text
                    if "sgcaptcha" in s_content and len(s_content) < 5000:
                        # Skip if blocked for now to keep it fast, or could use browser here too
                        continue
                    s_locs = re.findall(r"<loc>(.*?)</loc>", s_content)
                    product_urls.extend([l.replace('&amp;', '&') for l in s_locs if is_product(l)])
                except:
                    pass
            
        unique_urls = list(set(product_urls))
        logger.info(f"Found {len(unique_urls)} unique product URLs in sitemap")
        return unique_urls

    def _fetch_with_page(self, page, url: str) -> str:
        """Fetch content using an existing page instance and return raw response text"""
        try:
            logger.info(f"Browser fetching: {url}")
            response = page.goto(url, wait_until="load", timeout=90000)
            
            # Check for Robot Challenge Screen
            max_wait = 20
            waited = 0
            while waited < max_wait:
                try:
                    title = page.title()
                    if "Robot Challenge Screen" not in title:
                        break
                    if waited == 0:
                        logger.info("Sitemap: Detected Robot Challenge Screen. Waiting for solve...")
                except:
                    pass
                time.sleep(1)
                waited += 1
            
            page.wait_for_timeout(3000)
            content = page.content()
            
            try:
                # Direct body is most reliable for XML
                text = response.text()
                if len(text) > 1000: return text
            except:
                pass
            return content
        except Exception as e:
            logger.error(f"Page fetch failed for {url}: {e}")
            return ""
