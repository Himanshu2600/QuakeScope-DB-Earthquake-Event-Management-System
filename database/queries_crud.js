// queries_crud.js
// QuakeScope DB - Stage 2: MongoDB CRUD Demonstration Script (mongosh)
// Course: CSE494 Intelligent NoSQL Databases

db = db.getSiblingDB("quakescope_db");

print("===============================================================================");
print("QUAKESCOPE DB - STAGE 2: MONGODB CRUD OPERATIONS DEMONSTRATION");
print("Database: " + db.getName());
print("Collection: earthquake_events");
print("===============================================================================");

const originalCount = db.earthquake_events.countDocuments({});
print("\nInitial Document Count: " + originalCount);

// -----------------------------------------------------------------------------
// 1. READ EXAMPLES (Safe, Non-Destructive Queries on Real Data)
// -----------------------------------------------------------------------------
print("\n--- 1. READ: Find Event by ID ---");
const sampleEvent = db.earthquake_events.findOne(
  { event_id: "us7000rm06" },
  { _id: 0, event_id: 1, event_time: 1, magnitude: 1, location: 1 }
);
printjson(sampleEvent);

print("\n--- 2. READ: Find Events with Magnitude >= 7.5 ---");
const majorQuakes = db.earthquake_events.find(
  { magnitude: { $gte: 7.5 } },
  { _id: 0, event_id: 1, magnitude: 1, location: 1, depth_km: 1 }
).sort({ magnitude: -1 }).toArray();
print("Found " + majorQuakes.length + " events:");
printjson(majorQuakes);

print("\n--- 3. READ: Find Events by Location Keyword (Case-Insensitive 'Japan') ---");
const japanEvents = db.earthquake_events.find(
  { location: { $regex: "Japan", $options: "i" } },
  { _id: 0, event_id: 1, magnitude: 1, location: 1 }
).limit(3).toArray();
printjson(japanEvents);

// -----------------------------------------------------------------------------
// 2. WRITE & DELETE EXAMPLES (Safe Cycle Using a Temporary Test Document)
// -----------------------------------------------------------------------------
const testId = "test_mongosh_demo_001";

print("\n--- 4. CREATE: Insert a Temporary Test Record (insertOne) ---");
print("Inserting test record: " + testId + " (Simulating student test event)");

const insertResult = db.earthquake_events.insertOne({
  event_id: testId,
  event_time: new Date(),
  latitude: 35.6762,
  longitude: 139.6503,
  depth_km: 15.0,
  magnitude: 4.5,
  magnitude_type: "ml",
  location: "Demo Test Site, Tokyo Bay, Japan",
  event_type: "earthquake",
  review_status: "automatic",
  network: "demo"
});
printjson(insertResult);
print("Count after insertion: " + db.earthquake_events.countDocuments({}));

print("\n--- 5. READ: Verify Inserted Test Record ---");
const retrievedTest = db.earthquake_events.findOne({ event_id: testId });
printjson(retrievedTest);

print("\n--- 6. UPDATE: Modify Test Record ($set with updateOne) ---");
print("Updating magnitude to 4.9 and modifying location description...");
const updateResult = db.earthquake_events.updateOne(
  { event_id: testId },
  {
    $set: {
      magnitude: 4.9,
      location: "Updated Demo Site, Tokyo Bay, Japan (Reviewed)",
      review_status: "reviewed"
    }
  }
);
print("Matched Count : " + updateResult.matchedCount);
print("Modified Count: " + updateResult.modifiedCount);

print("\n--- 7. READ: Verify Updated Record ---");
const verifiedUpdated = db.earthquake_events.findOne(
  { event_id: testId },
  { _id: 0, event_id: 1, magnitude: 1, location: 1, review_status: 1 }
);
printjson(verifiedUpdated);

print("\n--- 8. DELETE: Clean Up Temporary Test Record (deleteOne) ---");
const deleteResult = db.earthquake_events.deleteOne({ event_id: testId });
print("Deleted Count: " + deleteResult.deletedCount);

const finalCount = db.earthquake_events.countDocuments({});
print("\nFinal Document Count: " + finalCount);

if (finalCount === originalCount) {
  print("[CONFIRMED] Collection returned to pristine state (" + finalCount + " records). Original data intact!");
} else {
  print("[WARNING] Document count mismatch!");
}

print("\n===============================================================================");
print("CRUD DEMONSTRATION COMPLETE!");
print("===============================================================================");
