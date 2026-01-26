from playwright.sync_api import sync_playwright

url = "http://www.comfort-gifts.com/promotion-gadgets-Technology/Power-Bank-Chargers/2104-Vega"

with sync_playwright() as p:
    print("Launching WebKit...")
    browser = p.webkit.launch(headless=True)
    page = browser.new_page()
    print(f"Navigating to {url}...")
    try:
        # Default wait_until is load
        page.goto(url, timeout=45000)
        
        # Wait a bit for potential redirects
        page.wait_for_timeout(5000)
        
        title = page.title()
        print("Page title:", title)
        content = page.content()
        print(f"Content length: {len(content)}")
        
        if "forbidden" in  title.lower() or "captcha" in content.lower():
             print("FAILURE: Blocked.")
        else:
             print("SUCCESS: Page loaded!")
             
    except Exception as e:
        print(f"Error: {e}")
    finally:
        browser.close()
