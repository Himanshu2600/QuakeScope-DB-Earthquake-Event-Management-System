"""
import_data.py
QuakeScope DB - Stage 1: Data Import Script

This script imports earthquake events from the CSV file (data/query.csv)
into the MongoDB collection 'earthquake_events' in the 'quakescope_db' database.

Key Features:
- Reads the CSV file using Python's standard csv module
- Maps raw CSV column names to clear, readable document fields
- Converts data into appropriate BSON types (ISODate, float, int, str)
- Validates data against the MongoDB schema validator
- Prevents duplicate inserts by tracking existing 'event_id' values
- Reports total rows read, inserted, skipped, and rejected

Usage:
    python scripts/import_data.py
"""

import csv
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import PyMongoError, BulkWriteError

# Configuration
DATA_PATH = os.path.join("data", "query.csv")
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "quakescope_db"
COLLECTION_NAME = "earthquake_events"
BATCH_SIZE = 1000

def parse_date(date_string):
    """Parse ISO 8601 timestamp string into Python datetime object."""
    if not date_string or date_string.strip() == "":
        return None
    try:
        clean_str = date_string.strip().replace("Z", "+00:00")
        return datetime.fromisoformat(clean_str)
    except Exception:
        return None

def parse_float(value):
    """Safely convert a string to float; returns None if empty or invalid."""
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None

def parse_int(value):
    """Safely convert a string to int; returns None if empty or invalid."""
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None

def transform_row(row):
    """
    Transforms a single CSV row into a clean MongoDB earthquake document.
    Maps USGS column names to descriptive, student-friendly field names.
    """
    event_id = row.get("id", "").strip()
    if not event_id:
        return None

    # Parse mandatory timestamps and numeric measurements
    event_time = parse_date(row.get("time"))
    latitude = parse_float(row.get("latitude"))
    longitude = parse_float(row.get("longitude"))
    depth_km = parse_float(row.get("depth"))
    magnitude = parse_float(row.get("mag"))
    magnitude_type = row.get("magType", "").strip()
    location = row.get("place", "").strip()
    event_type = row.get("type", "").strip()

    # Ensure required fields are present
    if (event_time is None or latitude is None or longitude is None or
        depth_km is None or magnitude is None or not magnitude_type or
        not location or not event_type):
        return None

    doc = {
        "event_id": event_id,
        "event_time": event_time,
        "latitude": latitude,
        "longitude": longitude,
        "depth_km": depth_km,
        "magnitude": magnitude,
        "magnitude_type": magnitude_type,
        "location": location,
        "event_type": event_type,
    }

    # Optional timestamps and metadata
    updated_time = parse_date(row.get("updated"))
    if updated_time:
        doc["updated_time"] = updated_time

    review_status = row.get("status", "").strip()
    if review_status:
        doc["review_status"] = review_status

    network = row.get("net", "").strip()
    if network:
        doc["network"] = network

    # Optional seismic quality metrics (included only when non-empty)
    nst = parse_int(row.get("nst"))
    if nst is not None:
        doc["station_count"] = nst

    gap = parse_float(row.get("gap"))
    if gap is not None:
        doc["azimuthal_gap"] = gap

    dmin = parse_float(row.get("dmin"))
    if dmin is not None:
        doc["min_distance"] = dmin

    rms = parse_float(row.get("rms"))
    if rms is not None:
        doc["rms_residual"] = rms

    horizontal_error = parse_float(row.get("horizontalError"))
    if horizontal_error is not None:
        doc["horizontal_error"] = horizontal_error

    depth_error = parse_float(row.get("depthError"))
    if depth_error is not None:
        doc["depth_error"] = depth_error

    mag_error = parse_float(row.get("magError"))
    if mag_error is not None:
        doc["magnitude_error"] = mag_error

    mag_nst = parse_int(row.get("magNst"))
    if mag_nst is not None:
        doc["magnitude_station_count"] = mag_nst

    loc_source = row.get("locationSource", "").strip()
    if loc_source:
        doc["location_source"] = loc_source

    mag_source = row.get("magSource", "").strip()
    if mag_source:
        doc["magnitude_source"] = mag_source

    return doc

