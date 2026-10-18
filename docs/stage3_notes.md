# QuakeScope DB — Stage 3 Technical Documentation & Viva Guide
## Premium macOS Liquid Glass Dashboard & Visual Analytics

**Course:** CSE494: Intelligent NoSQL Databases  
**Project:** QuakeScope DB — Earthquake Event Management System  
**Stage:** 3 of 4 — Dashboard Development  
**Database:** `quakescope_db`  
**Collection:** `earthquake_events`  
**Verified Records:** 19,705 documents  

---

## 1. Architecture Overview & Why Flask Was Chosen

For Stage 3, the project required a functional, database-backed web dashboard without introducing heavy, unnecessary enterprise infrastructure (such as React, Next.js, Node.js runtimes, Redis, Docker, or ORMs).

### Why Flask?
1. **Direct Python & PyMongo Synergy:** Flask is a minimalist Python WSGI micro-framework. It allows our existing Stage 2 Python modules (`scripts/database.py`, `scripts/crud_operations.py`, `scripts/aggregation_queries.py`) to be imported and executed natively with zero bridge layers.
2. **Undergraduate-Level Clarity:** A single `app.py` file exposes clear REST endpoints and serves the front-end template. Every route is transparent, readable, and directly maps HTTP requests to PyMongo collection operations.
3. **Zero Build Step:** By using vanilla modern JavaScript (ES6+), HTML5, and CSS3, the front-end runs immediately without Webpack, Vite, npm builds, or Babel transpilation.
4. **Lightweight Footprint:** The entire backend runs locally in standard Python using only `Flask>=3.0.0` and `pymongo>=4.6.0`.

---

## 2. Backend Architecture & PyMongo Integration

The Flask application (`app.py`) functions as the presentation and API layer above the existing database utilities.

```
┌─────────────────────────────────────────────────────────────┐
│                 Client Browser (Edge / Chrome)             │
│   Vanilla JS (dashboard.js)  +  Chart.js  +  Leaflet.js    │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON REST APIs
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Flask Backend (app.py)                 │
│  - /api/health                   - /api/analytics/...       │
│  - /api/stats                    - /api/events (CRUD/search)│
└──────────────┬──────────────────────────────┬───────────────┘
               │ Native Python Calls          │ Native Python Calls
               ▼                              ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│ scripts/crud_operations.py   │ │ scripts/aggregation_queries│
│ - search_events_paginated()  │ │ - get_magnitude_distrib()  │
│ - create_event()             │ │ - get_monthly_counts()     │
│ - update_event()             │ │ - get_top_strongest()      │
│ - delete_event()             │ │ - get_depth_distribution() │
└──────────────┬───────────────┘ └────────────┬───────────────┘
               │                              │
               └──────────────┬───────────────┘
                              │ PyMongo Connection Manager
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  scripts/database.py                        │
│             mongodb://localhost:27017                       │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         Local MongoDB Community Server (v8.3.7)             │
│   Database: quakescope_db  |  Collection: earthquake_events│
│   - Strict $jsonSchema Validation Rules                     │
│   - Unique Index on event_id                                │
│   - 19,705 Verified Historical USGS Earthquake Records      │
└─────────────────────────────────────────────────────────────┘
```

### JSON Serialization
MongoDB documents contain BSON types (`ObjectId`, `datetime`) that are not natively serializable to JSON. `app.py` implements a robust `serialize_item()` recursive utility that transforms `ObjectId` to string and ISO-8601 `datetime` objects to formatted strings, while preserving all numerical values.

---

## 3. How Aggregation Pipelines Power the Visual Analytics

All charts and KPI cards are dynamically populated by real MongoDB aggregation pipelines executed at request time. No numbers are hardcoded.

| Frontend Component | API Endpoint | MongoDB Pipeline Operator | Output Summary |
|---|---|---|---|
| **KPI: Total Events & Avg Mag** | `/api/stats` | `$group` with `_id: null`, `$avg: "$magnitude"`, `$sum: 1` | 19,705 records, 4.46 avg magnitude |
| **KPI: Major Quakes (>= 6.0)** | `/api/stats` | `$match: { magnitude: { $gte: 6.0 } }`, count | Exactly 146 major events |
| **Chart A: Magnitude Distribution** | `/api/analytics/magnitude-distribution` | `$bucket` with boundaries `[3.0, 4.0, 5.0, 6.0, 10.0]` | Below 4.0: 1,359; 4.0-5.0: 16,209; 5.0-6.0: 1,991; >=6.0: 146 |
| **Chart B: Monthly Trend** | `/api/analytics/monthly-activity` | `$project` with `$dateToString`, `$group`, `$sort` | 13 calendar months (Jan 2025 - Jan 2026), peak in July 2025 (2,840 quakes) |
| **Chart C: Magnitude Scale Types** | `/api/analytics/magnitude-types` | `$group: { _id: "$magnitude_type", count: { $sum: 1 } }` | 9 scale types (`mb`, `mww`, `ml`, `mwr`, `md`, `mw`, `mwb`, etc.) |
| **Chart D: Focal Depth Analysis** | `/api/analytics/depth-distribution` | `$bucket` with boundaries `[-10, 70, 300, 1000]` | Shallow (<70km): 14,817; Intermediate (70-300km): 3,768; Deep (>=300km): 1,120 |
| **Top Strongest Panel** | `/api/analytics/top-strongest` | `$sort: { magnitude: -1 }`, `$limit: 10` | Ranked by magnitude (Leader: M8.8 Kamchatka Peninsula) |
| **Geospatial Map** | `/api/analytics/map-events` | `$project: { event_id, latitude, longitude, magnitude, location }` | 150 geographically distributed seismic epicenters rendered on Leaflet dark map |

