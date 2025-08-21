import pytest
from httpx import AsyncClient


class TestChat:
    """Test chat endpoints."""
    
    async def test_send_message_new_conversation(self, async_client: AsyncClient, test_user):
        """Test sending a message that creates a new conversation."""
        chat_data = {
            "message": "Hello, I need help with project planning",
            "metadata": {"priority": "high"}
        }
        
        response = await async_client.post(
            "/api/v1/chat/",
            headers=test_user["headers"],
            json=chat_data
        )
        assert response.status_code == 201
        
        data = response.json()
        assert "task_id" in data
        assert "conversation_id" in data
        assert "user_message" in data
        assert data["user_message"]["content"] == chat_data["message"]
        assert data["user_message"]["role"] == "user"
        assert data["assistant_responses"] == []
    
    async def test_send_message_existing_conversation(self, async_client: AsyncClient, test_user):
        """Test sending a message to an existing conversation."""
        # First, create a conversation by sending a message
        initial_message = {
            "message": "Initial message",
            "metadata": {}
        }
        
        response = await async_client.post(
            "/api/v1/chat/",
            headers=test_user["headers"],
            json=initial_message
        )
        assert response.status_code == 201
        conversation_id = response.json()["conversation_id"]
        
        # Send another message to the same conversation
        follow_up_message = {
            "message": "Follow up question",
            "conversation_id": conversation_id,
            "metadata": {}
        }
        
        response = await async_client.post(
            "/api/v1/chat/",
            headers=test_user["headers"],
            json=follow_up_message
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["conversation_id"] == conversation_id
        assert data["user_message"]["content"] == follow_up_message["message"]
    
    async def test_continue_conversation(self, async_client: AsyncClient, test_user):
        """Test continuing a conversation using the specific endpoint."""
        # Create initial conversation
        initial_message = {
            "message": "Start conversation",
            "metadata": {}
        }
        
        response = await async_client.post(
            "/api/v1/chat/",
            headers=test_user["headers"],
            json=initial_message
        )
        conversation_id = response.json()["conversation_id"]
        
        # Continue the conversation
        continue_message = {
            "message": "Continue the conversation",
            "metadata": {}
        }
        
        response = await async_client.post(
            f"/api/v1/chat/{conversation_id}/continue",
            headers=test_user["headers"],
            json=continue_message
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["conversation_id"] == conversation_id
        assert data["user_message"]["content"] == continue_message["message"]
    
    async def test_chat_unauthorized(self, async_client: AsyncClient):
        """Test chat endpoint without authentication."""
        chat_data = {
            "message": "Hello",
            "metadata": {}
        }
        
        response = await async_client.post("/api/v1/chat/", json=chat_data)
        assert response.status_code == 401 