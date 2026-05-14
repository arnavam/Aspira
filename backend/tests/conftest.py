import pytest
import os
import asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock

# Set test environment variables
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"
os.environ["GROQ_API_KEY"] = "gsk_test_api_key_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

from database import Database
from api_server import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """Provides a fresh, mocked MongoDB database for each test."""
    from mongomock_motor import AsyncMongoMockClient

    # Use a real DB name with the mock client, though it's all in-memory
    mock_client = AsyncMongoMockClient()
    mock_db = Database(uri="mongodb://localhost:27017/", db_name="aspira_test_db")
    
    # Replace the actual client with the mocked one
    mock_db.client = mock_client
    mock_db.db = mock_client["aspira_test_db"]
    
    # Initialize indexes
    await mock_db._init_indexes()
    
    # Yield the database instance
    yield mock_db
    
    # No need to drop since mongomock starts fresh, but good practice
    await mock_client.drop_database("aspira_test_db")


@pytest.fixture(scope="function")
async def async_client(test_db):
    """Provides an async client for API testing."""
    # Override the global DB dependency in api_server with our test DB
    with patch('api_server.db', test_db):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client


@pytest.fixture(scope="function")
def mock_groq():
    """Mocks the Groq API client to avoid real network calls during tests."""
    with patch('api_server.Groq') as MockGroq:
        mock_instance = MockGroq.return_value
        
        # Mock transcription response
        mock_transcription = MagicMock()
        mock_transcription.text = "This is a mocked transcription."
        mock_instance.audio.transcriptions.create.return_value = mock_transcription
        
        # You can add more mock responses here if needed (e.g. for completions)
        yield mock_instance


@pytest.fixture(scope="function")
def mock_edge_tts():
    """Mocks edge-tts to prevent real audio file generation."""
    with patch('api_server.edge_tts.Communicate') as MockCommunicate:
        mock_instance = MockCommunicate.return_value
        
        # Mock the save function (which is async)
        async def mock_save(*args, **kwargs):
            # Optionally create an empty file if the test checks for it
            path = args[0]
            with open(path, "w") as f:
                f.write("mocked audio content")
            pass
            
        mock_instance.save = mock_save
        yield mock_instance
