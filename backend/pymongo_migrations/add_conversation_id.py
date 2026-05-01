"""
Migration to add conversation_id to conversations and keywords collections
"""
import pymongo

name = 'add_conversation_id'
dependencies = []


def upgrade(db: "pymongo.database.Database"):
    # 1. Update conversations
    db.conversation.update_many(
        {"conversation_id": {"$exists": False}},
        {"$set": {"conversation_id": "default"}}
    )
    
    # 2. Update keywords
    db.keywords.update_many(
        {"conversation_id": {"$exists": False}},
        {"$set": {"conversation_id": "default"}}
    )


def downgrade(db: "pymongo.database.Database"):
    # Revert conversations
    db.conversation.update_many(
        {"conversation_id": "default"},
        {"$unset": {"conversation_id": ""}}
    )
    
    # Revert keywords
    db.keywords.update_many(
        {"conversation_id": "default"},
        {"$unset": {"conversation_id": ""}}
    )
