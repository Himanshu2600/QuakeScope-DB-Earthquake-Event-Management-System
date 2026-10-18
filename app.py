"""
app.py
QuakeScope DB - Premium macOS Liquid Glass Dashboard Backend
Course: CSE494 Intelligent NoSQL Databases

This Flask application serves the QuakeScope visual dashboard and exposes
clean RESTful JSON endpoints connected to MongoDB via PyMongo.
It reuses the verified database connection, CRUD operations, and aggregation
pipelines created in Stage 1 and Stage 2.
"""

import os
import sys
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scripts.database import get_client, get_collection, DB_NAME, COLLECTION_NAME
from scripts.crud_operations import (
    create_event,
    find_event_by_id,
    find_latest_events,
    update_event,
    delete_event,
    search_events_paginated
)
from scripts.aggregation_queries import (
    get_average_magnitude_and_total,
    get_magnitude_distribution,
    get_top_strongest_events,
    get_counts_by_magnitude_type,
    get_monthly_earthquake_counts,
    get_depth_distribution,
    get_map_events
)

app = Flask(__name__)


# -----------------------------------------------------------------------------
# JSON SERIALIZATION HELPER
# -----------------------------------------------------------------------------
def serialize_item(item):
    """Recursively converts MongoDB/Python objects (datetime, ObjectId) to JSON-serializable types."""
    if isinstance(item, list):
        return [serialize_item(elem) for elem in item]
    if isinstance(item, dict):
        clean = {}
        for k, v in item.items():
            if k == "_id":
                clean[k] = str(v)
            elif isinstance(v, datetime):
                clean[k] = v.isoformat()
            elif isinstance(v, (list, dict)):
                clean[k] = serialize_item(v)
            else:
                clean[k] = v
        return clean
    if isinstance(item, datetime):
        return item.isoformat()
    return item


# -----------------------------------------------------------------------------
# 1. PAGE ROUTE
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    """Renders the single-page Liquid Glass Dashboard."""
    return render_template("index.html")


@app.route("/backend-verification")
def backend_verification():
    """Renders backend verification terminal view."""
    return render_template("backend_verification.html")


# -----------------------------------------------------------------------------
# 2. SYSTEM HEALTH & METRICS API
# -----------------------------------------------------------------------------
@app.route("/api/health")
def api_health():
    """Returns real MongoDB server connectivity status and metadata."""
    try:
        client = get_client()
        client.admin.command("ping")
        server_info = client.server_info()
        coll = get_collection()
        total_count = coll.count_documents({})
        
        return jsonify({
            "status": "connected",
            "message": "Connected to local MongoDB Community Server",
            "database": DB_NAME,
            "collection": COLLECTION_NAME,
            "total_documents": total_count,
            "server_version": server_info.get("version", "Unknown")
        })
    except Exception as err:
        return jsonify({
            "status": "disconnected",
            "message": f"MongoDB connection error: {str(err)}",
            "database": DB_NAME,
            "collection": COLLECTION_NAME,
            "total_documents": 0,
            "server_version": None
        }), 503


@app.route("/api/stats")
def api_stats():
    """Returns summary KPIs for the Overview cards."""
    try:
        stats = get_average_magnitude_and_total()
        coll = get_collection()
        # Count strong earthquakes (magnitude >= 6.0)
        strong_count = coll.count_documents({"magnitude": {"$gte": 6.0}})
        
        # Get strongest earthquake details
        top_quake = coll.find_one(
            {},
            sort=[("magnitude", -1)],
            projection={"_id": 0, "event_id": 1, "magnitude": 1, "location": 1, "depth_km": 1, "event_time": 1}
        )
        
        return jsonify({
            "total_events": stats.get("total_events", 0),
            "avg_magnitude": stats.get("avg_magnitude", 0.0),
            "min_magnitude": stats.get("min_magnitude", 0.0),
            "max_magnitude": stats.get("max_magnitude", 0.0),
            "strong_events_count": strong_count,
            "strongest_event": serialize_item(top_quake) if top_quake else None
        })
    except Exception as err:
        return jsonify({"error": str(err)}), 500


# -----------------------------------------------------------------------------
# 3. VISUAL ANALYTICS API (Connected to Aggregation Pipelines)
# -----------------------------------------------------------------------------
@app.route("/api/analytics/magnitude-distribution")
def api_magnitude_distribution():
    """Returns binned magnitude counts from $bucket aggregation."""
    try:
        buckets = get_magnitude_distribution()
        return jsonify(buckets)
    except Exception as err:
        return jsonify({"error": str(err)}), 500


@app.route("/api/analytics/monthly-activity")
def api_monthly_activity():
    """Returns monthly earthquake frequency from $dateToString aggregation."""
    try:
        monthly = get_monthly_earthquake_counts()
        return jsonify(monthly)
    except Exception as err:
        return jsonify({"error": str(err)}), 500


@app.route("/api/analytics/magnitude-types")
def api_magnitude_types():
    """Returns counts and average magnitudes by measurement scale."""
    try:
        mag_types = get_counts_by_magnitude_type()
        return jsonify(mag_types)
    except Exception as err:
        return jsonify({"error": str(err)}), 500


@app.route("/api/analytics/depth-distribution")
def api_depth_distribution():
    """Returns depth category distribution from $bucket aggregation."""
    try:
        depths = get_depth_distribution()
        return jsonify(depths)
    except Exception as err:
        return jsonify({"error": str(err)}), 500


