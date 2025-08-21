from typing import Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.v1.schemas import UserCreate
from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.repositories.user import UserRepository


class AuthService:
    """Authentication service for user management."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.user_repo = UserRepository(db)
    
    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user."""
        # Check if email already exists
        if await self.user_repo.email_exists(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        if await self.user_repo.username_exists(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user data
        user_dict = {
            "email": user_data.email,
            "username": user_data.username,
            "full_name": user_data.full_name,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_superuser": False
        }
        
        # Create user
        user = await self.user_repo.create(user_dict)
        return user
    
    async def authenticate_user(self, identifier: str, password: str) -> Optional[User]:
        """Authenticate user by email/username and password."""
        user = await self.user_repo.get_by_email_or_username(identifier)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return await self.user_repo.get_by_id(user_id)
    
    async def activate_user(self, user_id: str) -> Optional[User]:
        """Activate a user account."""
        return await self.user_repo.update(user_id, {"is_active": True})
    
    async def deactivate_user(self, user_id: str) -> Optional[User]:
        """Deactivate a user account."""
        return await self.user_repo.update(user_id, {"is_active": False})
    
    async def update_user_profile(self, user_id: str, update_data: dict) -> Optional[User]:
        """Update user profile information."""
        # Remove sensitive fields that shouldn't be updated directly
        allowed_fields = {"full_name", "is_active"}
        filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not filtered_data:
            return await self.user_repo.get_by_id(user_id)
        
        return await self.user_repo.update(user_id, filtered_data)
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
        
        if not verify_password(current_password, user.hashed_password):
            return False
        
        new_hashed_password = get_password_hash(new_password)
        updated_user = await self.user_repo.update(user_id, {"hashed_password": new_hashed_password})
        
        return updated_user is not None 