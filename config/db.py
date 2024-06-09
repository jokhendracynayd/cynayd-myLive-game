from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

try:
    client = MongoClient('mongodb://localhost:27017/myLive')
    db = client['myLive']
    # If the connection is successful, this code will execute.
    print("Connected to MongoDB successfully")
except ConnectionFailure as e:
    # If there's an error connecting to MongoDB, this code will execute.
    print(f"Error connecting to MongoDB: {e}")
