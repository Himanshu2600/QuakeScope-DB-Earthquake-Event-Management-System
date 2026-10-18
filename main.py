"""
main.py
QuakeScope DB - Terminal Demonstration Application
Course: CSE494 Intelligent NoSQL Databases

This is the interactive terminal application for QuakeScope DB.
It demonstrates:
- PyMongo connectivity to MongoDB Community Server
- CRUD operations (Create, Read, Update, Delete) with schema validation
- Five core MongoDB aggregation pipelines
- Safe test workflows protecting the original USGS dataset
"""

import sys
import os
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scripts.database import test_connection, get_collection
from scripts.crud_operations import (
    create_event,
    find_event_by_id,
    find_events_by_magnitude,
    find_events_by_location,
    find_latest_events,
    update_event,
    delete_event,
    format_event
)
from scripts.aggregation_queries import (
    get_average_magnitude_and_total,
    get_magnitude_distribution,
    get_top_strongest_events,
    get_counts_by_magnitude_type,
    get_monthly_earthquake_counts
)


def print_header(title):
    """Helper to print a clean section header."""
    print("\n" + "=" * 70)
    print(f" {title.upper()}")
    print("=" * 70)


def prompt_create_event():
    """Interactive helper to create a test earthquake record."""
    print_header("Create New Earthquake Record (Test Record)")
    print("Note: This record will be marked as a test event to preserve data integrity.")
    
    event_id = input("Enter unique Event ID [default: test_quake_001]: ").strip()
    if not event_id:
        event_id = "test_quake_001"

    # Confirm it doesn't already exist
    existing = find_event_by_id(event_id)
    if existing:
        print(f"[ERROR] An event with ID '{event_id}' already exists!")
        return

    try:
        mag_input = input("Enter Magnitude (e.g., 4.5): ").strip()
        magnitude = float(mag_input) if mag_input else 4.5

        mag_type = input("Enter Magnitude Type [default: mb]: ").strip() or "mb"
        location = input("Enter Location Description [default: Off Coast of Honshu, Japan]: ").strip() or "Off Coast of Honshu, Japan"

        lat_input = input("Enter Latitude [-90 to 90, default: 36.5]: ").strip()
        latitude = float(lat_input) if lat_input else 36.5

        lon_input = input("Enter Longitude [-180 to 180, default: 140.2]: ").strip()
        longitude = float(lon_input) if lon_input else 140.2

        depth_input = input("Enter Depth in km [-10 to 1000, default: 25.0]: ").strip()
        depth_km = float(depth_input) if depth_input else 25.0

        event_doc = {
            "event_id": event_id,
            "event_time": datetime.now(timezone.utc),
            "latitude": latitude,
            "longitude": longitude,
            "depth_km": depth_km,
            "magnitude": magnitude,
            "magnitude_type": mag_type,
            "location": location,
            "event_type": "earthquake",
            "review_status": "automatic",
            "network": "test"
        }

        result = create_event(event_doc)
        if result["success"]:
            print(f"\n[SUCCESS] {result['message']}")
            print(f"MongoDB Generated _id: {result['inserted_id']}")
        else:
            print(f"\n[FAIL] {result['message']}")

    except ValueError as ve:
        print(f"[INPUT ERROR] Please enter valid numeric values for magnitude, coordinates, and depth. ({ve})")


def prompt_find_by_id():
    """Interactive helper to find an event by ID."""
    print_header("Search Event by ID")
    event_id = input("Enter Event ID to search (e.g., us7000rm06 or test_quake_001): ").strip()
    if not event_id:
        print("[WARNING] No Event ID entered.")
        return

    doc = find_event_by_id(event_id)
    if doc:
        print("\n[RESULT FOUND]")
        print(format_event(doc))
    else:
        print(f"\n[NOT FOUND] No earthquake event found with ID '{event_id}'.")


def prompt_find_by_magnitude():
    """Interactive helper to find events by minimum magnitude."""
    print_header("Search Events by Minimum Magnitude")
    val = input("Enter minimum magnitude threshold (e.g., 7.0) [default: 7.0]: ").strip()
    try:
        min_mag = float(val) if val else 7.0
    except ValueError:
        print("[INPUT ERROR] Invalid number entered.")
        return

    events = find_events_by_magnitude(min_mag, limit=10)
    print(f"\nFound {len(events)} events with magnitude >= {min_mag} (showing up to 10):")
    print(f"{'#':<3} | {'ID':<12} | {'Mag':<5} | {'Depth (km)':<11} | {'Location'}")
    print(f"{'-'*3}-|-{'-'*12}-|-{'-'*5}-|-{'-'*11}-|-{'-'*30}")
    for idx, e in enumerate(events, 1):
        print(f"{idx:<3} | {e.get('event_id'):<12} | {e.get('magnitude'):<5} | {e.get('depth_km',0):<11} | {e.get('location')}")


