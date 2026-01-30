import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
AIRTABLE_BASE_ID = "app1tMmtuC7BGfJLu"
AIRTABLE_TABLE_ID = "tblBCHyKV17WGYmgh" 

def add_mockup_fields():
    if not AIRTABLE_PAT:
        print("Error: AIRTABLE_PAT not found")
        return

    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json"
    }

    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables/{AIRTABLE_TABLE_ID}/fields"

    fields_to_create = []

    # Add Slot Fields
    for i in range(1, 6):
        fields_to_create.append({
            "name": f"Mockup {i}",
            "type": "multipleAttachments"
        })

    print(f"Creating {len(fields_to_create)} Mockup fields in table {AIRTABLE_TABLE_ID}...")

    success_count = 0
    skipped_count = 0
    error_count = 0

    for field_def in fields_to_create:
        print(f"Creating field: {field_def['name']}...")
        try:
            r = requests.post(url, headers=headers, json=field_def)
            if r.status_code == 200:
                print("  [SUCCESS]")
                success_count += 1
            else:
                err = r.json()
                # Check for "Duplicated field name" error
                if err.get("error", {}).get("type") == "DUPLICATED_FIELD_NAME":
                     print("  [SKIPPED] Field already exists.")
                     skipped_count += 1
                else:
                    print(f"  [ERROR] {r.status_code}: {r.text}")
                    error_count += 1
            
            # Rate limit politeness
            time.sleep(0.2)
            
        except Exception as e:
            print(f"  [EXCEPTION] {e}")
            error_count += 1

    print("\n--- Summary ---")
    print(f"Created: {success_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Errors: {error_count}")

if __name__ == "__main__":
    add_mockup_fields()
