# QuakeScope DB — Stage 1 Technical Notes & Evidence Log

**Course:** CSE494: Intelligent NoSQL Databases  
**Project:** QuakeScope DB — Earthquake Event Management System  
**Stage:** Stage 1 — Dataset Inspection, MongoDB Foundation & Evidence Capture  
**Database Name:** `quakescope_db`  
**Collection Name:** `earthquake_events`  
**Environment:** MongoDB Community Server 8.3.7, MongoDB Shell (`mongosh`) 2.9.2, Python 3.13.5, PyMongo 4.19.0  

---

## 1. Dataset Inspection & Provenance

### 1.1 Dataset Source and Attribution
- **Source Agency:** United States Geological Survey (USGS) Earthquake Hazards Program
- **Catalog Name:** ANSS Comprehensive Earthquake Catalog (ComCat)
- **Source URL:** [https://earthquake.usgs.gov/earthquakes/feed/](https://earthquake.usgs.gov/earthquakes/feed/)
- **Data License:** U.S. Government Public Domain (free of copyright restrictions)
- **Local File Path:** `data/query.csv`
- **File Size:** 3,761,342 bytes (3.59 MB)

### 1.2 Dataset Dimensions & Temporal Bounds
- **Total Data Rows:** 19,705 (excluding header line)
- **Total Columns:** 22
- **Earliest Earthquake:** `2025-01-01T00:13:22.650Z`
- **Latest Earthquake:** `2026-01-01T23:30:51.522Z`
- **Temporal Coverage:** Exactly 365 calendar days (full year 2025 seismic activity)
- **Identifier Uniqueness:** Column `id` contains 19,705 unique values with **0 duplicate IDs**. The USGS event identifier (e.g., `us7000rm06`, `us6000pjr6`) serves as our natural primary key.

### 1.3 Data Quality & Missing Value Analysis
The original raw dataset was preserved untouched at `data/query.csv`. Our inspection script (`scripts/inspect_dataset.py`) analyzed every column:

| Column Name | Raw Type | Missing Count | % Missing | Handling & Conversion Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `time` | ISO String | 0 | 0.00% | Converted to BSON `ISODate` (named `event_time`) |
| `latitude` | Float string | 0 | 0.00% | Converted to BSON `double` (-73.2204 to 87.0815) |
| `longitude` | Float string | 0 | 0.00% | Converted to BSON `double` (-179.9944 to 179.9994) |
| `depth` | Float string | 0 | 0.00% | Converted to BSON `double` (named `depth_km`) |
| `mag` | Float string | 0 | 0.00% | Converted to BSON `double` (named `magnitude`, 3.50 to 8.80) |
| `magType` | String | 0 | 0.00% | Stored as BSON `string` (named `magnitude_type`) |
| `nst` | Integer string | 157 | 0.80% | Optional; converted to integer or omitted |
| `gap` | Float string | 161 | 0.82% | Optional; converted to float or omitted |
| `dmin` | Float string | 162 | 0.82% | Optional; converted to float or omitted |
| `rms` | Float string | 0 | 0.00% | Converted to float (named `rms_residual`) |
| `net` | String | 0 | 0.00% | Stored as string (named `network`) |
| `id` | String | 0 | 0.00% | Stored as string (named `event_id`, unique index) |
| `updated` | ISO String | 0 | 0.00% | Converted to BSON `ISODate` (named `updated_time`) |
| `place` | String | 0 | 0.00% | Stored as string (named `location`) |
| `type` | String | 0 | 0.00% | Stored as string (named `event_type`) |
| `horizontalError` | Float string | 193 | 0.98% | Optional; converted to float or omitted |
| `depthError` | Float string | 0 | 0.00% | Converted to float (named `depth_error`) |
| `magError` | Float string | 257 | 1.30% | Optional; converted to float or omitted |
| `magNst` | Integer string | 187 | 0.95% | Optional; converted to integer or omitted |
| `status` | String | 0 | 0.00% | Stored as string (named `review_status`) |
| `locationSource` | String | 0 | 0.00% | Stored as string (named `location_source`) |
| `magSource` | String | 0 | 0.00% | Stored as string (named `magnitude_source`) |

> [!NOTE]
> **Scientific Finding on Negative Depth Values:**
> The inspection revealed minimum depth of `-2.39 km`. In USGS seismological practice, negative depths represent events whose hypocenter is situated above standard sea level datum (such as earthquakes in high mountain ranges, e.g., the Andes, or high-elevation volcanic peaks). This is a physically legitimate measurement and must NOT be filtered out or discarded.

---

## 2. MongoDB Document & Schema Design

### 2.1 Target Document Structure
Each document represents a single seismic event. Below is the exact BSON representation stored in `quakescope_db.earthquake_events`:

```javascript
{
  "_id": ObjectId("6ad443d19865cbbca9ffd93a"),
  "event_id": "us7000rm06",
  "event_time": ISODate("2026-01-01T23:30:51.522Z"),
  "latitude": -15.4795,
  "longitude": -76.3908,
  "depth_km": 10.0,
  "magnitude": 4.2,
  "magnitude_type": "mb",
  "location": "132 km W of San Juan, Peru",
  "event_type": "earthquake",
  "updated_time": ISODate("2026-04-07T22:11:50.040Z"),
  "review_status": "reviewed",
  "network": "us",
  "station_count": 18,
  "azimuthal_gap": 172.0,
  "min_distance": 3.499,
  "rms_residual": 0.64,
  "horizontal_error": 11.61,
  "depth_error": 1.974,
  "magnitude_error": 0.236,
  "magnitude_station_count": 5,
  "location_source": "us",
  "magnitude_source": "us"
}
```

### 2.2 Schema Validation Rules (`$jsonSchema`)
Collection validation is applied with `validationLevel: "strict"` and `validationAction: "error"`.

```javascript
{
  $jsonSchema: {
    bsonType: "object",
    required: [
      "event_id",
      "event_time",
      "latitude",
      "longitude",
      "depth_km",
      "magnitude",
      "magnitude_type",
      "location",
      "event_type"
    ],
    properties: {
      event_id: {
        bsonType: "string",
        description: "Must be a string and is required (USGS unique event ID)"
      },
      event_time: {
        bsonType: "date",
        description: "Must be a BSON Date and is required"
      },
      latitude: {
        bsonType: ["double", "int", "long"],
        minimum: -90,
        maximum: 90,
        description: "Latitude must be between -90 and 90 degrees"
      },
      longitude: {
        bsonType: ["double", "int", "long"],
        minimum: -180,
        maximum: 180,
        description: "Longitude must be between -180 and 180 degrees"
      },
      depth_km: {
        bsonType: ["double", "int", "long"],
        minimum: -10,
        maximum: 1000,
        description: "Focal depth in kilometers (between -10 and 1000 km)"
      },
      magnitude: {
        bsonType: ["double", "int", "long"],
        minimum: -2.0,
        maximum: 10.0,
        description: "Earthquake magnitude (between -2.0 and 10.0)"
      },
      magnitude_type: {
        bsonType: "string",
        description: "Magnitude calculation method (e.g., mb, mw, md)"
      },
      location: {
        bsonType: "string",
        description: "Human-readable place description"
      },
      event_type: {
        bsonType: "string",
        description: "Event classification (e.g., earthquake, explosion)"
      }
    }
  }
}
```

### 2.3 Indexing Strategy
A unique index is enforced on `event_id`:
```javascript
db.earthquake_events.createIndex({ event_id: 1 }, { unique: true })
```
This guarantees that duplicate events cannot be inserted at the database engine level.

---

## 3. Data Import & Deduplication Logic

The import script `scripts/import_data.py`:
1. Connects to `mongodb://localhost:27017/`.
2. Queries existing `event_id` keys from the database to build an in-memory set before processing.
3. Streams the CSV using Python's standard `csv.DictReader` to minimize memory overhead.
4. Performs ISO 8601 date parsing (`datetime.fromisoformat`) and numeric casts (`float`, `int`).
5. Batches records into groups of 1,000 documents using `insert_many(..., ordered=False)`.
6. Enforces idempotency: rerunning the script skips all 19,705 already-existing records with 0 duplicates and 0 errors.

### Real Execution Output (Import Run 1 — Initial Load):
```
======================================================================
QUAKESCOPE DB - STAGE 1: DATA IMPORT PROCESS
======================================================================
[SUCCESS] Connected to MongoDB at mongodb://localhost:27017/
Retrieving existing event IDs from 'earthquake_events'...
Collection currently contains 0 existing documents.

Reading dataset from 'data\query.csv'...
  -> Inserted batch of 1,000 records (Total inserted: 1,000)
  ...
  -> Inserted final batch of 705 records

======================================================================
IMPORT SUMMARY REPORT:
  - Total records read from CSV : 19,705
  - Records newly inserted     : 19,705
  - Records skipped (duplicate) : 0
  - Records rejected (invalid)  : 0
  - Total documents in MongoDB  : 19,705
======================================================================
```

### Real Execution Output (Import Run 2 — Idempotency Test):
```
======================================================================
IMPORT SUMMARY REPORT:
  - Total records read from CSV : 19,705
  - Records newly inserted     : 0
  - Records skipped (duplicate) : 19,705
  - Records rejected (invalid)  : 0
  - Total documents in MongoDB  : 19,705
======================================================================
```

---

## 4. Manual `mongosh` Commands & Execution Results

To demonstrate operations in the MongoDB Shell (`mongosh`), open your terminal and run the following commands sequentially.

### 4.1 Launch mongosh and Connect to Database
```javascript
// Launch MongoDB Shell from terminal:
// mongosh

// Switch to the project database
use quakescope_db
```
**Expected Output:**
```
switched to db quakescope_db
```

### 4.2 Verify Collections
```javascript
show collections
```
**Output Confirmed:**
```
earthquake_events
```

### 4.3 Count Total Documents
```javascript
db.earthquake_events.countDocuments({})
```
**Output Confirmed:**
```
19705
```

### 4.4 Inspect Sample Document
```javascript
db.earthquake_events.findOne()
```
**Output Confirmed:**
```javascript
{
  _id: ObjectId('6ad443d19865cbbca9ffd93a'),
  event_id: 'us7000rm06',
  event_time: ISODate('2026-01-01T23:30:51.522Z'),
  latitude: -15.4795,
  longitude: -76.3908,
  depth_km: 10,
  magnitude: 4.2,
  magnitude_type: 'mb',
  location: '132 km W of San Juan, Peru',
  event_type: 'earthquake',
  updated_time: ISODate('2026-04-07T22:11:50.040Z'),
  review_status: 'reviewed',
  network: 'us',
  station_count: 18,
  azimuthal_gap: 172,
  min_distance: 3.499,
  rms_residual: 0.64,
  horizontal_error: 11.61,
  depth_error: 1.974,
  magnitude_error: 0.236,
  magnitude_station_count: 5,
  location_source: 'us',
  magnitude_source: 'us'
}
```

### 4.5 Retrieve Limited Records
```javascript
db.earthquake_events.find({}, { event_id: 1, magnitude: 1, depth_km: 1, location: 1, _id: 0 }).limit(3)
```
**Output Confirmed:**
```javascript
[
  {
    event_id: 'us7000rm06',
    depth_km: 10,
    magnitude: 4.2,
    location: '132 km W of San Juan, Peru'
  },
  {
    event_id: 'us7000rre2',
    depth_km: 10,
    magnitude: 4.8,
    location: '133 km ESE of Yigo Village, Guam'
  },
  {
    event_id: 'us7000rlzy',
    depth_km: 131.526,
    magnitude: 4.7,
    location: '57 km SSW of Ollagüe, Chile'
  }
]
```

### 4.6 Filter High-Magnitude Events (Magnitude >= 7.0) Sorted by Magnitude Descending
```javascript
db.earthquake_events.find(
  { magnitude: { $gte: 7.0 } },
  { event_id: 1, magnitude: 1, magnitude_type: 1, depth_km: 1, location: 1, event_time: 1, _id: 0 }
).sort({ magnitude: -1 }).limit(5)
```
**Output Confirmed:**
```javascript
[
  {
    event_id: 'us6000qw60',
    event_time: ISODate('2025-07-29T23:24:52.483Z'),
    depth_km: 35,
    magnitude: 8.8,
    magnitude_type: 'mww',
    location: '2025 Kamchatka Peninsula, Russia Earthquake'
  },
  {
    event_id: 'us7000qx2g',
    event_time: ISODate('2025-09-18T18:58:14.939Z'),
    depth_km: 27,
    magnitude: 7.8,
    magnitude_type: 'mww',
    location: '140 km E of Petropavlovsk-Kamchatsky, Russia'
  },
  {
    event_id: 'us7000pn9s',
    event_time: ISODate('2025-03-28T06:20:52.715Z'),
    depth_km: 10,
    magnitude: 7.7,
    magnitude_type: 'mww',
    location: '2025 Mandalay, Burma (Myanmar) Earthquake'
  },
  {
    event_id: 'us6000rtdt',
    event_time: ISODate('2025-12-08T14:15:09.896Z'),
    depth_km: 40.72,
    magnitude: 7.6,
    magnitude_type: 'mww',
    location: '2025 Aomori Prefecture, Japan Earthquake'
  },
  {
    event_id: 'us6000rgf4',
    event_time: ISODate('2025-10-10T20:29:20.075Z'),
    depth_km: 5.639,
    magnitude: 7.6,
    magnitude_type: 'mww',
    location: 'Drake Passage'
  }
]
```

### 4.7 Sort by Event Time (Most Recent Earthquakes)
```javascript
db.earthquake_events.find(
  {},
  { event_id: 1, event_time: 1, magnitude: 1, location: 1, _id: 0 }
).sort({ event_time: -1 }).limit(3)
```
**Output Confirmed:**
```javascript
[
  {
    event_id: 'us7000rm06',
    event_time: ISODate('2026-01-01T23:30:51.522Z'),
    magnitude: 4.2,
    location: '132 km W of San Juan, Peru'
  },
  {
    event_id: 'us7000rre2',
    event_time: ISODate('2026-01-01T23:27:18.120Z'),
    magnitude: 4.8,
    location: '133 km ESE of Yigo Village, Guam'
  },
  {
    event_id: 'us7000rlzy',
    event_time: ISODate('2026-01-01T22:49:46.878Z'),
    magnitude: 4.7,
    location: '57 km SSW of Ollagüe, Chile'
  }
]
```

### 4.8 Schema Validation Rejection Test
```javascript
try {
  db.earthquake_events.insertOne({
    event_id: "test_invalid_record_001",
    latitude: 999.0, // Invalid: exceeds max 90.0
    magnitude: -5.0  // Invalid: below min -2.0
  });
} catch (error) {
  print("Validation Rejection Code: " + error.code);
  print("Validation Message: " + error.message);
}
```
**Output Confirmed:**
```
Validation Rejection Code: 121
Validation Message: Document failed validation
```

### 4.9 Verify Collection Integrity After Validation Failure
```javascript
db.earthquake_events.countDocuments({})
```
**Output Confirmed:**
```
19705
```
*(The invalid test record was rejected and the collection remains pristine with exactly 19,705 documents).*

---

## 5. Evidence Log & Screenshot Guide

### 5.1 Environment Reality & Integrity Disclosure
In accordance with the project instructions:
> *"If you cannot directly capture screenshots in your environment, do not fake them. Instead, create a clear evidence checklist and exact reproduction commands so I can capture the genuine screenshots on my Windows machine."*

**Technical Reason:** Automated agents run in non-interactive background Windows session processes (Session 0). Windows explicitly prevents background service processes from accessing the interactive GUI desktop window station (Win32 `CopyFromScreen` raises `The handle is invalid`). We did not fabricate fake terminal graphics or mock up fake desktop frames.

Instead, we provide:
1. Exact verified terminal commands and identical verified outputs.
2. An interactive batch runner `run_stage1_interactive.bat` that runs each step and pauses, allowing you to take crisp Windows Snipping Tool (`Win + Shift + S`) screenshots.
3. The exact evidence table mapping below.

### 5.2 Mandatory Screenshot Checklist

| # | Screenshot Filename | Target Window | Exact Command to Display | What the Output Proves to Examiner |
| :---: | :--- | :--- | :--- | :--- |
| **01** | `01_dataset_inspection.png` | PowerShell / CMD | `python scripts/inspect_dataset.py` | Shows row count (19,705), 22 columns, date bounds (2025), missing-value breakdown, and USGS ComCat attribution. |
| **02** | `02_mongosh_connection.png` | `mongosh` terminal | `mongosh`<br>`db.version()` | Proves local MongoDB Community Server connection (v8.3.7) without external cloud dependencies. |
| **03** | `03_database_creation.png` | `mongosh` terminal | `use quakescope_db`<br>`show collections` | Proves database selection and existence of `earthquake_events`. |
| **04** | `04_collection_validation.png` | VS Code / Editor | Open `database/setup_database.js` | Displays the `$jsonSchema` validator, numeric boundaries, required fields, and unique index. |
| **05** | `05_data_import.png` | PowerShell / CMD | `python scripts/import_data.py` | Shows live batch insertion, 19,705 inserted records, 0 skipped, 0 rejected, and BSON type verification. |
| **06** | `06_document_structure.png` | `mongosh` terminal | `db.earthquake_events.findOne()` | Shows a genuine document with BSON `ISODate`, `Double`, `String`, and clear field names. |
| **07** | `07_record_count.png` | `mongosh` terminal | `db.earthquake_events.countDocuments({})` | Confirms exact total count of `19705` documents in MongoDB. |
| **08** | `08_basic_queries.png` | `mongosh` terminal | `db.earthquake_events.find({ magnitude: { $gte: 7.0 } }, { event_id: 1, magnitude: 1, location: 1, _id: 0 }).sort({ magnitude: -1 }).limit(5)` | Proves MongoDB `$gte` query filtering and descending sorting (showing Kamchatka M8.8). |
| **09** | `09_validation_test.png` | `mongosh` terminal | `db.earthquake_events.insertOne({ event_id: "inv", latitude: 999 })` | Captures MongoDB error code `121` (`Document failed validation`), proving strict validation works. |
| **10** | `10_idempotent_rerun.png` | PowerShell / CMD | `python scripts/import_data.py` *(second run)* | Shows deduplication in action: `19,705 skipped (duplicate)`, proving repeatable, idempotent import. |

### 5.3 Easy Capture Instructions for Windows
1. Open PowerShell in `c:\quakescopedb`.
2. Run `.\run_stage1_interactive.bat` (or run each command listed above).
3. Press `Win + Shift + S` to capture the window.
4. Save the screenshot directly into `screenshots/stage1/<filename>.png`.

---

## 6. Viva & Presentation Readiness (Student Q&A)

### Q1: What is the source of the dataset and why are there negative depths?
**Answer:** The dataset is from the USGS Comprehensive Earthquake Catalog (ComCat) covering the entire year of 2025 (19,705 events). Negative depth (e.g. -2.39 km) occurs when an event hypocenter is located above sea level datum, typically in high-elevation mountain chains like the Andes. In USGS ComCat, this is legitimate physical data, not an error.

### Q2: Why did you use `event_id` instead of just MongoDB's `_id` for deduplication?
**Answer:** MongoDB's `_id` is an internally generated `ObjectId` unique to each database document. If an import script is rerun, MongoDB generates new `_id`s for every document, resulting in duplicate records. Using the USGS natural identifier `id` as `event_id` with a unique index guarantees real-world deduplication and idempotency.

### Q3: Why is schema validation important in NoSQL databases?
**Answer:** While MongoDB is schema-flexible, production data integrity requires guardrails. Our `$jsonSchema` validator enforces required fields, coordinate boundaries (-90 to +90 for latitude, -180 to +180 for longitude), and reasonable magnitude ranges (-2 to 10), preventing corrupted records from entering the database.

### Q4: Why did you convert timestamps to BSON Date instead of keeping them as strings?
**Answer:** String timestamps require lexicographical comparisons and cannot take advantage of MongoDB's rich date aggregation operators (such as `$year`, `$month`, `$dayOfWeek`, and date arithmetic). BSON `ISODate` enables efficient time-series indexing, date filtering, and temporal aggregations in Stage 2.
