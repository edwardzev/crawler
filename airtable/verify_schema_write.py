import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
AIRTABLE_BASE_ID = "app1tMmtuC7BGfJLu"
AIRTABLE_TABLE_NAME = "Orders"
AIRTABLE_API_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

def verify_write():
    if not AIRTABLE_PAT:
        print("Error: AIRTABLE_PAT not found")
        return

    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json"
    }

    print("Creating test record...")
    try:
        # 1. Create empty record
        r = requests.post(AIRTABLE_API_URL, headers=headers, json={"fields": {}})
        r.raise_for_status()
        record_id = r.json()["id"]
        print(f"Created draft record: {record_id}")

        # 2. Test payload with all fields individually to see which ones exist
        fields_to_test = [
            "Job Name", "Deadline", "Method", "Notes", "Final check", "Notes to Design",
            "Name", "Client", "Order ID", "Status" # Common alternatives
        ]
        
        # Add slot fields
        for i in range(1, 6):
            # Standardized: Always use "Width N cm"
            fields_to_test.append(f"Width {i} cm")
            fields_to_test.append(f"Graphic {i}")
            fields_to_test.append(f"Mockup {i}")

        print(f"Testing {len(fields_to_test)} fields...")
        
        valid_fields = []
        invalid_fields = []
        
        for field in fields_to_test:
            # Prepare a dummy value
            val = "test"
            if "Number" in field or "Width" in field:
                val = 10
            if "Final check" in field:
                val = True
            if "Graphic" in field or "Mockup" in field:
                # Attachments field takes array of objects, but let's try just empty array
                val = []

            update_payload = {"fields": {field: val}}
            
            try:
                r_update = requests.patch(f"{AIRTABLE_API_URL}/{record_id}", headers=headers, json=update_payload)
                if r_update.status_code == 200:
                    print(f"  [OK] {field}")
                    valid_fields.append(field)
                else:
                    err = r_update.json().get('error', {})
                    msg = err.get('message', 'Unknown error')
                    print(f"  [FAIL] {field}: {msg}")
                    invalid_fields.append(field)
            except Exception as e:
                 print(f"  [ERROR] {field}: {e}")

        print("\n--- Summary ---")
        print("Valid Fields:", valid_fields)
        print("Invalid Fields:", invalid_fields)

        # Cleanup
        print("Deleting test record...")
        requests.delete(f"{AIRTABLE_API_URL}/{record_id}", headers=headers)

    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response:
             print(f"Response: {e.response.text}")

if __name__ == "__main__":
    verify_write()
