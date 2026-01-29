import os
import sqlite3
import requests
import json
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
# Table ID from legacy config
TABLE_ID = "tblZSBzsMEbr2R2wJ" 

META_API = "https://api.airtable.com/v0/meta"

def headers():
    return {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json",
    }

def get_table_info():
    url = f"{META_API}/bases/{BASE_ID}/tables"
    r = requests.get(url, headers=headers())
    if not r.ok:
        print(f"ERROR: {r.status_code} - {r.text}")
        return None
    return r.json()

# Updated ID mapping from debug script
FIELD_IDS = {
    "category_major": "fldDfU6boCflYzlYA",
    "category_sub": "fldGum42aOdVf0Eb3",
    "category_sub2": "fldMa8vvW9fwdnGZT"
}

def update_field_choices(field_id: str, field_name: str, new_choices: set):
    url = f"{META_API}/bases/{BASE_ID}/tables/{TABLE_ID}/fields/{field_id}"
    
    # Get current field info
    r = requests.get(f"{META_API}/bases/{BASE_ID}/tables", headers=headers())
    if not r.ok: return False
    
    field_info = None
    for table in r.json().get("tables", []):
        if table["id"] == TABLE_ID:
            for f in table.get("fields", []):
                if f["id"] == field_id:
                    field_info = f
                    break
    
    if not field_info: return False

    existing_choices = field_info.get("options", {}).get("choices", [])
    existing_names = {c["name"] for c in existing_choices}
    
    # Merge
    updated_choices = list(existing_choices)
    added = 0
    for name in sorted(new_choices):
        name_str = str(name).strip()
        if name_str and name_str not in existing_names:
            updated_choices.append({"name": name_str})
            existing_names.add(name_str)
            added += 1
            
    if added == 0:
        print(f"  {field_name}: No new choices")
        return True

    print(f"  {field_name}: Attempting to add {added} choices (Total: {len(updated_choices)})")
    
    payload = {"options": {"choices": updated_choices}}
    r = requests.patch(url, headers=headers(), json=payload)
    if r.ok:
        print(f"  {field_name}: SUCCESS")
        return True
    else:
        print(f"  {field_name}: FAILED {r.status_code} - {r.text}")
        return False

def main():
    conn = sqlite3.connect("products.db")
    cur = conn.execute("SELECT DISTINCT category_path FROM products WHERE category_path IS NOT NULL")
    
    majors = set()
    subs = set()
    sub2s = set()
    
    for (cat_path,) in cur.fetchall():
        if not cat_path: continue
        try:
            parts = json.loads(cat_path) if cat_path.startswith("[") else [cat_path]
            if len(parts) > 0: majors.add(parts[0])
            if len(parts) > 1: subs.add(parts[1])
            if len(parts) > 2: sub2s.add(parts[2])
        except:
            majors.add(cat_path)

    # Also handle legacy split categories if they exist in DB
    try:
        cur = conn.execute("SELECT DISTINCT category_major, category_sub, category_sub2 FROM products")
        for m, s, s2 in cur.fetchall():
            if m: majors.add(m)
            if s: subs.add(s)
            if s2: sub2s.add(s2)
    except:
        pass

    table_data = get_table_info()
    if not table_data: return
    
    fields = {}
    for table in table_data.get("tables", []):
        if table["id"] == TABLE_ID or table["name"] == TABLE_NAME:
            for f in table.get("fields", []):
                fields[f["name"]] = f

    if "category_major" in fields:
        update_field_choices(fields["category_major"]["id"], "category_major", majors)
    if "category_sub" in fields and fields["category_sub"]["type"] in ["singleSelect", "multipleSelects"]:
        update_field_choices(fields["category_sub"]["id"], "category_sub", subs)
    if "category_sub2" in fields and fields["category_sub2"]["type"] in ["singleSelect", "multipleSelects"]:
        update_field_choices(fields["category_sub2"]["id"], "category_sub2", sub2s)
    
    print("Choice update finished.")

if __name__ == "__main__":
    main()
