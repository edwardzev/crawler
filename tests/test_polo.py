import sys
import os
import yaml
from playwright.sync_api import sync_playwright

def test_polo_selectors(url):
    config_path = os.path.join(os.path.dirname(__file__), '../config/polo.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    selectors = config['selectors']
    
    with sync_playwright() as p:
        print(f"Testing URL: {url}")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        
        results = {}
        results['title'] = page.inner_text(selectors['title']) if page.query_selector(selectors['title']) else "MISSING"
        results['sku'] = page.inner_text(selectors['sku']) if page.query_selector(selectors['sku']) else "MISSING"
        results['description'] = page.inner_text(selectors['description']) if page.query_selector(selectors['description']) else "MISSING"
        
        main_img = page.query_selector(selectors['main_image'])
        results['main_image'] = main_img.get_attribute('src') if main_img else "MISSING"
        
        add_imgs = page.query_selector_all(selectors['additional_images'])
        results['additional_images'] = [img.get_attribute('src') for img in add_imgs]
        
        variations = page.query_selector_all(selectors['variations'])
        results['variations'] = [v.inner_text() for v in variations]
        
        breadcrumbs = page.query_selector_all(selectors['breadcrumbs'])
        results['breadcrumbs'] = [b.inner_text() for b in breadcrumbs]
        
        for key, value in results.items():
            print(f"{key.capitalize()}: {value}")
        
        browser.close()

if __name__ == "__main__":
    sample_url = "https://www.polo.co.il/AP5614/"
    if len(sys.argv) > 1:
        sample_url = sys.argv[1]
    test_polo_selectors(sample_url)
