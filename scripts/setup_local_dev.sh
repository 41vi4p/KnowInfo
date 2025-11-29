#!/bin/bash
# Local Development Setup Script for KnowInfo
# This script sets up the Python environment to run directly on your laptop
# while databases run in Docker containers

set -e  # Exit on error

echo "================================================"
echo "KnowInfo Local Development Setup"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# # Check if Python 3.11+ is installed
# echo -e "${YELLOW}Checking Python version...${NC}"
# if ! command -v python3 &> /dev/null; then
#     echo -e "${RED}Error: Python 3 is not installed${NC}"
#     exit 1
# fi

# PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
# REQUIRED_VERSION="3.11"

# if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
#     echo -e "${RED}Error: Python 3.11+ is required. Current version: $PYTHON_VERSION${NC}"
#     exit 1
# fi

# echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"
# echo ""

# # Check if .env file exists
# if [ ! -f .env ]; then
#     echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
#     cp .env.example .env
#     echo -e "${GREEN}✓ .env file created${NC}"
#     echo -e "${YELLOW}⚠ Please edit .env file with your configuration${NC}"
# else
#     echo -e "${GREEN}✓ .env file already exists${NC}"
# fi
# echo ""

# # Create virtual environment
# echo -e "${YELLOW}Creating Python virtual environment...${NC}"
# if [ ! -d "venv" ]; then
#     python3 -m venv venv
#     echo -e "${GREEN}✓ Virtual environment created${NC}"
# else
#     echo -e "${GREEN}✓ Virtual environment already exists${NC}"
# fi
# echo ""

# # Activate virtual environment
# echo -e "${YELLOW}Activating virtual environment...${NC}"
# source venv/bin/activate
# echo -e "${GREEN}✓ Virtual environment activated${NC}"
# echo ""

# # Upgrade pip
# echo -e "${YELLOW}Upgrading pip...${NC}"
# pip install --upgrade pip --quiet
# echo -e "${GREEN}✓ pip upgraded${NC}"
# echo ""

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
echo -e "${YELLOW}This may take several minutes...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Create data directories
echo -e "${YELLOW}Creating data directories...${NC}"
mkdir -p data/vector_db data/knowledge_base data/models
echo -e "${GREEN}✓ Data directories created${NC}"
echo ""

# Check if Docker is running
echo -e "${YELLOW}Checking Docker status...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker and run this script again"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Start database containers
echo -e "${YELLOW}Starting database containers...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Database containers started${NC}"
echo ""

# Wait for databases to be ready
echo -e "${YELLOW}Waiting for databases to be ready...${NC}"
sleep 5

# Check MongoDB
echo -n "Checking MongoDB..."
until docker exec knowinfo-mongodb mongosh --eval "db.runCommand({ ping: 1 })" > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✓${NC}"

# Check Redis
echo -n "Checking Redis..."
until docker exec knowinfo-redis redis-cli ping > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✓${NC}"

# Check Neo4j
echo -n "Checking Neo4j..."
sleep 10  # Neo4j takes longer to start
echo -e " ${GREEN}✓${NC}"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit your .env file with your API keys and configuration"
echo "2. Activate the virtual environment: ${GREEN}source venv/bin/activate${NC}"
echo "3. Run the application: ${GREEN}uvicorn main:app --reload --host 0.0.0.0 --port 8000${NC}"
echo ""
echo -e "${YELLOW}Database access:${NC}"
echo "- MongoDB: mongodb://localhost:27017"
echo "- Neo4j Browser: http://localhost:7474 (user: neo4j, pass: knowinfo_password)"
echo "- Redis: localhost:6379"
echo ""
echo -e "${YELLOW}To stop databases:${NC} docker-compose down"
echo -e "${YELLOW}To view database logs:${NC} docker-compose logs -f"
echo ""
