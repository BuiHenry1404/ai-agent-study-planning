from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import get_autogen_llm_client
from app.api.v1.schemas import ChatRequest, ChatResponse, TaskCreate, ChatMessageResponse
from app.services.task import TaskService
from app.services.conversation import ConversationService
from app.agents.soulcare_team import SoulcareTeam


class ChatService:
    """Service for handling chat interactions."""
    
    def __init__(self, db: AsyncIOMotorDatabase, llm_client = None):
        self.task_service = TaskService(db)
        self.conversation_service = ConversationService(db)
        self.llm_client = llm_client
    
    async def process_message(self, user_id: str, chat_request: ChatRequest) -> ChatResponse:
        """Process a chat message and create appropriate task/conversation."""
        task_data = TaskCreate(
            conversation_id=chat_request.conversation_id,
            user_message=chat_request.message,
            metadata=chat_request.metadata,
            priority="medium",
            tags=["chat"]
        )
        
        task = await self.task_service.create_task(
            user_id=user_id,
            task_data=task_data
        )

        soulcare_team = SoulcareTeam(self.llm_client)

        await soulcare_team.start(task)