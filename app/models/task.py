import datetime
from typing import List, Optional, Literal
from pydantic import Field, ConfigDict
from app.models.base import BaseDocument, PyObjectId


class ChatMessage(BaseDocument):
    """Individual chat message within a task."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "content": "Can you help me plan a project?",
                "metadata": {
                    "timestamp": "2023-12-01T10:00:00Z",
                    "client_id": "web-app"
                }
            }
        }
    )
    
    role: Literal["user", "assistant", "system"] = Field(..., description="Role of the message sender")
    content: str = Field(..., min_length=1, description="Message content")
    metadata: dict = Field(default_factory=dict, description="Additional message metadata")


class Task(BaseDocument):
    """Task model - contains one user message and multiple chatbot responses."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_message": "Help me create a project timeline",
                "status": "in_progress",
                "priority": "high",
                "category": "planning",
                "tags": ["project", "timeline"],
                "completion_percentage": 50,
                "estimated_duration": 30,
                "metadata": {
                    "complexity": "medium",
                    "requires_approval": False
                }
            }
        }
    )
    
    conversation_id: PyObjectId = Field(..., description="ID of the parent conversation")
    user_id: PyObjectId = Field(..., description="ID of the user who created this task")
    
    # The original user message that started this task
    user_message: str = Field(..., min_length=1, description="Original user message")
    
    # All messages in this task (user + assistant responses)
    messages: List[ChatMessage] = Field(default_factory=list, description="All messages in this task")
    
    # Task status and metadata
    status: Literal["pending", "in_progress", "completed", "failed"] = Field(default="pending", description="Task status")
    priority: Literal["low", "medium", "high", "urgent"] = Field(default="medium", description="Task priority")
    
    # Optional categorization
    category: Optional[str] = Field(None, max_length=50, description="Task category")
    tags: List[str] = Field(default_factory=list, description="Task tags")
    
    # Completion tracking
    completion_percentage: int = Field(default=0, ge=0, le=100, description="Task completion percentage")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")
    actual_duration: Optional[int] = Field(None, description="Actual duration in minutes")
    
    # Additional metadata
    metadata: dict = Field(default_factory=dict, description="Additional task metadata")

    # Agent team state and type
    agent_state: dict = Field(default_factory=dict, description="Saved state from agent team")
    
    # Task execution details
    started_at: Optional[datetime] = Field(None, description="Datetime when task processing started")
    completed_at: Optional[datetime] = Field(None, description="Datetime when task processing completed")
    error_message: Optional[str] = Field(None, description="Error message if task failed")