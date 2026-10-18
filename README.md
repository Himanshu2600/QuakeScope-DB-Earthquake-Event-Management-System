# QuakeScope DB — Earthquake Event Management System

**Course:** CSE494: Intelligent NoSQL Databases  
**Project:** QuakeScope DB  
**Current Milestone:** Stage 3 — Premium macOS Liquid Glass Dashboard & Visual Analytics (Complete)  

---

## 1. Project Overview

QuakeScope DB is an earthquake event management system built on MongoDB and Python. It manages, indexes, and queries global seismic activity recorded by international monitoring stations.

The academic project is structured into four sequential stages:
* **Stage 1 (Complete):** Dataset inspection, MongoDB foundation, `$jsonSchema` strict validation, idempotent batch import (19,705 records), and core shell queries.
* **Stage 2 (Complete):** Python/PyMongo CRUD operations, five core aggregation pipelines, dual shell demonstrations, interactive terminal menu, and automated test suite.
* **Stage 3 (Complete):** Premium macOS Liquid Glass Web Dashboard, dynamic Chart.js analytics, Leaflet geospatial visualization, server-side paginated explorer, web-based CRUD with validation enforcement, and verified screenshot evidence.
* **Stage 4 (Upcoming):** Final academic report and university presentation.

---

## 2. Technology Stack

- **Database:** MongoDB Community Server 8.3.7 (Local instance on Windows, port 27017)
- **Database Shell:** MongoDB Shell (`mongosh`) 2.9.2
- **Backend Language:** Python 3.13.5
- **Web Framework:** Flask 3.0.0+ (Lightweight WSGI micro-framework)
- **MongoDB Driver:** PyMongo 4.19.0
- **Frontend Architecture:** Vanilla HTML5, CSS3 (Custom Liquid Glass Design System), Vanilla JavaScript (ES6+)
- **Charting & Visual Analytics:** Chart.js 4.4.1 (Dark theme configuration)
- **Geospatial Mapping:** Leaflet.js 1.9.4 (CartoDB Dark Matter tile layer)
- **Standard Libraries:** `csv`, `datetime`, `re`, `os`, `sys`

---

## 3. Dataset Attribution & Provenance

