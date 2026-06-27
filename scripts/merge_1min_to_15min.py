#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Merge 1-min CSV files to 15-min CSV files.

Reads 1min data from morning_report/YYYY-MM-DD/{SYMBOL}_morning.csv,
produces 15min data as {PREFIX}_{CONTRACT}_15min.csv.

Usage:
    python merge_1min_to_15min.py
"""

import csv
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# Mapping: internal symbol -> (prefix, contract_code, source_filename)
# Contract months inferred from data date
DATA_DATE = "2026-06-26"
YEAR, MONTH, DAY = map(int, DATA_DATE.split("-"))

# Determine contract month: use nearest active contract
# For simplicity, use 09-month contracts for most, adjust per exchange
CONTRACT_MONTHS = {
    "RB": "2610",   # SHFE rebar -> Oct
    "JM": "2609",   # DCE coking coal -> Sep
    "J": "2609",    # DCE coke -> Sep
    "JD": "2609",   # SHFE plywood -> Sep
    "TA": "2609",   # CZCE PTA -> Sep
    "CF": "2609",   # CZCE cotton yarn -> Sep
    "AP": "2609",   # CZCE alumina -> Sep
    "AU": "2606",   # SHFE gold -> Jun (already exists)
    "AG": "2606",   # SHFE silver -> Jun (already exists)
}

# Prefix mapping: internal symbol -> CSV filename prefix
PREFIX_MAP = {
    "RB": "RB",
    "JM": "JM",
    "J": "J",
    "JD": "JD",
    "TA": "TA",
    "CF": "CF",
    "AP": "AP",
    "AU": "AU",
    "AG": "AG",
}

SYMBOLS = ["RB", "JM", "J", "JD", "TA", "CF", "AP"]

INPUT_DIR = r"E:\aiprojects\kandlecnen\cnenkandle\scripts\morning_report\2026-06-26"
OUTPUT_DIR = r"E:\aiprojects\kandlecnen\cnenkandle\data_prod"


def merge_1min_to_15min(rows):
    """Merge 1-minute bars into 15-minute bars.

    Group by 15-min bucket:
      - open = first bar's open
      - high = max of highs
      - low = min of lows
      - close = last bar's close
      - volume = sum of volumes
      - hold = last bar's hold (open interest)
    """
    buckets = defaultdict(list)

    for row in rows:
        dt = datetime.strptime(row["datetime"].strip(), "%Y-%m-%d %H:%M:%S")
        # Round down to 15-min boundary
        minute_bucket = (dt.minute // 15) * 15
        bucket_key = dt.replace(minute=minute_bucket, second=0)
        buckets[bucket_key].append(row)

    merged = []
    for bucket_key in sorted(buckets.keys()):
        bars = buckets[bucket_key]
        if not bars:
            continue

        first_bar = bars[0]
        last_bar = bars[-1]

        highs = []
        lows = []
        volumes = []
        holds = []

        for b in bars:
            try:
                highs.append(float(b["high"]))
                lows.append(float(b["low"]))
                volumes.append(int(float(b["volume"])))
                h = b.get("hold", "").strip()
                if h:
                    holds.append(float(h))
            except (ValueError, KeyError):
                pass

        merged.append({
            "datetime": bucket_key.strftime("%Y-%m-%d %H:%M:%S"),
            "open": first_bar["open"],
            "high": max(highs) if highs else first_bar["high"],
            "low": min(lows) if lows else first_bar["low"],
            "close": last_bar["close"],
            "volume": sum(volumes),
            "hold": last_bar.get("hold", ""),
        })

    return merged


def process_symbol(symbol):
    """Process one symbol: read 1min CSV, merge to 15min, write output."""
    prefix = PREFIX_MAP.get(symbol, symbol)
    contract = CONTRACT_MONTHS.get(symbol, "2609")

    input_file = os.path.join(INPUT_DIR, f"{symbol}_morning.csv")
    output_file = os.path.join(OUTPUT_DIR, f"{prefix}_{prefix.lower()}{contract}_15min.csv")

    if not os.path.exists(input_file):
        print(f"  SKIP: {input_file} not found")
        return False

    # Read 1min data
    rows = []
    with open(input_file, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("datetime", "").strip():
                rows.append(row)

    if not rows:
        print(f"  SKIP: {symbol} has no data")
        return False

    print(f"  {symbol}: {len(rows)} 1-min bars -> ", end="", flush=True)

    # Merge to 15min
    merged = merge_1min_to_15min(rows)
    print(f"{len(merged)} 15-min bars")

    # Write output
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["datetime", "open", "high", "low", "close", "volume", "hold"])
        writer.writeheader()
        writer.writerows(merged)

    print(f"  -> {output_file}")
    return True


def main():
    print("=" * 60)
    print("1-min to 15-min CSV merger")
    print("=" * 60)
    print(f"Input:  {INPUT_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    success = 0
    skip = 0

    for symbol in SYMBOLS:
        if process_symbol(symbol):
            success += 1
        else:
            skip += 1

    print()
    print(f"Done: {success} merged, {skip} skipped")

    # Also list what's in data_prod now
    print()
    print("Files in data_prod:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith(".csv"):
            size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
            print(f"  {f} ({size:,} bytes)")


if __name__ == "__main__":
    main()
