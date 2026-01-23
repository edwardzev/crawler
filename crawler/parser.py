from selectolax.lexbor import LexborHTMLParser
from urllib.parse import urljoin
from selectolax.lexbor import LexborHTMLParser
from urllib.parse import urljoin
from typing import Set, Dict, Any, List, Optional

class HTMLParser:
    def __init__(self, html: str):
        self.html = html
        self.tree = LexborHTMLParser(html)
        
    def parse_product(self, selectors: Dict[str, str]) -> Dict[str, Any]:
        data = self.extract_json_ld() or {}
        
        # Selectors override or enrich JSON-LD
        for field, selector in selectors.items():
            value = None
            attr = None
            
            # Check for attribute syntax: "selector::attribute"
            if "::" in selector:
                sel_part, attr = selector.split("::", 1)
                elements = self.tree.css(sel_part)
                if elements:
                    values = [el.attributes.get(attr) for el in elements if el.attributes.get(attr)]
                    if field == 'images':
                        data[field] = values
                    elif values:
                        data[field] = values[0]
            else:
                # Special handling for breadcrumb -> category_path (list)
                if field == 'breadcrumb':
                    elements = self.tree.css(selector)
                    if elements:
                        value = [el.text(strip=True) for el in elements]
                        # Map breadcrumb to category_path
                        data['category_path'] = value
                        continue
                else:
                    element = self.tree.css_first(selector)
                    if element:
                        value = element.text(separator=' ', strip=True)
                        if value:
                            data[field] = value
        
        return data

    def extract_links(self, base_url: str) -> Set[str]:
        links = set()
        for node in self.tree.css("a"):
            href = node.attributes.get("href")
            # logger.info(f"Found href: {href}")
            if href:
                full_url = urljoin(base_url, href)
                # Filter out obvious non-crawlable links
                if full_url.startswith("http"):
                    links.add(full_url)
        return links

    def extract_json_ld(self) -> Optional[Dict[str, Any]]:
        import json
        for script in self.tree.css('script[type="application/ld+json"]'):
            try:
                content = script.text(strip=True)
                if not content:
                    continue
                data = json.loads(content)
                
                # Handle list of objects or single object
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "Product":
                            return item
                elif isinstance(data, dict):
                     if data.get("@type") == "Product":
                        return data
            except json.JSONDecodeError:
                continue
        return None