- **Source:** United States Geological Survey (USGS) Earthquake Hazards Program
- **Catalog:** ANSS Comprehensive Earthquake Catalog (ComCat)
- **URL:** [https://earthquake.usgs.gov/earthquakes/feed/](https://earthquake.usgs.gov/earthquakes/feed/)
- **License:** U.S. Government Public Domain (Free of copyright restrictions)
- **File:** `data/query.csv`
- **Total Records:** 19,705 earthquake events (365 calendar days of 2025 activity)
- **Total Columns:** 22 attributes (spatial coordinates, focal depth, magnitude, seismic station counts, error uncertainties)

---

## 4. Repository Structure

```
QuakeScope-DB/
├── app.py                         # Stage 3: Flask web dashboard server & REST API endpoints
├── main.py                        # Stage 2: Interactive terminal demonstration menu
├── requirements.txt               # Python dependencies (pymongo, flask)
├── README.md                      # Comprehensive project documentation & execution guide
├── data/
│   └── query.csv                  # Original USGS earthquake CSV (19,705 records)
├── database/
│   ├── setup_database.js          # Stage 1: MongoDB schema validator & unique index setup
│   ├── verify_queries.js          # Stage 1: Initial query verification suite
│   ├── queries_crud.js            # Stage 2: MongoDB Shell CRUD demonstrations (Create, Read, Update, Delete)
│   └── queries_aggregation.js     # Stage 2: MongoDB Shell aggregation pipelines (5 analyses)
├── docs/
│   ├── stage1_notes.md            # Stage 1 technical notes, schema, & evidence log
│   ├── stage2_notes.md            # Stage 2 technical notes, CRUD/agg pipelines, & viva guide
│   └── stage3_notes.md            # Stage 3 technical notes, Liquid Glass design, REST APIs, & viva Q&A
├── screenshots/
│   ├── stage1/                    # Stage 1 screenshot evidence directory
│   ├── stage2/                    # Stage 2 screenshot evidence directory
│   └── stage3/                    # Stage 3 screenshot evidence directory (6 verified screenshots)
├── scripts/
│   ├── __init__.py                # Python package marker
│   ├── inspect_dataset.py         # Stage 1: Dataset exploratory inspection script
│   ├── import_data.py             # Stage 1: Idempotent batch import script using PyMongo
│   ├── database.py                # Stage 2: PyMongo connection manager & health check
│   ├── crud_operations.py         # Stage 2 & 3: PyMongo CRUD operations & server-side paginated search
│   └── aggregation_queries.py     # Stage 2 & 3: PyMongo aggregation pipelines (magnitude, monthly, depth, map)
├── templates/
│   ├── index.html                 # Stage 3: Liquid Glass single-page application template
│   └── backend_verification.html  # Stage 3: Backend server terminal verification view
├── static/
│   ├── css/
│   │   └── style.css              # Stage 3: Apple-inspired Liquid Glass design system
│   └── js/
│       └── dashboard.js           # Stage 3: Client dashboard logic, Chart.js graphs, Leaflet, and CRUD
├── run_stage1_interactive.bat     # Stage 1 interactive evidence capture runner
└── run_stage2_interactive.bat     # Stage 2 interactive evidence capture runner
```

---

## 5. Quickstart & Execution Guide

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 2: Start the Web Dashboard (Stage 3)
Launch the Flask development server:
```powershell
python app.py
```
Open your browser and navigate to:  
👉 **`http://127.0.0.1:5000/`**

To stop the server at any time, press `CTRL + C` in the terminal.

### Step 3: Run Full Automated Verification Suite
Execute an end-to-end self-test of all CRUD functions, schema validation error handling, duplicate prevention, and aggregation pipelines:
```powershell
python -c "import main; main.run_automated_self_test()"
```

### Step 4: MongoDB Shell Demonstrations (`mongosh`)
Execute the shell demonstration scripts directly in `mongosh`:
```powershell
# Run CRUD demonstration
mongosh database/queries_crud.js

# Run Aggregation pipelines
mongosh database/queries_aggregation.js
```

### Step 5: Python Aggregation Pipeline Demonstration
Run the Python aggregation suite to inspect formatted tabular results:
```powershell
python scripts/aggregation_queries.py
```

### Step 6: Launch Interactive Terminal Application (Stage 2)
Launch the terminal-based menu for live CLI demonstrations:
```powershell
python main.py
```

---

## 6. Stage 3 — Premium macOS Liquid Glass Dashboard

### 6.1 Purpose & Design Philosophy
The Stage 3 dashboard provides an executive, highly aesthetic visual interface over the 19,705 earthquake documents. Designed using an original Apple macOS Liquid Glass visual language:
- **Atmosphere:** Deep midnight background (`#080B12`) with ambient radial glows (`#FF7A18` orange and `#FFB547` amber).
- **Glassmorphism:** Layered surfaces with `backdrop-filter: blur(20px)`, subtle semi-transparent borders, and soft specular highlights along top edges.
- **Visual Hierarchy:** Distinct surface strengths for the sidebar, header, KPI metric cards, analytical charts, data tables, and modals.

### 6.2 Key Features
1. **Live MongoDB Health Indicator:** Real-time backend status checking (`/api/health`) displaying MongoDB connection state and server version (v8.3.7).
2. **Four Prominent KPI Cards:**
   - **Total Events:** Real collection count (**19,705**).
   - **Average Magnitude:** Computed via `$avg: "$magnitude"` (**4.46**).
   - **Strongest Earthquake:** Peak magnitude (**8.8 M**, 2025 Kamchatka Peninsula).
   - **Major Earthquakes (M >= 6.0):** Filtered threshold count (**146**).
3. **Visual Analytics Suite (Chart.js):**
   - **Magnitude Distribution:** Bar chart categorized using MongoDB `$bucket`.
   - **Monthly Seismic Frequency:** Chronological trend curve using `$dateToString` (peak: July 2025 with 2,840 events).
   - **Magnitude Scale Types:** Doughnut chart grouping calculation methods (`mb`, `mww`, `ml`, `mwr`, etc.).
   - **Focal Depth Distribution:** Horizontal bar chart categorizing Shallow (<70km), Intermediate (70-300km), and Deep (>=300km) earthquakes.
4. **Earthquake Explorer:**
   - Search by Location or Event ID using safe, case-insensitive regular expressions.
   - Multidimensional filters: Minimum Magnitude, Scale Type, Focal Depth Category.
   - Server-side sorting (Newest first, Highest magnitude, Deepest, Shallowest).
   - Server-side pagination (15 records per page) with zero browser lag.
5. **Interactive Manage Events (CRUD):**
   - **Create Event:** Form mapped to `$jsonSchema` rules, rejecting invalid inputs (Code 121) or duplicates (Code 11000).
   - **Event Lookup & Update:** Modify magnitude, location, or focal depth using `$set`.
   - **Safe Delete:** User confirmation modal preventing accidental data loss.
   - **Live CRUD Self-Test Demo:** Runs an automated insert -> read -> update -> delete -> verify cycle directly from the web UI.
6. **Geospatial Seismic Map:** Leaflet map with dark theme styling, plotting 150 real earthquake epicenters scaled and colored by magnitude.

---

## 7. Stage 3 Screenshot Evidence Log

All verified screenshots are stored in `screenshots/stage3/`:

| Filename | Resolution | Description & Verified Functionality |
|---|---|---|
| `01_liquid_glass_overview.png` | 1366 × 880 | **macOS / Windhawk Liquid Glass Overview:** Translucent floating sidebar with rounded pill edges, floating header pill, continuous ambient glow, 4 dynamic KPI cards (19,705, 4.46 avg, 8.8 strongest, 146 major), and live database tables. |
| `02_working_seismic_map.png` | 1366 × 880 | **Repaired Geospatial Seismic Map:** Genuine Esri Dark Gray basemap with real landmasses and oceans, zero watermarks/API keys, plotting 150 real USGS earthquake epicenters. |
| `03_explorer_or_analytics.png` | 1366 × 880 | **Earthquake Explorer:** Case-insensitive search, multidimensional filters, and paginated table (15 per page) over a translucent glass surface. |
| `01_dashboard_overview.png` | 1280 × 850 | **Overview Baseline:** Overview dashboard showing MongoDB Connected badge and status indicator. |
| `02_analytics_charts.png` | 1366 × 880 | **Visual Analytics:** 4 Chart.js charts powered by MongoDB aggregations ($bucket magnitude, $dateToString monthly trend, $group scale types, $bucket depth analysis). |
| `03_earthquake_explorer.png` | 1280 × 850 | **Earthquake Explorer:** Search bar, filter dropdowns, server-side sorting, and paginated table. |
| `04_manage_events.png` | 1280 × 850 | **CRUD Interface:** Form for creating new events enforcing `$jsonSchema`, event lookup/update/delete panel, and the live CRUD cycle test button. |
| `05_backend_verification.png` | 1280 × 850 | **Backend Verification:** Terminal console showing Flask dev server running, handling real REST API calls, and passing the automated test suite with zero regression. |
| `06_detail_view.png` | 1280 × 850 | **Detail Modal:** Glass modal inspecting M8.8 Kamchatka event with coordinates, depth, review status, and station count over a translucent blurred backdrop. |

---

## 8. Stage 3 Verification Checklist

- [x] Flask backend (`app.py`) implemented with clean REST endpoints.
- [x] Apple-inspired Liquid Glass design implemented in `static/css/style.css` (translucent surfaces, specular reflections, `#FF7A18` / `#FFB547` palette).
- [x] Overview dashboard displaying live MongoDB KPI cards (19,705 records, 4.46 avg magnitude, 8.8 max magnitude, 146 major quakes).
- [x] 4 Chart.js charts connected to real MongoDB aggregation pipelines.
- [x] Earthquake Explorer with case-insensitive search, filters, sorting, and server-side pagination.
- [x] Manage Events CRUD interface with strict MongoDB `$jsonSchema` validation and duplicate prevention.
- [x] Optional Geospatial Seismic Map implemented with Leaflet and styled circle markers.
- [x] Zero regressions: Stage 2 automated self-test passes with 100% success.
- [x] Dataset integrity verified: final collection count remains exactly **19,705** documents.
- [x] 6 genuine screenshots captured and verified in `screenshots/stage3/`.
- [x] Technical notes and viva guide documented in `docs/stage3_notes.md`.
- [x] Ready for Stage 4 (Final Academic Report & Presentation).
