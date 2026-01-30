import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
AIRTABLE_BASE_ID = "app1tMmtuC7BGfJLu"
AIRTABLE_TABLE_NAME = "Orders"
AIRTABLE_API_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

def check_schema():
    if not AIRTABLE_PAT:
        print("Error: AIRTABLE_PAT not found in environment")
        return

    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json"
    }

    print(f"Fetching record from {AIRTABLE_TABLE_NAME}...")
    try:
        # Fetch 1 record to see fields
        r = requests.get(f"{AIRTABLE_API_URL}?maxRecords=1", headers=headers)
        r.raise_for_status()
        data = r.json()
        
        if not data.get("records"):
            print("Table is empty. Cannot infer schema from existing records.")
            # Try creating a dummy record with all expected fields to see if it fails
            # But that might mess up data. 
            # Better to just report it's empty.
            return

        record = data["records"][0]
        fields = record.get("fields", {}).keys()
        
        print("\nExisting Fields in Record:")
        for f in sorted(fields):
            print(f"- {f}")
            
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response:
             print(f"Response: {e.response.text}")

if __name__ == "__main__":
    check_schema()
