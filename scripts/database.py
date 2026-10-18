"""
database.py
QuakeScope DB - PyMongo Connection Module
Course: CSE494 Intelligent NoSQL Databases

This module establishes and manages a reusable connection to the local
MongoDB Community Server instance using PyMongo.
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Standard local MongoDB connection configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "quakescope_db"
COLLECTION_NAME = "earthquake_events"

# Module-level variable to hold the shared client
_mongo_client = None

def get_client():
    """
    Returns a shared MongoClient instance.
    Uses a 5-second timeout to prevent indefinite hangs if the server is stopped.
    """
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Ping the admin database to verify the connection is alive
            _mongo_client.admin.command("ping")
        except (ConnectionFailure, ServerSelectionTimeoutError) as error:
            print("\n[ERROR] Failed to connect to MongoDB server at " + MONGO_URI)
            print("Detail: " + str(error))
            print("Hint: Please ensure the MongoDB Windows Service is running (run 'net start MongoDB').\n")
            _mongo_client = None
            raise
    return _mongo_client

def get_db():
    """
    Returns the 'quakescope_db' database object.
    """
    client = get_client()
    return client[DB_NAME]

def get_collection():
    """
    Returns the 'earthquake_events' collection object.
    """
    db = get_db()
    return db[COLLECTION_NAME]

def test_connection():
    """
    Tests and prints connectivity status and basic collection stats.
    Returns True if connection succeeded, False otherwise.
    """
    try:
        client = get_client()
        # Ping the server
        client.admin.command("ping")
        db = client[DB_NAME]
        coll = db[COLLECTION_NAME]
        doc_count = coll.count_documents({})
        server_info = client.server_info()
        
        print("=" * 65)
        print("MONGODB CONNECTION TEST: SUCCESS")
        print("=" * 65)
        print(f"Server URI       : {MONGO_URI}")
        print(f"MongoDB Version  : {server_info.get('version', 'Unknown')}")
        print(f"Active Database  : {DB_NAME}")
        print(f"Collection Name  : {COLLECTION_NAME}")
        print(f"Total Documents  : {doc_count:,}")
        print("=" * 65)
        return True
    except Exception as error:
        print(f"[FAIL] MongoDB connection test failed: {error}")
        return False

if __name__ == "__main__":
    # When run directly, test the connection
    test_connection()
