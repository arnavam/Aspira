import asyncio
import logging
from typing import Literal, Dict, Any, Optional
from pydantic import BaseModel, Field
from agent_factory import create_agent, extract_agent_data

from logger_config import get_logger

logger = get_logger(__name__)

# Define the structured output format for the judge
class InterviewEvaluation(BaseModel):
    technical_accuracy: Literal["bad", "neutral", "good", "great", "excellent"] = Field(
        description="Evaluate the technical correctness and depth of the user's answers."
    )
    communication: Literal["bad", "neutral", "good", "great", "excellent"] = Field(
        description="Evaluate clarity, structure, and professionalism of the user's answers."
    )
    role_fit: Literal["bad", "neutral", "good", "great", "excellent"] = Field(
        description="Evaluate how well the user fits the specific company and role requirements, or general professionalism if missing."
    )
    feedback: str = Field(
        description="2-3 sentences of constructive feedback for the user on their performance."
    )

def convert_grades_to_scores(eval_obj: InterviewEvaluation) -> Dict[str, Any]:
    """Convert categorical string grades to numerical scores out of 10."""
    mapping = {
        "bad": 1,
        "neutral": 4,
        "good": 6,
        "great": 8,
        "excellent": 10
    }
    
    t_score = mapping.get(eval_obj.technical_accuracy, 5)
    c_score = mapping.get(eval_obj.communication, 5)
    r_score = mapping.get(eval_obj.role_fit, 5)
    
    overall = round((t_score + c_score + r_score) / 3.0, 1)
    
    return {
        "technical_accuracy": t_score,
        "communication": c_score,
        "role_fit": r_score,
        "overall_score": overall,
        "feedback": eval_obj.feedback,
        "grades": {
            "technical_accuracy": eval_obj.technical_accuracy,
            "communication": eval_obj.communication,
            "role_fit": eval_obj.role_fit
        }
    }

async def evaluate_interview(history: list[str], answer_stats: dict, metadata: dict) -> Dict[str, Any]:
    """
    Run the LLM-as-a-Judge to evaluate the entire conversation history.
    """
    try:
        system_prompt = (
            "You are an expert technical recruiter and interviewer. "
            "Your task is to review the following interview transcript and provide a final evaluation. "
            "Be objective and strict. Pay attention to both the candidate's technical skills and communication."
        )
        
        judge_agent = create_agent(
            system_prompt=system_prompt,
            output_type=InterviewEvaluation
        )
        
        history_text = "\n".join(history)
        
        # Build prompt context
        context = []
        if metadata.get("company") or metadata.get("role"):
            context.append(f"Company: {metadata.get('company', 'Not specified')}")
            context.append(f"Role: {metadata.get('role', 'Not specified')}")
            context.append(f"Requirements: {metadata.get('requirements', 'Not specified')}")
        else:
            context.append("Evaluation Context: General Professional Interview.")
            
        if answer_stats:
            context.append(f"\nStatistical Baseline Metrics (Last Answer): {answer_stats}")
            
        prompt = (
            "Please evaluate the candidate based on the following context and transcript.\n\n"
            f"=== CONTEXT ===\n{chr(10).join(context)}\n\n"
            f"=== TRANSCRIPT ===\n{history_text}"
        )
        
        logger.info("Running LLM judge evaluation...")
        result = await judge_agent.run(prompt)
        
        evaluation_data = convert_grades_to_scores(extract_agent_data(result))
        logger.info(f"Evaluation complete. Overall Score: {evaluation_data['overall_score']}")
        return evaluation_data
        
    except Exception as e:
        logger.error(f"Error during LLM evaluation: {e}")
        # Return a fallback evaluation structure
        return {
            "technical_accuracy": 0,
            "communication": 0,
            "role_fit": 0,
            "overall_score": 0,
            "feedback": f"An error occurred during evaluation: {e}",
            "grades": {
                "technical_accuracy": "bad",
                "communication": "bad",
                "role_fit": "bad"
            }
        }