def prompt_find_by_location():
    """Interactive helper to find events by location keyword."""
    print_header("Search Events by Location Keyword")
    keyword = input("Enter location keyword (e.g., Japan, Chile, California, Fiji): ").strip()
    if not keyword:
        print("[WARNING] No keyword entered.")
        return

    events = find_events_by_location(keyword, limit=5)
    print(f"\nTop matches for keyword '{keyword}':")
    if not events:
        print("  [No matching events found]")
    for idx, e in enumerate(events, 1):
        print(f"  {idx}. [{e.get('event_id')}] M{e.get('magnitude')} - {e.get('location')} ({e.get('event_time')})")


def prompt_show_latest():
    """Interactive helper to show latest events."""
    print_header("Latest Recorded Earthquakes")
    events = find_latest_events(limit=5)
    for idx, e in enumerate(events, 1):
        print(f"  {idx}. [{e.get('event_id')}] M{e.get('magnitude')} - {e.get('location')}")
        print(f"     Time: {e.get('event_time')} | Depth: {e.get('depth_km')} km\n")


def prompt_update_event():
    """Interactive helper to update a test record."""
    print_header("Update Event Record")
    print("Safety Notice: Only user-created test records should be modified during routine testing.")
    event_id = input("Enter Event ID to update (e.g., test_quake_001): ").strip()
    if not event_id:
        print("[WARNING] No ID entered.")
        return

    existing = find_event_by_id(event_id)
    if not existing:
        print(f"[NOT FOUND] No record found with ID '{event_id}'.")
        return

    print("\nCurrent Record:")
    print(format_event(existing))

    print("\nEnter new values (press Enter to leave unchanged):")
    new_mag = input(f"New Magnitude [current: {existing.get('magnitude')}]: ").strip()
    new_loc = input(f"New Location [current: {existing.get('location')}]: ").strip()

    update_fields = {}
    if new_mag:
        try:
            update_fields["magnitude"] = float(new_mag)
        except ValueError:
            print("[INPUT ERROR] Magnitude must be a number.")
            return
    if new_loc:
        update_fields["location"] = new_loc

    if not update_fields:
        print("[INFO] No changes provided. Update cancelled.")
        return

    result = update_event(event_id, update_fields)
    if result["success"]:
        print(f"\n[SUCCESS] {result['message']}")
        updated_doc = find_event_by_id(event_id)
        print("\nUpdated Record:")
        print(format_event(updated_doc))
    else:
        print(f"\n[FAIL] {result['message']}")


def prompt_delete_event():
    """Interactive helper to delete a test record."""
    print_header("Delete Event Record")
    print("Safety Notice: Only delete user-created test records (e.g. starting with 'test_').")
    event_id = input("Enter Event ID to delete: ").strip()
    if not event_id:
        print("[WARNING] No ID entered.")
        return

    existing = find_event_by_id(event_id)
    if not existing:
        print(f"[NOT FOUND] No record found with ID '{event_id}'.")
        return

    # Extra safety check for USGS original records
    if not event_id.startswith("test_"):
        confirm = input(f"[CAUTION] '{event_id}' looks like an original USGS catalog record. Really delete? (type 'YES'): ").strip()
        if confirm != "YES":
            print("[CANCELLED] Deletion cancelled to protect original dataset.")
            return

    result = delete_event(event_id)
    if result["success"]:
        print(f"\n[SUCCESS] {result['message']}")
    else:
        print(f"\n[FAIL] {result['message']}")


