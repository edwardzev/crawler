import requests
import logging
from typing import Optional
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

class HTMLFetcher:
    def __init__(self, headers: Optional[dict] = None):
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,he;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Upgrade-Insecure-Requests": "1"
        }
        
    def fetch(self, url: str) -> Optional[str]:
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Static fetch failed for {url}: {e}")
            return None
        
    def fetch_dynamic(self, url: str) -> Optional[str]:
        try:
            with sync_playwright() as p:
                browser = p.webkit.launch()
                page = browser.new_page()
                # page.set_extra_http_headers(self.headers) # Let playwright manage headers to avoid mismatches
                page.goto(url, wait_until="load", timeout=45000)
                page.wait_for_timeout(5000) # Allow JS redirects/rendering
                # Wait for some content if needed, for now just return html
                content = page.content()
                browser.close()
                return content
        except Exception as e:
            logger.error(f"Dynamic fetch failed for {url}: {e}")
            return None

