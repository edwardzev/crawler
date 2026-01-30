import requests
from selectolax.lexbor import LexborHTMLParser
import json

url = "https://www.zeus.co.il/product/ROLLINK-Mini-Bag-TOUR-%D7%AA%D7%99%D7%A7-%D7%A6%D7%93-%D7%A7%D7%A9%D7%99%D7%97-%D7%A1%D7%9C%D7%99%D7%A0%D7%92-%D7%9E%D7%91%D7%99%D7%AA-%D7%94%D7%9E%D7%95%D7%AA%D7%92-2726/160"

try:
    response = requests.get(url, timeout=10)
    html = response.text
    tree = LexborHTMLParser(html)
    
    # Check JSON-LD
    json_lds = tree.css('script[type="application/ld+json"]')
    print(f"Found {len(json_lds)} JSON-LD blocks")
    for i, script in enumerate(json_lds):
        print(f"--- JSON-LD {i} ---")
        try:
            data = json.loads(script.text(strip=True))
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Error parsing JSON: {e}")

    # Print some interesting elements to help find selectors
    print("\n--- Potential Selectors ---")
    title = tree.css_first("h1")
    if title:
        print(f"H1: {title.text(strip=True)}")
        print(f"H1 classes: {title.attributes.get('class')}")
        print(f"H1 id: {title.attributes.get('id')}")
        
    price = tree.css_first(".price, [itemprop='price'], .product-price")
    if price:
         print(f"Price approximation: {price.text(strip=True)}")
         print(f"Price classes: {price.attributes.get('class')}")

except Exception as e:
    print(f"Error: {e}")
