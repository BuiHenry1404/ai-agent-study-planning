# Development Guide

This guide will help your development team understand and work with the FastAPI Chatbot Template.

## 🏗️ Architecture Overview

The application follows a clean architecture pattern with clear separation of concerns:

```
app/
├── core/           # Configuration, security, logging
├── models/         # Pydantic models (MongoDB documents)
├── repositories/   # Database operations (CRUD)
├── services/       # Business logic (framework-agnostic)
├── api/            # FastAPI routes and dependencies
│   └── v1/
│       ├── routers/    # API endpoints
│       └── schemas.py  # Request/response models
└── utils/          # Utility functions
```

### Key Principles

1. **Services are framework-agnostic** - No FastAPI dependencies in service layer
2. **Repository pattern** - Database operations abstracted from business logic
3. **Dependency injection** - Resources injected via FastAPI's Depends
4. **Type safety** - Everything is type-hinted and validated

## 🚀 Quick Start

1. **Clone and setup**:
   ```bash
   ./setup.sh
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start with Docker** (recommended):
   ```bash
   docker-compose up --build
   ```

4. **Or start manually**:
   ```bash
   source venv/bin/activate
   # Start MongoDB separately
   uvicorn main:app --reload
   ```

## 📊 Data Models

### Core Entities

1. **User** - Authentication and user management
2. **Conversation** - Groups related tasks together
3. **Task** - Contains user message + chatbot responses
4. **ChatMessage** - Individual messages within tasks

### Relationships

- User → Conversations (1:many)
- Conversation → Tasks (1:many)
- Task → ChatMessages (1:many)

## 🔄 Typical Flow

1. **User sends message** → `/api/v1/chat/`
2. **System creates**:
   - New conversation (if needed)
   - New task with user message
3. **Background worker** adds assistant responses
4. **Frontend polls** or uses webhooks for updates

## 🛠️ Development Workflow

### Adding a New Feature

1. **Define models** in `app/models/`
2. **Create repository** in `app/repositories/`
3. **Implement service** in `app/services/`
4. **Add API schemas** in `app/api/v1/schemas.py`
5. **Create router** in `app/api/v1/routers/`
6. **Write tests** in `tests/`

### Example: Adding Categories

1. **Model** (`app/models/category.py`):
```python
class Category(BaseDocument):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    color: str = Field(default="#007bff")
    user_id: PyObjectId
```

2. **Repository** (`app/repositories/category.py`):
```python
class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Category, "categories")
    
    async def get_user_categories(self, user_id: str) -> List[Category]:
        return await self.find({"user_id": ObjectId(user_id)})
```

3. **Service** (`app/services/category.py`):
```python
class CategoryService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.category_repo = CategoryRepository(db)
    
    async def create_category(self, user_id: str, data: CategoryCreate) -> Category:
        category_dict = {
            "user_id": ObjectId(user_id),
            **data.dict()
        }
        return await self.category_repo.create(category_dict)
```

4. **Router** (`app/api/v1/routers/categories.py`):
```python
@router.post("/", response_model=CategoryResponse, status_code=201)
async def create_category(
    category_data: CategoryCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    service = CategoryService(db)
    category = await service.create_category(str(current_user.id), category_data)
    return CategoryResponse(**category.dict())
```

## 🧪 Testing

### Test Structure
```
tests/
├── conftest.py         # Fixtures and test configuration
├── test_auth.py        # Authentication tests
├── test_chat.py        # Chat functionality tests
├── test_tasks.py       # Task management tests
└── test_conversations.py  # Conversation tests
```

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=app

# Specific test file
pytest tests/test_auth.py -v

# Specific test
pytest tests/test_auth.py::TestAuth::test_login_success -v
```

### Writing Tests

Always use the provided fixtures:

```python
async def test_create_task(async_client: AsyncClient, test_user):
    response = await async_client.post(
        "/api/v1/tasks/",
        headers=test_user["headers"],
        json={"user_message": "Test message"}
    )
    assert response.status_code == 201
```

## 🔒 Security Best Practices

### Authentication Flow
1. User registers → password hashed with bcrypt
2. User logs in → JWT token issued
3. Protected routes → token validated via dependency injection

### Key Security Features
- Password hashing with bcrypt
- JWT tokens with configurable expiration
- CORS protection
- Input validation with Pydantic
- API key support for internal services

### Security Checklist
- [ ] Never log passwords or tokens
- [ ] Use HTTPS in production
- [ ] Set strong JWT secrets
- [ ] Configure CORS properly
- [ ] Validate all inputs
- [ ] Use dependency injection for auth

## 📝 Database Operations

### Using Repositories

```python
# In a service
async def get_user_tasks(self, user_id: str, status: str = None):
    filter_dict = {"user_id": ObjectId(user_id)}
    if status:
        filter_dict["status"] = status
    
    return await self.task_repo.find(filter_dict)
```

### Indexes

The application automatically creates indexes on startup. Add new indexes in repository `create_indexes()` methods:

```python
async def create_indexes(self):
    await self.collection.create_index([("user_id", 1), ("created_at", -1)])
    await self.collection.create_index("status")
```

## 🔧 Configuration

### Environment Variables

All configuration is in `app/core/config.py` using Pydantic Settings:

```python
class Settings(BaseSettings):
    # Add new settings here
    new_feature_enabled: bool = False
    external_api_url: str = "https://api.example.com"
    
    class Config:
        env_file = ".env"
```

### Development vs Production

- **Development**: Debug mode, detailed logs, auto-reload
- **Production**: Optimized, security headers, monitoring

## 📦 Deployment

### Docker (Recommended)

```bash
# Build and run
docker-compose up --build

# Production with external MongoDB
docker build -t chatbot-api .
docker run -p 8000:8000 --env-file .env chatbot-api
```

### Traditional Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🐛 Debugging

### Logging

The app uses structured logging. Add context to your logs:

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

logger.info("Processing task", task_id=task_id, user_id=user_id)
logger.error("Task failed", task_id=task_id, error=str(e))
```

### Common Issues

1. **MongoDB Connection**: Check `MONGO_URI` in `.env`
2. **JWT Errors**: Verify `JWT_SECRET` is set
3. **Import Errors**: Ensure `PYTHONPATH` includes project root
4. **Permission Errors**: Check file permissions in Docker

## 🚀 Performance Tips

1. **Database**:
   - Use appropriate indexes
   - Implement pagination for large datasets
   - Use projections to limit returned fields

2. **API**:
   - Use async/await consistently
   - Implement caching for frequently accessed data
   - Add rate limiting for public endpoints

3. **Monitoring**:
   - Use health check endpoints
   - Monitor response times
   - Track error rates

## 🤝 Contributing

### Code Style

We use:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

Run before committing:
```bash
black app/ tests/
ruff check app/ tests/
mypy app/
```

### Pull Request Process

1. Create feature branch from `main`
2. Write tests for new functionality
3. Ensure all tests pass
4. Update documentation if needed
5. Submit PR with clear description

### Commit Messages

Use conventional commits:
```
feat: add task categories
fix: resolve authentication bug
docs: update API documentation
test: add conversation tests
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Motor Documentation](https://motor.readthedocs.io/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [pytest Documentation](https://docs.pytest.org/)

## 🆘 Getting Help

1. Check the API docs at `/docs`
2. Review test cases for examples
3. Check logs for error details
4. Create an issue on the repository

Happy coding! 🚀 