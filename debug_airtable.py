import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Orders"
URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}?maxRecords=1"

headers = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

try:
    print(f"Fetching 1 record from {URL}...")
    r = requests.get(URL, headers=headers)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {r.text}")
        exit(1)
        
    data = r.json()
    if "records" in data and len(data["records"]) > 0:
        fields = data["records"][0]["fields"]
        print("--- Valid Field Names (from existing record) ---")
        for k in fields.keys():
            print(f"- {k}")
    else:
        print("No records found, cannot infer schema via GET.")
        # Try creating with empty fields to see if it lists allowed fields in error? 
        # Airtable usually doesn't.
        
except Exception as e:
    print(f"Error: {e}")
