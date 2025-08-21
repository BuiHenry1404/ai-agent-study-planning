from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import get_db, get_current_active_user, CommonQueryParams
from app.api.v1.schemas import (
    ConversationCreate, ConversationUpdate, ConversationResponse, ConversationList
)
from app.models.user import CurrentUser
from app.services.conversation import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationResponse, status_code=201, summary="Create conversation")
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new conversation."""
    conversation_service = ConversationService(db)
    conversation = await conversation_service.create_conversation(
        user_id=str(current_user.id),
        conversation_data=conversation_data
    )
    return ConversationResponse(**conversation.model_dump())


@router.get("/", response_model=ConversationList, summary="List conversations")
async def list_conversations(
    params: CommonQueryParams = Depends(),
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List user's conversations with pagination."""
    conversation_service = ConversationService(db)
    conversations, total = await conversation_service.list_user_conversations(
        user_id=str(current_user.id),
        skip=params.skip,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order
    )
    
    return ConversationList(
        conversations=[ConversationResponse(**conv.model_dump()) for conv in conversations],
        total=total,
        skip=params.skip,
        limit=params.limit
    )


@router.get("/{conversation_id}", response_model=ConversationResponse, summary="Get conversation")
async def get_conversation(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get a specific conversation by ID."""
    conversation_service = ConversationService(db)
    conversation = await conversation_service.get_user_conversation(
        conversation_id=conversation_id,
        user_id=str(current_user.id)
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return ConversationResponse(**conversation.model_dump())


@router.put("/{conversation_id}", response_model=ConversationResponse, summary="Update conversation")
async def update_conversation(
    conversation_id: str,
    conversation_data: ConversationUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update a conversation."""
    conversation_service = ConversationService(db)
    conversation = await conversation_service.update_conversation(
        conversation_id=conversation_id,
        user_id=str(current_user.id),
        update_data=conversation_data
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return ConversationResponse(**conversation.model_dump())


@router.delete("/{conversation_id}", status_code=204, summary="Delete conversation")
async def delete_conversation(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a conversation and all its tasks."""
    conversation_service = ConversationService(db)
    success = await conversation_service.delete_conversation(
        conversation_id=conversation_id,
        user_id=str(current_user.id)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        ) 