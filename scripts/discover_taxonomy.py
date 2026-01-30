import os
import json
import random
from openai import OpenAI

# Load environment variables (ensure .env is loaded or vars are set)
from dotenv import load_dotenv
load_dotenv()

INPUT_FILE = "data/out/products.frontend.json"
OUTPUT_FILE = "taxonomy_draft.md"

def discover_taxonomy():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables.")
        print("Please enable it in .env or export it.")
        return

    client = OpenAI(api_key=api_key)

    print(f"Loading products from {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            products = json.load(f)
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
        return

    # Sample data
    sample_size = 400
    if len(products) > sample_size:
        print(f"Sampling {sample_size} products from {len(products)} total...")
        sample = random.sample(products, sample_size)
    else:
        sample = products

    # Prepare prompt content
    items_text = ""
    for p in sample:
        title = p.get("title", "N/A")
        # Strip HTML from description if possible, or just take raw for now. 
        # For simplicity, taking title + a snippet of description.
        desc = p.get("description", "")
        # Very basic HTML strip (can be improved)
        desc = desc.replace("<p>", "").replace("</p>", " ").replace("<br>", " ")
        items_text += f"- {title}: {desc[:100]}...\n"

    print("Constructing prompt...")
    system_prompt = (
        "You are an expert taxonomist for an e-commerce store selling promotional products (gadgets, gifts, office supplies).\n"
        "Your task is to create a clear, logical **3-level hierarchy** in **Hebrew**."
    )
    
    user_prompt = f"""
I have a dataset of {len(sample)} products. Here is a list of their titles and brief descriptions:

{items_text}

---

**Task:**
1. Analyze these items.
2. Propose a **3-Level Taxonomy** that covers them.
   - Level 1: Main Category (קתגוריה ראשית) - e.g. "כלי כתיבה"
   - Level 2: Sub Category 1 (תת קטגוריה 1) - e.g. "עטים"
   - Level 3: Sub Category 2 (תת קטגוריה 2) - e.g. "עטי מתכת"
3. Output the result in **Markdown** format as a nested list or a table.
4. Ensure the categories are professional and standard for the Israeli market.
5. Cover ALL items provided. Do not leave items "Uncategorized".

**Output Example:**
# Proposed Taxonomy

## כלי כתיבה
*   **עטים**
    *   עטי מתכת
    *   עטי פלסטיק
*   **עפרונות**
    *   עפרונות מכניים

## תיקים
*   **תיקי גב**
    *   תיקים למחשב
...
"""

    print("Sending request to OpenAI (this may take 30-60 seconds)...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Or gpt-4-turbo
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
        )
        
        content = response.choices[0].message.content
        
        print("Received response.")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Draft taxonomy saved to: {OUTPUT_FILE}")
        print("Please review and edit it before we finalize.")
        
    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    discover_taxonomy()
