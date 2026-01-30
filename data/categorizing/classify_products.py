import json
import csv
import time
from bs4 import BeautifulSoup
from tqdm import tqdm
from openai import OpenAI

# ================= CONFIG =================

OPENAI_MODEL = "gpt-5-mini"   # or gpt-5-mini / whatever you use
BATCH_SIZE = 15                # SAFE with stripped text
MAX_DESC_CHARS = 500
RETRY_LIMIT = 3
SLEEP_BETWEEN_CALLS = 0.5

PRODUCTS_FILE = "products.frontend.json"
TAXONOMY_FILE = "taxonomy_operational_flat.json"
OUTPUT_CSV = "ai_categories.csv"

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

    for attempt in range(RETRY_LIMIT):
        try:
            response = client.responses.create(
                model=OPENAI_MODEL,
                input=prompt
            )
            text = response.output_text
            return json.loads(text)
        except Exception as e:
            if attempt == RETRY_LIMIT - 1:
                raise e
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

    results = []

    for i in tqdm(range(0, len(products), BATCH_SIZE)):
        batch = products[i:i+BATCH_SIZE]
        classified = classify_batch(taxonomy, batch)
        results.extend(classified)
        time.sleep(SLEEP_BETWEEN_CALLS)

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
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
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"\n✅ Done. Wrote {len(results)} rows to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()