import asyncio
import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.testclient import TestClient

from main import app
from app.core.config import settings
from app.api.deps import get_db
from app.infrastructure.database import create_mongodb_connection

# Test database settings
TEST_MONGO_URI = "mongodb://localhost:27017"
TEST_DB_NAME = "chatbot_test_db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_mongo_db():
    """Create test database connection."""
    mongo_db = await create_mongodb_connection(
        uri=TEST_MONGO_URI, 
        db_name=TEST_DB_NAME
    )
    yield mongo_db
    # Cleanup: drop test database and close connection
    await mongo_db.get_client().drop_database(TEST_DB_NAME)
    await mongo_db.disconnect()


@pytest.fixture(scope="session")
async def test_db(test_mongo_db):
    """Get test database instance."""
    return test_mongo_db.get_database()


@pytest.fixture
def override_get_db(test_db):
    """Override the get_db dependency for testing."""
    def _override_get_db():
        return test_db
    return _override_get_db


@pytest.fixture
def test_app(override_get_db):
    """Create test FastAPI application."""
    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
async def async_client(test_app):
    """Create async test client."""
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user(async_client):
    """Create a test user and return auth token."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    # Register user
    response = await async_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    
    # Login to get token
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    response = await async_client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    return {
        "user": user_data,
        "token": token_data["access_token"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"}
    } 