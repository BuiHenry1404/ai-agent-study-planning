from typing import Optional
from pydantic import EmailStr, Field, ConfigDict
from app.models.base import BaseDocument


class User(BaseDocument):
    """User model."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "is_active": True,
                "is_superuser": False
            }
        }
    )
    
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False


class CurrentUser(BaseDocument):
    """Current authenticated user (without sensitive fields)."""
    
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool 