"""
crud_operations.py
QuakeScope DB - PyMongo CRUD Operations Module
Course: CSE494 Intelligent NoSQL Databases

This module implements the four fundamental database operations:
- CREATE : Insert a new earthquake document (insert_one)
- READ   : Query earthquake events by ID, magnitude, location, or time (find_one, find)
- UPDATE : Modify fields of an existing event (update_one with $set)
- DELETE : Remove an event from the collection (delete_one)

All operations enforce MongoDB schema validation and unique indexing rules.
Safety guards ensure routine testing never alters the original imported USGS dataset.
"""

import os
import sys
from datetime import datetime, timezone

# Ensure project root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pymongo.errors import DuplicateKeyError, WriteError, PyMongoError
from scripts.database import get_collection

def format_event(doc):
    """Formats a single earthquake document for clear terminal display."""
    if not doc:
        return "  [No record found]"
    
    time_str = doc.get("event_time")
    if isinstance(time_str, datetime):
        time_str = time_str.strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        f"  ID           : {doc.get('event_id')}",
        f"  Time         : {time_str}",
        f"  Location     : {doc.get('location')}",
        f"  Magnitude    : {doc.get('magnitude')} ({doc.get('magnitude_type', 'N/A')})",
        f"  Depth        : {doc.get('depth_km')} km",
        f"  Coordinates  : Lat {doc.get('latitude')}, Long {doc.get('longitude')}",
        f"  Event Type   : {doc.get('event_type')}",
        f"  Review Status: {doc.get('review_status', 'N/A')}"
    ]
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# 1. CREATE OPERATION
# -----------------------------------------------------------------------------

def create_event(event_data):
    """
    Inserts a single new earthquake event into 'earthquake_events'.
    
    Parameters:
        event_data (dict): Dictionary containing event attributes.
        
    Returns:
        dict: {'success': bool, 'inserted_id': str, 'message': str}
    """
    collection = get_collection()
    
    try:
        # Validate that required keys are present
        required_fields = [
            "event_id", "event_time", "latitude", "longitude",
            "depth_km", "magnitude", "magnitude_type", "location", "event_type"
        ]
        for field in required_fields:
            if field not in event_data or event_data[field] is None:
                return {
                    "success": False,
                    "inserted_id": None,
                    "message": f"Missing required field: '{field}'"
                }

        # Execute insertion using PyMongo's insert_one()
        result = collection.insert_one(event_data)
        return {
            "success": True,
            "inserted_id": str(result.inserted_id),
            "message": f"Successfully inserted event '{event_data['event_id']}'"
        }

    except DuplicateKeyError:
        return {
            "success": False,
            "inserted_id": None,
            "message": f"DuplicateKeyError: Event ID '{event_data.get('event_id')}' already exists in database."
        }
    except WriteError as we:
        return {
            "success": False,
            "inserted_id": None,
            "message": f"Schema ValidationError (Code {we.code}): Document violates collection $jsonSchema rules."
        }
    except PyMongoError as pe:
        return {
            "success": False,
            "inserted_id": None,
            "message": f"PyMongo Error: {pe}"
        }


# -----------------------------------------------------------------------------
# 2. READ OPERATIONS
# -----------------------------------------------------------------------------

def find_event_by_id(event_id):
    """
    Finds a single earthquake event by its unique 'event_id'.
    
    Parameters:
        event_id (str): USGS event identifier or test ID.
        
    Returns:
        dict or None: Document matching the ID, or None if not found.
    """
    collection = get_collection()
    # Query using find_one() with event_id filter
    return collection.find_one({"event_id": event_id})


def find_events_by_magnitude(min_magnitude, limit=10):
    """
    Finds earthquake events with magnitude greater than or equal to a threshold.
    Results are sorted by magnitude descending.
    
    Parameters:
        min_magnitude (float): Minimum magnitude threshold.
        limit (int): Maximum records to return.
        
    Returns:
        list: List of matching documents.
    """
    collection = get_collection()
    # Filter using $gte operator and sort descending
    cursor = collection.find(
        {"magnitude": {"$gte": float(min_magnitude)}},
        projection={"_id": 0, "event_id": 1, "magnitude": 1, "magnitude_type": 1, "location": 1, "event_time": 1, "depth_km": 1}
    ).sort("magnitude", -1).limit(limit)
    return list(cursor)


def find_events_by_location(keyword, limit=10):
    """
    Finds earthquake events whose location string contains the given keyword (case-insensitive).
    
    Parameters:
        keyword (str): Search term (e.g., 'Japan', 'Chile', 'California').
        limit (int): Maximum records to return.
        
    Returns:
        list: List of matching documents.
    """
    collection = get_collection()
    # Case-insensitive regex search
    cursor = collection.find(
        {"location": {"$regex": keyword, "$options": "i"}},
        projection={"_id": 0, "event_id": 1, "magnitude": 1, "location": 1, "event_time": 1, "depth_km": 1}
    ).sort("event_time", -1).limit(limit)
    return list(cursor)


def find_latest_events(limit=5):
    """
    Retrieves the most recent earthquake events sorted by event_time descending.
    
    Parameters:
        limit (int): Number of events to retrieve.
        
    Returns:
        list: List of recent documents.
    """
    collection = get_collection()
    cursor = collection.find(
        {},
        projection={"_id": 0, "event_id": 1, "event_time": 1, "magnitude": 1, "location": 1, "depth_km": 1}
    ).sort("event_time", -1).limit(limit)
    return list(cursor)


