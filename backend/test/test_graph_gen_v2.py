
from K_llamaindex_graph import build_knowledge_graph
import json
import os

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Test data with keywords
test_answer = "I want to become a machine learning engineer at Google"
test_chunks = [
    "Machine learning engineers design and implement ML models using Python and TensorFlow.",
]
test_questions = [
    "What is your experience with neural networks?",
    "How do you handle overfitting?",
]
test_keywords = {
    "machine learning": 0.9, 
    "google": 0.8,
    "engineer": 0.7
}
test_urls = ["https://careers.google.com/ml", "https://wikipedia.org/wiki/Machine_learning"]

# Generate to a test file
save_path = "log/knowledge_map_test.json"
if os.path.exists(save_path):
    os.remove(save_path)

result = build_knowledge_graph(test_answer, test_chunks, test_questions, save_path=save_path, keywords=test_keywords, source_urls=test_urls)
print(f"Generated {save_path}")
