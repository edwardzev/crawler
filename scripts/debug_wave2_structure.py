import sys
import requests
import json
from selectolax.lexbor import LexborHTMLParser

def debug_structure():
    url = "https://www.wave2.co.il/product/575/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        resp = requests.get(url, headers=headers)
        parser = LexborHTMLParser(resp.text)
        
        # Check JSON-LD
        print("=== JSON-LD ===")
        for script in parser.css('script[type="application/ld+json"]'):
             try:
                 data = json.loads(script.text(strip=True))
                 print(json.dumps(data, indent=2, ensure_ascii=False))
             except: pass
             
        # Check Summary Text
        summary = parser.css_first(".summary.entry-summary")
        if summary:
            print("\n=== Summary Text ===")
            print(summary.text(strip=True, separator='\n'))
            
            print("\n=== Summary InnerHTML (First 1000 chars) ===")
            print(summary.html[:1000])

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_structure()
