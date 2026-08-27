"""
PEVN Backend — Authoritative DUE National Dataset Harvester & Archiver

Fetches the complete national dataset of Colombian Educational Establishments
from the official Ministry of Education SODA endpoint:
  Resource: cfw5-qzt5 (MEN_ESTABLECIMIENTOS_EDUCATIVOS_PREESCOLAR_BÁSICA_Y_MEDIA)
  Filter: a_o = 2024
  Target Cardinality: 18,076 records

Saves the immutable raw archive and computes its deterministic SHA-256 fingerprint.
"""

from __future__ import annotations

import hashlib
import json
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SOURCE_RESOURCE = "cfw5-qzt5"
BASE_URL = f"https://www.datos.gov.co/resource/{SOURCE_RESOURCE}.json"
DATASET_YEAR = "2024"
PAGE_SIZE = 1000
TARGET_COUNT = 18076
OUTPUT_PATH = Path(__file__).parent / "official_due_national_dataset_2024.json"


def harvest_national_dataset() -> tuple[list[dict[str, Any]], str]:
    ctx = ssl.create_default_context()
    all_records: list[dict[str, Any]] = []

    print(f"[*] Starting national DUE harvest from {BASE_URL} for year {DATASET_YEAR}...")
    offset = 0
    page_num = 1

    while True:
        query_params = {
            "$where": f"a_o={DATASET_YEAR}",
            "$limit": PAGE_SIZE,
            "$offset": offset,
            "$order": "codigo_dane ASC",
        }
        url = f"{BASE_URL}?{urllib.parse.urlencode(query_params)}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "PEvN-National-Harvester/1.0",
                "Accept": "application/json",
            },
        )

        retries = 3
        page_records = None
        while retries > 0:
            try:
                with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                    if resp.status != 200:
                        raise ValueError(f"HTTP Error {resp.status}")
                    body = resp.read().decode("utf-8")
                    page_records = json.loads(body)
                    break
            except Exception as e:
                retries -= 1
                print(f"    [!] Warning: page {page_num} fetch error ({e}), retrying ({retries} left)...")
                time.sleep(2)

        if page_records is None:
            raise RuntimeError(f"Failed to fetch page {page_num} at offset {offset} after retries.")

        count_in_page = len(page_records)
        all_records.extend(page_records)
        print(f"    [+] Chunk {page_num:02d}: fetched {count_in_page} records (Total so far: {len(all_records)})")

        if count_in_page < PAGE_SIZE or len(all_records) >= TARGET_COUNT:
            break

        offset += PAGE_SIZE
        page_num += 1
        time.sleep(0.3)  # Respect government API rate limits

    total_harvested = len(all_records)
    print(f"[*] Harvest completed: {total_harvested} total records retrieved.")

    # Compute deterministic SHA-256
    serialized = json.dumps(all_records, sort_keys=True, default=str).encode("utf-8")
    checksum = hashlib.sha256(serialized).hexdigest()
    print(f"[*] Dataset SHA-256: {checksum}")

    # Save to disk
    OUTPUT_PATH.write_text(json.dumps(all_records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[*] Saved raw archive to: {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size / 1024 / 1024:.2f} MB)")

    return all_records, checksum


if __name__ == "__main__":
    harvest_national_dataset()
