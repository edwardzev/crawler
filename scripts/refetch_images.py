import logging
import sqlite3
import json
import time
import random
from playwright.sync_api import sync_playwright

DB_PATH = "products.db"
SUPPLIER = "Comfort Gifts"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

def refetch_images():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Fetch all missing images again
    cursor.execute("SELECT rowid, url, sku FROM products WHERE supplier = ? AND (images IS NULL OR images = '[]' OR images = '')", (SUPPLIER,))
    rows = cursor.fetchall()
    
    logger.info(f"Found {len(rows)} products missing images.")
    if not rows: return

    with sync_playwright() as p:
        # Launch options - trying to mimic a real user better
        browser = p.chromium.launch(
            headless=False,
            slow_mo=50,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        
        # Apply stealth manually-ish by ensuring navigator properties
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        updated_count = 0

        for i, row in enumerate(rows):
            rid = row['rowid']
            url = row['url']
            sku = row['sku']
            
            logger.info(f"[{i+1}/{len(rows)}] Processing SKU {sku}...")
            
            try:
                # Go to page
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Check for captcha title
                if "Robot Challenge" in page.title() or "Access denied" in page.title():
                    logger.warning("  -> Blocked. Retrying with delay...")
                    time.sleep(5)
                    page.reload(wait_until="domcontentloaded")
                
                # Explicit wait for the element we want
                try:
                    page.wait_for_selector("a.popup-image", timeout=5000)
                except:
                    # Ignore timeout, maybe logic below handles it
                    pass

                # Extract
                images = page.evaluate("""() => {
                    let srcs = new Set();
                    // Selector 1: Configuration default
                    document.querySelectorAll('a.popup-image img').forEach(img => srcs.add(img.src));
                    return Array.from(srcs).filter(s => s.includes('/image/') || s.includes('/cache/'));
                }""")
                
                if images:
                    logger.info(f"  -> Found {len(images)} images.")
                    cursor.execute("UPDATE products SET images = ? WHERE rowid = ?", (json.dumps(images), rid))
                    conn.commit()
                    updated_count += 1
                else:
                    logger.warning("  -> No images found (selector mismatch or blocked).")
                    
                # Small random delay to avoid rate limit
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"  -> Error: {e}")
                # Re-create page if context died
                if "Target closed" in str(e) or "Execution context" in str(e):
                    try:
                        page.close()
                    except: pass
                    page = context.new_page()

        browser.close()
        
    logger.info(f"Refetch complete. Updated {updated_count} products.")
    conn.close()

if __name__ == "__main__":
    refetch_images()
