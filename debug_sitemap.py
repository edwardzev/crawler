import requests
import re
from playwright.sync_api import sync_playwright

url = 'https://www.comfort-gifts.com/sitemap.xml'

print("--- Requests Test ---")
try:
    r_c = requests.get(url, timeout=15).text
    r_locs = re.findall(r'<loc>(.*?)</loc>', r_c)
    print(f"Requests count: {len(r_locs)}")
except Exception as e:
    print(f"Requests failed: {e}")

print("\n--- Playwright Test ---")
try:
    with sync_playwright() as p:
        browser = p.webkit.launch()
        page = browser.new_page()
        response = page.goto(url, wait_until="load", timeout=60000)
        content = page.content()
        raw_text = response.text()
        p_locs = re.findall(r'<loc>(.*?)</loc>', content)
        r_locs = re.findall(r'<loc>(.*?)</loc>', raw_text)
        print(f"Playwright content length: {len(content)}")
        print(f"Playwright raw_text length: {len(raw_text)}")
        print(f"Playwright content locs: {len(p_locs)}")
        print(f"Playwright raw_text locs: {len(r_locs)}")
        
        # Check inner_text as well
        inner = page.inner_text("body")
        i_locs = re.findall(r'<loc>(.*?)</loc>', inner)
        print(f"Playwright inner_text locs count: {len(i_locs)}")
        browser.close()
except Exception as e:
    print(f"Playwright failed: {e}")
