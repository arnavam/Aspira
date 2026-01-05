
from K_llamaindex_graph import build_knowledge_graph
import json
import os

# Test data
test_answer = "I want to become a machine learning engineer at Google"
test_chunks = [
    "Machine learning engineers design and implement ML models using Python and TensorFlow.",
]
test_questions = [
    "What is your experience with neural networks?",
    "How do you handle overfitting?",
]

# Generate to a test file
save_path = "log/knowledge_map_test.json"
if os.path.exists(save_path):
    os.remove(save_path)

result = build_knowledge_graph(test_answer, test_chunks, test_questions, save_path=save_path)
print(f"Generated {save_path}")
