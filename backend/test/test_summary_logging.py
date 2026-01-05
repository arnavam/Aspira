
import unittest
import os
import logging
from H_Summaraizer import textrank

class TestSummaryLogging(unittest.TestCase):
    def test_logging(self):
        # clean up
        log_file = "log/corpus_debug.log"
        if os.path.exists(log_file):
            os.remove(log_file)
            
        text = "This is a test sentence. This is another test sentence. Python is great for testing."
        source_link = "http://test.com"
        
        # Run textrank
        _ = textrank(text, source_link=source_link)
        
        # Check if log file exists and contains the link
        self.assertTrue(os.path.exists(log_file))
        
        with open(log_file, "r") as f:
            content = f.read()
            self.assertIn("=== SOURCE: http://test.com ===", content)
            self.assertIn("This is a test sentence", content)

if __name__ == '__main__':
    unittest.main()
