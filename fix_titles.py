import sqlite3
import urllib.parse
import re

def fix_titles(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT product_id, url, title, sku FROM products")
    rows = cursor.fetchall()
    
    updated_count = 0
    
    for product_id, url, title, sku in rows:
        try:
            # 1. Parse URL to get slug
            path = urllib.parse.urlparse(url).path
            slug = path.strip('/').split('/')[-1]
            # Decode URL-encoded Hebrew
            decoded_slug = urllib.parse.unquote(slug)
            
            # 2. Extract words from slug
            # Slugs use dashes as separators
            slug_words = decoded_slug.split('-')
            
            if len(slug_words) < 2:
                continue
                
            # 3. Reconstruct title
            # Usually the first word is SKU, but we already have SKU.
            # We want the Hebrew words.
            hebrew_words = []
            for word in slug_words:
                # Basic check for Hebrew characters or common product words
                if any(u'\u0590' <= c <= u'\u05FF' for c in word):
                    hebrew_words.append(word)
                elif not hebrew_words and word.lower() == sku.lower():
                     # Skip the SKU if it's at the start
                     continue
                elif hebrew_words:
                    # After hebrew started, keep other words (like 429, etc)
                    hebrew_words.append(word)
            
            if not hebrew_words:
                continue
                
            new_title_hebrew = " ".join(hebrew_words)
            new_title = f"{sku} • {new_title_hebrew}"
            
            if new_title != title:
                cursor.execute("UPDATE products SET title = ? WHERE product_id = ?", (new_title, product_id))
                updated_count += 1
                
        except Exception as e:
            print(f"Error processing {sku}: {e}")
            
    conn.commit()
    conn.close()
    print(f"✓ Fixed {updated_count} titles in database.")

if __name__ == "__main__":
    fix_titles("products.db")
