from typing import List, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.v1.schemas import TaskCreate, TaskUpdate, AddMessageToTask
from app.models.task import Task, ChatMessage
from app.repositories.task import TaskRepository
from app.repositories.conversation import ConversationRepository
from app.services.conversation import ConversationService


class TaskService:
    """Service for managing tasks."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.task_repo = TaskRepository(db)
        self.conversation_repo = ConversationRepository(db)
        self.conversation_service = ConversationService(db)
    
    async def create_task(self, user_id: str, task_data: TaskCreate) -> Task:
        """Create a new task."""
        conversation_id = task_data.conversation_id
        
        # If no conversation_id provided, create a new conversation
        if not conversation_id:
            from app.api.v1.schemas import ConversationCreate
            
            # Generate conversation title from user message (first 50 chars)
            title = task_data.user_message[:50] + ("..." if len(task_data.user_message) > 50 else "")
            
            conversation_data = ConversationCreate(
                title=title,
                description="Auto-generated conversation",
                metadata={"auto_generated": True}
            )
            
            conversation = await self.conversation_service.create_conversation(
                user_id=user_id,
                conversation_data=conversation_data
            )
            conversation_id = str(conversation.id)
        
        # Create task data
        task_dict = {
            "conversation_id": ObjectId(conversation_id),
            "user_id": ObjectId(user_id),
            "user_message": task_data.user_message,
            "status": "pending",
            "priority": task_data.priority,
            "category": task_data.category,
            "tags": task_data.tags,
            "completion_percentage": 0,
            "estimated_duration": task_data.estimated_duration,
            "metadata": task_data.metadata
        }
        
        # Create the task
        task = await self.task_repo.create(task_dict)
        
        # Add task to conversation
        await self.conversation_service.add_task_to_conversation(conversation_id, str(task.id))
        
        return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return await self.task_repo.get_by_id(task_id)
    
    async def get_user_task(self, task_id: str, user_id: str) -> Optional[Task]:
        """Get a specific task for a user."""
        return await self.task_repo.get_user_task(task_id, user_id)
    
    async def list_user_tasks(
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
        """List tasks for a user with filtering and pagination."""
        return await self.task_repo.get_user_tasks(
            user_id=user_id,
            conversation_id=conversation_id,
            status=status,
            priority=priority,
            category=category,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
    
    async def update_task(
        self,
        task_id: str,
        user_id: str,
        update_data: TaskUpdate
    ) -> Optional[Task]:
        """Update a task."""
        # First check if the task belongs to the user
        task = await self.task_repo.get_user_task(task_id, user_id)
        if not task:
            return None
        
        # Prepare update data
        update_dict = {}
        if update_data.status is not None:
            update_dict["status"] = update_data.status
        if update_data.priority is not None:
            update_dict["priority"] = update_data.priority
        if update_data.category is not None:
            update_dict["category"] = update_data.category
        if update_data.tags is not None:
            update_dict["tags"] = update_data.tags
        if update_data.completion_percentage is not None:
            update_dict["completion_percentage"] = update_data.completion_percentage
        if update_data.estimated_duration is not None:
            update_dict["estimated_duration"] = update_data.estimated_duration
        if update_data.actual_duration is not None:
            update_dict["actual_duration"] = update_data.actual_duration
        if update_data.metadata is not None:
            update_dict["metadata"] = update_data.metadata
        
        if not update_dict:
            return task
        
        return await self.task_repo.update(task_id, update_dict)
    
    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task."""
        # First check if the task belongs to the user
        task = await self.task_repo.get_user_task(task_id, user_id)
        if not task:
            return False
        
        # Remove task from conversation
        await self.conversation_service.remove_task_from_conversation(
            str(task.conversation_id), task_id
        )
        
        # Delete the task
        return await self.task_repo.delete_user_task(task_id, user_id)
    
    async def add_message_to_task(
        self,
        task_id: str,
        user_id: str,
        message_data: AddMessageToTask
    ) -> Optional[ChatMessage]:
        """Add a message to a task."""
        # First check if the task belongs to the user
        task = await self.task_repo.get_user_task(task_id, user_id)
        if not task:
            return None
        
        # Create the message
        message = ChatMessage(
            role=message_data.role,
            content=message_data.content,
            metadata=message_data.metadata
        )
        
        # Add message to task
        updated_task = await self.task_repo.add_message_to_task(task_id, message)
        if not updated_task:
            return None
        
        # Return the newly added message (last in the list)
        return updated_task.messages[-1]
    
    async def get_task_messages(self, task_id: str, user_id: str) -> Optional[List[ChatMessage]]:
        """Get all messages for a task."""
        task = await self.task_repo.get_user_task(task_id, user_id)
        if not task:
            return None
        
        return task.messages
    
    async def update_task_status(self, task_id: str, user_id: str, status: str) -> bool:
        """Update task status."""
        # First check if the task belongs to the user
        task = await self.task_repo.get_user_task(task_id, user_id)
        if not task:
            return False
        
        return await self.task_repo.update_task_status(task_id, status)
    
    async def complete_task(self, task_id: str, user_id: str) -> Optional[Task]:
        """Mark a task as completed."""
        return await self.update_task(
            task_id=task_id,
            user_id=user_id,
            update_data=TaskUpdate(status="completed", completion_percentage=100)
        )
    
    async def get_conversation_tasks(
        self,
        conversation_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Task]:
        """Get all tasks in a conversation for a user."""
        # First check if the conversation belongs to the user
        conversation = await self.conversation_repo.get_user_conversation(conversation_id, user_id)
        if not conversation:
            return []
        
        return await self.task_repo.get_conversation_tasks(
            conversation_id=conversation_id,
            skip=skip,
            limit=limit
        )
    
    async def get_pending_tasks(self, limit: int = 100) -> List[Task]:
        """Get pending tasks for background processing."""
        return await self.task_repo.get_tasks_by_status("pending", limit)
    
    async def create_soulcare_task(
        self, 
        user_id: str, 
        user_message: str, 
        conversation_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Task:
        """Create a new soulcare task."""
        # If no conversation_id provided, create a new conversation
        if not conversation_id:
            from app.api.v1.schemas import ConversationCreate
            
            # Generate conversation title from user message (first 50 chars)
            title = f"Soulcare: {user_message[:40]}" + ("..." if len(user_message) > 40 else "")
            
            conversation_data = ConversationCreate(
                title=title,
                description="Soulcare conversation",
                metadata={"auto_generated": True, "type": "soulcare"}
            )
            
            conversation = await self.conversation_service.create_conversation(
                user_id=user_id,
                conversation_data=conversation_data
            )
            conversation_id = str(conversation.id)
        
        # Create task data for soulcare
        task_dict = {
            "conversation_id": ObjectId(conversation_id),
            "user_id": ObjectId(user_id),
            "user_message": user_message,
            "status": "in_progress",  # Start as in_progress since we're processing immediately
            "priority": "medium",
            "category": "soulcare",
            "tags": ["soulcare", "life-advice", "emotional-support"],
            "completion_percentage": 0,
            "agent_type": "soulcare",
            "started_at": datetime.now(),
            "metadata": metadata or {}
        }
        
        # Create the task
        task = await self.task_repo.create(task_dict)
        
        # Add task to conversation
        await self.conversation_service.add_task_to_conversation(conversation_id, str(task.id))
        
        return task
    
    async def update_task_with_agent_state(
        self, 
        task_id: str, 
        agent_state: dict, 
        status: str = "completed",
        error_message: Optional[str] = None
    ) -> Optional[Task]:
        """Update task with agent team state and completion info."""
        update_dict = {
            "agent_state": agent_state,
            "status": status,
            "completed_at": datetime.now()
        }
        
        if error_message:
            update_dict["error_message"] = error_message
            update_dict["status"] = "failed"
        
        if status == "completed":
            update_dict["completion_percentage"] = 100
        
        return await self.task_repo.update(task_id, update_dict)
    
    async def get_soulcare_tasks(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> Tuple[List[Task], int]:
        """Get soulcare tasks for a user."""
        return await self.task_repo.get_user_tasks(
            user_id=user_id,
            status=status,
            category="soulcare",
            skip=skip,
            limit=limit,
            sort_by="created_at",
            sort_order=-1
        )
    
    async def get_task_by_id_with_user_check(self, task_id: str, user_id: str) -> Optional[Task]:
        """Get task by ID with user ownership check."""
        return await self.task_repo.get_user_task(task_id, user_id)
    
    async def get_conversation_state(self, conversation_id: str, user_id: str) -> Optional[dict]:
        """Get the state of the latest completed task for a conversation."""
        # First check if the conversation belongs to the user
        conversation = await self.conversation_repo.get_user_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        return await self.task_repo.get_conversation_state(conversation_id) 