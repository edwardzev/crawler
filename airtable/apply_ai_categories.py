#!/usr/bin/env python3
"""Apply AI category results to Airtable Products table.

Updates string fields:
- category_major
- category_sub
- category_path

Matches on (supplier, sku).

Usage:
  python airtable/apply_ai_categories.py --csv data/categorizing/ai_categories.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

import requests
from dotenv import load_dotenv

BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_BASE = "https://api.airtable.com/v0"
API_URL = f"{API_BASE}/{BASE_ID}/{TABLE_NAME}"

PAGE_SIZE = 100
BATCH_SIZE = 10
MAX_RETRIES = 5
SLEEP_BETWEEN_BATCHES = 0.2


def must_pat() -> str:
    pat = os.getenv("AIRTABLE_PAT")
    if not pat:
        raise SystemExit("ERROR: AIRTABLE_PAT env var not set")
    return pat


def headers(pat: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {pat}", "Content-Type": "application/json"}


def airtable_get_json(url: str, *, pat: str, params: List[Tuple[str, str]] | None = None) -> Dict[str, Any]:
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, headers=headers(pat), params=params, timeout=30)
            if r.status_code in (429, 500, 502, 503, 504):
                retry_after = r.headers.get("Retry-After")
                sleep_s = float(retry_after) if retry_after else min(2**attempt, 20)
                time.sleep(sleep_s)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            time.sleep(min(2**attempt, 20))
            continue
    raise SystemExit(f"ERROR: Airtable request failed after {MAX_RETRIES} retries: {last_err}")


def airtable_patch(records: List[Dict[str, Any]], pat: str) -> requests.Response:
    payload = {"records": records}
    return requests.patch(API_URL, headers=headers(pat), json=payload, timeout=45)


def load_ai_csv(path: Path) -> Dict[Tuple[str, str], Dict[str, str]]:
    mapping: Dict[Tuple[str, str], Dict[str, str]] = {}
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            supplier = (row.get("supplier") or "").strip()
            sku = (row.get("sku") or "").strip()
            if not supplier or not sku:
                continue
            mapping[(supplier, sku)] = {
                "major": (row.get("ai_major_category_he") or "").strip(),
                "sub": (row.get("ai_subcategory_he") or "").strip(),
            }
    return mapping


def build_category_path(major: str, sub: str) -> str:
    if major and sub:
        return f"{major} > {sub}"
    return major or sub or ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply AI categories to Airtable")
    parser.add_argument("--csv", type=str, default="data/categorizing/ai_categories.csv")
    args = parser.parse_args()

    load_dotenv(os.path.join(os.getcwd(), ".env"))
    pat = must_pat()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    ai_map = load_ai_csv(csv_path)
    print(f"Loaded {len(ai_map)} AI rows")

    updates: List[Dict[str, Any]] = []
    offset = None
    total = 0

    while True:
        params: List[Tuple[str, str]] = [("pageSize", str(PAGE_SIZE))]
        for field in ("sku", "supplier", "category_major", "category_sub", "category_path"):
            params.append(("fields[]", field))
        if offset:
            params.append(("offset", offset))

        data = airtable_get_json(API_URL, pat=pat, params=params)
        records = data.get("records", [])
        total += len(records)

        for rec in records:
            fields = rec.get("fields", {})
            supplier = (fields.get("supplier") or "").strip()
            sku = (fields.get("sku") or "").strip()
            key = (supplier, sku)
            if key not in ai_map:
                continue
            major = ai_map[key]["major"]
            sub = ai_map[key]["sub"]
            cat_path = build_category_path(major, sub)

            updates.append({
                "id": rec.get("id"),
                "fields": {
                    "category_major": major,
                    "category_sub": sub,
                    "category_path": cat_path,
                },
            })

        offset = data.get("offset")
        if not offset:
            break

    print(f"Prepared {len(updates)} updates from {total} Airtable records")

    # Batch update
    for i in range(0, len(updates), BATCH_SIZE):
        chunk = updates[i : i + BATCH_SIZE]
        resp = airtable_patch(chunk, pat)
        if not resp.ok:
            print(f"Batch {i}: Error {resp.status_code}: {resp.text}")
        else:
            if (i + len(chunk)) % 200 == 0 or (i + len(chunk)) == len(updates):
                print(f"Updated {i + len(chunk)}/{len(updates)}")
        time.sleep(SLEEP_BETWEEN_BATCHES)

    print("✅ Done")


if __name__ == "__main__":
    main()
