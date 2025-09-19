from pymongo import MongoClient

MONGO_URI = "mongodb+srv://aspira1:arnavam@cluster0.zgeiza0.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["aspira1"]      # choose DB name
users_collection = db["users"] # choose collection name
