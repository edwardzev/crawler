import requests
import logging
from typing import Optional
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

class HTMLFetcher:
    def __init__(self, headers: Optional[dict] = None):
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
                browser = p.chromium.launch()
                page = browser.new_page()
                page.set_extra_http_headers(self.headers)
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Wait for some content if needed, for now just return html
                content = page.content()
                browser.close()
                return content
        except Exception as e:
            logger.error(f"Dynamic fetch failed for {url}: {e}")
            return None

