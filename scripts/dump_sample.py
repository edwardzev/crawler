import json
import random

INPUT_FILE = "data/out/products.frontend.json"

def print_sample():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            products = json.load(f)
            
        # Shuffle to get a good mix
        random.seed(42) 
        sample = random.sample(products, min(len(products), 300))
        
        print(f"--- SAMPLE OF {len(sample)} PRODUCTS ---")
        for p in sample:
            title = p.get("title", "N/A")
            desc = p.get("description", "") or ""
            # Simple cleanup
            desc = desc.replace("<p>", "").replace("</p>", " ").replace("<br>", " ").replace("\n", " ")[:150]
            print(f"- {title} | {desc}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print_sample()
