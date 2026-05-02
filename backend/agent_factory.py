import os
from typing import Any, Optional
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel

from logger_config import get_logger

logger = get_logger(__name__)

# Lazy initialization
_groq_model = None

def get_groq_model() -> GroqModel:
    """
    Lazily instantiate and return the GroqModel.
    Ensures that missing API keys or model loading doesn't block module import.
    """
    global _groq_model
    if _groq_model is None:
        # Pydantic AI will automatically look for GROQ_API_KEY environment variable.
        # We can proactively check it here if we want a clearer error message.
        if not os.environ.get("GROQ_API_KEY"):
            logger.warning("GROQ_API_KEY environment variable is not set. API calls will fail.")
            
        logger.info("Initializing GroqModel lazily...")
        _groq_model = GroqModel("llama-3.1-8b-instant")
    return _groq_model

def create_agent(system_prompt: str, output_type: Optional[Any] = None) -> Agent:
    """
    Unified factory for creating configured pydantic_ai Agents on the fly.
    """
    return Agent(
        model=get_groq_model(),
        system_prompt=system_prompt,
        output_type=output_type or str
    )

def extract_agent_data(result: Any) -> Any:
    """
    Extracts the 'output' attribute from a pydantic_ai RunResult strictly.
    Matches version 1.89.1+ naming conventions.
    """
    if hasattr(result, "output"):
        return result.output
    else:
        raise AttributeError(
            f"Agent result has no 'output' attribute! (Got {type(result).__name__}). "
            "Ensure you are using pydantic-ai v1.0+."
        )
