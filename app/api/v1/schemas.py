from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.base import PyObjectId


# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime


class UserList(BaseModel):
    users: List[UserResponse]
    total: int
    skip: int
    limit: int


# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# Conversation schemas
class ConversationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    metadata: dict = Field(default_factory=dict)


class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    task_ids: List[str] = Field(default_factory=list)
    is_active: bool
    metadata: dict
    created_at: datetime
    updated_at: datetime


class ConversationList(BaseModel):
    conversations: List[ConversationResponse]
    total: int
    skip: int
    limit: int


# Task schemas
class ChatMessageCreate(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1)
    metadata: dict = Field(default_factory=dict)


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    metadata: dict
    timestamp: float  # Unix timestamp


class TaskCreate(BaseModel):
    conversation_id: Optional[str] = None  # If None, a new conversation will be created
    user_message: str = Field(..., min_length=1)
    category: Optional[str] = Field(None, max_length=50)
    tags: List[str] = Field(default_factory=list)
    priority: Literal["low", "medium", "high", "urgent"] = Field(default="medium")
    estimated_duration: Optional[int] = None
    metadata: dict = Field(default_factory=dict)


class TaskUpdate(BaseModel):
    status: Optional[Literal["pending", "in_progress", "completed", "failed"]] = None
    priority: Optional[Literal["low", "medium", "high", "urgent"]] = None
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    metadata: Optional[dict] = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    conversation_id: str
    user_id: str
    user_message: str
    messages: List[ChatMessageResponse] = Field(default_factory=list)
    status: Literal["pending", "in_progress", "completed", "failed"]
    priority: Literal["low", "medium", "high", "urgent"]
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    completion_percentage: int
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    metadata: dict
    created_at: datetime
    updated_at: datetime


class TaskList(BaseModel):
    tasks: List[TaskResponse]
    total: int
    skip: int
    limit: int


class AddMessageToTask(BaseModel):
    role: Literal["assistant", "system"]  # Only allow non-user messages to be added
    content: str = Field(..., min_length=1)
    metadata: dict = Field(default_factory=dict)


# Chat interaction schemas
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    task_id: str
    conversation_id: str
    user_message: ChatMessageResponse
    assistant_responses: List[ChatMessageResponse] = Field(default_factory=list)


# Health check schema
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0" 