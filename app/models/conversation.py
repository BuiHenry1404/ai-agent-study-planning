from typing import List, Optional
from pydantic import Field, ConfigDict
from app.models.base import BaseDocument, PyObjectId


class Conversation(BaseDocument):
    """Conversation model - groups related tasks together."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Project Planning Discussion",
                "description": "Planning the new feature development",
                "is_active": True,
                "metadata": {
                    "category": "work",
                    "priority": "high"
                }
            }
        }
    )
    
    user_id: PyObjectId = Field(..., description="ID of the user who owns this conversation")
    title: str = Field(..., min_length=1, max_length=200, description="Conversation title")
    description: Optional[str] = Field(None, max_length=1000, description="Optional conversation description")
    task_ids: List[PyObjectId] = Field(default_factory=list, description="List of task IDs in this conversation")
    is_active: bool = Field(True, description="Whether the conversation is active")
    metadata: dict = Field(default_factory=dict, description="Additional conversation metadata") 