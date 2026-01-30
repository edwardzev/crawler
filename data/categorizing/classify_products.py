import json
import csv
import time
from bs4 import BeautifulSoup
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.getcwd(), ".env"))

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("WARNING: OPENAI_API_KEY not found in env. Client init may fail.")


# ================= CONFIG =================

OPENAI_MODEL = "gpt-4o"   # Using high-quality model for best Hebrew taxonomy results
BATCH_SIZE = 15                # SAFE with stripped text
MAX_DESC_CHARS = 500
RETRY_LIMIT = 3
SLEEP_BETWEEN_CALLS = 0.5

PRODUCTS_FILE = "products.frontend.json"
TAXONOMY_FILE = "/Users/edwardzev/crawler/data/categorizing/taxonomy_operational_flat.json"
OUTPUT_CSV = "/Users/edwardzev/crawler/data/categorizing/ai_categories.csv"

# ==========================================

client = OpenAI()

def strip_html(html):
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ", strip=True)

def resolve_products_path():
    candidates = [
        PRODUCTS_FILE,
        "../out/products.frontend.json",
        "../../frontend/public/data/products.frontend.json",
        "frontend/public/data/products.frontend.json",
        "/Users/edwardzev/crawler/frontend/public/data/products.frontend.json",
    ]
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8"):
                return path
        except FileNotFoundError:
            continue
    raise FileNotFoundError(
        f"products.frontend.json not found. Tried: {', '.join(candidates)}"
    )


def load_products():
    path = resolve_products_path()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_taxonomy():
    with open(TAXONOMY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def build_prompt(taxonomy, products):
    return f"""
You are a deterministic classification engine for a B2B promotional-products catalog.

You MUST classify each product using ONLY the taxonomy below.
Do NOT invent categories.
If unsure, return UNCLASSIFIED with confidence < 0.5.

TAXONOMY (allowed values only):
{json.dumps(taxonomy, ensure_ascii=False)}

Return ONLY valid JSON array.
One output object per input product, SAME ORDER.

Each object must be:
{{
  "sku": "...",
  "supplier": "...",
  "ai_major_category_he": "...",
  "ai_major_category_slug": "...",
  "ai_subcategory_he": "...",
  "ai_subcategory_slug": "...",
  "ai_confidence": 0.00
}}

PRODUCTS:
{json.dumps(products, ensure_ascii=False)}
"""

def classify_batch(taxonomy, batch):
    prompt = build_prompt(taxonomy, batch)

    text = ""
    for attempt in range(RETRY_LIMIT):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            text = response.choices[0].message.content
            
            # Strip Markdown if present
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")
            elif text.startswith("```"):
                text = text.replace("```", "")
                
            return json.loads(text)
        except Exception as e:
            print(f"Match Batch Error (Attempt {attempt+1}): {e}")
            if text:
                print(f"RAW OUTPUT START:\n{text[:200]}\nRAW OUTPUT END")
            
            if attempt == RETRY_LIMIT - 1:
                print("Skipping batch due to repeated errors.")
                return []
            time.sleep(2)

def preprocess_products(raw_products):
    cleaned = []
    for p in raw_products:
        cleaned.append({
            "sku": p.get("sku"),
            "supplier": p.get("supplier"),
            "title": p.get("title"),
            "description": strip_html(p.get("description", ""))[:MAX_DESC_CHARS]
        })
    return cleaned

def main():
    products = preprocess_products(load_products())
    taxonomy = load_taxonomy()

    # Load existing to skip
    existing_keys = set()
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_keys.add((row["supplier"], row["sku"]))
    
    print(f"Found {len(existing_keys)} existing categorizations.")
    
    # Filter products
    to_process = []
    for p in products:
        if (p["supplier"], p["sku"]) not in existing_keys:
            to_process.append(p)
            
    print(f"Products to classify: {len(to_process)}")
    
    if not to_process:
        print("Nothing new to classify.")
        return

    results = []

    for i in tqdm(range(0, len(to_process), BATCH_SIZE)):
        batch = to_process[i:i+BATCH_SIZE]
        classified = classify_batch(taxonomy, batch)
        if classified:
             results.extend(classified)
        time.sleep(SLEEP_BETWEEN_CALLS)

    # Append to CSV
    file_exists = os.path.exists(OUTPUT_CSV)
    mode = "a" if file_exists else "w"
    
    with open(OUTPUT_CSV, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "sku",
                "supplier",
                "ai_major_category_he",
                "ai_major_category_slug",
                "ai_subcategory_he",
                "ai_subcategory_slug",
                "ai_confidence"
            ]
        )
        if not file_exists:
            writer.writeheader()
        
        for row in results:
            writer.writerow(row)

    print(f"\n✅ Done. Appended {len(results)} rows to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()