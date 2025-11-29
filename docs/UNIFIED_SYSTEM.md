# Unified System Startup Guide

## Overview

The KnowInfo system now runs **both** the FastAPI server **and** the Telegram bot in a single unified process!

## Quick Start

### Start Everything Together

```bash
# Activate conda environment
conda activate knowinfo

# Start unified system (BOTH API + Bot)
python main.py
```

This single command starts:
- ✅ FastAPI server (port 8000)
- ✅ Telegram bot (background task)
- ✅ All databases (MongoDB, Redis, Neo4j)
- ✅ Model manager (Gemini/Ollama)

## What Changed

### Before
```bash
# Had to run separately
python main.py          # API only
python run_telegram_bot.py  # Bot only
```

### Now
```bash
# One command for everything!
python main.py
```

## Architecture

```
┌─────────────────────────────────────┐
│        FastAPI Application          │
│  ┌──────────────┐ ┌──────────────┐ │
│  │  API Server  │ │ Telegram Bot │ │  
│  │  (Port 8000) │ │(Background)  │ │
│  └──────┬───────┘ └───────┬──────┘ │
│         │                  │         │
│         └──────┬───────────┘         │
│                │                     │
│    ┌───────────▼──────────┐         │
│    │  Shared Resources    │         │
│    │  - MongoDB           │         │
│    │  - Redis             │         │
│    │  - Neo4j            │         │
│    │  - Model Manager    │         │
│    │  - RAG Engine       │         │
│    └─────────────────────┘         │
└─────────────────────────────────────┘
```

## New API Endpoints

### `/api/telegram/status`
Get Telegram bot status and configuration
```bash
curl http://localhost:8000/api/telegram/status
```

Response:
```json
{
  "status": "running",
  "running": true,
  "bot_info": {
    "supports_commands": ["/start", "/help", "/verify"]
  }
}
```

### `/api/telegram/info`
Get bot information and usage guide
```bash
curl http://localhost:8000/api/telegram/info
```

### `/health` (Updated)
Now includes Telegram bot status
```bash
curl http://localhost:8000/health
```

Response includes:
```json
{
  "components": {
    "mongodb": "healthy",
    "redis": "healthy",
    "neo4j": "healthy",
    "telegram_bot": "running"
  }
}
```

## Using the System

### 1. Start the Unified System
```bash
conda activate knowinfo
python main.py
```

Output:
```
INFO: Starting KnowInfo system
INFO: MongoDB initialized
INFO: Redis initialized  
INFO: Neo4j initialized
INFO: Model manager initialized
INFO: Starting Telegram bot
INFO: Telegram bot started as background task
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 2. Use the API
```bash
# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# Check bot status
curl http://localhost:8000/api/telegram/status
```

### 3. Use the Telegram Bot
1. Open Telegram app
2. Search for your bot
3. Send `/start`
4. Send claims to verify!

### 4. Stop the System
Press `Ctrl+C` in the terminal - both API and bot will shutdown gracefully.

## Benefits

✅ **Simpler deployment** - One process, one command
✅ **Shared resources** - No duplicate connections
✅ **Unified logging** - All logs in one place
✅ **Better monitoring** - Single health check
✅ **Docker ready** - One container for everything
✅ **Less memory** - Shared model manager

## Environment Variables

All configured in `.env`:
```bash
# Required
TELEGRAM_BOT_TOKEN=your_token

# Databases (already configured)
MONGODB_URI=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687

# LLM Provider (at least one)
GEMINI_API_KEY=your_key
```

## Troubleshooting

### Bot doesn't start
- Check `TELEGRAM_BOT_TOKEN` is set in `.env`
- Look for errors in startup logs
- Bot will log warning if token missing

### API works but bot doesn't
- Check `/api/telegram/status` endpoint
- Verify bot token is valid
- Check Telegram app for bot messages

### Neither starts
- Check databases are running: `docker ps`
- Verify conda environment: `conda activate knowinfo`
- Check for port conflicts on 8000

## Legacy Support

The standalone `run_telegram_bot.py` still works if you need to run just the bot:

```bash
python run_telegram_bot.py  # Bot only (no API)
```

But the recommended approach is to use `main.py` for everything!

## Next Steps

1. **Development**: `python main.py` and you're ready!
2. **Production**: Use `docker-compose up` or systemd service
3. **Monitoring**: Check `/health` and `/metrics` endpoints

---

**That's it! One command, full system. Happy fact-checking! 🚀**
