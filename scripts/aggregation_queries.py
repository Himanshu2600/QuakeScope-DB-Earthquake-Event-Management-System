"""
aggregation_queries.py
QuakeScope DB - PyMongo Aggregation Queries Module
Course: CSE494 Intelligent NoSQL Databases

This module implements five core MongoDB aggregation pipelines:
1. Overall Average Magnitude and Total Event Count ($group with _id: null, $avg, $sum)
2. Earthquake Count by Magnitude Range ($bucket with defined boundary bins)
3. Top 10 Strongest Earthquakes ($sort, $limit, $project)
4. Earthquake Counts by Magnitude Scale Type ($group, $sum, $sort)
5. Monthly Earthquake Frequency Distribution ($dateToString, $group, $sort)

All pipelines query the real 'quakescope_db.earthquake_events' collection.
"""

import os
import sys

# Ensure project root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.database import get_collection

# -----------------------------------------------------------------------------
# 1. AGGREGATION 1: Average Magnitude & Total Events
# -----------------------------------------------------------------------------
def get_average_magnitude_and_total():
    """
    Computes dataset-wide statistics: total count, average, min, and max magnitude.
    Demonstrates $group with _id: None to aggregate all documents into one record.
    """
    collection = get_collection()
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_events": {"$sum": 1},
                "avg_magnitude": {"$avg": "$magnitude"},
                "min_magnitude": {"$min": "$magnitude"},
                "max_magnitude": {"$max": "$magnitude"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "total_events": 1,
                "avg_magnitude": {"$round": ["$avg_magnitude", 2]},
                "min_magnitude": 1,
                "max_magnitude": 1
            }
        }
    ]
    results = list(collection.aggregate(pipeline))
    return results[0] if results else {}


# -----------------------------------------------------------------------------
# 2. AGGREGATION 2: Earthquake Count by Magnitude Range
# -----------------------------------------------------------------------------
def get_magnitude_distribution():
    """
    Groups earthquakes into standard seismic classification bins using $bucket:
    - 3.0 to < 4.0: Minor
    - 4.0 to < 5.0: Light
    - 5.0 to < 6.0: Moderate
    - 6.0 to 10.0 : Strong to Great
    """
    collection = get_collection()
    pipeline = [
        {
            "$bucket": {
                "groupBy": "$magnitude",
                "boundaries": [3.0, 4.0, 5.0, 6.0, 10.0],
                "default": "Other",
                "output": {
                    "count": {"$sum": 1},
                    "avg_magnitude": {"$avg": "$magnitude"},
                    "min_in_bin": {"$min": "$magnitude"},
                    "max_in_bin": {"$max": "$magnitude"}
                }
            }
        },
        {
            "$project": {
                "count": 1,
                "avg_magnitude": {"$round": ["$avg_magnitude", 2]},
                "min_in_bin": 1,
                "max_in_bin": 1
            }
        }
    ]
    raw_buckets = list(collection.aggregate(pipeline))
    
    # Map raw numeric boundary IDs to human-readable labels
    labeled_buckets = []
    labels = {
        3.0: "Below 4.0 (Minor: 3.0 to < 4.0)",
        4.0: "4.0 to < 5.0 (Light)",
        5.0: "5.0 to < 6.0 (Moderate)",
        6.0: "6.0 and above (Strong to Great)"
    }
    for b in raw_buckets:
        boundary_id = b.get("_id")
        labeled_buckets.append({
            "category": labels.get(boundary_id, str(boundary_id)),
            "count": b.get("count", 0),
            "avg_magnitude": b.get("avg_magnitude", 0.0),
            "range": f"{b.get('min_in_bin')} to {b.get('max_in_bin')}"
        })
    return labeled_buckets


# -----------------------------------------------------------------------------
# 3. AGGREGATION 3: Top 10 Strongest Earthquakes
# -----------------------------------------------------------------------------
def get_top_strongest_events(limit=10):
    """
    Retrieves the strongest earthquakes sorted by magnitude descending.
    Uses $sort with -1 and caps result length using $limit.
    """
    collection = get_collection()
    pipeline = [
        {"$sort": {"magnitude": -1}},
        {"$limit": limit},
        {
            "$project": {
                "_id": 0,
                "event_id": 1,
                "magnitude": 1,
                "magnitude_type": 1,
                "event_time": 1,
                "location": 1,
                "depth_km": 1
            }
        }
    ]
    return list(collection.aggregate(pipeline))


