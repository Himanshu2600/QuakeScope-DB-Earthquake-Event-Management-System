"""
inspect_dataset.py
QuakeScope DB - Stage 1: Dataset Inspection Script

This script inspects the earthquake CSV dataset downloaded from the USGS
(United States Geological Survey) Earthquake Hazards Program.
It analyzes:
- File metadata (row count, columns, headers)
- Representative records from beginning, middle, and end
- Data types and missing values per column
- Value ranges for latitude, longitude, depth, and magnitude
- Identification of unique event IDs and duplicate checks
- Categorical distributions (magnitude types, event types, review status)

Usage:
    python scripts/inspect_dataset.py
"""

import csv
import os
from datetime import datetime

# Path to the dataset inside the project's data folder
DATA_FILE = os.path.join("data", "query.csv")

def inspect_dataset():
    # Check if the dataset file exists
    if not os.path.exists(DATA_FILE):
        print(f"[ERROR] Dataset file not found at: {DATA_FILE}")
        return

    print("=" * 75)
    print("QUAKESCOPE DB - STAGE 1: DATASET INSPECTION")
    print(f"Dataset File : {DATA_FILE}")
    print(f"File Size    : {os.path.getsize(DATA_FILE):,} bytes ({os.path.getsize(DATA_FILE) / (1024*1024):.2f} MB)")
    print("=" * 75)

    with open(DATA_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        rows = list(reader)

    total_rows = len(rows)
    total_cols = len(headers)

    print(f"\n1. GENERAL SUMMARY")
    print(f"   - Total Data Rows    : {total_rows:,}")
    print(f"   - Total Columns      : {total_cols}")
    print(f"   - Header Columns     : {', '.join(headers)}")

    # Check date range and parse timestamps
    times = []
    ids = set()
    duplicate_ids = []
    
    # Track missing values per column
    missing_counts = {col: 0 for col in headers}
    
    # Range trackers
    latitudes = []
    longitudes = []
    depths = []
    magnitudes = []
    mag_types = set()
    event_types = set()
    statuses = set()

    for idx, row in enumerate(rows):
        # Missing values check
        for col in headers:
            val = row.get(col, "").strip()
            if val == "":
                missing_counts[col] += 1

        # Check unique event ID
        event_id = row.get("id", "").strip()
        if event_id in ids:
            duplicate_ids.append(event_id)
        else:
            ids.add(event_id)

        # Parse event time
        time_str = row.get("time", "").strip()
        if time_str:
            try:
                # Format: 2026-01-01T23:30:51.522Z
                # Replace 'Z' for ISO parsing
                clean_time = time_str.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_time)
                times.append(dt)
            except Exception as e:
                pass

        # Numeric conversions for coordinates and measurements
        try:
            if row.get("latitude", "").strip():
                latitudes.append(float(row["latitude"]))
            if row.get("longitude", "").strip():
                longitudes.append(float(row["longitude"]))
            if row.get("depth", "").strip():
                depths.append(float(row["depth"]))
            if row.get("mag", "").strip():
                magnitudes.append(float(row["mag"]))
        except ValueError:
            pass

        # Categoricals
        if row.get("magType", "").strip():
            mag_types.add(row["magType"].strip())
        if row.get("type", "").strip():
            event_types.add(row["type"].strip())
        if row.get("status", "").strip():
            statuses.add(row["status"].strip())

    print(f"\n2. DATA INTEGRITY & UNIQUE IDENTIFIERS")
    print(f"   - Unique 'id' count  : {len(ids):,}")
    print(f"   - Duplicate 'id's    : {len(duplicate_ids)}")

    if times:
        min_time = min(times)
        max_time = max(times)
        print(f"\n3. TEMPORAL COVERAGE (DATE RANGE)")
        print(f"   - Earliest Event     : {min_time.isoformat()}")
        print(f"   - Latest Event       : {max_time.isoformat()}")
        print(f"   - Time Span          : {(max_time - min_time).days} days")

    print(f"\n4. NUMERIC RANGES & COORDINATE VALIDATION")
    if latitudes and longitudes:
        print(f"   - Latitude Range     : min = {min(latitudes):.4f}, max = {max(latitudes):.4f} (Valid: -90 to +90)")
        print(f"   - Longitude Range    : min = {min(longitudes):.4f}, max = {max(longitudes):.4f} (Valid: -180 to +180)")
    if depths:
        print(f"   - Depth (km) Range   : min = {min(depths):.2f} km, max = {max(depths):.2f} km, avg = {sum(depths)/len(depths):.2f} km")
    if magnitudes:
        print(f"   - Magnitude Range    : min = {min(magnitudes):.2f}, max = {max(magnitudes):.2f}, avg = {sum(magnitudes)/len(magnitudes):.2f}")

    print(f"\n5. CATEGORICAL VALUES")
    print(f"   - Event Types        : {sorted(list(event_types))}")
    print(f"   - Magnitude Types    : {sorted(list(mag_types))}")
    print(f"   - Review Statuses    : {sorted(list(statuses))}")

    print(f"\n6. MISSING VALUE ANALYSIS (Empty Strings)")
    print(f"   {'Column Name':<18} | {'Missing Count':<14} | {'% Missing':<10}")
    print(f"   {'-'*18}-|-{'-'*14}-|-{'-'*10}")
    for col in headers:
        m_count = missing_counts[col]
        pct = (m_count / total_rows) * 100
        print(f"   {col:<18} | {m_count:<14,} | {pct:.2f}%")

    print(f"\n7. REPRESENTATIVE RECORDS")
    print("\n   --- FIRST RECORD (Row 1) ---")
    for k, v in rows[0].items():
        print(f"     {k:<18}: {v}")

    mid_idx = total_rows // 2
    print(f"\n   --- MIDDLE RECORD (Row {mid_idx + 1}) ---")
    for k, v in rows[mid_idx].items():
        print(f"     {k:<18}: {v}")

    print(f"\n   --- LAST RECORD (Row {total_rows}) ---")
    for k, v in rows[-1].items():
        print(f"     {k:<18}: {v}")

    print("\n" + "=" * 75)
    print("DATASET ATTRIBUTION & PROVENANCE:")
    print("Source: U.S. Geological Survey (USGS) Earthquake Hazards Program")
    print("Catalog: ANSS Comprehensive Earthquake Catalog (ComCat)")
    print("URL: https://earthquake.usgs.gov/earthquakes/feed/")
    print("License/Terms: U.S. Government Public Domain (Data is free of copyright)")
    print("=" * 75)

if __name__ == "__main__":
    inspect_dataset()
