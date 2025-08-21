from typing import List, Optional, Tuple
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from app.models.task import Task, ChatMessage
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Task repository for database operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Task, "tasks")
    
    async def get_user_tasks(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: int = -1
    ) -> Tuple[List[Task], int]:
        """Get tasks for a specific user with filtering and pagination."""
        filter_dict = {"user_id": ObjectId(user_id)}
        
        if conversation_id and ObjectId.is_valid(conversation_id):
            filter_dict["conversation_id"] = ObjectId(conversation_id)
        
        if status:
            filter_dict["status"] = status
        
        if priority:
            filter_dict["priority"] = priority
        
        if category:
            filter_dict["category"] = category
        
        tasks = await self.find(
            filter_dict=filter_dict,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        total = await self.count(filter_dict)
        return tasks, total
    
    async def get_user_task(self, task_id: str, user_id: str) -> Optional[Task]:
        """Get a specific task for a user."""
        if not ObjectId.is_valid(task_id):
            return None
            
        return await self.find_one({
            "_id": ObjectId(task_id),
            "user_id": ObjectId(user_id)
        })
    
    async def get_conversation_tasks(
        self,
        conversation_id: str,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: int = -1
    ) -> List[Task]:
        """Get all tasks in a conversation."""
        if not ObjectId.is_valid(conversation_id):
            return []
        
        return await self.find(
            filter_dict={"conversation_id": ObjectId(conversation_id)},
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
    
    async def add_message_to_task(self, task_id: str, message: ChatMessage) -> Optional[Task]:
        """Add a message to a task's messages array."""
        if not ObjectId.is_valid(task_id):
            return None
        
        message_dict = message.model_dump()
        message_dict["_id"] = ObjectId()  # Generate ID for the message
        
        updated_task = await self.collection.find_one_and_update(
            {"_id": ObjectId(task_id)},
            {
                "$push": {"messages": message_dict},
                "$set": {"updated_at": self._get_current_time()}
            },
            return_document=ReturnDocument.AFTER
        )
        
        if updated_task:
            return Task(**updated_task)
        return None
    
    async def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status."""
        if not ObjectId.is_valid(task_id):
            return False
        
        result = await self.collection.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "status": status,
                    "updated_at": self._get_current_time()
                }
            }
        )
        return result.modified_count > 0
    
    async def update_task_completion(self, task_id: str, completion_percentage: int) -> bool:
        """Update task completion percentage."""
        if not ObjectId.is_valid(task_id):
            return False
        
        result = await self.collection.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "completion_percentage": completion_percentage,
                    "updated_at": self._get_current_time()
                }
            }
        )
        return result.modified_count > 0
    
    async def delete_user_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task belonging to a specific user."""
        if not ObjectId.is_valid(task_id):
            return False
        
        result = await self.collection.delete_one({
            "_id": ObjectId(task_id),
            "user_id": ObjectId(user_id)
        })
        return result.deleted_count > 0
    
    async def delete_conversation_tasks(self, conversation_id: str) -> int:
        """Delete all tasks in a conversation."""
        if not ObjectId.is_valid(conversation_id):
            return 0
        
        result = await self.collection.delete_many({"conversation_id": ObjectId(conversation_id)})
        return result.deleted_count
    
    async def get_tasks_by_status(self, status: str, limit: int = 100) -> List[Task]:
        """Get tasks by status (useful for background processing)."""
        return await self.find(
            filter_dict={"status": status},
            limit=limit,
            sort_by="created_at",
            sort_order=1  # Oldest first
        )
    
    async def get_conversation_state(self, conversation_id: str) -> Optional[dict]:
        """Get the state of the latest completed task for a conversation."""
        if not ObjectId.is_valid(conversation_id):
            return None
        
        filter_dict = {
            "conversation_id": ObjectId(conversation_id),
            "completed_at": {"$exists": True}
        }
        
        # Use MongoDB aggregation to only return the agent_state field
        pipeline = [
            {"$match": filter_dict},
            {"$sort": {"completed_at": -1}},
            {"$limit": 1},
            {"$project": {"agent_state": 1, "_id": 0}}
        ]
        
        cursor = self.collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        
        if result and result[0].get("agent_state"):
            return result[0]["agent_state"]
        
        return None
    
    async def create_indexes(self):
        """Create database indexes for optimal performance."""
        # Compound indexes
        await self.collection.create_index([("user_id", 1), ("created_at", -1)])
        await self.collection.create_index([("user_id", 1), ("conversation_id", 1)])
        await self.collection.create_index([("conversation_id", 1), ("created_at", -1)])
        await self.collection.create_index([("conversation_id", 1), ("completed_at", -1)])
        await self.collection.create_index([("user_id", 1), ("status", 1)])
        await self.collection.create_index([("user_id", 1), ("priority", 1)])
        
        # Regular indexes
        await self.collection.create_index("status")
        await self.collection.create_index("priority")
        await self.collection.create_index("category")
        await self.collection.create_index("created_at")
        await self.collection.create_index("updated_at")
        await self.collection.create_index("completed_at")
    
    def _get_current_time(self):
        """Get current UTC time."""
        from datetime import datetime
        return datetime.utcnow() 