// queries_aggregation.js
// QuakeScope DB - Stage 2: MongoDB Aggregation Pipelines
// Course: CSE494 Intelligent NoSQL Databases

db = db.getSiblingDB("quakescope_db");

print("===============================================================================");
print("QUAKESCOPE DB - STAGE 2: MONGODB AGGREGATION DEMONSTRATION");
print("Database: " + db.getName());
print("Collection: earthquake_events");
print("===============================================================================");

// -----------------------------------------------------------------------------
// AGGREGATION 1: Overall Average Magnitude & Total Events
// -----------------------------------------------------------------------------
print("\n--- AGGREGATION 1: Overall Average Magnitude and Total Events ---");
print("Concept: '$group' with '_id: null' groups ALL documents into a single group.");
print("Pipeline: [ { $group: { _id: null, total: { $sum: 1 }, avg: { $avg: '$magnitude' } } } ]");

const agg1 = db.earthquake_events.aggregate([
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
]).toArray();
printjson(agg1);


// -----------------------------------------------------------------------------
// AGGREGATION 2: Earthquake Count by Magnitude Range
// -----------------------------------------------------------------------------
print("\n--- AGGREGATION 2: Earthquake Count by Magnitude Range ---");
print("Concept: '$bucket' categorizes continuous numeric values into defined boundary bins.");
print("Boundaries: [3.0, 4.0, 5.0, 6.0, 10.0]");

const agg2 = db.earthquake_events.aggregate([
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
]).toArray();

// Print in a friendly format
printjson(agg2.map(function(b) {
  let label = "";
  if (b._id === 3.0) label = "Below 4.0 (Minor: 3.0 to < 4.0)";
  else if (b._id === 4.0) label = "4.0 to < 5.0 (Light)";
  else if (b._id === 5.0) label = "5.0 to < 6.0 (Moderate)";
  else if (b._id === 6.0) label = "6.0 and above (Strong to Great)";
  else label = String(b._id);
  
  return {
    magnitude_range: label,
    count: b.count,
    avg_magnitude: b.avg_magnitude,
    sample_range: b.min_in_bin + " to " + b.max_in_bin
  };
}));


// -----------------------------------------------------------------------------
// AGGREGATION 3: Top 10 Strongest Earthquakes
// -----------------------------------------------------------------------------
print("\n--- AGGREGATION 3: Top 10 Strongest Earthquakes ---");
print("Concept: '$sort' with -1 arranges records descending, '$limit' caps output at 10.");

const agg3 = db.earthquake_events.aggregate([
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
]).toArray();
printjson(agg3);


// -----------------------------------------------------------------------------
// AGGREGATION 4: Earthquake Counts by Magnitude Type
// -----------------------------------------------------------------------------
print("\n--- AGGREGATION 4: Earthquake Counts by Magnitude Type ---");
print("Concept: Groups by 'magnitude_type' scale (e.g. mb, mww, ml).");
print("Note: Different scales measure distinct seismic wave properties and are not equivalent.");

const agg4 = db.earthquake_events.aggregate([
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
]).toArray();
printjson(agg4);


// -----------------------------------------------------------------------------
// AGGREGATION 5: Monthly Earthquake Counts
// -----------------------------------------------------------------------------
print("\n--- AGGREGATION 5: Monthly Earthquake Distribution ---");
print("Concept: Extracts '%Y-%m' from 'event_time' via '$dateToString', groups and sorts.");

const agg5 = db.earthquake_events.aggregate([
  {
    $group: {
      _id: {
        $dateToString: { format: "%Y-%m", date: "$event_time" }
      },
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
]).toArray();
printjson(agg5);

print("\n===============================================================================");
print("AGGREGATION DEMONSTRATION COMPLETE (All pipelines verified safely without data mutation).");
print("===============================================================================");
