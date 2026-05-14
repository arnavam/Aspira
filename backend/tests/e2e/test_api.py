import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_register_and_login(async_client: AsyncClient):
    # Register
    register_data = {
        "username": "e2e_user",
        "password": "secure_password",
        "groq_api_key": "gsk_1234567890abcdefghijklmnopqrstuvwxyz12345678"
    }
    response = await async_client.post("/register", json=register_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    
    # Login
    login_data = {
        "username": "e2e_user",
        "password": "secure_password"
    }
    login_response = await async_client.post("/token", data=login_data)
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
    
    return login_response.json()["access_token"]

@pytest.mark.asyncio
async def test_setup_interview(async_client: AsyncClient):
    token = await test_register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}
    
    setup_data = {
        "conversation_id": "conv_e2e_1",
        "company": "Test Co",
        "role": "QA Engineer",
        "requirements": "Pytest"
    }
    
    response = await async_client.post("/setup_interview", json=setup_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Interview metadata saved successfully."

@pytest.mark.asyncio
async def test_get_conversations(async_client: AsyncClient):
    token = await test_register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.get("/conversations", headers=headers)
    assert response.status_code == 200
    assert "conversations" in response.json()

@pytest.mark.asyncio
async def test_transcribe_audio(async_client: AsyncClient, mock_groq):
    token = await test_register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a dummy file
    files = {'file': ('test.wav', b'dummy audio data', 'audio/wav')}
    
    response = await async_client.post("/transcribe", files=files, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"text": "This is a mocked transcription."}
