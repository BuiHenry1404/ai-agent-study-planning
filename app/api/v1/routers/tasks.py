from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import get_db, get_current_active_user, CommonQueryParams
from app.api.v1.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskList, 
    AddMessageToTask, ChatMessageResponse
)
from app.models.user import CurrentUser
from app.services.task import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=201, summary="Create task")
async def create_task(
    task_data: TaskCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new task. If conversation_id is not provided, a new conversation will be created."""
    task_service = TaskService(db)
    task = await task_service.create_task(
        user_id=str(current_user.id),
        task_data=task_data
    )
    return TaskResponse(**task.model_dump())


@router.get("/", response_model=TaskList, summary="List tasks")
async def list_tasks(
    conversation_id: str = None,
    status: str = None,
    priority: str = None,
    category: str = None,
    params: CommonQueryParams = Depends(),
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List user's tasks with optional filtering and pagination."""
    task_service = TaskService(db)
    tasks, total = await task_service.list_user_tasks(
        user_id=str(current_user.id),
        conversation_id=conversation_id,
        status=status,
        priority=priority,
        category=category,
        skip=params.skip,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order
    )
    
    return TaskList(
        tasks=[TaskResponse(**task.model_dump()) for task in tasks],
        total=total,
        skip=params.skip,
        limit=params.limit
    )


@router.get("/{task_id}", response_model=TaskResponse, summary="Get task")
async def get_task(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get a specific task by ID."""
    task_service = TaskService(db)
    task = await task_service.get_user_task(
        task_id=task_id,
        user_id=str(current_user.id)
    )
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return TaskResponse(**task.model_dump())


@router.put("/{task_id}", response_model=TaskResponse, summary="Update task")
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update a task."""
    task_service = TaskService(db)
    task = await task_service.update_task(
        task_id=task_id,
        user_id=str(current_user.id),
        update_data=task_data
    )
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return TaskResponse(**task.model_dump())


@router.delete("/{task_id}", status_code=204, summary="Delete task")
async def delete_task(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a task."""
    task_service = TaskService(db)
    success = await task_service.delete_task(
        task_id=task_id,
        user_id=str(current_user.id)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )


@router.post("/{task_id}/messages", response_model=ChatMessageResponse, status_code=201, summary="Add message to task")
async def add_message_to_task(
    task_id: str,
    message_data: AddMessageToTask,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Add a chatbot message to an existing task."""
    task_service = TaskService(db)
    message = await task_service.add_message_to_task(
        task_id=task_id,
        user_id=str(current_user.id),
        message_data=message_data
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return ChatMessageResponse(**message.model_dump())


@router.get("/{task_id}/messages", response_model=list[ChatMessageResponse], summary="Get task messages")
async def get_task_messages(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all messages for a specific task."""
    task_service = TaskService(db)
    messages = await task_service.get_task_messages(
        task_id=task_id,
        user_id=str(current_user.id)
    )
    
    if messages is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return [ChatMessageResponse(**msg.model_dump()) for msg in messages] 