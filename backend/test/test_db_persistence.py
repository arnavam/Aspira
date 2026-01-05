
import unittest
import os
import shutil
import json
from database import Database

class TestDatabasePersistence(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "log/test_aspira.db"
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = Database(self.test_db_path)

    def tearDown(self):
        # We might want to inspect the file, so maybe don't delete immediately if debugging
        # But for clean tests:
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_keywords_persistence(self):
        # 1. Update keywords
        kw = {"python": [0.5, 0.8], "coding": [0.9, 0.1]}
        self.db.update_keywords(kw)
        
        # 2. Re-instantiate DB
        self.db = Database(self.test_db_path) # Simulates app restart
        
        # 3. Check values
        stored_kw = self.db.get_keywords()
        self.assertEqual(stored_kw["python"], [0.5, 0.8])
        self.assertEqual(stored_kw["coding"], [0.9, 0.1])

    def test_history_persistence(self):
        self.db.add_conversation_message("User: Hello")
        self.db.add_conversation_message("Interviewer: Hi")
        
        self.db = Database(self.test_db_path)
        
        history = self.db.get_conversation_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0], "User: Hello")
        self.assertEqual(history[1], "Interviewer: Hi")

    def test_session_counter(self):
        self.assertEqual(self.db.get_session_counter(), 0)
        self.db.increment_session_counter()
        
        self.db = Database(self.test_db_path)
        self.assertEqual(self.db.get_session_counter(), 1)

    def test_textbook(self):
        self.db.add_textbook("http://example.com/1", "Content 1")
        self.db.add_textbook("http://example.com/2", "Content 2")
        
        self.db = Database(self.test_db_path)
        tb = self.db.get_textbook()
        self.assertEqual(len(tb), 2)
        self.assertEqual(tb["http://example.com/1"], "Content 1")

    def test_qa(self):
        qa_data = {"Q1": "A1", "Q2": "A2"}
        self.db.update_qa(qa_data)
        
        self.db = Database(self.test_db_path)
        start_qa = self.db.get_qa()
        self.assertEqual(start_qa["Q1"], "A1")
        
        # Update/Add more
        self.db.update_qa({"Q3": "A3"})
        final_qa = self.db.get_qa()
        self.assertEqual(final_qa["Q1"], "A1") # Should persist
        self.assertEqual(final_qa["Q3"], "A3")

if __name__ == '__main__':
    unittest.main()