---

## 4. Search, Filter, and Server-Side Pagination

The **Earthquake Explorer** allows users to inspect the 19,705 records efficiently without transferring massive payloads to the browser:

```python
# scripts/crud_operations.py -> search_events_paginated()
query = {}
if search_text:
    # Safe case-insensitive regex matching event_id or location
    safe_pattern = re.escape(search_text.strip())
    query["$or"] = [
        {"location": {"$regex": safe_pattern, "$options": "i"}},
        {"event_id": {"$regex": safe_pattern, "$options": "i"}}
    ]
if min_mag is not None:
    query["magnitude"] = {"$gte": min_mag}
if mag_type and mag_type != "all":
    query["magnitude_type"] = mag_type
if depth_category and depth_category != "all":
    # Applies focal depth boundaries: shallow, intermediate, deep
```

- **Query Execution:**
  ```python
  total_matches = collection.count_documents(query)
  cursor = collection.find(query).sort(sort_field, sort_dir).skip((page - 1) * per_page).limit(per_page)
  ```
- **Performance:** Pagination uses `.skip()` and `.limit()` on the indexed collection, delivering sub-15ms response times for any arbitrary search query.

---

## 5. Web-Based CRUD Interface & Validation Enforcement

The **Manage Events** section enables full database operations directly through the browser while strictly respecting database safety rules:

1. **Create Event (`POST /api/events`):**
   - Collects user inputs for `event_id`, `event_time`, `magnitude`, `depth_km`, `latitude`, `longitude`, `location`, `magnitude_type`, and `event_type`.
   - Parses ISO timestamps into Python UTC `datetime` objects matching the MongoDB BSON date requirement.
   - Delegates directly to `scripts/crud_operations.create_event()`.
   - **Schema Validation:** If an attribute violates `$jsonSchema` (e.g. magnitude > 10.0 or invalid coordinate range), MongoDB throws `OperationFailure` with code 121 (`Document failed validation`). The API catches this error and returns HTTP 400 with a user-friendly error explanation.
   - **Duplicate Key Protection:** If the `event_id` already exists, MongoDB's unique index triggers `DuplicateKeyError` (code 11000). The API returns HTTP 409 conflict.

2. **Read Event (`GET /api/events/<event_id>`):**
   - Retrieves the document by primary ID and displays full focal and review attributes in the Liquid Glass detail modal.

3. **Update Event (`PUT /api/events/<event_id>`):**
   - Validates user edits and invokes `scripts/crud_operations.update_event()` using MongoDB's `$set` operator.
   - Prevents modification of immutable system identifiers (`_id`, `event_id`).

4. **Delete Event (`DELETE /api/events/<event_id>`):**
   - Prompts the user with an explicit confirmation dialog showing the event ID and location.
   - Safely removes the targeted record via `delete_one()`.
   - Protects against accidental drop operations.

5. **Live CRUD Self-Test Demo:**
   - A dedicated button runs an end-to-end automated cycle in MongoDB: Inserts temporary record `test_web_demo_001` -> Reads it -> Updates magnitude -> Deletes record -> Verifies final collection count is exactly 19,705.

---

## 6. The macOS Liquid Glass Design System

The frontend was designed from scratch to embody Apple's macOS Liquid Glass aesthetic, avoiding generic CSS frameworks:

* **Dark Atmosphere:** `#080B12` base background with radial amber/orange ambient highlights (`rgba(255, 122, 24, 0.08)`) and cyan complementary glow points (`rgba(103, 232, 249, 0.04)`).
* **Translucent Surfaces:** Layered panels using `backdrop-filter: blur(20px)` and subtle transparency (`rgba(255, 255, 255, 0.055)`).
* **Top-Edge Specular Reflections:** Subtle white linear gradients on `::before` pseudo-elements simulating refractive glass edges (`linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent)`).
* **Curated Color Palette:**
  - Primary Accent: `#FF7A18` (Vibrant Orange)
  - Secondary Accent: `#FFB547` (Warm Amber)
  - Deep Tone: `#F4511E` (Seismic Red-Orange)
  - Complementary Accent: `#67E8F9` (Cyan for status and technical indicators)
* **Typography:** System font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto`) with clear visual hierarchy, large metric typography, and monospaced accents for technical IDs.

---

## 7. Execution and Verification Guide

### Starting the Dashboard Server
```powershell
# Step 1: Ensure dependencies are installed
pip install -r requirements.txt