def import_earthquakes():
    print("=" * 70)
    print("QUAKESCOPE DB - STAGE 1: DATA IMPORT PROCESS")
    print("=" * 70)

    # 1. Verify CSV dataset existence
    if not os.path.exists(DATA_PATH):
        print(f"[ERROR] CSV dataset not found at '{DATA_PATH}'. Aborting.")
        sys.exit(1)

    # 2. Connect to local MongoDB
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command("ping")
        print(f"[SUCCESS] Connected to MongoDB at {MONGO_URI}")
    except Exception as e:
        print(f"[ERROR] Could not connect to MongoDB: {e}")
        print("Please ensure the MongoDB Community Server service is running.")
        sys.exit(1)

    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # 3. Retrieve existing event IDs to prevent duplicate insertion
    print(f"Retrieving existing event IDs from '{COLLECTION_NAME}'...")
    existing_ids = set(collection.distinct("event_id"))
    initial_count = len(existing_ids)
    print(f"Collection currently contains {initial_count:,} existing documents.")

    # 4. Read and process CSV file
    total_read = 0
    skipped_count = 0
    rejected_count = 0
    documents_to_insert = []
    inserted_count = 0

    print(f"\nReading dataset from '{DATA_PATH}'...")
    with open(DATA_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            total_read += 1
            raw_id = row.get("id", "").strip()

            # Deduplication check: skip if event_id is already in the database
            if raw_id in existing_ids:
                skipped_count += 1
                continue

            doc = transform_row(row)
            if doc is None:
                rejected_count += 1
                continue

            documents_to_insert.append(doc)
            existing_ids.add(raw_id)  # Avoid within-batch duplicates

            # Insert in batches
            if len(documents_to_insert) >= BATCH_SIZE:
                try:
                    result = collection.insert_many(documents_to_insert, ordered=False)
                    inserted_count += len(result.inserted_ids)
                    print(f"  -> Inserted batch of {len(result.inserted_ids):,} records (Total inserted: {inserted_count:,})")
                except BulkWriteError as bwe:
                    # Capture partial batch insertion if any error occurs
                    inserted_count += bwe.details.get("nInserted", 0)
                    print(f"  [WARNING] BulkWriteError during batch insert: {bwe.details.get('writeErrors', [])[:2]}")
                documents_to_insert.clear()

        # Insert remaining documents
        if documents_to_insert:
            try:
                result = collection.insert_many(documents_to_insert, ordered=False)
                inserted_count += len(result.inserted_ids)
                print(f"  -> Inserted final batch of {len(result.inserted_ids):,} records")
            except BulkWriteError as bwe:
                inserted_count += bwe.details.get("nInserted", 0)
                print(f"  [WARNING] BulkWriteError during final insert: {bwe.details.get('writeErrors', [])[:2]}")
            documents_to_insert.clear()

    # 5. Final summary
    final_count = collection.count_documents({})
    print("\n" + "=" * 70)
    print("IMPORT SUMMARY REPORT:")
    print(f"  - Total records read from CSV : {total_read:,}")
    print(f"  - Records newly inserted     : {inserted_count:,}")
    print(f"  - Records skipped (duplicate) : {skipped_count:,}")
    print(f"  - Records rejected (invalid)  : {rejected_count:,}")
    print(f"  - Total documents in MongoDB  : {final_count:,}")
    print("=" * 70)

    # 6. Verify sample document structure
    sample = collection.find_one()
    if sample:
        print("\nSAMPLE STORED DOCUMENT (BSON Verification):")
        for key, val in sample.items():
            print(f"  {key:<22}: {val} (Type: {type(val).__name__})")
    print("=" * 70)

if __name__ == "__main__":
    import_earthquakes()
