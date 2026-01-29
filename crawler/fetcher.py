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
        self.playwright = None
        self.browser = None
        self.page = None
        
    def _init_browser(self):
        if not self.browser:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            self.page = self.context.new_page()
            
            # Apply stealth
            from playwright_stealth import stealth
            stealth(self.page)
            
            # Set a standard timeout
            self.page.set_default_timeout(30000)

    def fetch(self, url: str, retries: int = 3) -> Optional[str]:
        # Force dynamic fetch for Comfort Gifts to handle challenges
        return self.fetch_dynamic(url, retries=retries)
        
    def fetch_dynamic(self, url: str, retries: int = 2) -> Optional[str]:
        import time
        self._init_browser()
        for attempt in range(retries):
            try:
                # Shield Genius can takes a few seconds to clear
                logger.info(f"Navigating to {url}...")
                self.page.goto(url, wait_until="load", timeout=60000)
                
                # Check for Robot Challenge Screen
                max_wait = 20
                waited = 0
                while waited < max_wait:
                    try:
                        title = self.page.title()
                        if "Robot Challenge Screen" not in title:
                            break
                        if waited == 0:
                            logger.info("Detected Robot Challenge Screen. Waiting for auto-solve...")
                    except Exception:
                        # Context might be destroyed during refresh
                        pass
                    time.sleep(1)
                    waited += 1
                
                try:
                    if "Robot Challenge Screen" in self.page.title():
                        raise Exception("Robot Challenge failed to solve in time.")
                except:
                    pass

                content = self.page.content()
                if "sgcaptcha" in content or "access denied" in content.lower():
                    raise Exception("Blocked by anti-bot/captcha after challenge")
                
                # Final wait for dynamic content
                try:
                    self.page.wait_for_selector("#tab-description, .product-info, #content", timeout=5000)
                except:
                    pass
                    
                return self.page.content()
            except Exception as e:
                logger.warning(f"Dynamic fetch attempt {attempt+1} failed: {e}")
                if "challenge" in str(e).lower() or "block" in str(e).lower():
                    logger.info("Hit block/challenge, attempting cooldown and refresh...")
                    self.context.clear_cookies()
                    time.sleep(30)
                if attempt == retries - 1:
                    logger.error(f"Dynamic fetch failed for {url} after {retries} attempts.")
        return None

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