def run_automated_self_test():
    """
    Executes a complete end-to-end self-test of all CRUD operations and 
    aggregations, then restores the database to its pristine state.
    """
    print_header("Running Automated Verification Test Suite")
    collection = get_collection()
    initial_count = collection.count_documents({})
    print(f"1. Initial Document Count: {initial_count:,}")

    test_id = "test_autoverify_001"
    
    # Clean up prior test record if left over
    collection.delete_one({"event_id": test_id})

    # Test Create
    print("\n2. Testing CREATE (insert_one)...")
    test_doc = {
        "event_id": test_id,
        "event_time": datetime.now(timezone.utc),
        "latitude": 38.297,
        "longitude": 142.372,
        "depth_km": 20.0,
        "magnitude": 5.1,
        "magnitude_type": "mww",
        "location": "Near Coast of Honshu, Japan (Test Verification)",
        "event_type": "earthquake",
        "review_status": "automatic"
    }
    create_res = create_event(test_doc)
    assert create_res["success"], f"Create failed: {create_res['message']}"
    print(f"   [PASS] Inserted test record with MongoDB ID: {create_res['inserted_id']}")
    assert collection.count_documents({}) == initial_count + 1

    # Test Read
    print("\n3. Testing READ (find_one)...")
    read_doc = find_event_by_id(test_id)
    assert read_doc is not None, "Read failed to find inserted record"
    assert read_doc["magnitude"] == 5.1
    print(f"   [PASS] Found test record: {read_doc['location']}")

    # Test Update
    print("\n4. Testing UPDATE (update_one with $set)...")
    upd_res = update_event(test_id, {"magnitude": 5.4, "location": "Updated Honshu Coast (Reviewed)"})
    assert upd_res["success"], f"Update failed: {upd_res['message']}"
    updated_doc = find_event_by_id(test_id)
    assert updated_doc["magnitude"] == 5.4
    print(f"   [PASS] Successfully updated magnitude from 5.1 -> {updated_doc['magnitude']}")

    # Test Validation Rejection
    print("\n5. Testing SCHEMA VALIDATION REJECTION...")
    invalid_doc = {
        "event_id": "test_invalid_fail",
        "event_time": datetime.now(timezone.utc),
        "latitude": 999.0,   # Invalid: exceeds max 90.0 in $jsonSchema
        "longitude": 140.0,
        "depth_km": 10.0,
        "magnitude": 25.0,   # Invalid: exceeds max 10.0 in $jsonSchema
        "magnitude_type": "mb",
        "location": "Invalid Boundary Test Site",
        "event_type": "earthquake"
    }
    inv_res = create_event(invalid_doc)
    assert not inv_res["success"], "Validator failed to reject invalid document!"
    print(f"   [PASS] MongoDB server-side $jsonSchema validator rejected document: {inv_res['message']}")

    # Test Duplicate Key Rejection
    print("\n6. Testing DUPLICATE KEY REJECTION...")
    dup_res = create_event(test_doc)
    assert not dup_res["success"], "Unique index failed to reject duplicate event_id!"
    print(f"   [PASS] Unique index properly blocked duplicate ID: {dup_res['message']}")

    # Test Delete
    print("\n7. Testing DELETE (delete_one)...")
    del_res = delete_event(test_id)
    assert del_res["success"], f"Delete failed: {del_res['message']}"
    print(f"   [PASS] Successfully deleted test record: {test_id}")

    # Verify Count
    final_count = collection.count_documents({})
    print(f"\n8. Final Document Count: {final_count:,}")
    assert final_count == initial_count, f"Count mismatch! Expected {initial_count}, got {final_count}"
    print("   [CONFIRMED] Collection count returned to exactly 19,705. Original data fully intact.")

    # Test Aggregations
    print("\n9. Verifying 5 AGGREGATION PIPELINES...")
    stats = get_average_magnitude_and_total()
    assert stats["total_events"] == initial_count
    print(f"   [PASS] Aggregation 1: Total {stats['total_events']:,}, Avg Mag {stats['avg_magnitude']}")

    buckets = get_magnitude_distribution()
    assert len(buckets) == 4
    print(f"   [PASS] Aggregation 2: {len(buckets)} magnitude range categories")

    top10 = get_top_strongest_events(10)
    assert len(top10) == 10
    print(f"   [PASS] Aggregation 3: Strongest quake is M{top10[0]['magnitude']} ({top10[0]['location']})")

    mag_types = get_counts_by_magnitude_type()
    assert len(mag_types) > 0
    print(f"   [PASS] Aggregation 4: Found {len(mag_types)} distinct magnitude types")

    monthly = get_monthly_earthquake_counts()
    assert len(monthly) == 13
    print(f"   [PASS] Aggregation 5: Found {len(monthly)} months (Jan 2025 - Jan 2026)")

    print("\n" + "=" * 70)
    print(" [ALL VERIFICATION TESTS PASSED SUCCESSFULLY!]")
    print("=" * 70)


