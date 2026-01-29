import logging
import sqlite3
import json
import time
import random
from playwright.sync_api import sync_playwright

DB_PATH = "products.db"
SUPPLIER = "Comfort Gifts"

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

def refetch_images_v3():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Fetch all missing images again
    cursor.execute("SELECT rowid, url, sku FROM products WHERE supplier = ? AND (images IS NULL OR images = '[]' OR images = '')", (SUPPLIER,))
    rows = cursor.fetchall()
    
    logger.info(f"Found {len(rows)} products missing images.")
    if not rows: return

    # Use a persistent context to keep cookies/session alive
    user_data_dir = "./browser_data"
    
    # User provided raw cookie string (from fix_language.py)
    raw_cookie = 'currency=ILS; _gid=GA1.2.2000003724.1769685630; language=he-il; _ga_V7RXWZK55D=GS2.1.s1769685630$o4$g1$t1769687077$j59$l0$h0; _ga=GA1.1.1549641350.1769369680'
    
    cookies_to_add = []
    for part in raw_cookie.split(';'):
        if '=' in part:
            name, value = part.strip().split('=', 1)
            cookies_to_add.append({
                "name": name,
                "value": value,
                "domain": ".comfort-gifts.com", 
                "path": "/"
            })

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False, 
            slow_mo=50,    
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 800}
        )
        
        # Inject cookies
        browser.add_cookies(cookies_to_add)
        
        page = browser.pages[0]
        
        updated_count = 0

        for i, row in enumerate(rows):
            rid = row['rowid']
            url = row['url']
            sku = row['sku']
            
            logger.info(f"[{i+1}/{len(rows)}] Processing SKU {sku}...")
            
            try:
                # Navigate
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                
                # Check for image selector
                # We wait for EITHER the image OR a captcha title
                found_img = False
                try:
                    page.wait_for_selector("a.popup-image", timeout=5000)
                    found_img = True
                except:
                    # If not found immediately, check if we are blocked
                    title = page.title()
                    if "Robot" in title or "Access denied" in title:
                        logger.warning("  -> Blocked. Pausing 10s...")
                        time.sleep(10)
                        page.reload()
                        try:
                            page.wait_for_selector("a.popup-image", timeout=5000)
                            found_img = True
                        except: pass

                # Extract
                if found_img:
                    images = page.evaluate("""() => {
                        let srcs = new Set();
                        document.querySelectorAll('a.popup-image img').forEach(img => srcs.add(img.src));
                        return Array.from(srcs).filter(s => s.includes('/image/') || s.includes('/cache/'));
                    }""")
                    
                    if images:
                        logger.info(f"  -> Found {len(images)} images.")
                        cursor.execute("UPDATE products SET images = ? WHERE rowid = ?", (json.dumps(images), rid))
                        conn.commit()
                        updated_count += 1
                    else:
                        logger.warning("  -> Selector found but no SRCs extracted.")
                else:
                    logger.warning("  -> Image selector not found.")
                    
            except Exception as e:
                logger.error(f"  -> Failed: {e}")
                # If context crashes, we might need to recreate, but persistent context is hard to recreate in loop
                # Just continue
                pass
                
            # Random delay
            time.sleep(random.uniform(1, 3))

        browser.close()
        
    logger.info(f"Refetch complete. Updated {updated_count} products.")
    conn.close()

if __name__ == "__main__":
    refetch_images_v3()
