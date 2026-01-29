from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page()
    pg.goto('https://www.comfort-gifts.com/sitemap.xml', wait_until='networkidle')
    waited = 0
    while 'Robot Challenge' in pg.title() and waited < 20:
        time.sleep(1)
        waited += 1
    print(f"Final Title: {pg.title()}")
    print(f"Content Length: {len(pg.content())}")
    print(f"Content Sample: {pg.content()[:500]}")
    b.close()
