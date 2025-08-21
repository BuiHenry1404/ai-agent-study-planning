# Socket.IO Real-time Chat Integration

This document explains the Socket.IO integration for real-time chat functionality in the FastAPI Chatbot Template.

## 🚀 Features

- **Real-time messaging**: Send and receive chat messages instantly
- **JWT Authentication**: Secure WebSocket connections with JWT tokens
- **Room Management**: Join/leave conversation rooms for organized chat
- **User Sessions**: Track connected users and their sessions
- **Error Handling**: Graceful error handling with proper event responses
- **Test Client**: Built-in HTML test client for development

## 📋 Architecture

```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   Client        │◄──────────────►│  SocketIOService │
│   (Browser/App) │                │                 │
└─────────────────┘                └─────────────────┘
                                           │
                                           ▼
                                   ┌─────────────────┐
                                   │   ChatService   │
                                   │                 │
                                   └─────────────────┘
                                           │
                                           ▼
                                   ┌─────────────────┐
                                   │   MongoDB       │
                                   │   (Tasks &      │
                                   │   Conversations)│
                                   └─────────────────┘
```

## 🔧 Implementation Details

### SocketIOService

The `SocketIOService` class handles all Socket.IO functionality:

- **Authentication**: Validates JWT tokens on connection
- **Session Management**: Tracks user sessions and rooms
- **Event Handling**: Processes client events and emits responses
- **Chat Integration**: Integrates with existing chat services

### Key Components

1. **Connection Handler**: Authenticates users and manages sessions
2. **Chat Handler**: Processes chat messages and returns responses
3. **Room Management**: Handles joining/leaving conversation rooms
4. **Error Handling**: Manages errors and sends appropriate responses

## 📡 Socket.IO Events

### Client to Server

| Event | Description | Data Format |
|-------|-------------|-------------|
| `chat` | Send a chat message | `{message: string, conversation_id?: string, metadata?: object}` |
| `join_conversation` | Join a conversation room | `{conversation_id: string}` |
| `leave_conversation` | Leave a conversation room | `{conversation_id: string}` |

### Server to Client

| Event | Description | Data Format |
|-------|-------------|-------------|
| `connected` | Connection established | `{message: string, user: object}` |
| `conversation` | Chat response received | `{task_id: string, conversation_id: string, user_message: object, assistant_responses: array}` |
| `error` | Error occurred | `{message: string, error?: string}` |
| `joined_conversation` | Successfully joined conversation | `{conversation_id: string, message: string}` |
| `left_conversation` | Successfully left conversation | `{conversation_id: string, message: string}` |

## 🔐 Authentication

Socket.IO connections require JWT authentication:

```javascript
const socket = io('http://localhost:8000', {
    auth: {
        token: 'your_jwt_token_here'
    }
});
```

The server validates the token and stores the user session for subsequent events.

## 💻 Usage Examples

### JavaScript Client

```javascript
// Connect with authentication
const socket = io('http://localhost:8000', {
    auth: { token: jwtToken }
});

// Listen for connection success
socket.on('connected', (data) => {
    console.log('Connected:', data.user.username);
});

// Send a chat message
socket.emit('chat', {
    message: 'Hello, chatbot!',
    conversation_id: 'optional_conversation_id',
    metadata: { client: 'web_app' }
});

// Listen for chat responses
socket.on('conversation', (data) => {
    console.log('User message:', data.user_message.content);
    data.assistant_responses.forEach(msg => {
        console.log('Bot response:', msg.content);
    });
});

// Handle errors
socket.on('error', (error) => {
    console.error('Socket error:', error.message);
});

// Join a conversation room
socket.emit('join_conversation', {
    conversation_id: 'some_conversation_id'
});
```

### Python Client

```python
import socketio
import asyncio

sio = socketio.AsyncClient()

@sio.event
async def connect():
    print('Connected to server')

@sio.event
async def conversation(data):
    print(f"User: {data['user_message']['content']}")
    for response in data['assistant_responses']:
        print(f"Bot: {response['content']}")

@sio.event
async def error(data):
    print(f"Error: {data['message']}")

async def main():
    await sio.connect('http://localhost:8000', auth={'token': 'your_jwt_token'})
    
    # Send a message
    await sio.emit('chat', {
        'message': 'Hello from Python!',
        'metadata': {'client': 'python_client'}
    })
    
    await sio.wait()

if __name__ == '__main__':
    asyncio.run(main())
```

## 🧪 Testing

### Test Client

Access the built-in test client at: `http://localhost:8000/static/socketio_test.html`

