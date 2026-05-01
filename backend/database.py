
import os
import json
from logger_config import get_logger
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


class Database:
    def __init__(self, uri=None, db_name="aspira_db"):
        if uri is None:
            uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self._init_indexes()

    def _init_indexes(self):
        """Create indexes for performance and uniqueness"""
        # User uniqueness
        self.db.users.create_index("username", unique=True)

        # Meta: user_id + key unique
        self.db.meta.create_index([("user_id", 1), ("key", 1)], unique=True)

        # Keywords: user_id + conversation_id + keyword unique
        self.db.keywords.create_index(
            [("user_id", 1), ("conversation_id", 1), ("keyword", 1)], unique=True)

        # QA Cache: user_id + question unique
        self.db.qa_cache.create_index(
            [("user_id", 1), ("question", 1)], unique=True)

        # Conversation: index on user_id and conversation_id for fast retrieval
        self.db.conversation.create_index(
            [("user_id", 1), ("conversation_id", 1), ("id", 1)])

        # Scores: user_id unique
        self.db.scores.create_index("user_id", unique=True)

    # --- USER MANAGEMENT ---
    def create_user(self, username, password_hash):
        try:
            result = self.db.users.insert_one({
                "username": username,
                "password_hash": password_hash,
                "created_at": datetime.utcnow()
            })
            return str(result.inserted_id)
        except DuplicateKeyError:
            return None

    def get_user(self, username):
        return self.db.users.find_one({"username": username})

    # --- SESSION_COUNTER ---
    def get_session_counter(self, user_id: str) -> int:
        doc = self.db.meta.find_one(
            {"user_id": user_id, "key": "session_counter"})
        return int(doc["value"]) if doc else 0

    def increment_session_counter(self, user_id: str) -> int:
        # Atomic increment
        result = self.db.meta.find_one_and_update(
            {"user_id": user_id, "key": "session_counter"},
            {"$inc": {"value": 1}},
            upsert=True,
            return_document=True
        )
        return result["value"]

    # --- RESUME ---
    def save_resume(self, user_id: str, text: str):
        self.db.meta.update_one(
            {"user_id": user_id, "key": "resume"},
            {"$set": {"value": text, "updated_at": datetime.utcnow()}},
            upsert=True
        )

    def get_resume(self, user_id: str) -> str:
        doc = self.db.meta.find_one({"user_id": user_id, "key": "resume"})
        return doc["value"] if doc else None

    # --- KEYWORDS (KW) ---
    def get_keywords(self, user_id: str, conversation_id: str = "default") -> dict:
        cursor = self.db.keywords.find({"user_id": user_id})
        kw = {}
        for doc in cursor:
            # Default to 1 if it's missing
            version = doc.get("schema_version", 1)

            # If it's the old state, pretend it belongs to the "default" conversation
            if version == 1:
                if conversation_id == "default":
                    kw[doc["keyword"]] = doc["scores"]

            # If it's the new state, strictly match the conversation_id
            elif version == 2:
                if doc.get("conversation_id") == conversation_id:
                    kw[doc["keyword"]] = doc["scores"]
        return kw

    def update_keywords(self, user_id: str, kw_dict: dict, conversation_id: str = "default"):
        """Replaces keywords for the user. 
        Using bulk write for efficiency if needed, but for now loop upsert is fine 
        or delete-insert. Given the logic 'decays old, adds new', 
        we probably want to just overwrite the current state efficiently.
        """
        # Strategy: Delete all and re-insert? Or Upsert?
        # The calling code calculates the 'new state' fully.
        # So we should sync DB to this state.

        # Bulk operations
        from pymongo import UpdateOne

        operations = []
        # We might want to remove keywords that are NOT in kw_dict?
        # The python code `KW = sorted_scores` implies KW is fully replaced.
        # So yes, we should probably clear for this user first or mark them.

        # Simple approach match previous SQLite logic: Delete all for user, insert new.
        # Transaction support requires replica set. We will do delete-then-insert.
        try:
            self.db.keywords.delete_many(
                {"user_id": user_id, "conversation_id": conversation_id})
            if kw_dict:
                self.db.keywords.insert_many([
                    {"user_id": user_id, "conversation_id": conversation_id, "keyword": k, "scores": v,
                        "updated_at": datetime.utcnow(), "schema_version": 2}
                    for k, v in kw_dict.items()
                ])
        except Exception as e:
            logger.error(f"Error updating keywords: {e}")

    # --- QA ---
    def update_qa(self, user_id: str, qa_dict: dict):
        from pymongo import UpdateOne
        ops = []
        for q, a in qa_dict.items():
            ops.append(UpdateOne(
                {"user_id": user_id, "question": q},
                {"$set": {"answer_chunk": a, "created_at": datetime.utcnow()}},
                upsert=True
            ))
        if ops:
            try:
                self.db.qa_cache.bulk_write(ops)
            except Exception as e:
                logger.error(f"Error updating QA: {e}")

    def get_qa(self, user_id: str) -> dict:
        cursor = self.db.qa_cache.find({"user_id": user_id})
        return {doc["question"]: doc["answer_chunk"] for doc in cursor}

    # --- CONVERSATION HISTORY ---
    def add_conversation_message(self, user_id: str, message: str, conversation_id: str = "default"):
        role = "user" if message.startswith("User:") else "interviewer"

        # Get next ID for order (or rely on timestamp, but ID is safer for exact order)
        # We can just rely on insertion order / timestamp for MongoDB usually.
        # But if we want strict ordering, we can sort by _id which is time-based.

        self.db.conversation.insert_one({
            "user_id": user_id,
            "conversation_id": conversation_id,
            "message": message,
            "role": role,
            "timestamp": datetime.utcnow(),
            "schema_version": 2
        })

    def get_conversation_history(self, user_id: str, conversation_id: str = "default") -> list:
        cursor = self.db.conversation.find(
            {"user_id": user_id}).sort("timestamp", 1)
        history = []
        for doc in cursor:
            version = doc.get("schema_version", 1)  # Default to 1 if missing

            # Legacy records (version 1) default to "default" conversation
            if version == 1 and conversation_id == "default":
                history.append(doc["message"])

            # New records (version 2) check the explicit conversation_id
            elif version == 2 and doc.get("conversation_id") == conversation_id:
                history.append(doc["message"])

        return history

    def get_conversations(self, user_id: str) -> list:
        """Returns a list of unique conversation IDs for the user."""
        return self.db.conversation.distinct("conversation_id", {"user_id": user_id})

    # --- SCORES ---
    def get_score(self, user_id: str) -> dict:
        doc = self.db.scores.find_one({"user_id": user_id})
        return doc.get("data", {}) if doc else {}

    def update_score(self, user_id: str, score_data: dict):
        """Update user's score data (accumulated interview performance)."""
        try:
            self.db.scores.update_one(
                {"user_id": user_id},
                {"$set": {"data": score_data, "updated_at": datetime.utcnow()}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error updating score: {e}")
