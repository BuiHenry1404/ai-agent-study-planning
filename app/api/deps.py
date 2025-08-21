from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.security import verify_token, verify_api_key
from app.models.user import CurrentUser
from app.repositories.user import UserRepository
from app.infrastructure.llm import LLMManager

security = HTTPBearer()


def get_db(request: Request) -> AsyncIOMotorDatabase:
    """Get database instance from app state."""
    if hasattr(request.app.state, 'db'):
        return request.app.state.db
    else:
        raise RuntimeError("Database not initialized in application state")


def get_llm_client(request: Request) -> LLMManager:
    """Get LLM manager instance from app state."""
    if hasattr(request.app.state, 'llm_manager'):
        return request.app.state.llm_manager
    else:
        raise RuntimeError("LLM manager not initialized in application state")


def get_autogen_llm_client(request: Request):
    """Get raw AutoGen model client for use with AutoGen agents."""
    if hasattr(request.app.state, 'llm_manager'):
        # Get the raw AutoGen client from the manager
        client = request.app.state.llm_manager.get_client()
        if hasattr(client, 'client'):
            return client.client
        else:
            raise RuntimeError("Client does not have underlying AutoGen client")
    else:
        raise RuntimeError("LLM manager not initialized in application state")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> CurrentUser:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return CurrentUser(**user.model_dump())


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def verify_api_key_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> bool:
    """Verify API key for internal services."""
    api_key = credentials.credentials
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return True


class CommonQueryParams:
    """Common query parameters for list endpoints."""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: int = -1  # -1 for desc, 1 for asc
    ):
        self.skip = max(0, skip)
        self.limit = min(100, max(1, limit))  # Cap at 100 items
        self.sort_by = sort_by
        self.sort_order = sort_order 