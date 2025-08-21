#!/usr/bin/env python3
"""
Test script to verify Pydantic v2 compatibility fixes.
Run this after installing dependencies to ensure the template works.
"""

import os
import sys

# Set required environment variables for testing
os.environ.update({
    'MONGO_URI': 'mongodb://localhost:27017',
    'JWT_SECRET': 'test-secret-key-for-development',
    'API_KEY': 'test-api-key-for-development'
})

def test_imports():
    """Test that all imports work correctly."""
    print("🧪 Testing imports...")
    
    try:
        from app.models.base import BaseDocument, PyObjectId
        print("✅ Base models imported successfully")
        
        from app.models.user import User, CurrentUser
        print("✅ User models imported successfully")
        
        from app.models.conversation import Conversation
        print("✅ Conversation model imported successfully")
        
        from app.models.task import Task, ChatMessage
        print("✅ Task models imported successfully")
        
        from app.core.config import settings
        print("✅ Configuration loaded successfully")
        print(f"   App name: {settings.app_name}")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_model_creation():
    """Test that models can be created and serialized."""
    print("\n🧪 Testing model creation...")
    
    try:
        from app.models.base import PyObjectId
        from app.models.user import User
        from app.models.conversation import Conversation
        from app.models.task import Task, ChatMessage
        from datetime import datetime
        
        # Test PyObjectId
        obj_id = PyObjectId()
        print(f"✅ PyObjectId created: {obj_id}")
        
        # Test User model
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "hashed_password": "hashed_password_here",
            "full_name": "Test User"
        }
        user = User(**user_data)
        print("✅ User model created successfully")
        
        # Test model_dump (Pydantic v2 method)
        user_dict = user.model_dump()
        print("✅ User model serialization works")
        
        # Test Conversation model
        conv_data = {
            "user_id": obj_id,
            "title": "Test Conversation",
            "description": "A test conversation"
        }
        conversation = Conversation(**conv_data)
        print("✅ Conversation model created successfully")
        
        # Test Task model
        task_data = {
            "conversation_id": obj_id,
            "user_id": obj_id,
            "user_message": "Hello, this is a test message"
        }
        task = Task(**task_data)
        print("✅ Task model created successfully")
        
        # Test ChatMessage model
        message_data = {
            "role": "user",
            "content": "Test message content"
        }
        message = ChatMessage(**message_data)
        print("✅ ChatMessage model created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_schemas():
    """Test that API schemas work correctly."""
    print("\n🧪 Testing API schemas...")
    
    try:
        from app.api.v1.schemas import (
            UserCreate, UserResponse, ConversationCreate, ConversationResponse,
            TaskCreate, TaskResponse, ChatRequest, ChatResponse
        )
        
        # Test UserCreate schema
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        print("✅ UserCreate schema works")
        
        # Test ChatRequest schema
        chat_request = ChatRequest(message="Hello, world!")
        print("✅ ChatRequest schema works")
        
        return True
    except Exception as e:
        print(f"❌ API schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 FastAPI Chatbot Template - Pydantic v2 Compatibility Test\n")
    
    tests = [
        test_imports,
        test_model_creation,
        test_api_schemas
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! The Pydantic v2 fixes are working correctly.")
        print("\n📋 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Create .env file: cp .env.example .env")
        print("3. Start MongoDB: sudo systemctl start mongodb")
        print("4. Run the app: uvicorn main:app --reload")
        print("5. Visit: http://localhost:8000/docs")
        return True
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except ImportError as e:
        print(f"❌ Dependencies not installed: {e}")
        print("\n📦 Install dependencies first:")
        print("   pip install fastapi uvicorn motor pydantic pydantic-settings")
        print("   # Or install all dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1) 