// setup_database.js
// QuakeScope DB - Stage 1: MongoDB Database & Collection Setup with Schema Validation
// Course: CSE494 Intelligent NoSQL Databases

// Switch to the project database
db = db.getSiblingDB("quakescope_db");

print("========================================================");
print("QuakeScope DB: Initializing Database & Schema Validation");
print("========================================================");

// Define the JSON schema validator for earthquake_events collection
const earthquakeSchema = {
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
      updated_time: {
        bsonType: ["date", "null"],
        description: "Optional BSON Date for last update timestamp"
      },
      latitude: {
        bsonType: ["double", "int", "long"],
        minimum: -90,
        maximum: 90,
        description: "Must be a number between -90 and 90 degrees and is required"
      },
      longitude: {
        bsonType: ["double", "int", "long"],
        minimum: -180,
        maximum: 180,
        description: "Must be a number between -180 and 180 degrees and is required"
      },
      depth_km: {
        bsonType: ["double", "int", "long"],
        minimum: -10,
        maximum: 1000,
        description: "Focal depth in kilometers (between -10 and 1000 km) and is required"
      },
      magnitude: {
        bsonType: ["double", "int", "long"],
        minimum: -2.0,
        maximum: 10.0,
        description: "Earthquake magnitude (between -2.0 and 10.0) and is required"
      },
      magnitude_type: {
        bsonType: "string",
        description: "Magnitude calculation method (e.g., mb, mw, md) and is required"
      },
      location: {
        bsonType: "string",
        description: "Human-readable place description and is required"
      },
      event_type: {
        bsonType: "string",
        description: "Event classification (e.g., earthquake, explosion) and is required"
      },
      review_status: {
        bsonType: ["string", "null"],
        description: "Review status: automatic or reviewed"
      },
      network: {
        bsonType: ["string", "null"],
        description: "Network data contributor (e.g., us, pr)"
      }
    }
  }
};

// Check if collection already exists
const collections = db.getCollectionNames();
if (collections.includes("earthquake_events")) {
  print("Collection 'earthquake_events' already exists. Updating schema validation via collMod...");
  db.runCommand({
    collMod: "earthquake_events",
    validator: earthquakeSchema,
    validationLevel: "strict",
    validationAction: "error"
  });
  print("Schema validation updated successfully.");
} else {
  print("Creating collection 'earthquake_events' with strict schema validation...");
  db.createCollection("earthquake_events", {
    validator: earthquakeSchema,
    validationLevel: "strict",
    validationAction: "error"
  });
  print("Collection 'earthquake_events' created successfully.");
}

// Create unique index on event_id to prevent duplicate earthquake records
db.earthquake_events.createIndex({ event_id: 1 }, { unique: true });
print("Unique index on 'event_id' created.");

print("========================================================");
print("Database and collection setup complete!");
print("Current collections in quakescope_db:");
printjson(db.getCollectionNames());
print("========================================================");