# -----------------------------------------------------------------------------
# 4. AGGREGATION 4: Earthquake Counts by Magnitude Scale Type
# -----------------------------------------------------------------------------
def get_counts_by_magnitude_type():
    """
    Groups earthquakes by magnitude calculation method (mb, mww, ml, md, etc.).
    Note: Scales calculate energy from different wave types and are not directly identical.
    """
    collection = get_collection()
    pipeline = [
        {
            "$group": {
                "_id": "$magnitude_type",
                "count": {"$sum": 1},
                "avg_magnitude": {"$avg": "$magnitude"}
            }
        },
        {"$sort": {"count": -1}},
        {
            "$project": {
                "_id": 0,
                "magnitude_type": "$_id",
                "count": 1,
                "avg_magnitude": {"$round": ["$avg_magnitude", 2]}
            }
        }
    ]
    return list(collection.aggregate(pipeline))


# -----------------------------------------------------------------------------
# 5. AGGREGATION 5: Monthly Earthquake Frequency Distribution
# -----------------------------------------------------------------------------
def get_monthly_earthquake_counts():
    """
    Aggregates earthquake occurrence counts by month using $dateToString on event_time.
    Sorts chronologically by year-month string.
    """
    collection = get_collection()
    pipeline = [
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m", "date": "$event_time"}
                },
                "count": {"$sum": 1},
                "avg_magnitude": {"$avg": "$magnitude"}
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "_id": 0,
                "month": "$_id",
                "count": 1,
                "avg_magnitude": {"$round": ["$avg_magnitude", 2]}
            }
        }
    ]
    return list(collection.aggregate(pipeline))


# -----------------------------------------------------------------------------
# 6. DEPTH DISTRIBUTION ANALYSIS ($bucket)
# -----------------------------------------------------------------------------
def get_depth_distribution():
    """
    Groups earthquakes into focal depth categories using $bucket:
    - Shallow: < 70 km
    - Intermediate: 70 km to < 300 km
    - Deep: >= 300 km
    """
    collection = get_collection()
    pipeline = [
        {
            "$bucket": {
                "groupBy": "$depth_km",
                "boundaries": [-10.0, 70.0, 300.0, 1000.0],
                "default": "Other",
                "output": {
                    "count": {"$sum": 1},
                    "avg_depth": {"$avg": "$depth_km"}
                }
            }
        },
        {
            "$project": {
                "count": 1,
                "avg_depth": {"$round": ["$avg_depth", 1]}
            }
        }
    ]
    raw = list(collection.aggregate(pipeline))
    labels = {
        -10.0: "Shallow (< 70 km)",
        70.0: "Intermediate (70 to < 300 km)",
        300.0: "Deep (>= 300 km)"
    }
    results = []
    for b in raw:
        results.append({
            "category": labels.get(b.get("_id"), str(b.get("_id"))),
            "count": b.get("count", 0),
            "avg_depth": b.get("avg_depth", 0.0)
        })
    return results


# -----------------------------------------------------------------------------
# 7. MAP EVENTS RETRIEVAL (Bounded set of major & recent events)
# -----------------------------------------------------------------------------
def get_map_events(limit=150):
    """
    Retrieves a bounded set of earthquakes with coordinates for geospatial rendering.
    Combines high-magnitude events to keep browser payload lightweight and responsive.
    """
    collection = get_collection()
    cursor = collection.find(
        {"latitude": {"$ne": None}, "longitude": {"$ne": None}},
        projection={
            "_id": 0,
            "event_id": 1,
            "latitude": 1,
            "longitude": 1,
            "magnitude": 1,
            "magnitude_type": 1,
            "depth_km": 1,
            "location": 1,
            "event_time": 1
        }
    ).sort("magnitude", -1).limit(limit)
    return list(cursor)


