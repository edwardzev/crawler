from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page()
    pg.goto('https://www.comfort-gifts.com/promotional-pens', wait_until='networkidle')
    waited = 0
    while 'Robot Challenge' in pg.title() and waited < 20:
        print(f"[{waited}s] Title: {pg.title()}")
        time.sleep(1)
        waited += 1
    print(f"Final Title: {pg.title()}")
    print(f"Content Sample: {pg.content()[:300]}")
    b.close()
