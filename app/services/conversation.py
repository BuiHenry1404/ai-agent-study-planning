from typing import List, Optional, Tuple
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.v1.schemas import ConversationCreate, ConversationUpdate
from app.models.conversation import Conversation
from app.repositories.conversation import ConversationRepository
from app.repositories.task import TaskRepository


class ConversationService:
    """Service for managing conversations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.conversation_repo = ConversationRepository(db)
        self.task_repo = TaskRepository(db)
    
    async def create_conversation(self, user_id: str, conversation_data: ConversationCreate) -> Conversation:
        """Create a new conversation."""
        conversation_dict = {
            "user_id": ObjectId(user_id),
            "title": conversation_data.title,
            "description": conversation_data.description,
            "task_ids": [],
            "is_active": True,
            "metadata": conversation_data.metadata
        }
        
        conversation = await self.conversation_repo.create(conversation_dict)
        return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        return await self.conversation_repo.get_by_id(conversation_id)
    
    async def get_user_conversation(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Get a specific conversation for a user."""
        return await self.conversation_repo.get_user_conversation(conversation_id, user_id)
    
    async def list_user_conversations(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: int = -1,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Conversation], int]:
        """List conversations for a user with pagination."""
        return await self.conversation_repo.get_user_conversations(
            user_id=user_id,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            is_active=is_active
        )
    
    async def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        update_data: ConversationUpdate
    ) -> Optional[Conversation]:
        """Update a conversation."""
        # First check if the conversation belongs to the user
        conversation = await self.conversation_repo.get_user_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        # Prepare update data
        update_dict = {}
        if update_data.title is not None:
            update_dict["title"] = update_data.title
        if update_data.description is not None:
            update_dict["description"] = update_data.description
        if update_data.is_active is not None:
            update_dict["is_active"] = update_data.is_active
        if update_data.metadata is not None:
            update_dict["metadata"] = update_data.metadata
        
        if not update_dict:
            return conversation
        
        return await self.conversation_repo.update(conversation_id, update_dict)
    
    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation and all its tasks."""
        # First check if the conversation belongs to the user
        conversation = await self.conversation_repo.get_user_conversation(conversation_id, user_id)
        if not conversation:
            return False
        
        # Delete all tasks in the conversation
        await self.task_repo.delete_conversation_tasks(conversation_id)
        
        # Delete the conversation
        return await self.conversation_repo.delete_user_conversation(conversation_id, user_id)
    
    async def add_task_to_conversation(self, conversation_id: str, task_id: str) -> bool:
        """Add a task to a conversation."""
        return await self.conversation_repo.add_task_to_conversation(conversation_id, task_id)
    
    async def remove_task_from_conversation(self, conversation_id: str, task_id: str) -> bool:
        """Remove a task from a conversation."""
        return await self.conversation_repo.remove_task_from_conversation(conversation_id, task_id)
    
    async def get_conversation_with_tasks(self, conversation_id: str, user_id: str) -> Optional[dict]:
        """Get conversation with all its tasks."""
        conversation = await self.conversation_repo.get_user_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        tasks = await self.task_repo.get_conversation_tasks(conversation_id)
        
        return {
            "conversation": conversation,
            "tasks": tasks
        }
    
    async def archive_conversation(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Archive a conversation (set is_active to False)."""
        return await self.update_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            update_data=ConversationUpdate(is_active=False)
        )
    
    async def activate_conversation(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Activate a conversation (set is_active to True)."""
        return await self.update_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            update_data=ConversationUpdate(is_active=True)
        ) 