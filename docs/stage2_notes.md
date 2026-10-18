# QuakeScope DB — Stage 2 Technical Notes & Evidence Log

**Course:** CSE494: Intelligent NoSQL Databases  
**Project:** QuakeScope DB — Earthquake Event Management System  
**Stage:** Stage 2 — Python/PyMongo CRUD, Aggregation & Screenshot Evidence  
**Database:** `quakescope_db`  
**Collection:** `earthquake_events`  
**Base Record Count:** 19,705 documents (preserved 100% intact)  

---

## 1. Overview & Deliverables

Stage 2 establishes complete application integration between MongoDB and Python using PyMongo. It introduces:
1. Reusable, robust database connection management in [`scripts/database.py`](file:///c:/quakescopedb/scripts/database.py).
2. Four complete CRUD operations with strict schema validation and unique indexing in [`scripts/crud_operations.py`](file:///c:/quakescopedb/scripts/crud_operations.py).
3. Five core MongoDB aggregation pipelines in [`scripts/aggregation_queries.py`](file:///c:/quakescopedb/scripts/aggregation_queries.py).
4. Dual shell implementations for viva demonstration in [`database/queries_crud.js`](file:///c:/quakescopedb/database/queries_crud.js) and [`database/queries_aggregation.js`](file:///c:/quakescopedb/database/queries_aggregation.js).
5. Interactive 15-option terminal application with self-test suite in [`main.py`](file:///c:/quakescopedb/main.py).
6. Interactive step-by-step runner for screenshot capture: [`run_stage2_interactive.bat`](file:///c:/quakescopedb/run_stage2_interactive.bat).

---

## 2. PyMongo Connection (`scripts/database.py`)

### 2.1 Connection Design
Connection management is encapsulated in `scripts/database.py`:
* **URI:** `mongodb://localhost:27017/`
* **Driver:** PyMongo 4.19.0 on Python 3.13.5
* **Timeout:** `serverSelectionTimeoutMS=5000` (prevents indefinite blocking if the local service is stopped).
* **Connection Reusability:** Employs a module-level cached `MongoClient` instance (`_mongo_client`). It does NOT disconnect or re-handshake after every query, preventing socket exhaustion.
* **Connectivity Verification:** Uses `client.admin.command("ping")` to verify heartbeat.

### 2.2 Direct Execution Output:
```
=================================================================
MONGODB CONNECTION TEST: SUCCESS
=================================================================
Server URI       : mongodb://localhost:27017/
MongoDB Version  : 8.3.7
Active Database  : quakescope_db
Collection Name  : earthquake_events
Total Documents  : 19,705
=================================================================
```

---

## 3. CRUD Operations (`scripts/crud_operations.py`)

### 3.1 Create (`insert_one`)
* **Function:** `create_event(event_data)`
* **Validation:** Ensures mandatory fields (`event_id`, `event_time`, `latitude`, `longitude`, `depth_km`, `magnitude`, `magnitude_type`, `location`, `event_type`) exist and casts them to appropriate Python/BSON types.
* **Error Handling:** 
  * Intercepts `DuplicateKeyError` when an existing `event_id` is passed.
  * Intercepts `WriteError` (Error Code 121) when coordinates or magnitudes violate `$jsonSchema` rules.
* **Demonstration Output:**
  ```
  Inserting test record: test_mongosh_demo_001
  Acknowledged: true, insertedId: ObjectId('6ad44c69c7cb41ffde94ce05')
  Collection Count: 19,705 -> 19,706
  ```

### 3.2 Read (`find_one` & `find`)
* **Find by ID:** `find_event_by_id(event_id)` uses `collection.find_one({"event_id": event_id})`.
* **Find by Magnitude:** `find_events_by_magnitude(min_magnitude, limit=10)` uses `{"magnitude": {"$gte": min_magnitude}}`, sorted by `magnitude` descending.
* **Find by Location Keyword:** `find_events_by_location(keyword, limit=5)` performs a case-insensitive regex search: `{"location": {"$regex": keyword, "$options": "i"}}`.
* **Find Latest Events:** `find_latest_events(limit=5)` retrieves recent earthquakes sorted by `event_time: -1`.

### 3.3 Update (`update_one` with `$set`)
* **Function:** `update_event(event_id, update_fields)`
* **Protection:** Strips immutable fields (`_id`, `event_id`) to prevent schema violations.
* **Execution:** Executes `collection.update_one({"event_id": event_id}, {"$set": update_fields})`.
* **Output:** Reports `matched_count` (1) and `modified_count` (1).

### 3.4 Delete (`delete_one`)
* **Function:** `delete_event(event_id)`
* **Dataset Protection:** By design, routine testing only modifies and deletes user-created test records (e.g. `test_quake_001`). Interactive deletions of original USGS records require explicit confirmation.
* **Execution:** Executes `collection.delete_one({"event_id": event_id})`.
* **Integrity Confirmation:** Post-cleanup count returns to **exactly 19,705**.

---

## 4. Five Core MongoDB Aggregation Pipelines

All pipelines were tested and verified in both MongoDB Shell (`database/queries_aggregation.js`) and PyMongo (`scripts/aggregation_queries.py`).

### Aggregation 1: Overall Average Magnitude & Total Events
* **Concept:** Groups all matching documents into a single group using `_id: null` to calculate dataset-wide statistics.
* **Pipeline:**
  ```javascript
  [
    {
      $group: {
        _id: null,
        total_events: { $sum: 1 },
        avg_magnitude: { $avg: "$magnitude" },
        min_magnitude: { $min: "$magnitude" },
        max_magnitude: { $max: "$magnitude" }
      }
    },
    {
      $project: {
        _id: 0,
        total_events: 1,
        avg_magnitude: { $round: ["$avg_magnitude", 2] },
        min_magnitude: 1,
        max_magnitude: 1
      }
    }
  ]
  ```
* **Real Output:**
  ```json
  {
    "total_events": 19705,
    "avg_magnitude": 4.46,
    "min_magnitude": 3.5,
    "max_magnitude": 8.8
  }
  ```

### Aggregation 2: Earthquake Count by Magnitude Range ($bucket)
* **Concept:** Uses `$bucket` to bin numeric continuous magnitudes into distinct categories without dropping edge records.
* **Boundaries:** `[3.0, 4.0, 5.0, 6.0, 10.0]` (covers all 19,705 records from min 3.5 to max 8.8).
* **Pipeline:**
  ```javascript
  [
    {
      $bucket: {
        groupBy: "$magnitude",
        boundaries: [3.0, 4.0, 5.0, 6.0, 10.0],
        default: "Other",
        output: {
          count: { $sum: 1 },
          avg_magnitude: { $avg: "$magnitude" },
          min_in_bin: { $min: "$magnitude" },
          max_in_bin: { $max: "$magnitude" }
        }
      }
    },
    {
      $project: {
        count: 1,
        avg_magnitude: { $round: ["$avg_magnitude", 2] },
        min_in_bin: 1,
        max_in_bin: 1
      }
    }
  ]
  ```
* **Real Output Breakdown:**
  * **Below 4.0 (Minor):** 1,359 events (Avg: 3.70, Range: 3.50 to 3.99)
  * **4.0 to < 5.0 (Light):** 16,209 events (Avg: 4.41, Range: 4.00 to 4.92)
  * **5.0 to < 6.0 (Moderate):** 1,991 events (Avg: 5.23, Range: 5.00 to 5.90)
  * **6.0 and above (Strong to Great):** 146 events (Avg: 6.39, Range: 6.00 to 8.80)
  * **Sum:** $1,359 + 16,209 + 1,991 + 146 = \mathbf{19,705}$ (100% accounted for).

### Aggregation 3: Top 10 Strongest Earthquakes
* **Concept:** Orders records by `magnitude: -1` (descending) and limits output to the top 10 events.
* **Pipeline:**
  ```javascript
  [
    { $sort: { magnitude: -1 } },
    { $limit: 10 },
    {
      $project: {
        _id: 0,
        event_id: 1,
        magnitude: 1,
        magnitude_type: 1,
        event_time: 1,
        location: 1,
        depth_km: 1
      }
    }
  ]
  ```
* **Real Output (Top 5 Displayed):**
  1. `us6000qw60` — **M8.8** | 35.0 km depth | *2025 Kamchatka Peninsula, Russia Earthquake*
  2. `us7000qx2g` — **M7.8** | 27.0 km depth | *140 km E of Petropavlovsk-Kamchatsky, Russia*
  3. `us7000pn9s` — **M7.7** | 10.0 km depth | *2025 Mandalay, Burma (Myanmar) Earthquake*
  4. `us6000rtdt` — **M7.6** | 40.7 km depth | *2025 Aomori Prefecture, Japan Earthquake*
  5. `us7000pcdl` — **M7.6** | 14.3 km depth | *210 km SSW of George Town, Cayman Islands*

### Aggregation 4: Earthquake Counts by Magnitude Scale Type
* **Concept:** Groups by `magnitude_type` scale. Note: `mb` measures short-period body waves, `mww` measures long-period W-phase moment tensors, and `ml` measures local Richter waves. They are not directly interchangeable.
* **Pipeline:**
  ```javascript
  [
    {
      $group: {
        _id: "$magnitude_type",
        count: { $sum: 1 },
        avg_magnitude: { $avg: "$magnitude" }
      }
    },
    { $sort: { count: -1 } },
    {
      $project: {
        _id: 0,
        magnitude_type: "$_id",
        count: 1,
        avg_magnitude: { $round: ["$avg_magnitude", 2] }
      }
    }
  ]
  ```
* **Real Output:**
  * `mb` (Body wave): 16,784 quakes (Avg: 4.43)
  * `mww` (W-phase moment): 1,482 quakes (Avg: 5.31)
  * `ml` (Local Richter): 529 quakes (Avg: 3.72)
  * `mwr` (Regional moment): 409 quakes (Avg: 4.30)
  * `md` (Duration magnitude): 401 quakes (Avg: 3.74)
  * `mw` (General moment): 90 quakes (Avg: 3.93)
  * `mwb`, `mb_lg`, `ms_vx`: 10 quakes combined.

### Aggregation 5: Monthly Earthquake Distribution
* **Concept:** Formats BSON Date `event_time` to `%Y-%m` strings, groups by month, and sorts chronologically.
* **Pipeline:**
  ```javascript
  [
    {
      $group: {
        _id: { $dateToString: { format: "%Y-%m", date: "$event_time" } },
        count: { $sum: 1 },
        avg_magnitude: { $avg: "$magnitude" }
      }
    },
    { $sort: { _id: 1 } },
    {
      $project: {
        _id: 0,
        month: "$_id",
        count: 1,
        avg_magnitude: { $round: ["$avg_magnitude", 2] }
      }
    }
  ]
  ```
* **Real Output Highlights:**
  * Consistent monthly baseline: ~1,300 to 1,500 quakes/month.
  * **July 2025 Peak:** **2,840 earthquakes** (caused by the aftershock sequence following the July 29 M8.8 Kamchatka event).
  * **August 2025 Elevated:** **2,330 earthquakes** (continued regional aftershocks).

---

## 5. Automated Verification Test Suite

Executing `python -c "import main; main.run_automated_self_test()"` runs all CRUD operations and aggregations end-to-end, confirming:
1. `initial_count == 19705`
2. `create_event` inserts `test_autoverify_001` -> count = `19706`.
3. `find_event_by_id` retrieves the record.
4. `update_event` modifies magnitude (5.1 -> 5.4).
5. `create_event` with `latitude: 999.0` is blocked by MongoDB's `$jsonSchema` (Code 121).
6. `create_event` with duplicate `event_id` is blocked by unique index (`DuplicateKeyError`).
7. `delete_event` removes `test_autoverify_001`.
8. `final_count == 19705` (pristine collection verified).
9. All 5 aggregation pipelines return valid, expected shapes.

---

## 6. Screenshot Evidence Checklist (6 Essential Screenshots)

To comply with the requirement for genuine, un-fabricated screenshots, use [`run_stage2_interactive.bat`](file:///c:/quakescopedb/run_stage2_interactive.bat). It pauses after each step so you can press **`Win + Shift + S`** (Windows Snipping Tool) and save the screenshot directly to `screenshots/stage2/`.

| # | Screenshot Filename | Target Window / Command | What it Proves to Examiner |
| :---: | :--- | :--- | :--- |
| **01** | `01_pymongo_crud.png` | Editor (`scripts/database.py` & `scripts/crud_operations.py`) alongside Terminal (`python scripts/database.py`) | PyMongo connection to `localhost:27017`, active MongoDB version 8.3.7, and CRUD helper definitions. |
| **02** | `02_mongosh_queries.png` | MongoDB Shell: `mongosh database/queries_crud.js` (Steps 1-3) | Direct `mongosh` commands showing single document retrieval by `event_id`, `$gte: 7.5` magnitude filtering, and location regex queries. |
| **03** | `03_aggregation_code.png` | Editor view of `scripts/aggregation_queries.py` | Implementation of all 5 PyMongo aggregation pipelines: `$group` with `_id: None`, `$bucket`, `$sort`/`$limit`, magnitude type counts, and `$dateToString`. |
| **04** | `04_aggregation_results.png` | Terminal output of `python scripts/aggregation_queries.py` | Complete Python terminal execution displaying the 5 formatted analytical tables (overall average, bucket distribution, top 10 quakes, mag types, monthly counts). |
| **05** | `05_crud_test_results.png` | MongoDB Shell: `mongosh database/queries_crud.js` (Steps 4-8) | Successful insertion of temporary test record (`acknowledged: true`, count 19,706), `updateOne` with `$set`, and `deleteOne` cleanup. |
| **06** | `06_final_verification.png` | Terminal: `python -c "import main; main.run_automated_self_test()"` and count command | Full 9-point automated test suite pass (CRUD, schema validator error 121, duplicate key error, 5 aggregations) and final document count of **19,705**. |

---

## 7. Viva Q&A Preparation (Student Reference)

### Q1: What is the purpose of `_id: null` in MongoDB's `$group` stage?
**Answer:** In MongoDB aggregation, the `_id` expression defines the grouping key. When we specify `_id: null` (or `_id: None` in PyMongo), all input documents are grouped into a single combined partition, allowing us to calculate dataset-wide summary statistics like overall `$avg`, `$sum`, `$min`, and `$max`.

### Q2: What is the difference between `$bucket` and standard `$group`?
**Answer:** `$bucket` is an aggregation stage specifically optimized for categorizing continuous numeric data into predefined boundary bins (such as grouping magnitudes into `[3.0, 4.0, 5.0, 6.0, 10.0]`). While standard `$group` can achieve similar results using complex `$switch` or conditional `$cond` expressions, `$bucket` is cleaner, more readable, and semantically expresses numeric binning.

### Q3: Why does `scripts/database.py` reuse the `MongoClient` instance instead of opening a new client in every function?
**Answer:** Creating a `MongoClient` initializes a connection pool, performs server discovery, and handshakes sockets with the MongoDB daemon. Creating and closing clients on every CRUD operation causes socket exhaustion, high latency, and excessive memory overhead. Reusing a module-level client is the standard production best practice in PyMongo.

### Q4: How does MongoDB's collection validator interact with PyMongo updates?
**Answer:** MongoDB collection validation (configured with `validationLevel: "strict"` and `validationAction: "error"`) is enforced by the database engine itself, regardless of whether a query originates from `mongosh` or PyMongo. If an `update_one` operation sets a value that violates the `$jsonSchema` (e.g. setting `magnitude: 25.0`), the database server rejects the write and PyMongo raises a `WriteError` with Error Code 121.

### Q5: Why is July 2025 the highest month for earthquake frequency in this dataset?
**Answer:** On July 29, 2025, an enormous magnitude 8.8 earthquake struck the Kamchatka Peninsula, Russia (event ID `us6000qw60`). Major subduction earthquakes trigger thousands of aftershocks over subsequent weeks, leading to 2,840 recorded events in July 2025 compared to the baseline of ~1,400 events per month.
