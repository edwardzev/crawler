import sqlite3
import json
from bs4 import BeautifulSoup

DB_PATH = "products.db"

def clean_html(html_text):
    if not html_text:
        return ""
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        return soup.get_text(separator="\n", strip=True)
    except Exception:
        return html_text

def reclean_comfort():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get all Comfort products
    c.execute("SELECT catalog_id, description FROM products WHERE supplier='Comfort'")
    rows = c.fetchall()
    
    print(f"Found {len(rows)} Comfort products.")
    
    updated_count = 0
    
    for row in rows:
        original = row['description']
        if not original:
            continue
            
        # Check if it looks like HTML (basic check)
        if '<' in original and '>' in original:
            cleaned = clean_html(original)
            
            if cleaned != original:
                c.execute("UPDATE products SET description = ? WHERE catalog_id = ?", (cleaned, row['catalog_id']))
                updated_count += 1
                
    conn.commit()
    conn.close()
    
    print(f"cleaned {updated_count} descriptions.")

if __name__ == "__main__":
    reclean_comfort()
