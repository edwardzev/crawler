import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
AIRTABLE_BASE_ID = "app1tMmtuC7BGfJLu"
AIRTABLE_TABLE_NAME = "Products"
AIRTABLE_API_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

def check_products_schema():
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.get(f"{AIRTABLE_API_URL}?maxRecords=1", headers=headers)
        r.raise_for_status()
        data = r.json()
        
        if not data.get("records"):
            print("Table is empty.")
            return

        record = data["records"][0]
        fields = record.get("fields", {}).keys()
        
        print("\nExisting Fields in Record:")
        for f in sorted(fields):
            print(f"- {f}")
            
        # Check specific field
        img_val = record.get("fields", {}).get("cloudinary_images")
        print(f"\ncloudinary_images value: {img_val}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_products_schema()
