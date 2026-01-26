#!/usr/bin/env python3
"""Describe Airtable base/table schema + stats.

Reads AIRTABLE_PAT from env.
"""

from __future__ import annotations

import os
import sys
import time
from collections import Counter
from typing import Any, Dict, List, Tuple

import requests
from requests.exceptions import ConnectionError, ReadTimeout, Timeout

BASE_ID = "app1tMmtuC7BGfJLu"
TABLE_NAME = "Products"

META_API = "https://api.airtable.com/v0/meta"
DATA_API = "https://api.airtable.com/v0"


def must_pat() -> str:
    pat = os.getenv("AIRTABLE_PAT")
    if not pat:
        raise SystemExit("ERROR: AIRTABLE_PAT env var not set")
    return pat


def meta_headers(pat: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {pat}"}


def data_headers(pat: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {pat}", "Content-Type": "application/json"}


def get_tables(pat: str) -> List[Dict[str, Any]]:
    url = f"{META_API}/bases/{BASE_ID}/tables"
    data = airtable_get_json(url, headers=meta_headers(pat), timeout=30)
    return data.get("tables", [])


def airtable_get_json(
    url: str,
    *,
    headers: Dict[str, str],
    params: List[Tuple[str, str]] | None = None,
    timeout: float = 30,
    max_retries: int = 5,
) -> Dict[str, Any]:
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                retry_after = r.headers.get("Retry-After")
                sleep_s = float(retry_after) if retry_after else min(2**attempt, 20)
                time.sleep(sleep_s)
                continue
            r.raise_for_status()
            return r.json()
        except (Timeout, ReadTimeout, ConnectionError) as e:
            last_err = e
            time.sleep(min(2**attempt, 20))
            continue

    raise SystemExit(f"ERROR: Airtable request failed after {max_retries} retries: {last_err}")


def find_table(tables: List[Dict[str, Any]]) -> Dict[str, Any]:
    for t in tables:
        if t.get("name") == TABLE_NAME:
            return t
    raise SystemExit(f"ERROR: table '{TABLE_NAME}' not found")


def paginate_records(pat: str, fields: List[str]) -> Tuple[int, Counter, int, int, int, int, int]:
    url = f"{DATA_API}/{BASE_ID}/{TABLE_NAME}"
    offset = None

    page = 0

    total = 0
    status_counts: Counter = Counter()
    status_empty = 0
    needs_fix = 0
    has_catalog = 0
    with_images = 0
    price_set = 0

    while True:
        page += 1
        params: List[Tuple[str, str]] = [("pageSize", "100")]
        for f in fields:
            params.append(("fields[]", f))
        if offset:
            params.append(("offset", offset))

        data = airtable_get_json(url, headers=data_headers(pat), params=params, timeout=30)
        recs = data.get("records", [])
        total += len(recs)

        if page == 1 or page % 5 == 0:
            off = data.get("offset")
            off_preview = (off[:8] + "…") if isinstance(off, str) and len(off) > 8 else (off or "(end)")
            print(f"Scanning records… page={page} total={total} next_offset={off_preview}")

        for rec in recs:
            fs = rec.get("fields", {})

            st = fs.get("status")
            if st is None:
                status_empty += 1
            else:
                status_counts[str(st)] += 1

            if fs.get("needs_fix_id"):
                needs_fix += 1
            if fs.get("catalog_id"):
                has_catalog += 1
            if fs.get("images"):
                with_images += 1
            if fs.get("price") not in (None, ""):
                price_set += 1

        offset = data.get("offset")
        if not offset:
            break

    return total, status_counts, status_empty, needs_fix, has_catalog, with_images, price_set


def main() -> None:
    pat = must_pat()

    tables = get_tables(pat)
    products = find_table(tables)

    table_id = products.get("id")
    primary_field_id = products.get("primaryFieldId")
    fields = products.get("fields", [])
    field_by_id = {f.get("id"): f for f in fields}
    primary_field_name = field_by_id.get(primary_field_id, {}).get("name")

    # Build schema summary
    schema_rows = []
    for f in fields:
        name = f.get("name")
        ftype = f.get("type")
        opts = f.get("options") or {}
        choices = opts.get("choices") or []
        choice_names = [c.get("name") for c in choices if c.get("name")]
        schema_rows.append((name, ftype, choice_names))

    # Stats
    fields_to_scan = [
        primary_field_name or "",
        "legacy_product_id",
        "sku",
        "supplier",
        "sku_clean",
        "supplier_slug",
        "catalog_id",
        "status",
        "tags",
        "featured_rank",
        "needs_fix_id",
        "id_conflict_note",
        "images",
        "image_urls",
        "price",
        "currency",
    ]
    fields_to_scan = [f for f in fields_to_scan if f]

    total, status_counts, status_empty, needs_fix, has_catalog, with_images, price_set = paginate_records(pat, fields_to_scan)

    print("Airtable Base Summary")
    print(f"- Base ID: {BASE_ID}")
    print(f"- Table: {TABLE_NAME} ({table_id})")
    print(f"- Primary field: {primary_field_name}")
    print(f"- Total records: {total}")
    print(f"- Records with catalog_id: {has_catalog}")
    print(f"- Records flagged needs_fix_id: {needs_fix}")
    print(f"- Records with images attachment: {with_images}")
    print(f"- Records with price set: {price_set}")

    print("\nStatus Field")
    print(f"- Empty/missing: {status_empty}")
    if status_counts:
        for k, v in status_counts.most_common():
            print(f"- {k}: {v}")
    else:
        print("- (no non-empty status values found)")

    print("\nSchema (fields)")
    for name, ftype, choice_names in schema_rows:
        if choice_names and ftype in ("singleSelect", "multipleSelects"):
            preview = ", ".join(choice_names[:10])
            more = "" if len(choice_names) <= 10 else f" (+{len(choice_names) - 10} more)"
            print(f"- {name}: {ftype} choices=[{preview}]{more}")
        else:
            print(f"- {name}: {ftype}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise
