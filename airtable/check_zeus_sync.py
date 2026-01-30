import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
}

def check_zeus():
    params = {
        "pageSize": 5,
        "filterByFormula": "{supplier}='Zeus'",
        "fields": ["sku", "product_id", "image_urls", "catalog_id"]
    }
    r = requests.get(API_URL, headers=HEADERS, params=params)
    r.raise_for_status()
    records = r.json().get("records", [])
    for rec in records:
        print(f"SKU: {rec['fields'].get('sku')}")
        print(f"Product ID: {rec['fields'].get('product_id')}")
        print(f"Catalog ID: {rec['fields'].get('catalog_id')}")
        print(f"Image URLs: {rec['fields'].get('image_urls')[:100]}...")
        print("-" * 20)

if __name__ == "__main__":
    check_zeus()
