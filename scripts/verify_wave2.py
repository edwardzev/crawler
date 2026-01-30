
import sys
import os
import requests
import yaml
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crawler.parser import HTMLParser

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def test_extraction():
    config_path = Path("config/wave2.yaml")
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        return

    config = load_config(config_path)
    selectors = config['selectors']
    
    # Test URL - using the one found during analysis
    url = "https://www.wave2.co.il/product/575/" 
    print(f"Fetching {url}...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return

    print("Parsing content...")
    parser = HTMLParser(response.text)
    data = parser.parse_product(selectors)
    
    print("\nExtracted Data:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # Basic Validation
    required_fields = ['title', 'sku']
    missing = [f for f in required_fields if not data.get(f)]
    
    if missing:
        print(f"\nWARNING: Missing required fields: {missing}")
    else:
        print("\nSUCCESS: All required fields extracted.")

if __name__ == "__main__":
    test_extraction()
