#!/bin/bash

# KnowInfo Quick Start Script
# This script sets up the development environment

set -e

echo "========================================="
echo "KnowInfo Quick Start Setup"
echo "========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi
echo "✅ Docker found"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
echo "✅ Docker Compose found"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+."
    exit 1
fi
echo "✅ Python 3 found"

echo ""
echo "========================================="
echo "Step 1: Setting up environment"
echo "========================================="

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys!"
    echo "   At minimum, set GEMINI_API_KEY or configure Ollama"
else
    echo ".env file already exists"
fi

echo ""
echo "========================================="
echo "Step 2: Creating data directories"
echo "========================================="

mkdir -p data/vector_db
mkdir -p data/knowledge_base
mkdir -p data/models

echo "✅ Data directories created"

echo ""
echo "========================================="
echo "Step 3: Installing Ollama on Host"
echo "========================================="

echo "Installing Ollama on your system (not Docker)..."
./scripts/install_ollama_host.sh

echo ""
echo "========================================="
echo "Step 4: Starting infrastructure services"
echo "========================================="

echo "Starting MongoDB, Neo4j, and Redis..."
docker-compose up -d mongodb neo4j redis

echo "Waiting for services to be ready..."
sleep 10

# Check MongoDB
echo -n "Checking MongoDB... "
if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo "✅"
else
    echo "❌ MongoDB not ready"
fi

# Check Neo4j
echo -n "Checking Neo4j... "
sleep 5  # Neo4j takes longer to start
if docker-compose exec -T neo4j cypher-shell -u neo4j -p knowinfo_password "RETURN 1" > /dev/null 2>&1; then
    echo "✅"
else
    echo "⚠️  Neo4j may still be starting (this is normal on first run)"
fi

# Check Redis
echo -n "Checking Redis... "
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅"
else
    echo "❌ Redis not ready"
fi

# Check Ollama (on host)
echo -n "Checking Ollama (host system)... "
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅"
else
    echo "⚠️  Ollama may not be started. Run: sudo systemctl start ollama"
fi

echo ""
echo "========================================="
echo "Step 5: Installing Python dependencies"
echo "========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm

echo "✅ Python dependencies installed"

echo ""
echo "========================================="
echo "Step 6: Seeding knowledge base"
echo "========================================="

echo "Seeding initial authoritative sources..."
python scripts/seed_knowledge_base.py

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your API keys (if using cloud models)"
echo "   - GEMINI_API_KEY (recommended)"
echo "   - or OPENAI_API_KEY"
echo "   - Social media API keys for monitoring"
echo ""
echo "2. Start the API server:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "3. Access the system:"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Neo4j Browser: http://localhost:7474 (user: neo4j, pass: knowinfo_password)"
echo "   - Health Check: http://localhost:8000/health"
echo ""
echo "4. View logs:"
echo "   docker-compose logs -f"
echo ""
echo "5. Stop services:"
echo "   docker-compose down"
echo ""
echo "For detailed implementation guide, see IMPLEMENTATION_GUIDE.md"
echo ""
