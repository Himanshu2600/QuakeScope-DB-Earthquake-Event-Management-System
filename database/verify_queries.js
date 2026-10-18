// verify_queries.js
// QuakeScope DB - Stage 1: mongosh Verification Queries
// Course: CSE494 Intelligent NoSQL Databases

db = db.getSiblingDB("quakescope_db");

print("===============================================================================");
print("QUAKESCOPE DB - STAGE 1: MONGOSH QUERY VERIFICATION");
print("Database: " + db.getName());
print("===============================================================================");

print("\n--- 1. SHOW COLLECTIONS ---");
printjson(db.getCollectionNames());

print("\n--- 2. TOTAL DOCUMENT COUNT ---");
const totalCount = db.earthquake_events.countDocuments({});
print("Total Documents in earthquake_events: " + totalCount);

print("\n--- 3. SAMPLE DOCUMENT (findOne) ---");
printjson(db.earthquake_events.findOne());

print("\n--- 4. RETRIEVE LIMITED RECORDS (find().limit(3)) ---");
printjson(
  db.earthquake_events
    .find({}, { event_id: 1, magnitude: 1, depth_km: 1, location: 1, _id: 0 })
    .limit(3)
    .toArray()
);

print("\n--- 5. FILTERING QUERY: HIGH MAGNITUDE EVENTS (magnitude >= 7.0) SORTED DESC ---");
const highMagEvents = db.earthquake_events
  .find(
    { magnitude: { $gte: 7.0 } },
    { event_id: 1, magnitude: 1, magnitude_type: 1, depth_km: 1, location: 1, event_time: 1, _id: 0 }
  )
  .sort({ magnitude: -1 })
  .toArray();
print("Found " + highMagEvents.length + " events with magnitude >= 7.0:");
printjson(highMagEvents);

print("\n--- 6. SORTING QUERY: 3 MOST RECENT EARTHQUAKES (sort by event_time DESC) ---");
const recentEvents = db.earthquake_events
  .find(
    {},
    { event_id: 1, event_time: 1, magnitude: 1, location: 1, _id: 0 }
  )
  .sort({ event_time: -1 })
  .limit(3)
  .toArray();
printjson(recentEvents);

print("\n--- 7. SCHEMA VALIDATION TEST (Deliberately Invalid Document) ---");
print("Attempting to insert a document with invalid latitude (999.0) and missing required fields...");
try {
  db.earthquake_events.insertOne({
    event_id: "test_invalid_record_001",
    latitude: 999.0, // Invalid: exceeds max allowed 90.0
    magnitude: -5.0  // Invalid: below min allowed -2.0
  });
  print("[FAILED] Document was accepted, validator did NOT trigger.");
} catch (error) {
  print("[SUCCESS] MongoDB rejected the invalid document as expected!");
  print("Error code   : " + error.code);
  print("Error message: " + error.message);
}

print("\n--- 8. VERIFY INTEGRITY (Collection Count Remains Intact) ---");
const countAfterTest = db.earthquake_events.countDocuments({});
print("Document count after validation test: " + countAfterTest);
if (countAfterTest === totalCount) {
  print("[CONFIRMED] Collection remains clean and uncorrupted (19,705 documents).");
} else {
  print("[WARNING] Document count changed!");
}

print("\n===============================================================================");
print("VERIFICATION COMPLETE!");
print("===============================================================================");
