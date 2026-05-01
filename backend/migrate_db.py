import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def run_migration():
    print("Starting database migration...")
    
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    client = MongoClient(uri)
    db = client["aspira_db"]
    
    # 1. Update conversations
    print("Migrating 'conversation' collection...")
    conv_result = db.conversation.update_many(
        {"conversation_id": {"$exists": False}},
        {"$set": {"conversation_id": "default"}}
    )
    print(f"Updated {conv_result.modified_count} documents in 'conversation'.")
    
    # 2. Update keywords
    print("Migrating 'keywords' collection...")
    kw_result = db.keywords.update_many(
        {"conversation_id": {"$exists": False}},
        {"$set": {"conversation_id": "default"}}
    )
    print(f"Updated {kw_result.modified_count} documents in 'keywords'.")
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