# -----------------------------------------------------------------------------
# FORMATTED PRINTERS FOR TERMINAL DISPLAY
# -----------------------------------------------------------------------------
def display_all_aggregations():
    """Runs all 5 aggregations and prints clean, student-friendly tabular results."""
    print("=" * 75)
    print("QUAKESCOPE DB - STAGE 2: PYMONGO AGGREGATION PIPELINE RESULTS")
    print("=" * 75)

    # 1. Overall stats
    print("\n--- 1. OVERALL STATS ($group with _id: null, $avg, $sum) ---")
    stats = get_average_magnitude_and_total()
    print(f"  Total Earthquakes : {stats.get('total_events', 0):,}")
    print(f"  Average Magnitude : {stats.get('avg_magnitude', 0.0)}")
    print(f"  Magnitude Range   : {stats.get('min_magnitude')} to {stats.get('max_magnitude')}")

    # 2. Magnitude Distribution
    print("\n--- 2. MAGNITUDE DISTRIBUTION ($bucket) ---")
    print(f"  {'Magnitude Category':<35} | {'Count':<8} | {'Avg Mag':<8} | {'Observed Range':<15}")
    print(f"  {'-'*35}-|-{'-'*8}-|-{'-'*8}-|-{'-'*15}")
    for b in get_magnitude_distribution():
        print(f"  {b['category']:<35} | {b['count']:<8,} | {b['avg_magnitude']:<8} | {b['range']:<15}")

    # 3. Top 10 Strongest
    print("\n--- 3. TOP 10 STRONGEST EARTHQUAKES ($sort, $limit) ---")
    print(f"  {'#':<3} | {'ID':<12} | {'Mag':<5} | {'Type':<5} | {'Depth (km)':<11} | {'Location'}")
    print(f"  {'-'*3}-|-{'-'*12}-|-{'-'*5}-|-{'-'*5}-|-{'-'*11}-|-{'-'*30}")
    for i, q in enumerate(get_top_strongest_events(10), 1):
        print(f"  {i:<3} | {q.get('event_id'):<12} | {q.get('magnitude'):<5} | {q.get('magnitude_type',''):<5} | {q.get('depth_km',0):<11} | {q.get('location')}")

    # 4. By Magnitude Type
    print("\n--- 4. EARTHQUAKE COUNTS BY MAGNITUDE TYPE ($group, $sort) ---")
    print(f"  {'Magnitude Type':<16} | {'Count':<8} | {'Avg Magnitude':<14} | Description")
    print(f"  {'-'*16}-|-{'-'*8}-|-{'-'*14}-|----------------------------")
    type_descriptions = {
        "mb": "Short-period body wave (deep/distant quakes)",
        "mww": "Moment tensor from W-phase (large global events)",
        "ml": "Local Richter magnitude (shallow/regional quakes)",
        "mwr": "Regional complete waveform moment magnitude",
        "md": "Duration magnitude (small local quakes)",
        "mw": "Moment magnitude (general)",
        "mwb": "Body-wave moment tensor",
        "mb_lg": "Short-period surface wave for stable continental crust",
        "ms_vx": "Surface wave magnitude"
    }
    for m in get_counts_by_magnitude_type():
        mtype = m.get('magnitude_type', 'N/A')
        desc = type_descriptions.get(mtype, "Standard seismic measurement scale")
        print(f"  {mtype:<16} | {m.get('count', 0):<8,} | {m.get('avg_magnitude', 0.0):<14} | {desc}")

    # 5. Monthly Distribution
    print("\n--- 5. MONTHLY EARTHQUAKE DISTRIBUTION ($dateToString, $group, $sort) ---")
    print(f"  {'Year-Month':<12} | {'Count':<8} | {'Avg Magnitude':<14} | Notes")
    print(f"  {'-'*12}-|-{'-'*8}-|-{'-'*14}-|----------------------------")
    for row in get_monthly_earthquake_counts():
        month = row.get("month", "N/A")
        notes = "Peak seismic month (Kamchatka M8.8 aftershocks)" if month == "2025-07" else ""
        print(f"  {month:<12} | {row.get('count', 0):<8,} | {row.get('avg_magnitude', 0.0):<14} | {notes}")

    print("\n" + "=" * 75)
    print("ALL 5 AGGREGATIONS EXECUTED SUCCESSFULLY ON REAL MONGODB DATABASE")
    print("=" * 75)

if __name__ == "__main__":
    display_all_aggregations()
