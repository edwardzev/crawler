import sys
import yaml
from pathlib import Path

# Add project root to sys.path to allow importing 'crawler' module
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from crawler.core import CrawlerEngine

def test_zeus_extraction():
    config_path = Path("config/zeus.yaml")
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        return

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Use a test database
    config['db_path'] = "zeus_test.db"
    
    print(f"Initializing crawler for {config['supplier']}...")
    engine = CrawlerEngine(config)

    # Test URL from previous steps
    test_url = "https://www.zeus.co.il/catalog/X-pen-%D7%A2%D7%98%D7%99-%D7%99%D7%95%D7%A7%D7%A8%D7%94"
    
    print(f"Fetching {test_url}...")
    # Manually invoke the pipeline processing for a single URL if possible, 
    # or just use internal methods to verify parsing.
    # Since CrawlerEngine.process_url might be internal or async, let's try to use the components directly 
    # if engine doesn't expose a single-url test method.
    
    # Looking at core.py (I'll assume standard structure based on previous interactions)
    # Usually: fetcher -> parser -> pipeline
    
    from crawler.fetcher import HTMLFetcher
    from crawler.parser import HTMLParser
    
    fetcher = HTMLFetcher()
    # Use fetch_dynamic if needed, or just fetch
    html = fetcher.fetch(test_url)
    fetcher.close()
    
    if not html:
        print("Failed to fetch HTML")
        return

    print("Parsing HTML...")
    parser = HTMLParser(html)
    data = parser.parse_product(config['selectors'])
    
    print("\n--- Extracted Data ---")
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # Also verify link extraction
    print("\n--- Extracted Links (Sample) ---")
    links = parser.extract_links(test_url)
    for link in list(links)[:5]:
        print(link)

if __name__ == "__main__":
    test_zeus_extraction()
