import os
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel

groq_model = GroqModel("llama-3.1-8b-instant")
agent = Agent(model=groq_model)
try:
    result = agent.run_sync("Say 'hello'")
    print("Attributes:", dir(result))
    print("Data:", result.data if hasattr(result, 'data') else "No data")
except Exception as e:
    print(f"Error: {e}")