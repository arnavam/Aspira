import pytest
from datetime import datetime
from database import Database

@pytest.mark.asyncio
async def test_create_and_get_user(test_db: Database):
    # Test create user
    user_id = await test_db.create_user("testuser", "hashed_pw", "encrypted_key")
    assert user_id is not None

    # Test get user
    user = await test_db.get_user("testuser")
    assert user is not None
    assert user["username"] == "testuser"
    assert user["password_hash"] == "hashed_pw"

    # Test duplicate user
    duplicate_id = await test_db.create_user("testuser", "pw", "key")
    assert duplicate_id is None

@pytest.mark.asyncio
async def test_session_counter(test_db: Database):
    user_id = "user_123"
    
    # Get initial counter (should be 0)
    count = await test_db.get_session_counter(user_id)
    assert count == 0
    
    # Increment counter
    new_count = await test_db.increment_session_counter(user_id)
    assert new_count == 1
    
    # Increment again
    newer_count = await test_db.increment_session_counter(user_id)
    assert newer_count == 2

@pytest.mark.asyncio
async def test_save_and_get_resume(test_db: Database):
    user_id = "user_123"
    resume_text = "This is a resume."
    
    await test_db.save_resume(user_id, resume_text)
    
    retrieved = await test_db.get_resume(user_id)
    assert retrieved == resume_text

@pytest.mark.asyncio
async def test_conversation_history(test_db: Database):
    user_id = "user_123"
    conv_id = "conv_1"
    
    await test_db.add_conversation_message(user_id, "User: Hello", conv_id)
    await test_db.add_conversation_message(user_id, "Interviewer: Hi there", conv_id)
    
    history = await test_db.get_conversation_history(user_id, conv_id)
    assert len(history) == 2
    assert history[0] == "User: Hello"
    assert history[1] == "Interviewer: Hi there"
    
    # Test get conversations list
    conv_list = await test_db.get_conversations(user_id)
    assert conv_id in conv_list

@pytest.mark.asyncio
async def test_keywords(test_db: Database):
    user_id = "user_123"
    conv_id = "conv_1"
    
    kw_dict = {
        "Python": [2.0, 0.9],
        "API": [1.0, 0.8]
    }
    
    await test_db.update_keywords(user_id, kw_dict, conv_id)
    
    retrieved = await test_db.get_keywords(user_id, conv_id)
    assert "Python" in retrieved
    assert retrieved["Python"] == [2.0, 0.9]

@pytest.mark.asyncio
async def test_metadata_and_evaluation(test_db: Database):
    user_id = "user_123"
    conv_id = "conv_1"
    
    metadata = {"role": "Engineer", "company": "Tech Corp"}
    await test_db.save_interview_metadata(user_id, conv_id, metadata)
    
    retrieved_meta = await test_db.get_interview_metadata(user_id, conv_id)
    assert retrieved_meta["role"] == "Engineer"
    
    evaluation = {"overall_score": 8.5}
    await test_db.save_evaluation(user_id, conv_id, evaluation)
    
    retrieved_eval = await test_db.get_evaluation(user_id, conv_id)
    assert retrieved_eval["overall_score"] == 8.5
