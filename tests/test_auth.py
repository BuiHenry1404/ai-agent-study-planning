import pytest
from httpx import AsyncClient


class TestAuth:
    """Test authentication endpoints."""
    
    async def test_register_user(self, async_client: AsyncClient):
        """Test user registration."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
            "full_name": "New User"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["full_name"] == user_data["full_name"]
        assert data["is_active"] is True
        assert "hashed_password" not in data  # Should not expose password
    
    async def test_register_duplicate_email(self, async_client: AsyncClient, test_user):
        """Test registration with duplicate email."""
        user_data = {
            "email": test_user["user"]["email"],  # Same email as test_user
            "username": "differentuser",
            "password": "password123"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    async def test_login_success(self, async_client: AsyncClient, test_user):
        """Test successful login."""
        login_data = {
            "username": test_user["user"]["username"],
            "password": test_user["user"]["password"]
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_invalid_credentials(self, async_client: AsyncClient):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    async def test_get_current_user(self, async_client: AsyncClient, test_user):
        """Test getting current user information."""
        response = await async_client.get(
            "/api/v1/auth/me", 
            headers=test_user["headers"]
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == test_user["user"]["email"]
        assert data["username"] == test_user["user"]["username"]
    
    async def test_get_current_user_unauthorized(self, async_client: AsyncClient):
        """Test getting current user without authentication."""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401 