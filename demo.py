from pymongo import MongoClient

try:
    # Connect to the local MongoDB server
    client = MongoClient("mongodb://localhost:27017/")
    
    # Access a database (will create if it doesn't exist)
    db = client['mydatabase']
    
    # Access a collection (will create if it doesn't exist)
    collection = db['mycollection']
    
    # Insert a sample document into the collection
    result = collection.insert_one({"name": "Alice", "age": 30})
    
    print(f"Inserted document ID: {result.inserted_id}")

except Exception as e:
    print(f"An error occurred: {e}")