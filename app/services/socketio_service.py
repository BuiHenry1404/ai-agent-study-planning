import socketio
from typing import Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.agents import study_planning_team
from app.core.logging import get_logger
from app.core.security import verify_token

from app.services.chat import ChatService
from app.services.auth import AuthService
from app.services.task import TaskService
from app.api.v1.schemas import ChatRequest, ChatResponse
from app.models.user import CurrentUser
from app.agents.study_planning_team import StudyPlanningTeam

logger = get_logger(__name__)


class SocketIOService:
    """Service for handling Socket.IO real-time chat functionality."""
    
    def __init__(self, db: AsyncIOMotorDatabase, llm_manager=None):
        self.db = db
        self.llm_manager = llm_manager
        self.chat_service = ChatService(db)
        self.auth_service = AuthService(db)
        self.task_service = TaskService(db)
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins="*",  # Configure based on your needs
            logger=False,  # Disable socket.io logging to avoid conflicts
            engineio_logger=False
        )
        self.user_sessions: Dict[str, str] = {}  # sid -> user_id mapping
        self.user_rooms: Dict[str, str] = {}  # user_id -> room mapping
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register Socket.IO event handlers."""
        
        @self.sio.event
        async def connect(sid, environ, auth):
            """Handle client connection with authentication."""
            try:
                # Extract token from auth data
                if not auth or 'token' not in auth:
                    logger.warning(f"Connection attempt without token: {sid}")
                    await self.sio.disconnect(sid)
                    return False
                
                token = auth['token']
                
                # Verify token and get user
                try:
                    payload = verify_token(token)
                    user_id = payload.get("sub")
                    if not user_id:
                        raise ValueError("Invalid token payload")
                    
                    user = await self.auth_service.get_user_by_id(user_id)
                    if not user or not user.is_active:
                        raise ValueError("User not found or inactive")
                    
                    # Store user session
                    self.user_sessions[sid] = user_id
                    room_name = f"user_{user_id}"
                    self.user_rooms[user_id] = room_name
                    
                    # Join user-specific room
                    await self.sio.enter_room(sid, room_name)
                    
                    logger.info(f"User {user.username} connected with session {sid}")
                    
                    # Send connection success
                    await self.sio.emit('connected', {
                        'message': 'Successfully connected',
                        'user': {
                            'id': str(user.id),
                            'username': user.username,
                            'email': user.email
                        }
                    }, room=sid)
                    
                    return True
                    
                except Exception as e:
                    logger.error(f"Authentication failed for {sid}: {e}")
                    await self.sio.disconnect(sid)
                    return False
                    
            except Exception as e:
                logger.error(f"Connection error for {sid}: {e}")
                await self.sio.disconnect(sid)
                return False
        
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection."""
            user_id = self.user_sessions.pop(sid, None)
            if user_id:
                room_name = self.user_rooms.pop(user_id, None)
                if room_name:
                    await self.sio.leave_room(sid, room_name)
                logger.info(f"User {user_id} disconnected from session {sid}")
        
        @self.sio.event
        async def chat(sid, data):
            """Handle chat messages from clients."""
            try:
                user_id = self.user_sessions.get(sid)
                if not user_id:
                    await self.sio.emit('error', {
                        'message': 'Not authenticated'
                    }, room=sid)
                    return
                
                # Validate message data
                if not isinstance(data, dict) or 'message' not in data:
                    await self.sio.emit('error', {
                        'message': 'Invalid message format'
                    }, room=sid)
                    return
                
                message = data.get('message', '').strip()
                if not message:
                    await self.sio.emit('error', {
                        'message': 'Message cannot be empty'
                    }, room=sid)
                    return
                conversation_id = data.get('conversation_id')
                metadata = data.get('metadata', {})
                
                # Add socket session info to metadata
                metadata.update({
                    'socket_session': sid,
                    'realtime': True
                })
                
                logger.info(f"Processing chat message from user {user_id}: {message[:50]}...")
                
                # Create chat request
                chat_request = ChatRequest(
                    message=message,
                    conversation_id=conversation_id,
                    metadata=metadata
                )
                
                # Process message through chat service
                await self.chat_service.process_message(user_id, chat_request)
                
            except Exception as e:
                logger.error(f"Chat error for session {sid}: {e}")
                await self.sio.emit('error', {
                    'message': 'Failed to process message',
                    'error': str(e)
                }, room=sid)
        
        @self.sio.event
        async def join_conversation(sid, data):
            """Allow users to join specific conversation rooms."""
            try:
                user_id = self.user_sessions.get(sid)
                if not user_id:
                    await self.sio.emit('error', {
                        'message': 'Not authenticated'
                    }, room=sid)
                    return
                
                conversation_id = data.get('conversation_id')
                if not conversation_id:
                    await self.sio.emit('error', {
                        'message': 'Conversation ID required'
                    }, room=sid)
                    return
                
                # Verify user has access to this conversation
                conversation = await self.chat_service.conversation_service.get_user_conversation(
                    conversation_id, user_id
                )
                
                if not conversation:
                    await self.sio.emit('error', {
                        'message': 'Conversation not found or access denied'
                    }, room=sid)
                    return
                
                # Join conversation room
                room_name = f"conversation_{conversation_id}"
                await self.sio.enter_room(sid, room_name)
                
                await self.sio.emit('joined_conversation', {
                    'conversation_id': conversation_id,
                    'message': 'Joined conversation successfully'
                }, room=sid)
                
                logger.info(f"User {user_id} joined conversation {conversation_id}")
                
            except Exception as e:
                logger.error(f"Join conversation error for session {sid}: {e}")
                await self.sio.emit('error', {
                    'message': 'Failed to join conversation',
                    'error': str(e)
                }, room=sid)
        
        @self.sio.event
        async def leave_conversation(sid, data):
            """Allow users to leave conversation rooms."""
            try:
                conversation_id = data.get('conversation_id')
                if not conversation_id:
                    return
                
                room_name = f"conversation_{conversation_id}"
                await self.sio.leave_room(sid, room_name)
                
                await self.sio.emit('left_conversation', {
                    'conversation_id': conversation_id,
                    'message': 'Left conversation successfully'
                }, room=sid)
                
            except Exception as e:
                logger.error(f"Leave conversation error for session {sid}: {e}")
        
        @self.sio.event
        async def study_planning_team_chat(sid, data):
            """Handle study planning team chat messages."""
            try:
                user_id = self.user_sessions.get(sid)
                if not user_id:
                    await self.sio.emit('error', {
                        'message': 'Not authenticated'
                    }, room=sid)
                    return
                
                # Validate message data
                if not isinstance(data, dict) or 'message' not in data:
                    await self.sio.emit('error', {
                        'message': 'Invalid message format'
                    }, room=sid)
                    return
                
                message = data.get('message', '').strip()
                if not message:
                    await self.sio.emit('error', {
                        'message': 'Message cannot be empty'
                    }, room=sid)
                    return
                
                conversation_id = data.get('conversation_id')
                metadata = data.get('metadata', {})
                metadata.update({
                    'socket_session': sid,
                    'realtime': True,
                    'agent_type': 'study_planning'
                })
                
                # Step 1: Create a soulcare task in the database
                try:
                    task = await self.task_service.create_study_planning_task(
                        user_id=user_id,
                        user_message=message,
                        conversation_id=conversation_id,
                        metadata=metadata
                    )
                    task_id = str(task.id)
                    
                    logger.info(f"Created study planning task {task_id} for user {user_id} in conversation {task.conversation_id}")
                    
                    # Emit task created event
                    await self.sio.emit('task_created', {
                        'task_id': task_id,
                        'conversation_id': str(task.conversation_id),
                        'message': 'Study planning task created successfully'
                    }, room=sid)
                    
                except Exception as e:
                    logger.error(f"Failed to create Study planning task: {e}")
                    await self.sio.emit('error', {
                        'message': 'Failed to create Study planning task',
                        'error': str(e)
                    }, room=sid)
                    return
                
                # Step 2: Get the AutoGen LLM client and run soulcare team
                try:
                    autogen_client = self.get_autogen_llm_client()
                    
                    # Import and create SoulcareTeam
                    from app.agents.study_planning_team import StudyPlanningTeam
                    study_planning_team = StudyPlanningTeam(autogen_client)
                    if conversation_id:
                        agent_state = await self.task_service.get_conversation_state(conversation_id, user_id)
                        if agent_state:
                            await study_planning_team.load_state(agent_state)
                    
                    # Run soulcare conversation with Socket.IO streaming
                    result = await study_planning_team.run_conversation_with_socket(
                        user_message=message,
                        user_sid=sid,
                        task_id=task_id,
                        socketio_service=self
                    )
                    # Step 3: Save agent team state after completion
                    try:
                        agent_state = await study_planning_team.save_state()
                        
                        # Update task with agent state and conversation history
                        await self.task_service.update_task_with_agent_state(
                            task_id=task_id,
                            agent_state=agent_state,
                            status="completed" if result.get("success") else "failed",
                            error_message=result.get("error")
                        )
                        
                        logger.info(f"Updated task {task_id} with agent state and conversation history")
                        
                        # Emit final task completion
                        await self.sio.emit('task_updated', {
                            'task_id': task_id,
                            'status': 'completed' if result.get("success") else "failed",
                            'message': 'Task completed and state saved'
                        }, room=sid)
                        
                    except Exception as e:
                        logger.error(f"Failed to save agent state for task {task_id}: {e}")
                        # Still update task as completed but log the error
                        await self.task_service.update_task_with_agent_state(
                            task_id=task_id,
                            agent_state={"error": "Failed to save state"},
                            status="completed",
                            conversation_history=result.get("conversation_history", []),
                            error_message=f"State save error: {str(e)}"
                        )
                    
                except Exception as e:
                    logger.error(f"Study planning team error: {e}")
                    
                    # Update task as failed
                    await self.task_service.update_task_with_agent_state(
                        task_id=task_id,
                        agent_state={"error": "Study planning team failed"},
                        status="failed",
                        error_message=str(e)
                    )
                    
                    await self.sio.emit('error', {
                        'task_id': task_id,
                        'message': 'Failed to process study planning request',
                        'error': str(e)
                    }, room=sid)
                
            except Exception as e:
                logger.error(f"Study planning team chat error for session {sid}: {e}")
                await self.sio.emit('error', {
                    'message': 'Failed to process Study planning team message',
                    'error': str(e)
                }, room=sid)
    
    async def broadcast_to_conversation(self, conversation_id: str, event: str, data: dict):
        """Broadcast message to all users in a conversation."""
        room_name = f"conversation_{conversation_id}"
        await self.sio.emit(event, data, room=room_name)
    
    async def send_to_user(self, user_id: str, event: str, data: dict):
        """Send message to a specific user."""
        room_name = f"user_{user_id}"
        await self.sio.emit(event, data, room=room_name)
    
    def get_asgi_app(self):
        """Get the Socket.IO ASGI application."""
        return socketio.ASGIApp(self.sio)
    
    def get_autogen_llm_client(self):
        """Get the raw AutoGen LLM client for use in Socket.IO handlers."""
        if not self.llm_manager:
            raise RuntimeError("LLM manager not available in SocketIOService")
        
        client = self.llm_manager.get_client()
        if hasattr(client, 'client'):
            return client.client
        else:
            raise RuntimeError("Client does not have underlying AutoGen client")
    
    async def get_connected_users(self) -> Dict[str, str]:
        """Get currently connected users."""
        return self.user_sessions.copy()
    
    async def disconnect_user(self, user_id: str):
        """Disconnect a specific user."""
        sessions_to_disconnect = [
            sid for sid, uid in self.user_sessions.items() 
            if uid == user_id
        ]
        
        for sid in sessions_to_disconnect:
            await self.sio.disconnect(sid) 