# -----------------------------------------------------------------------------
# 3. UPDATE OPERATION
# -----------------------------------------------------------------------------

def update_event(event_id, update_fields):
    """
    Updates specific fields of an existing event using $set and update_one().
    
    Parameters:
        event_id (str): The event identifier to update.
        update_fields (dict): Dictionary of field-value pairs to set.
        
    Returns:
        dict: {'success': bool, 'matched_count': int, 'modified_count': int, 'message': str}
    """
    collection = get_collection()
    
    # Protect immutable fields
    update_data = {k: v for k, v in update_fields.items() if k not in ["_id", "event_id"]}
    if not update_data:
        return {
            "success": False,
            "matched_count": 0,
            "modified_count": 0,
            "message": "No valid updatable fields provided."
        }

    try:
        result = collection.update_one(
            {"event_id": event_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return {
                "success": False,
                "matched_count": 0,
                "modified_count": 0,
                "message": f"No event found matching ID '{event_id}'."
            }
            
        return {
            "success": True,
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "message": f"Updated event '{event_id}' (Matched: {result.matched_count}, Modified: {result.modified_count})."
        }
        
    except WriteError as we:
        return {
            "success": False,
            "matched_count": 1,
            "modified_count": 0,
            "message": f"Schema ValidationError (Code {we.code}): Update values violate collection schema rules."
        }
    except PyMongoError as pe:
        return {
            "success": False,
            "matched_count": 0,
            "modified_count": 0,
            "message": f"PyMongo Error: {pe}"
        }


# -----------------------------------------------------------------------------
# 4. DELETE OPERATION
# -----------------------------------------------------------------------------

def delete_event(event_id):
    """
    Deletes an event by its unique 'event_id' using delete_one().
    
    Parameters:
        event_id (str): Event identifier to delete.
        
    Returns:
        dict: {'success': bool, 'deleted_count': int, 'message': str}
    """
    collection = get_collection()
    
    try:
        result = collection.delete_one({"event_id": event_id})
        if result.deleted_count == 0:
            return {
                "success": False,
                "deleted_count": 0,
                "message": f"No event found with ID '{event_id}'."
            }
        return {
            "success": True,
            "deleted_count": result.deleted_count,
            "message": f"Successfully deleted event '{event_id}'."
        }
    except PyMongoError as pe:
        return {
            "success": False,
            "deleted_count": 0,
            "message": f"PyMongo Error: {pe}"
        }


# -----------------------------------------------------------------------------
# 5. PAGINATED SEARCH & FILTER QUERY (Used by Web Dashboard Explorer)
# -----------------------------------------------------------------------------
def search_events_paginated(search_query="", min_mag=None, max_mag=None, 
                            mag_type=None, depth_category=None, 
                            sort_by="event_time", sort_order="desc", 
                            page=1, per_page=15):
    """
    Performs server-side filtered, sorted, and paginated queries on earthquake_events.
    Supports search by ID or location, magnitude bounds, depth category, and sorting.
    """
    import math
    collection = get_collection()
    query = {}
    
    # Text search on ID or Location
    if search_query and search_query.strip():
        term = search_query.strip()
        query["$or"] = [
            {"event_id": {"$regex": term, "$options": "i"}},
            {"location": {"$regex": term, "$options": "i"}}
        ]
        
    # Magnitude range filters
    mag_conditions = {}
    if min_mag is not None and str(min_mag).strip() != "":
        try:
            mag_conditions["$gte"] = float(min_mag)
        except (ValueError, TypeError):
            pass
    if max_mag is not None and str(max_mag).strip() != "":
        try:
            mag_conditions["$lte"] = float(max_mag)
        except (ValueError, TypeError):
            pass
    if mag_conditions:
        query["magnitude"] = mag_conditions
        
    # Magnitude scale filter
    if mag_type and mag_type.strip() and mag_type.strip() != "all":
        query["magnitude_type"] = mag_type.strip()
        
    # Depth category filter
    if depth_category == "shallow":
        query["depth_km"] = {"$lt": 70.0}
    elif depth_category == "intermediate":
        query["depth_km"] = {"$gte": 70.0, "$lt": 300.0}
    elif depth_category == "deep":
        query["depth_km"] = {"$gte": 300.0}
        
    # Sorting direction and field
    direction = -1 if str(sort_order).lower() == "desc" else 1
    sort_field = sort_by if sort_by in ["event_time", "magnitude", "depth_km"] else "event_time"
    
    # Safe pagination numbers
    page = max(1, int(page))
    per_page = min(100, max(5, int(per_page)))
    skip = (page - 1) * per_page
    
    total_matching = collection.count_documents(query)
    total_pages = max(1, math.ceil(total_matching / per_page)) if total_matching > 0 else 1
    
    cursor = collection.find(
        query,
        projection={
            "_id": 0,
            "event_id": 1,
            "event_time": 1,
            "magnitude": 1,
            "magnitude_type": 1,
            "depth_km": 1,
            "location": 1,
            "latitude": 1,
            "longitude": 1,
            "event_type": 1,
            "review_status": 1
        }
    ).sort(sort_field, direction).skip(skip).limit(per_page)
    
    return {
        "events": list(cursor),
        "total": total_matching,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }

