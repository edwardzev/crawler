import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
AIRTABLE_BASE_ID = "app1tMmtuC7BGfJLu"

def check_metadata():
    if not AIRTABLE_PAT:
        print("Error: AIRTABLE_PAT not found")
        return

    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
    }

    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    
    print(f"Checking metadata access for base {AIRTABLE_BASE_ID}...")
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            print("SUCCESS: Metadata API access granted.")
            tables = r.json().get("tables", [])
            print(f"Found {len(tables)} tables.")
            for t in tables:
                if t["name"] == "Orders":
                    print(f"Found Orders Table ID: {t['id']}")
        elif r.status_code == 403: # Forbidden
            print("FAILURE: 403 Forbidden. The token does not have 'schema.bases:read' scope.")
        elif r.status_code == 404:
            print("FAILURE: 404 Not Found. Base ID might be wrong or endpoint changed.")
        else:
            print(f"FAILURE: {r.status_code}")
            print(r.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_metadata()
