# FastAPI Chatbot Template

A production-ready FastAPI template for building chatbot applications with task and conversation management using MongoDB.

## 🚀 Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **MongoDB Integration**: Async MongoDB operations with Motor
- **JWT Authentication**: Secure user authentication and authorization
- **Task Management**: Create and manage chatbot tasks with messages
- **Conversation Management**: Group related tasks into conversations
- **Structured Logging**: JSON logging with structured context
- **Auto Documentation**: Interactive API docs with Swagger UI
- **Production Ready**: Follows FastAPI best practices and security guidelines

## 🎯 Using This Template

This repository serves as a comprehensive template for FastAPI chatbot applications. Here's how to use it:

### Option 1: GitHub Template (Recommended)

1. **Click "Use this template"** button on GitHub
2. **Create your new repository** from this template
3. **Clone your new repository**:
   ```bash
   git clone https://github.com/your-username/your-new-project.git
   cd your-new-project
   ```

### Option 2: Fork and Clone

1. **Fork this repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/fastapi-agent-template.git
   cd fastapi-agent-template
   ```
3. **Remove the original remote and add your own**:
   ```bash
   git remote remove origin
   git remote add origin https://github.com/your-username/your-new-project.git
   ```

### Option 3: Direct Clone and Reset

1. **Clone this repository**:
   ```bash
   git clone https://github.com/original-owner/fastapi-agent-template.git your-project-name
   cd your-project-name
   ```
2. **Remove git history and start fresh**:
   ```bash
   rm -rf .git
   git init
   git add .
   git commit -m "Initial commit from FastAPI chatbot template"
   ```
3. **Add your own remote repository**:
   ```bash
   git remote add origin https://github.com/your-username/your-new-project.git
   git push -u origin main
   ```

### Customization Steps

After cloning the template:

1. **Update project information**:
   - Edit `pyproject.toml` - change name, description, authors
   - Update `README.md` with your project details
   - Modify `.env.example` with your default configurations

2. **Customize the application**:
   - Rename the project in `pyproject.toml` and imports if needed
   - Modify models in `app/models/` for your specific use case
   - Update API schemas in `app/api/v1/schemas.py`
   - Customize business logic in `app/services/`

3. **Configure for your environment**:
   - Set up your MongoDB connection
   - Configure JWT secrets and API keys
   - Update CORS origins for your frontend

## 📋 Requirements

- Python 3.9+
- MongoDB 4.4+
- Virtual environment support (python3-venv)

## 🛠️ Installation

### Option 1: Docker Setup (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd fastapi-chatbot-template
```

2. **Start with Docker Compose**
```bash
docker-compose up --build
```

This will start:
- FastAPI app on http://localhost:8000
- MongoDB on port 27017
- Mongo Express (DB admin) on http://localhost:8081

### Option 2: Manual Setup

1. **Install system dependencies** (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3.12-venv python3-pip mongodb
```

2. **Clone and setup**
```bash
git clone <repository-url>
cd fastapi-chatbot-template
```

3. **Run setup script**
```bash
chmod +x setup.sh
./setup.sh
```

4. **Create environment file**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start MongoDB**
```bash
docker run -d \
  --name mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  -p 27017:27017 \
  mongo:latest
```

6. **Run the application**
```bash
source venv/bin/activate
uvicorn main:app --reload
```

## 🔧 Configuration

Create a `.env` file with your settings:

```env
# Application
APP_NAME=chatbot-api
ENV=dev
DEBUG=true

# Database
MONGO_URI=mongodb://admin:password@localhost:27017/?authSource=admin&authMechanism=SCRAM-SHA-256
MONGO_DB_NAME=chatbot_db

# Security
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# API Keys
API_KEY=your-internal-api-key-change-this

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Logging
LOG_LEVEL=INFO
```

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## 🏗️ Architecture

The project follows a clean architecture pattern:

```
app/
├── core/           # Configuration, security, logging
├── models/         # Pydantic models for MongoDB documents
├── repositories/   # Database operations (CRUD)
├── services/       # Business logic (framework-agnostic)
├── api/            # FastAPI routes and dependencies
│   └── v1/
│       ├── routers/    # API endpoints
│       └── schemas.py  # Request/response models
└── utils/          # Utility functions
```

## 🎯 Usage Examples

### 1. User Registration and Authentication

```python
import httpx

# Register a new user
response = httpx.post("http://localhost:8000/api/v1/auth/register", json={
    "email": "user@example.com",
    "username": "johndoe",
    "password": "securepassword123",
    "full_name": "John Doe"
})

# Login to get access token
response = httpx.post("http://localhost:8000/api/v1/auth/login", json={
    "username": "johndoe",
    "password": "securepassword123"
})
token = response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}
```