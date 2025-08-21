#!/bin/bash

set -e

echo "🚀 Setting up FastAPI Chatbot Template..."

# Check if Python 3.9+ is installed
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "📍 Detected Python version: $python_version"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "✅ Python version is compatible"
else
    echo "❌ Python 3.9+ is required. Current version: $python_version"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before running the app"
else
    echo "✅ .env file already exists"
fi

# Check if MongoDB is running (optional)
echo "🔍 Checking MongoDB connection..."
if command -v mongosh &> /dev/null; then
    if mongosh --eval "db.runCommand('ping')" --quiet > /dev/null 2>&1; then
        echo "✅ MongoDB is running"
    else
        echo "⚠️  MongoDB is not running. Please start MongoDB or use Docker Compose"
    fi
else
    echo "⚠️  MongoDB client not found. Please ensure MongoDB is installed and running"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Start MongoDB (or use 'docker-compose up -d mongo')"
echo "3. Activate virtual environment: source venv/bin/activate"
echo "4. Run the application: uvicorn main:app --reload"
echo "5. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "For Docker setup:"
echo "  docker-compose up --build"
echo ""
echo "For running tests:"
echo "  pytest"
echo "" 