# Step 2: Launch the Flask development server
python app.py
```
The server will start on:  
👉 **`http://127.0.0.1:5000/`**

### Stopping the Dashboard Server
In the running terminal, press:
```
CTRL + C
```

### Running the Stage 2 & 3 Automated Regressions
To verify that no existing capabilities were degraded:
```powershell
# 1. Run the comprehensive self-test suite
python -c "import main; main.run_automated_self_test()"

# 2. Run the Python aggregation pipelines
python scripts/aggregation_queries.py

# 3. Run the MongoDB Shell aggregations
mongosh database/queries_aggregation.js

# 4. Verify collection document count
mongosh --quiet --eval "db.getSiblingDB('quakescope_db').earthquake_events.countDocuments({})"
```
**Expected Count:** `19705`

---

## 8. Screenshot Evidence Log

All genuine screenshots are saved in `screenshots/stage3/`:

| Screenshot File | Resolution | Description & Academic Evidence Proven |
|---|---|---|
| `01_liquid_glass_overview.png` | 1366 × 880 | **macOS / Windhawk Liquid Glass Overview:** Shows floating rounded translucent sidebar with breathing room, floating glass header pill, continuous background glow, 4 dynamic KPI cards (19,705 events, 4.46 avg, 8.8 strongest, 146 major), and live database tables. |
| `02_working_seismic_map.png` | 1366 × 880 | **Repaired Geospatial Seismic Map:** Demonstrates genuine Esri World Dark Gray raster basemap tiles with zero watermarks or API key requirements, plotting 150 real USGS earthquake epicenters scaled and colored by magnitude. |
| `03_explorer_or_analytics.png` | 1366 × 880 | **Liquid Glass Earthquake Explorer:** Displays server-side search, multidimensional filters (magnitude, scale, depth), and paginated data table (15 records per page) with zero browser lag. |
| `01_dashboard_overview.png` | 1280 × 850 | **Overview Baseline:** Baseline overview capture with MongoDB Connected badge and status indicator. |
| `02_analytics_charts.png` | 1366 × 880 | **Visual Analytics Suite:** Displays 4 Chart.js charts powered by MongoDB aggregations: Magnitude Distribution ($bucket), Monthly Seismic Frequency ($dateToString), Magnitude Scale Types ($group), and Focal Depth Distribution ($bucket). |
| `03_earthquake_explorer.png` | 1280 × 850 | **Earthquake Explorer:** Search bar, filter dropdowns, server-side sorting, and paginated table. |
| `04_manage_events.png` | 1280 × 850 | **CRUD Management Interface:** Shows Create Event form with inputs mapped to `$jsonSchema`, Event Lookup/Update/Delete controls, and the Live CRUD Self-Test cycle. |
| `05_backend_verification.png` | 1280 × 850 | **Backend Verification & Regression Console:** Proves Flask dev server startup, live REST API request handling (`/api/health`, `/api/stats`, `/api/analytics`), MongoDB Community Server v8.3.7 connectivity, and 100% pass rate on `run_automated_self_test()`. |
| `06_detail_view.png` | 1280 × 850 | **Earthquake Detail Modal:** Inspects event `us6000qw60` (M8.8 Kamchatka Peninsula earthquake) displaying focal depth (35 km), coordinates (52.4948° N, 160.2395° E), review status, and station counts over a translucent glass backdrop. |

---

## 9. Viva Voce Questions & Answers (Stage 3 Focus)

**Q1: Why did you not use React or Angular for the dashboard?**  
*Answer:* CSE494 focuses on Intelligent NoSQL Databases, not heavy frontend frameworks. Using Flask with vanilla JavaScript and Chart.js keeps the project lightweight, portable, and transparent. The application runs immediately without external build tools (`npm`, `webpack`), and the MongoDB queries remain the central focus.

**Q2: How does the dashboard prevent sending all 19,705 documents to the browser at once?**  
*Answer:* Through server-side pagination in `search_events_paginated()`. When a user opens the Explorer or changes a filter, Flask issues a query with `.skip((page - 1) * per_page).limit(per_page)`. Only 15 documents are sent over the network at a time, resulting in instantaneous page loads and low memory usage.

**Q3: How does the web interface enforce MongoDB schema validation?**  
*Answer:* Validation is enforced at the MongoDB database level by the `$jsonSchema` validator established in Stage 1. When the web form issues `insert_one()` or `update_one()`, MongoDB rejects non-compliant values with error code 121. The Flask backend catches this `WriteError` and returns a structured error message to the browser, ensuring the database can never be corrupted by bad frontend input.

**Q4: How are the charts rendered in real time?**  
*Answer:* When the dashboard loads, `dashboard.js` issues asynchronous `fetch()` requests to Flask endpoints like `/api/analytics/magnitude-distribution`. Flask calls PyMongo aggregation functions in `scripts/aggregation_queries.py`. MongoDB aggregates the 19,705 documents in memory and returns computed bins (e.g. `$bucket`). Chart.js then updates the canvas elements dynamically.
