"""
Telegram Bot API Router

Provides endpoints for Telegram bot management and status
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/status")
async def get_bot_status():
    """
    Get Telegram bot status and information
    
    Returns bot runtime status, configuration, and statistics
    """
    # Import bot instance from main
    from main import bot_instance, bot_task
    
    if not bot_instance:
        return {
            "status": "not_started",
            "message": "Telegram bot is not running. Check TELEGRAM_BOT_TOKEN configuration.",
            "running": False
        }
    
    # Get task status
    task_running = bot_task is not None and not bot_task.done()
    
    return {
        "status": "running" if task_running else "stopped",
        "running": task_running,
        "bot_info": {
            "username": "Check Telegram @BotFather",
            "supports_commands": ["/start", "/help", "/verify"],
            "features": [
                "Claim verification",
                "Source citations",
                "Confidence scoring",
                "Response caching",
                "Rich formatting"
            ]
        },
        "configuration": {
            "knowledge_base_path": bot_instance.rag_engine.knowledge_base_path if hasattr(bot_instance, 'rag_engine') else "N/A",
            "vector_db_path": bot_instance.rag_engine.vector_db_path if hasattr(bot_instance, 'rag_engine') else "N/A"
        },
        "message": "Bot is operational and processing messages" if task_running else "Bot task has stopped"
    }


@router.get("/info")
async def get_bot_info():
    """
    Get general information about the Telegram bot
    
    Returns bot capabilities and usage instructions
    """
    return {
        "name": "KnowInfo Fact-Checking Bot",
        "description": "AI-powered fact-checking bot for instant claim verification",
        "version": "1.0.0",
        "commands": {
            "/start": "Show welcome message and instructions",
            "/help": "Display detailed help and usage guide",
            "/verify <claim>": "Verify a specific claim"
        },
        "features": [
            "Real-time claim verification",
            "RAG-based source retrieval",
            "Multi-source consensus building",
            "Confidence scoring (0-100%)",
            "Priority detection (P0-P3)",
            "Source citations with links",
            "Response caching for performance",
            "Rich Telegram formatting"
        ],
        "usage": {
            "how_to_use": [
                "1. Open Telegram and find your bot",
                "2. Send /start to begin",
                "3. Send any claim text to verify it",
                "4. Receive instant verification results"
            ],
            "example": "Send: 'WHO says vaccines cause autism' → Receive verification with sources"
        },
        "documentation": {
            "user_guide": "TELEGRAM_BOT.md",
            "quick_start": "QUICKSTART_TELEGRAM.md"
        }
    }
