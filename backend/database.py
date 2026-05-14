import os
import json
import time
import asyncio
from logger_config import get_logger
from datetime import datetime
from dotenv import load_dotenv
from pymongo import AsyncMongoClient, UpdateOne
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError, ConnectionFailure

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


class Database:
    def __init__(self, uri=None, db_name="aspira_db"):
        if uri is None:
            uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

        # Configure client to handle idle drops and timeouts properly
        self.client = AsyncMongoClient(
            uri,
            # Proactively close connections before load balancers (usually ~4 mins) drop them
            maxIdleTimeMS=210000,
            serverSelectionTimeoutMS=10000  # Wait 10s per attempt to find a server
        )
        self.db = self.client[db_name]

    async def initialize(self, retries=5, delay=5):
        """Tries to connect and initialize indexes, waiting if the Atlas cluster is paused."""
        for attempt in range(1, retries + 1):
            try:
                # Ping the database to force connection and check availability
                await self.client.admin.command('ping')
                await self._init_indexes()
                logger.info(
                    "Successfully connected to MongoDB and initialized indexes.")
                return
            except (ServerSelectionTimeoutError, ConnectionFailure) as e:
                logger.warning(f"MongoDB connection failed on attempt {attempt}/{retries}. Cluster might be waking up. Retrying in {delay}s...")
                if attempt == retries:
                    logger.error(
                        "Failed to connect to MongoDB after multiple retries. The backend might fail.")
                    raise e
                await asyncio.sleep(delay)

    async def _init_indexes(self):
        """Create indexes for performance and uniqueness"""
        # User uniqueness
        await self.db.users.create_index("username", unique=True)

        # Meta: user_id + key unique
        await self.db.meta.create_index([("user_id", 1), ("key", 1)], unique=True)

        # Keywords: user_id + conversation_id + keyword unique
        await self.db.keywords.create_index(
            [("user_id", 1), ("conversation_id", 1), ("keyword", 1)], unique=True)

        # QA Cache: user_id + question unique
        await self.db.qa_cache.create_index(
            [("user_id", 1), ("question", 1)], unique=True)

        # Conversation: index on user_id and conversation_id for fast retrieval
        await self.db.conversation.create_index(
            [("user_id", 1), ("conversation_id", 1), ("id", 1)])

        # Scores: user_id unique
        await self.db.scores.create_index("user_id", unique=True)

    # --- USER MANAGEMENT ---
    async def create_user(self, username, password_hash, groq_api_key_encrypted=""):
        try:
            result = await self.db.users.insert_one({
                "username": username,
                "password_hash": password_hash,
                "groq_api_key": groq_api_key_encrypted,
                "created_at": datetime.utcnow()
            })
            return str(result.inserted_id)
        except DuplicateKeyError:
            return None

    async def get_user(self, username):
        return await self.db.users.find_one({"username": username})

    async def get_user_by_id(self, user_id: str):
        from bson.objectid import ObjectId
        try:
            return await self.db.users.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None

    # --- SESSION_COUNTER ---
    async def get_session_counter(self, user_id: str) -> int:
        doc = await self.db.meta.find_one(
            {"user_id": user_id, "key": "session_counter"})
        return int(doc["value"]) if doc else 0

    async def increment_session_counter(self, user_id: str) -> int:
        # Atomic increment
        result = await self.db.meta.find_one_and_update(
            {"user_id": user_id, "key": "session_counter"},
            {"$inc": {"value": 1}},
            upsert=True,
            return_document=True
        )
        return result["value"]

    # --- RESUME ---
    async def save_resume(self, user_id: str, text: str):
        await self.db.meta.update_one(
            {"user_id": user_id, "key": "resume"},
            {"$set": {"value": text, "updated_at": datetime.utcnow()}},
            upsert=True
        )

    async def get_resume(self, user_id: str) -> str:
        doc = await self.db.meta.find_one({"user_id": user_id, "key": "resume"})
        return doc["value"] if doc else None

    # --- KEYWORDS (KW) ---
    async def get_keywords(self, user_id: str, conversation_id: str = "default") -> dict:
        cursor = self.db.keywords.find({"user_id": user_id})
        kw = {}
        async for doc in cursor:
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

    async def update_keywords(self, user_id: str, kw_dict: dict, conversation_id: str = "default"):
        """Replaces keywords for the user."""
        try:
            await self.db.keywords.delete_many(
                {"user_id": user_id, "conversation_id": conversation_id})
            if kw_dict:
                await self.db.keywords.insert_many([
                    {"user_id": user_id, "conversation_id": conversation_id, "keyword": k, "scores": v,
                        "updated_at": datetime.utcnow(), "schema_version": 2}
                    for k, v in kw_dict.items()
                ])
        except Exception as e:
            logger.error(f"Error updating keywords: {e}")

    # --- QA ---
    async def update_qa(self, user_id: str, qa_dict: dict):
        ops = []
        for q, a in qa_dict.items():
            ops.append(UpdateOne(
                {"user_id": user_id, "question": q},
                {"$set": {"answer_chunk": a, "created_at": datetime.utcnow()}},
                upsert=True
            ))
        if ops:
            try:
                await self.db.qa_cache.bulk_write(ops)
            except Exception as e:
                logger.error(f"Error updating QA: {e}")

    async def get_qa(self, user_id: str) -> dict:
        cursor = self.db.qa_cache.find({"user_id": user_id})
        return {doc["question"]: doc["answer_chunk"] async for doc in cursor}

    # --- CONVERSATION HISTORY ---
    async def add_conversation_message(self, user_id: str, message: str, conversation_id: str = "default"):
        role = "user" if message.startswith("User:") else "interviewer"
        await self.db.conversation.insert_one({
            "user_id": user_id,
            "conversation_id": conversation_id,
            "message": message,
            "role": role,
            "timestamp": datetime.utcnow(),
            "schema_version": 2
        })

    async def get_conversation_history(self, user_id: str, conversation_id: str = "default") -> list:
        cursor = self.db.conversation.find(
            {"user_id": user_id}).sort("timestamp", 1)
        history = []
        async for doc in cursor:
            version = doc.get("schema_version", 1)  # Default to 1 if missing

            # Legacy records (version 1) default to "default" conversation
            if version == 1 and conversation_id == "default":
                history.append(doc["message"])

            # New records (version 2) check the explicit conversation_id
            elif version == 2 and doc.get("conversation_id") == conversation_id:
                history.append(doc["message"])

        return history

    async def get_conversations(self, user_id: str) -> list:
        """Returns a list of unique conversation IDs for the user."""
        return await self.db.conversation.distinct("conversation_id", {"user_id": user_id})

    # --- SCORES ---
    async def get_score(self, user_id: str) -> dict:
        doc = await self.db.scores.find_one({"user_id": user_id})
        return doc.get("data", {}) if doc else {}

    async def update_score(self, user_id: str, score_data: dict):
        """Update user's score data (accumulated interview performance)."""
        try:
            await self.db.scores.update_one(
                {"user_id": user_id},
                {"$set": {"data": score_data, "updated_at": datetime.utcnow()}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error updating score: {e}")

    # --- METADATA ---
    async def get_interview_metadata(self, user_id: str, conversation_id: str) -> dict:
        doc = await self.db.metadata.find_one({"user_id": user_id, "conversation_id": conversation_id})
        return doc.get("metadata", {}) if doc else {}

    async def save_interview_metadata(self, user_id: str, conversation_id: str, metadata: dict):
        try:
            await self.db.metadata.update_one(
                {"user_id": user_id, "conversation_id": conversation_id},
                {"$set": {"metadata": metadata, "updated_at": datetime.utcnow()}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error updating interview metadata: {e}")

    # --- EVALUATION ---
    async def get_evaluation(self, user_id: str, conversation_id: str) -> dict:
        doc = await self.db.evaluations.find_one({"user_id": user_id, "conversation_id": conversation_id})
        return doc.get("evaluation", {}) if doc else {}

    async def save_evaluation(self, user_id: str, conversation_id: str, evaluation: dict):
        try:
            await self.db.evaluations.update_one(
                {"user_id": user_id, "conversation_id": conversation_id},
                {"$set": {"evaluation": evaluation, "updated_at": datetime.utcnow()}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error updating evaluation: {e}")

    # --- KNOWLEDGE GRAPH ---
    async def get_knowledge_graph(self, user_id: str, conversation_id: str) -> dict:
        """Retrieve the knowledge graph for a specific conversation."""
        doc = await self.db.knowledge_graphs.find_one(
            {"user_id": user_id, "conversation_id": conversation_id}
        )
        return doc.get("graph_data", {}) if doc else {}

    async def save_knowledge_graph(self, user_id: str, conversation_id: str, graph_data: dict):
        """Upsert the knowledge graph for a specific conversation."""
        try:
            await self.db.knowledge_graphs.update_one(
                {"user_id": user_id, "conversation_id": conversation_id},
                {"$set": {"graph_data": graph_data, "updated_at": datetime.utcnow()}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error saving knowledge graph: {e}")
