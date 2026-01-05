
import unittest
import os
from database import Database

class TestMongoDatabase(unittest.TestCase):
    def setUp(self):
        # Use a test database
        self.db = Database(uri="mongodb://localhost:27017/", db_name="test_aspira_db")
        # Clear collections
        self.db.db.users.delete_many({})
        self.db.db.meta.delete_many({})
        self.db.db.keywords.delete_many({})
        self.db.db.textbook.delete_many({})
        self.db.db.qa_cache.delete_many({})
        self.db.db.conversation.delete_many({})

    def tearDown(self):
        pass

    def test_user_creation(self):
        uid = self.db.create_user("testuser", "hashed_pw")
        self.assertIsNotNone(uid)
        
        user = self.db.get_user("testuser")
        self.assertEqual(user["username"], "testuser")
        
        # Duplicate test
        uid2 = self.db.create_user("testuser", "new_hash")
        self.assertIsNone(uid2)

    def test_keywords_persistence(self):
        uid = "user123"
        kw = {"python": [0.5, 0.8], "coding": [0.9, 0.1]}
        self.db.update_keywords(uid, kw)
        
        stored_kw = self.db.get_keywords(uid)
        self.assertEqual(stored_kw["python"], [0.5, 0.8])
        self.assertEqual(stored_kw["coding"], [0.9, 0.1])
        
        # Test update (replace)
        kw2 = {"java": [0.1, 0.1]}
        self.db.update_keywords(uid, kw2)
        stored_kw_2 = self.db.get_keywords(uid)
        self.assertNotIn("python", stored_kw_2)
        self.assertIn("java", stored_kw_2)

    def test_history_persistence(self):
        uid = "user123"
        self.db.add_conversation_message(uid, "User: Hello")
        self.db.add_conversation_message(uid, "Interviewer: Hi")
        
        history = self.db.get_conversation_history(uid)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0], "User: Hello")
        self.assertEqual(history[1], "Interviewer: Hi")

    def test_session_counter(self):
        uid = "user123"
        self.assertEqual(self.db.get_session_counter(uid), 0)
        
        val = self.db.increment_session_counter(uid)
        self.assertEqual(val, 1)
        self.assertEqual(self.db.get_session_counter(uid), 1)
        
        val = self.db.increment_session_counter(uid)
        self.assertEqual(val, 2)

    def test_textbook(self):
        uid = "user123"
        self.db.add_textbook(uid, "http://example.com/1", "Content 1")
        self.db.add_textbook(uid, "http://example.com/2", "Content 2")
        
        tb = self.db.get_textbook(uid)
        self.assertEqual(len(tb), 2)
        self.assertEqual(tb["http://example.com/1"], "Content 1")
        
        # Upsert test
        self.db.add_textbook(uid, "http://example.com/1", "Content 1 Updated")
        tb = self.db.get_textbook(uid)
        self.assertEqual(tb["http://example.com/1"], "Content 1 Updated")

    def test_qa(self):
        uid = "user123"
        qa_data = {"Q1": "A1", "Q2": "A2"}
        self.db.update_qa(uid, qa_data)
        
        qa = self.db.get_qa(uid)
        self.assertEqual(qa["Q1"], "A1")
        
        # Upsert
        self.db.update_qa(uid, {"Q1": "A1 Updated", "Q3": "A3"})
        qa = self.db.get_qa(uid)
        self.assertEqual(qa["Q1"], "A1 Updated")
        self.assertEqual(qa["Q3"], "A3")

if __name__ == '__main__':
    unittest.main()
