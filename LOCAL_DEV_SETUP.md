# Local Development Setup

This guide explains how to run the KnowInfo Python application directly on your laptop while keeping databases in Docker containers.

## Architecture

- **Python/AI components**: Run directly on your laptop (easier debugging, faster iteration)
- **Databases**: Run in Docker containers (MongoDB, Neo4j, Redis)
- **Ollama**: Runs on your host system (GPU access)

## Prerequisites

1. **Python 3.11+** installed on your system
2. **Docker & Docker Compose** installed and running
3. **Git** (already installed)
4. **Ollama** (optional, for local AI models)

## Quick Start

### 1. Automated Setup (Recommended)

Run the setup script:

```bash
chmod +x scripts/setup_local_dev.sh
./scripts/setup_local_dev.sh
```

This script will:
- Check Python version
- Create a virtual environment
- Install all dependencies
- Create data directories
- Start database containers
- Wait for databases to be ready

### 2. Manual Setup

If you prefer to set up manually:

#### Step 1: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 2: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 3: Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
nano .env  # or use your preferred editor
```

#### Step 4: Start Databases

```bash
docker-compose up -d
```

This starts:
- MongoDB on `localhost:27017`
- Neo4j on `localhost:7474` (browser) and `localhost:7687` (bolt)
- Redis on `localhost:6379`

#### Step 5: Wait for Databases

```bash
# Wait about 10-15 seconds for all databases to initialize
# You can check status with:
docker-compose ps
docker-compose logs
```

## Running the Application

### Start the API Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run with auto-reload for development
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

### Access Databases

#### MongoDB
```bash
# Via Docker
docker exec -it knowinfo-mongodb mongosh

# Or use MongoDB Compass
mongodb://localhost:27017
```

#### Neo4j
- Browser: http://localhost:7474
- Username: `neo4j`
- Password: `knowinfo_password`

#### Redis
```bash
# Via Docker
docker exec -it knowinfo-redis redis-cli
```

## Development Workflow

### Starting Your Day

```bash
# 1. Start databases
docker-compose up -d

# 2. Activate Python environment
source venv/bin/activate

# 3. Run the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Ending Your Day

```bash
# Stop the API (Ctrl+C in the terminal)

# Stop databases (optional - they can keep running)
docker-compose down

# Or just stop without removing containers
docker-compose stop
```

### Making Changes

The `--reload` flag automatically restarts the server when you change Python files. Just save and test!

## Installing Ollama (Optional)

For local AI models without API costs:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull required models
ollama pull llama3.2
ollama pull nomic-embed-text

# Verify it's running
curl http://localhost:11434/api/tags
```

## Troubleshooting

### Database Connection Issues

**Problem**: Can't connect to databases

**Solution**:
```bash
# Check if containers are running
docker-compose ps

# Check logs
docker-compose logs mongodb
docker-compose logs neo4j
docker-compose logs redis

# Restart containers
docker-compose restart
```

### Port Already in Use

**Problem**: Port 8000, 27017, 7474, 7687, or 6379 already in use

**Solution**:
```bash
# Find what's using the port (example for 8000)
sudo lsof -i :8000

# Kill the process or change the port in docker-compose.yml
```

### Virtual Environment Issues

**Problem**: Dependencies not found

**Solution**:
```bash
# Make sure venv is activated (you should see (venv) in prompt)
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### spaCy Model Issues

**Problem**: spaCy model not found

**Solution**:
```bash
# The model should install with requirements.txt
# If not, install manually:
python -m spacy download en_core_web_sm
```

## Useful Commands

### Database Management

```bash
# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v

# Restart a specific service
docker-compose restart mongodb
```

### Python Environment

```bash
# Deactivate virtual environment
deactivate

# List installed packages
pip list

# Update a specific package
pip install --upgrade package_name
```

### Development Tools

```bash
# Run tests (if available)
pytest

# Format code (if black is installed)
black .

# Lint code (if flake8 is installed)
flake8 .
```

## Switching Back to Full Docker

If you want to run everything in Docker again:

1. Edit `docker-compose.yml`
2. Uncomment the `api` service section
3. Run:
```bash
docker-compose up --build
```

## Performance Tips

1. **Use SSD**: Store `data/` directory on SSD for better performance
2. **Allocate Docker Resources**: Give Docker enough RAM (4GB minimum, 8GB recommended)
3. **Use Ollama**: Avoid API costs and latency with local models
4. **Enable GPU**: If you have NVIDIA GPU, use it with Ollama for faster inference

## Next Steps

1. Check out the main [README.md](README.md) for project overview
2. Read [SYSTEM_FLOW.md](SYSTEM_FLOW.md) to understand the architecture
3. Start building your misinformation detection system!

## Getting Help

- Check Docker logs: `docker-compose logs -f`
- Check application logs: Look at console output where uvicorn is running
- Verify environment: `cat .env` (be careful not to expose secrets)
- Test database connections: Use the commands in "Access Databases" section