Features:
- Login to get JWT token
- Connect/disconnect from Socket.IO
- Send chat messages
- Join/leave conversation rooms
- View raw event logs
- Real-time message display

### Testing Steps

1. **Start the server**:
   ```bash
   uv run uvicorn main:app --reload --port 8000
   ```

2. **Create a test user**:
   ```bash
   uv run python create_test_user.py
   ```

3. **Open test client**: Visit `http://localhost:8000/static/socketio_test.html`

4. **Login**: Use credentials `testuser` / `testpass123`

5. **Connect**: Click "Connect" with the generated JWT token

6. **Chat**: Send messages and see real-time responses

### Automated Testing

```python
import pytest
import socketio
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
async def socket_client():
    # Get JWT token for test user
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = response.json()["access_token"]
    
    # Create Socket.IO client
    sio = socketio.AsyncClient()
    await sio.connect('http://localhost:8000', auth={'token': token})
    yield sio
    await sio.disconnect()

@pytest.mark.asyncio
async def test_chat_message(socket_client):
    sio = socket_client
    
    # Send a chat message
    await sio.emit('chat', {'message': 'Test message'})
    
    # Wait for response
    response = await sio.receive()
    assert response[0] == 'conversation'
    assert 'task_id' in response[1]
    assert 'user_message' in response[1]
```

## 🔧 Configuration

### Environment Variables

```env
# CORS for Socket.IO (adjust as needed)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:8000
```

### Socket.IO Server Options

```python
self.sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",  # Configure based on your security needs
    logger=False,              # Disable to avoid log conflicts
    engineio_logger=False
)
```

## 🛡️ Security Considerations

1. **JWT Validation**: All connections must provide valid JWT tokens
2. **User Isolation**: Users can only access their own conversations
3. **CORS Configuration**: Configure allowed origins appropriately
4. **Rate Limiting**: Consider implementing rate limiting for production
5. **Error Sanitization**: Don't leak sensitive information in error messages

## 🚀 Production Deployment

### Scaling Considerations

1. **Multiple Workers**: Socket.IO supports multiple workers with Redis adapter
2. **Load Balancing**: Use sticky sessions for WebSocket connections
3. **Redis Integration**: For multi-instance deployments

```python
# For production with Redis
import socketio

# Create Redis manager
mgr = socketio.AsyncRedisManager('redis://localhost:6379')

# Initialize with manager
sio = socketio.AsyncServer(
    async_mode='asgi',
    client_manager=mgr
)
```

### Docker Configuration

```dockerfile
# Ensure WebSocket ports are exposed
EXPOSE 8000

# For production with Redis
ENV REDIS_URL=redis://redis:6379
```

## 📊 Monitoring

### Metrics to Track

1. **Connection Count**: Number of active Socket.IO connections
2. **Message Rate**: Messages per second
3. **Error Rate**: Socket.IO errors and disconnections
4. **Response Time**: Chat message processing time

### Logging

```python
# Structured logging in SocketIOService
logger.info(
    "Chat message processed",
    user_id=user_id,
    task_id=response.task_id,
    message_length=len(message),
    processing_time_ms=processing_time
)
```

## 🐛 Troubleshooting

### Common Issues

1. **Connection Failed**: Check JWT token validity
2. **CORS Errors**: Verify allowed origins configuration
3. **Message Not Received**: Check if user is in correct room
4. **Authentication Errors**: Ensure token includes required user ID

### Debug Mode

Enable Socket.IO logging for debugging:

```python
self.sio = socketio.AsyncServer(
    async_mode='asgi',
    logger=True,        # Enable for debugging
    engineio_logger=True
)
```

## 📈 Performance Tips

1. **Room Management**: Use rooms to limit message broadcast scope
2. **Message Batching**: Batch multiple messages when possible
3. **Connection Pooling**: Reuse database connections efficiently
4. **Caching**: Cache frequently accessed conversation data

## 🔄 Future Enhancements

- **Typing Indicators**: Show when users are typing
- **Read Receipts**: Track message read status
- **File Sharing**: Support file uploads in chat
- **Presence Status**: Show online/offline user status
- **Push Notifications**: Integrate with push notification services
- **Chat History**: Real-time sync of chat history
- **Multi-language**: Support for multiple languages

## 📚 Resources

- [Socket.IO Documentation](https://socket.io/docs/)
- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/)
- [Python Socket.IO Documentation](https://python-socketio.readthedocs.io/)
- [JWT Authentication Best Practices](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)

---

The Socket.IO integration provides a robust foundation for real-time chat functionality while maintaining security and scalability. Use the test client to explore the features and adapt the implementation to your specific needs! 