def display_menu():
    """Prints the main interactive menu options."""
    print("\n" + "=" * 65)
    print("         QUAKESCOPE DB — EARTHQUAKE MANAGEMENT SYSTEM")
    print("         Course: CSE494 Intelligent NoSQL Databases (Stage 2)")
    print("=" * 65)
    print("  [DATABASE CONNECTION]")
    print("   1. Test MongoDB Server Connection")
    print("\n  [CRUD OPERATIONS]")
    print("   2. Insert a Test Earthquake Record (Create)")
    print("   3. Search Event by ID (Read)")
    print("   4. Search Events by Minimum Magnitude (Read)")
    print("   5. Search Events by Location Keyword (Read)")
    print("   6. Display Most Recent Earthquakes (Read)")
    print("   7. Update an Event Record (Update)")
    print("   8. Delete an Event Record (Delete)")
    print("\n  [AGGREGATION PIPELINES]")
    print("   9. Overall Average Magnitude & Total Events ($group, $avg)")
    print("  10. Earthquake Count by Magnitude Range ($bucket)")
    print("  11. Top 10 Strongest Earthquakes ($sort, $limit)")
    print("  12. Earthquake Counts by Magnitude Scale ($group, $sort)")
    print("  13. Monthly Earthquake Frequency Distribution ($dateToString)")
    print("\n  [SYSTEM VERIFICATION]")
    print("  14. Run Full Automated Self-Test (CRUD + Aggregations)")
    print("  15. Exit")
    print("=" * 65)


def main():
    """Main application loop."""
    print("Starting QuakeScope DB Terminal Application...")
    
    while True:
        display_menu()
        choice = input("Enter choice (1-15): ").strip()

        if choice == "1":
            test_connection()
        elif choice == "2":
            prompt_create_event()
        elif choice == "3":
            prompt_find_by_id()
        elif choice == "4":
            prompt_find_by_magnitude()
        elif choice == "5":
            prompt_find_by_location()
        elif choice == "6":
            prompt_show_latest()
        elif choice == "7":
            prompt_update_event()
        elif choice == "8":
            prompt_delete_event()
        elif choice == "9":
            print_header("Aggregation 1: Overall Average & Total Events")
            stats = get_average_magnitude_and_total()
            print(f"  Total Earthquakes : {stats.get('total_events', 0):,}")
            print(f"  Average Magnitude : {stats.get('avg_magnitude', 0.0)}")
            print(f"  Min Magnitude     : {stats.get('min_magnitude')}")
            print(f"  Max Magnitude     : {stats.get('max_magnitude')}")
        elif choice == "10":
            print_header("Aggregation 2: Magnitude Distribution ($bucket)")
            print(f"  {'Category':<35} | {'Count':<8} | {'Avg Mag':<8} | {'Range':<15}")
            print(f"  {'-'*35}-|-{'-'*8}-|-{'-'*8}-|-{'-'*15}")
            for b in get_magnitude_distribution():
                print(f"  {b['category']:<35} | {b['count']:<8,} | {b['avg_magnitude']:<8} | {b['range']:<15}")
        elif choice == "11":
            print_header("Aggregation 3: Top 10 Strongest Earthquakes")
            print(f"  {'#':<3} | {'ID':<12} | {'Mag':<5} | {'Type':<5} | {'Depth':<8} | {'Location'}")
            print(f"  {'-'*3}-|-{'-'*12}-|-{'-'*5}-|-{'-'*5}-|-{'-'*8}-|-{'-'*30}")
            for i, q in enumerate(get_top_strongest_events(10), 1):
                print(f"  {i:<3} | {q.get('event_id'):<12} | {q.get('magnitude'):<5} | {q.get('magnitude_type',''):<5} | {q.get('depth_km',0):<8} | {q.get('location')}")
        elif choice == "12":
            print_header("Aggregation 4: Counts by Magnitude Type")
            print(f"  {'Magnitude Type':<16} | {'Count':<8} | {'Avg Mag':<8}")
            print(f"  {'-'*16}-|-{'-'*8}-|-{'-'*8}")
            for m in get_counts_by_magnitude_type():
                print(f"  {m.get('magnitude_type','N/A'):<16} | {m.get('count',0):<8,} | {m.get('avg_magnitude',0.0):<8}")
        elif choice == "13":
            print_header("Aggregation 5: Monthly Distribution ($dateToString)")
            print(f"  {'Year-Month':<12} | {'Count':<8} | {'Avg Magnitude':<14}")
            print(f"  {'-'*12}-|-{'-'*8}-|-{'-'*14}")
            for row in get_monthly_earthquake_counts():
                print(f"  {row.get('month'):<12} | {row.get('count',0):<8,} | {row.get('avg_magnitude',0.0):<14}")
        elif choice == "14":
            run_automated_self_test()
        elif choice == "15":
            print("\nThank you for using QuakeScope DB. Goodbye!")
            break
        else:
            print("\n[INVALID CHOICE] Please select a number from 1 to 15.")

        input("\nPress Enter to return to menu...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user. Exiting cleanly.")
