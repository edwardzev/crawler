import logging
import sqlite3
import time
import random
from playwright.sync_api import sync_playwright

DB_PATH = "products.db"
SUPPLIER = "Comfort Gifts"

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

def fix_language():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT rowid, url, sku, title FROM products WHERE supplier = ?", (SUPPLIER,))
    rows = cursor.fetchall()
    
    def needs_fix(title):
        if not title: return True
        for char in title:
            if '\u0590' <= char <= '\u05FF':
                return False
        return True

    # PROCESS ALL PRODUCTS to update descriptions even if title is already Hebrew
    worklist = rows 
    logger.info(f"Checking all {len(worklist)} products to ensure Hebrew title + HTML description...")
    
    if not worklist: return

    user_data_dir = "./browser_data"
    
    # User provided raw cookie string
    raw_cookie = 'currency=ILS; _gid=GA1.2.2000003724.1769685630; language=he-il; _ga_V7RXWZK55D=GS2.1.s1769685630$o4$g1$t1769687077$j59$l0$h0; _ga=GA1.1.1549641350.1769369680'
    
    cookies_to_add = []
    for part in raw_cookie.split(';'):
        if '=' in part:
            name, value = part.strip().split('=', 1)
            cookies_to_add.append({
                "name": name,
                "value": value,
                "domain": ".comfort-gifts.com", # Wildcard often safer
                "path": "/"
            })

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            # slow_mo=50,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 800}
        )
        
        # Inject provided cookies
        browser.add_cookies(cookies_to_add)
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        # WARMUP: Go to home page to get a valid session/pass challenges
        logger.info("Warming up on homepage...")
        try:
            page.goto("https://www.comfort-gifts.com/", wait_until="domcontentloaded")
            time.sleep(5)
            # Check for robot challenge here too
            if "Robot" in page.title():
                 logger.warning("Blocked on Homepage! Waiting longer...")
                 time.sleep(15)
        except Exception as e:
            logger.error(f"Warmup failed: {e}")

        updated_count = 0
        
        for i, row in enumerate(worklist):
            rid = row['rowid']
            url = row['url']
            sku = row['sku']
            
            logger.info(f"[{i+1}/{len(worklist)}] Fixing SKU {sku}...")
            
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                
                # Check for block
                title = page.title()
                if "Robot" in title or "Access denied" in title:
                    logger.warning(f"  -> Blocked! Title: {title}")
                    time.sleep(10)
                    page.reload()
                
                try:
                    # Try H1
                    try:
                        page.wait_for_selector("h1", timeout=3000)
                        new_title = page.locator("h1").first.text_content().strip()
                    except:
                        # Fallback to page title
                        raw_title = page.title()
                        # Usually "SKU-Name" or just "Name". 
                        # We can just save it as is, or strip common suffixes like " - Comfort"
                        new_title = raw_title.split(' - ')[0].strip() # valid assumption?
                        logger.info(f"  -> Used Page Title fallback: {new_title}")

                    if needs_fix(new_title):
                         logger.warning(f"  -> Still English: {new_title}")
                    else:
                        # Extract HTML description
                        new_desc = ""
                        try:
                            # Prefer #tab-description
                            desc_el = page.locator("#tab-description")
                            if desc_el.count() > 0:
                                # Get full HTML
                                raw_html = desc_el.inner_html()
                                # Remove "Categories:" part if present. 
                                # It's usually a list at the bottom. We can try simple string splitting or regex.
                                # Example structure: ... <hr> ... Categories: ...
                                if "קטגוריות:" in raw_html:
                                    new_desc = raw_html.split("קטגוריות:")[0].strip()
                                elif "Categories:" in raw_html:
                                    new_desc = raw_html.split("Categories:")[0].strip()
                                else:
                                    new_desc = raw_html
                            elif page.locator(".tab-content").count() > 0:
                                new_desc = page.locator(".tab-content").first.inner_html()
                        except:
                            pass
                        
                        logger.info(f"  -> Fixed: {new_title} (Desc len: {len(new_desc)})")
                        cursor.execute("UPDATE products SET title = ?, description = ? WHERE rowid = ?", 
                                       (new_title, new_desc, rid))
                        conn.commit()
                        updated_count += 1
                        
                except Exception as e:
                     logger.warning(f"  -> Element not found. Title: {page.title()}")

            except Exception as e:
                logger.error(f"  -> Navigation error: {e}")
                
            time.sleep(random.uniform(1.5, 3)) # Slightly slower to be safe

        browser.close()
        
    logger.info(f"Done. Updated {updated_count} products.")
    conn.close()

if __name__ == "__main__":
    fix_language()
