import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"

def headers():
    return {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
    }

def main():
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"
    r = requests.get(url, headers=headers())
    if not r.ok:
        print(f"Error: {r.status_code} - {r.text}")
        return

    tables = r.json().get("tables", [])
    for table in tables:
        print(f"Table: {table['name']} ({table['id']})")
        if table['name'] == "Products":
            for field in table.get("fields", []):
                print(f"  - {field['name']} ({field['id']}): {field['type']}")
                if field['type'] in ["singleSelect", "multipleSelects"]:
                    choices = [c['name'] for c in field.get("options", {}).get("choices", [])]
                    print(f"    Choices: {choices[:5]}...")

if __name__ == "__main__":
    main()
