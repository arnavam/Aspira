import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

uri = os.environ.get("MONGODB_URI", "mongodb://mongodb:27017")
print("Using URI:", uri)
client = MongoClient(uri)
db = client["aspira_db"]

try:
    db.keywords.drop_index("user_id_1_keyword_1")
    print("Old keyword index dropped successfully.")
except Exception as e:
    print("Error dropping index:", e)

# Let's list the current indexes to confirm
indexes = db.keywords.index_information()
print("Current indexes:")
for name, details in indexes.items():
    print(f"- {name}: {details['key']}")
