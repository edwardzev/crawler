import json
import math
import os

INPUT_FILE = "/Users/edwardzev/crawler/data/out/products.frontend.json"
OUTPUT_DIR = "/Users/edwardzev/crawler/data/out"
NUM_CHUNKS = 5

def split_chunks():
    print(f"Reading {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {INPUT_FILE}")
        return

    if not isinstance(data, list):
        print("Error: JSON data is not a list of products.")
        return

    total = len(data)
    chunk_size = math.ceil(total / NUM_CHUNKS)
    print(f"Total items: {total}. chunk_size ~= {chunk_size}")

    for i in range(NUM_CHUNKS):
        start = i * chunk_size
        end = start + chunk_size
        chunk = data[start:end]
        
        filename = os.path.join(OUTPUT_DIR, f"chunk{i+1}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {filename} with {len(chunk)} items.")

if __name__ == "__main__":
    split_chunks()
