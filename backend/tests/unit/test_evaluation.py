import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from I_evaluation import convert_grades_to_scores, evaluate_interview, InterviewEvaluation

def test_convert_grades_to_scores():
    eval_obj = InterviewEvaluation(
        technical_accuracy="great",
        communication="good",
        role_fit="excellent",
        feedback="This is feedback."
    )
    
    scores = convert_grades_to_scores(eval_obj)
    
    assert scores["technical_accuracy"] == 8
    assert scores["communication"] == 6
    assert scores["role_fit"] == 10
    
    # overall is average: (8+6+10)/3 = 24/3 = 8.0
    assert scores["overall_score"] == 8.0
    assert scores["feedback"] == "This is feedback."
    assert scores["grades"]["technical_accuracy"] == "great"

@pytest.mark.asyncio
async def test_evaluate_interview_success():
    history = ["User: Hello", "Interviewer: Hi"]
    answer_stats = {"avg_words": 10}
    metadata = {"company": "Test Co", "role": "Dev", "requirements": "Python"}
    
    with patch("I_evaluation.create_agent") as mock_create_agent:
        mock_agent_instance = MagicMock()
        mock_create_agent.return_value = mock_agent_instance
        
        # Mock the run method to be async and return a mocked response
        mock_run = AsyncMock()
        mock_agent_instance.run = mock_run
        
        with patch("I_evaluation.extract_agent_data") as mock_extract:
            mock_extract.return_value = InterviewEvaluation(
                technical_accuracy="good",
                communication="great",
                role_fit="good",
                feedback="Mock feedback."
            )
            
            result = await evaluate_interview(history, answer_stats, metadata)
            
            assert mock_run.called
            assert result["technical_accuracy"] == 6
            assert result["communication"] == 8
            assert result["role_fit"] == 6
            assert result["overall_score"] == 6.7
            assert result["feedback"] == "Mock feedback."

@pytest.mark.asyncio
async def test_evaluate_interview_exception():
    history = []
    
    with patch("I_evaluation.create_agent") as mock_create_agent:
        mock_agent_instance = MagicMock()
        mock_create_agent.return_value = mock_agent_instance
        
        mock_agent_instance.run = AsyncMock(side_effect=Exception("API Error"))
        
        result = await evaluate_interview(history, {}, {})
        
        assert result["overall_score"] == 0
        assert result["technical_accuracy"] == 0
        assert "API Error" in result["feedback"]
