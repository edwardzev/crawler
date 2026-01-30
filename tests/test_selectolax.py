from selectolax.lexbor import LexborHTMLParser
import requests
import re

url = "https://www.polo.co.il/AP5614/"
headers = {"User-Agent": "Mozilla/5.0"}
html = requests.get(url, headers=headers).text
tree = LexborHTMLParser(html)

print("Testing Title (h1):")
el = tree.css_first("h1")
print(f"Title: {el.text(strip=True) if el else 'NOT FOUND'}")

print("\nTesting SKU with standard selector + manual regex:")
found_sku = None
for p in tree.css("p"):
    text = p.text(strip=True)
    if "קוד דגם:" in text:
        match = re.search(r"קוד דגם:\s*([\w]+)", text)
        if match:
            found_sku = match.group(1)
            print(f"SKU Found: {found_sku}")
            break

print("\nTesting Images (.currentProductImage .slick-slide img):")
# Check if :not() works or just get all and filter
images = [img.attributes.get('src') for img in tree.css(".currentProductImage .slick-slide:not(.slick-cloned) img")]
print(f"Additional Images: {images}")

print("\nTesting Breadcrumbs (nav#breadcrumbs a):")
bc = [a.text(strip=True) for a in tree.css("nav#breadcrumbs a")]
print(f"Breadcrumbs: {bc}")