@app.route("/api/analytics/top-strongest")
def api_top_strongest():
    """Returns top 10 strongest earthquakes sorted by magnitude descending."""
    try:
        top_events = get_top_strongest_events(limit=10)
        return jsonify(serialize_item(top_events))
    except Exception as err:
        return jsonify({"error": str(err)}), 500


@app.route("/api/analytics/recent")
def api_recent_events():
    """Returns most recent recorded earthquakes."""
    try:
        recent = find_latest_events(limit=6)
        return jsonify(serialize_item(recent))
    except Exception as err:
        return jsonify({"error": str(err)}), 500


@app.route("/api/analytics/map-events")
def api_map_events():
    """Returns bounded set of major & recent events for Leaflet map markers."""
    try:
        map_events = get_map_events(limit=150)
        return jsonify(serialize_item(map_events))
    except Exception as err:
        return jsonify({"error": str(err)}), 500


# -----------------------------------------------------------------------------
# 4. EARTHQUAKE EXPLORER API (Search, Filter & Pagination)
# -----------------------------------------------------------------------------
@app.route("/api/events")
def api_search_events():
    """Server-side paginated search and filter query."""
    search_query = request.args.get("q", "").strip()
    min_mag = request.args.get("min_mag")
    max_mag = request.args.get("max_mag")
    mag_type = request.args.get("mag_type")
    depth_cat = request.args.get("depth_cat")
    sort_by = request.args.get("sort_by", "event_time")
    sort_order = request.args.get("sort_order", "desc")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 15, type=int)

    try:
        result = search_events_paginated(
            search_query=search_query,
            min_mag=min_mag,
            max_mag=max_mag,
            mag_type=mag_type,
            depth_category=depth_cat,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            per_page=per_page
        )
        return jsonify(serialize_item(result))
    except Exception as err:
        return jsonify({"error": str(err)}), 500


@app.route("/api/events/<event_id>", methods=["GET"])
def api_get_single_event(event_id):
    """Retrieves full details for a single event."""
    try:
        doc = find_event_by_id(event_id)
        if not doc:
            return jsonify({"error": f"Event '{event_id}' not found."}), 404
        return jsonify(serialize_item(doc))
    except Exception as err:
        return jsonify({"error": str(err)}), 500


# -----------------------------------------------------------------------------
# 5. CRUD MANAGEMENT API (Create, Update, Delete)
# -----------------------------------------------------------------------------
@app.route("/api/events", methods=["POST"])
def api_create_event():
    """Inserts a new event, enforcing MongoDB schema validation."""
    data = request.get_json() or {}
    
    event_id = data.get("event_id", "").strip()
    if not event_id:
        return jsonify({"success": False, "message": "Event ID is required."}), 400

    # Parse timestamp
    time_val = data.get("event_time")
    if time_val:
        try:
            # Parse ISO string
            clean_time = time_val.replace("Z", "+00:00")
            event_time = datetime.fromisoformat(clean_time)
        except Exception:
            event_time = datetime.now(timezone.utc)
    else:
        event_time = datetime.now(timezone.utc)

    # Convert numeric fields safely
    try:
        latitude = float(data.get("latitude"))
        longitude = float(data.get("longitude"))
        depth_km = float(data.get("depth_km"))
        magnitude = float(data.get("magnitude"))
    except (ValueError, TypeError) as conv_err:
        return jsonify({"success": False, "message": f"Numeric conversion error: {conv_err}"}), 400

    event_doc = {
        "event_id": event_id,
        "event_time": event_time,
        "latitude": latitude,
        "longitude": longitude,
        "depth_km": depth_km,
        "magnitude": magnitude,
        "magnitude_type": data.get("magnitude_type", "mb").strip(),
        "location": data.get("location", "").strip(),
        "event_type": data.get("event_type", "earthquake").strip(),
        "review_status": data.get("review_status", "automatic").strip(),
        "network": data.get("network", "user").strip()
    }

    result = create_event(event_doc)
    status_code = 201 if result["success"] else 400
    return jsonify(result), status_code


@app.route("/api/events/<event_id>", methods=["PUT"])
def api_update_event(event_id):
    """Updates selected fields of an existing event."""
    data = request.get_json() or {}
    update_fields = {}

    if "magnitude" in data and data["magnitude"] != "":
        try:
            update_fields["magnitude"] = float(data["magnitude"])
        except ValueError:
            return jsonify({"success": False, "message": "Magnitude must be a number."}), 400

    if "location" in data and data["location"].strip():
        update_fields["location"] = data["location"].strip()

    if "depth_km" in data and data["depth_km"] != "":
        try:
            update_fields["depth_km"] = float(data["depth_km"])
        except ValueError:
            return jsonify({"success": False, "message": "Depth must be a number."}), 400

    if "review_status" in data:
        update_fields["review_status"] = data["review_status"]

    if not update_fields:
        return jsonify({"success": False, "message": "No valid fields to update."}), 400

    result = update_event(event_id, update_fields)
    status_code = 200 if result["success"] else 400
    return jsonify(result), status_code


@app.route("/api/events/<event_id>", methods=["DELETE"])
def api_delete_event(event_id):
    """Deletes an event by event_id."""
    result = delete_event(event_id)
    status_code = 200 if result["success"] else 404
    return jsonify(result), status_code


# -----------------------------------------------------------------------------
# APPLICATION ENTRY POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 65)
    print("QUAKESCOPE DB - PREMIUM MACOS LIQUID GLASS DASHBOARD")
    print("Server starting on http://127.0.0.1:5000/")
    print("=" * 65)
    app.run(host="127.0.0.1", port=5000, debug=False)
