from typing import List, Optional, Tuple
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.conversation import Conversation
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Conversation repository for database operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Conversation, "conversations")
    
    async def get_user_conversations(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: int = -1,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Conversation], int]:
        """Get conversations for a specific user with pagination."""
        filter_dict = {"user_id": ObjectId(user_id)}
        
        if is_active is not None:
            filter_dict["is_active"] = is_active
        
        conversations = await self.find(
            filter_dict=filter_dict,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        total = await self.count(filter_dict)
        return conversations, total
    
    async def get_user_conversation(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Get a specific conversation for a user."""
        if not ObjectId.is_valid(conversation_id):
            return None
            
        return await self.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": ObjectId(user_id)
        })
    
    async def add_task_to_conversation(self, conversation_id: str, task_id: str) -> bool:
        """Add a task ID to conversation's task_ids list."""
        if not ObjectId.is_valid(conversation_id) or not ObjectId.is_valid(task_id):
            return False
        
        result = await self.collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {
                "$addToSet": {"task_ids": ObjectId(task_id)},
                "$set": {"updated_at": self._get_current_time()}
            }
        )
        return result.modified_count > 0
    
    async def remove_task_from_conversation(self, conversation_id: str, task_id: str) -> bool:
        """Remove a task ID from conversation's task_ids list."""
        if not ObjectId.is_valid(conversation_id) or not ObjectId.is_valid(task_id):
            return False
        
        result = await self.collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {
                "$pull": {"task_ids": ObjectId(task_id)},
                "$set": {"updated_at": self._get_current_time()}
            }
        )
        return result.modified_count > 0
    
    async def get_conversations_by_task_id(self, task_id: str) -> List[Conversation]:
        """Get conversations that contain a specific task."""
        if not ObjectId.is_valid(task_id):
            return []
        
        return await self.find({"task_ids": ObjectId(task_id)})
    
    async def delete_user_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation belonging to a specific user."""
        if not ObjectId.is_valid(conversation_id):
            return False
        
        result = await self.collection.delete_one({
            "_id": ObjectId(conversation_id),
            "user_id": ObjectId(user_id)
        })
        return result.deleted_count > 0
    
    async def create_indexes(self):
        """Create database indexes for optimal performance."""
        # Compound indexes
        await self.collection.create_index([("user_id", 1), ("created_at", -1)])
        await self.collection.create_index([("user_id", 1), ("is_active", 1)])
        
        # Regular indexes
        await self.collection.create_index("task_ids")
        await self.collection.create_index("created_at")
        await self.collection.create_index("updated_at")
    
    def _get_current_time(self):
        """Get current UTC time."""
        from datetime import datetime
        return datetime.utcnow() 