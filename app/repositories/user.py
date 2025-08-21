from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository for database operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, User, "users")
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return await self.find_one({"email": email})
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.find_one({"username": username})
    
    async def get_by_email_or_username(self, identifier: str) -> Optional[User]:
        """Get user by email or username."""
        return await self.find_one({
            "$or": [
                {"email": identifier},
                {"username": identifier}
            ]
        })
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        return await self.exists({"email": email})
    
    async def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        return await self.exists({"username": username})
    
    async def create_indexes(self):
        """Create database indexes for optimal performance."""
        # Unique indexes
        await self.collection.create_index("email", unique=True)
        await self.collection.create_index("username", unique=True)
        
        # Regular indexes
        await self.collection.create_index("is_active")
        await self.collection.create_index("created_at") 