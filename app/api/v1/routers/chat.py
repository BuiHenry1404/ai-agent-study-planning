from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import get_db, get_current_active_user
from app.api.v1.schemas import ChatRequest, ChatResponse
from app.models.user import CurrentUser
from app.services.chat import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse, status_code=201, summary="Send chat message")
async def send_message(
    chat_request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Send a message to the chatbot. This endpoint automatically:
    1. Creates a new conversation if conversation_id is not provided
    2. Creates a new task with the user message
    3. Returns the task with the user message (assistant responses can be added later)
    
    This is the main entry point for chat interactions.
    """
    chat_service = ChatService(db)
    response = await chat_service.process_message(
        user_id=str(current_user.id),
        chat_request=chat_request
    )
    
    return response


@router.post("/{conversation_id}/continue", response_model=ChatResponse, status_code=201, summary="Continue conversation")
async def continue_conversation(
    conversation_id: str,
    chat_request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Continue an existing conversation with a new message.
    This will create a new task in the specified conversation.
    """
    # Override the conversation_id from the path
    chat_request.conversation_id = conversation_id
    
    chat_service = ChatService(db)
    response = await chat_service.process_message(
        user_id=str(current_user.id),
        chat_request=chat_request
    )
    
    return response 