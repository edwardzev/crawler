#!/usr/bin/env python3
"""Export Airtable Products table to frontend JSON snapshots.

Writes:
- products.frontend.json
- categories.frontend.json
- categories.flat.json

Usage:
  python airtable/export_airtable_snapshot.py --output data/out --public frontend/public/data
"""
from __future__ import annotations

import argparse
import json
import os
import time
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from crawler.utils import slugify, clean_sku, slugify_supplier

BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"
API_BASE = "https://api.airtable.com/v0"
API_URL = f"{API_BASE}/{BASE_ID}/{TABLE_NAME}"

MAX_RETRIES = 5
PAGE_SIZE = 100
SLEEP_BETWEEN_PAGES = 0.2


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


def normalize_category_path(fields: Dict[str, Any]) -> List[str]:
    parts = []
    for key in ("category_major", "category_sub", "category_sub2"):
        val = fields.get(key)
        if isinstance(val, list):
            val = val[0] if val else ""
        if val is None:
            continue
        s = str(val).strip()
        if s:
            parts.append(s)
    return parts


def parse_properties(fields: Dict[str, Any]) -> Dict[str, str]:
    raw = fields.get("properties")
    if not raw:
        return {}
    if isinstance(raw, dict):
        return {str(k): str(v) for k, v in raw.items()}
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except Exception:
            return {}
    return {}


def collect_images(fields: Dict[str, Any]) -> List[str]:
    images: List[str] = []

    # Airtable attachments
    attachments = fields.get("images")
    if isinstance(attachments, list):
        for att in attachments:
            url = att.get("url") if isinstance(att, dict) else None
            if url:
                images.append(url)

    # image_urls newline-separated
    image_urls = fields.get("image_urls")
    if isinstance(image_urls, str):
        for line in image_urls.splitlines():
            line = line.strip()
            if line:
                images.append(line)

    # image_main_url fallback
    image_main_url = fields.get("image_main_url")
    if isinstance(image_main_url, str) and image_main_url.strip():
        images.append(image_main_url.strip())

    # de-dup
    seen = set()
    deduped = []
    for url in images:
        if url not in seen:
            seen.add(url)
            deduped.append(url)
    return deduped


def build_product(fields: Dict[str, Any], record_id: str) -> Dict[str, Any]:
    supplier = fields.get("supplier") or ""
    supplier_slug = fields.get("supplier_slug") or slugify_supplier(supplier)
    sku = fields.get("sku") or ""
    sku_clean = fields.get("sku_clean") or clean_sku(sku)
    catalog_id = fields.get("catalog_id") or ""
    product_id = fields.get("product_id") or fields.get("legacy_product_id") or ""
    title = fields.get("title") or ""
    description = fields.get("description") or ""

    category_path = normalize_category_path(fields)
    category_slug_path = [slugify(c) for c in category_path]

    images = collect_images(fields)
    image_main = images[0] if images else None

    slug_override = fields.get("slug_override") or ""
    slug_source = slug_override.strip() or (f"{title}-{sku}" if sku else title)
    slug = slugify(slug_source)

    properties = parse_properties(fields)
    search_parts = [title, sku] + category_path + list(properties.keys()) + list(properties.values())
    search_blob = " ".join([str(p) for p in search_parts if p])

    url = fields.get("source_url") or fields.get("url") or ""

    return {
        "id": catalog_id or product_id or record_id,
        "catalog_id": catalog_id or None,
        "sku_clean": sku_clean or None,
        "supplier_slug": supplier_slug or None,
        "supplier": supplier or None,
        "url": url or None,
        "url_clean": url or None,
        "slug": slug,
        "title": title,
        "sku": sku,
        "category_path": category_path,
        "category_slug_path": category_slug_path,
        "description": description or None,
        "properties": properties,
        "images": images,
        "image_main": image_main,
        "price": fields.get("price"),
        "currency": fields.get("currency"),
        "availability": fields.get("availability"),
        "variants": [],
        "content_hash": fields.get("content_hash"),
        "first_seen_at": str(fields.get("first_seen_at") or ""),
        "last_seen_at": str(fields.get("last_seen_in_crawl") or fields.get("last_seen_at") or ""),
        "search_blob": search_blob,
    }


def build_category_structures(all_paths: List[List[str]]):
    tree = {"name": "root", "slug": "", "children": []}

    for path in all_paths:
        current_node = tree
        for segment in path:
            slug = slugify(segment)
            found = None
            for child in current_node["children"]:
                if child["slug"] == slug:
                    found = child
                    break
            if not found:
                found = {"name": segment, "slug": slug, "count": 0, "children": []}
                current_node["children"].append(found)
            found["count"] += 1
            current_node = found

    flat_list: List[Dict[str, Any]] = []

    def traverse(node, path_names, path_slugs):
        if node["name"] != "root":
            flat_list.append({
                "path": path_names,
                "slug_path": path_slugs,
                "count": node["count"],
            })
        for child in node["children"]:
            traverse(child, path_names + [child["name"]], path_slugs + [child["slug"]])

    traverse(tree, [], [])
    return tree, flat_list


def export_snapshots(output_dir: Path, public_dir: Path | None = None) -> None:
    load_dotenv(os.path.join(os.getcwd(), ".env"))
    pat = must_pat()

    output_dir.mkdir(parents=True, exist_ok=True)
    if public_dir:
        public_dir.mkdir(parents=True, exist_ok=True)

    all_products: List[Dict[str, Any]] = []
    all_paths: List[List[str]] = []

    offset = None
    total = 0
    page = 0

    while True:
        page += 1
        params: List[Tuple[str, str]] = [("pageSize", str(PAGE_SIZE))]
        if offset:
            params.append(("offset", offset))

        data = airtable_get_json(API_URL, pat=pat, params=params)
        records = data.get("records", [])
        total += len(records)

        for rec in records:
            fields = rec.get("fields", {})
            product = build_product(fields, rec.get("id"))
            all_products.append(product)
            if product.get("category_path"):
                all_paths.append(product["category_path"])

        offset = data.get("offset")
        if not offset:
            break
        time.sleep(SLEEP_BETWEEN_PAGES)

    tree, flat = build_category_structures(all_paths)

    products_path = output_dir / "products.frontend.json"
    categories_path = output_dir / "categories.frontend.json"
    flat_path = output_dir / "categories.flat.json"

    products_path.write_text(json.dumps(all_products, ensure_ascii=False, indent=2), encoding="utf-8")
    categories_path.write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")
    flat_path.write_text(json.dumps(flat, ensure_ascii=False, indent=2), encoding="utf-8")

    if public_dir:
        (public_dir / "products.frontend.json").write_text(json.dumps(all_products, ensure_ascii=False, indent=2), encoding="utf-8")
        (public_dir / "categories.frontend.json").write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")
        (public_dir / "categories.flat.json").write_text(json.dumps(flat, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Exported {len(all_products)} products")
    print(f"Wrote snapshots to {output_dir}")
    if public_dir:
        print(f"Mirrored snapshots to {public_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Airtable Products to frontend snapshots")
    parser.add_argument("--output", type=str, default="data/out", help="Output directory for snapshots")
    parser.add_argument("--public", type=str, default="frontend/public/data", help="Public data mirror directory")
    parser.add_argument("--no-public", action="store_true", help="Do not mirror to frontend/public/data")
    args = parser.parse_args()

    output_dir = Path(args.output)
    public_dir = None if args.no_public else Path(args.public)

    export_snapshots(output_dir, public_dir)


if __name__ == "__main__":
    main()
