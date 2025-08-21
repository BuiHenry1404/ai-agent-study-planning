#!/usr/bin/env python3
"""
Script to create a test user for Socket.IO testing.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.services.auth import AuthService
from app.api.v1.schemas import UserCreate


async def create_test_user():
    """Create a test user for Socket.IO testing."""
    # Connect to MongoDB
    mongo = AsyncIOMotorClient(str(settings.mongo_uri))
    db = mongo[settings.mongo_db_name]
    
    try:
        # Create auth service
        auth_service = AuthService(db)
        
        # Create test user
        test_user_data = UserCreate(
            email="testuser@example.com",
            username="testuser",
            password="testpass123",
            full_name="Test User"
        )
        
        # Check if user already exists
        existing_user = await auth_service.user_repo.get_by_email_or_username("testuser")
        if existing_user:
            print("✅ Test user already exists!")
            print(f"   Username: {existing_user.username}")
            print(f"   Email: {existing_user.email}")
        else:
            # Create the user
            user = await auth_service.register_user(test_user_data)
            print("✅ Test user created successfully!")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   User ID: {user.id}")
        
        print("\n📋 Test credentials:")
        print("   Username: testuser")
        print("   Password: testpass123")
        print("\n🚀 You can now use these credentials to login and test Socket.IO!")
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
    finally:
        mongo.close()


if __name__ == "__main__":
    asyncio.run(create_test_user()) 