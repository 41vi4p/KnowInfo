"""
Telegram Bot for Fact-Checking (FREE Alternative to WhatsApp)

Telegram Bot API is 100% FREE with no message limits!
"""
import asyncio
from typing import Optional
import structlog
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from ..stage2_extraction.claim_extractor import ClaimExtractor
from ..stage3_verification.rag_engine import RAGEngine
from ..models.content import Content, SourcePlatform
from ..models.verification import VerificationResult
from ..database.redis_cache import get_redis
from ..utils.metrics import whatsapp_queries_total, whatsapp_response_duration_seconds
from datetime import datetime
import time

logger = structlog.get_logger(__name__)


class TelegramFactCheckBot:
    """
    FREE Telegram bot for fact-checking

    No cost, unlimited messages, better features than WhatsApp!
    """

    def __init__(
        self,
        token: str,
        knowledge_base_path: str,
        vector_db_path: str
    ):
        """
        Initialize Telegram bot

        Args:
            token: Telegram bot token (get from @BotFather)
            knowledge_base_path: Path to knowledge base
            vector_db_path: Path to vector database
        """
        self.token = token
        self.claim_extractor = ClaimExtractor()
        self.rag_engine = RAGEngine(knowledge_base_path, vector_db_path)

        # Create application
        self.app = Application.builder().token(token).build()

        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("verify", self.verify_command))
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message
        ))

        logger.info("Telegram bot initialized")

    async def start_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /start command"""
        welcome_message = """
🤖 **KnowInfo Fact-Checking Bot**

Send me any claim or message, and I'll verify it against authoritative sources!

**Commands:**
/start - Show this message
/help - Get help
/verify <claim> - Verify a specific claim

**Just send any text** and I'll check it for you!

Powered by AI • Free Forever • No Limits
        """
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown'
        )

    async def help_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /help command"""
        help_message = """
📚 **How to Use**

1️⃣ **Send a claim**: Just type any message
   Example: "WHO says vaccines are dangerous"

2️⃣ **Get instant verification**:
   • ✅ TRUE - Claim is accurate
   • ❌ FALSE - Claim is incorrect
   • ⚠️ MISLEADING - Partially true/false
   • 🔍 UNVERIFIED - Cannot verify

3️⃣ **Understand why**: Read the explanation

**Response Time**: Usually < 60 seconds

**Tip**: Forward messages from other chats to verify them!
        """
        await update.message.reply_text(
            help_message,
            parse_mode='Markdown'
        )

    async def verify_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /verify command"""
        if not context.args:
            await update.message.reply_text(
                "❓ Please provide a claim to verify.\n\n"
                "Example: `/verify WHO recommends vaccines`",
                parse_mode='Markdown'
            )
            return

        claim_text = " ".join(context.args)
        await self.verify_claim(update, claim_text)

    async def handle_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle regular text messages"""
        message_text = update.message.text

        # Log query
        whatsapp_queries_total.inc()

        # Send "typing" indicator
        await update.message.chat.send_action("typing")

        # Verify claim
        await self.verify_claim(update, message_text)

    async def verify_claim(self, update: Update, claim_text: str):
        """
        Verify a claim and send response

        Args:
            update: Telegram update object
            claim_text: Claim to verify
        """
        start_time = time.time()
        user_id = update.effective_user.id

        try:
            # Check cache first
            redis = await get_redis()
            cached_result = await redis.get_cached_verification(claim_text)

            if cached_result:
                logger.info(
                    "Cache hit",
                    user_id=user_id,
                    claim=claim_text[:50]
                )
                await self._send_verification_response(
                    update,
                    cached_result,
                    from_cache=True
                )
                return

            # Send "processing" message
            processing_msg = await update.message.reply_text(
                "🔍 Analyzing claim...\n"
                "⏳ Checking authoritative sources..."
            )

            # Create content object
            content = Content(
                source=SourcePlatform.WHATSAPP,
                platform_id=f"telegram_{user_id}_{int(time.time())}",
                text=claim_text,
                author_id=str(user_id),
                author_username=update.effective_user.username or "unknown",
                created_at=datetime.utcnow()
            )

            # Extract claims
            claims = await self.claim_extractor.extract_claims(content)

            if not claims:
                await processing_msg.edit_text(
                    "❓ **No verifiable claims found**\n\n"
                    "I couldn't identify any specific factual claims to verify. "
                    "Try rephrasing as a clear statement.\n\n"
                    "Example: 'WHO says vaccines cause autism'"
                )
                return

            # Verify first claim
            verification = await self.rag_engine.verify_claim(claims[0])

            # Cache result
            await redis.cache_verification(claim_text, verification.dict())

            # Delete processing message
            await processing_msg.delete()

            # Send verification response
            await self._send_verification_response(update, verification)

            # Record metrics
            duration = time.time() - start_time
            whatsapp_response_duration_seconds.observe(duration)

            logger.info(
                "Verification completed",
                user_id=user_id,
                status=verification.status,
                confidence=verification.confidence_score,
                duration=duration
            )

        except Exception as e:
            logger.error(
                "Verification failed",
                user_id=user_id,
                error=str(e)
            )
            await update.message.reply_text(
                "❌ **Error**\n\n"
                "Sorry, something went wrong while verifying your claim. "
                "Please try again in a moment."
            )

    async def _send_verification_response(
        self,
        update: Update,
        verification: dict,
        from_cache: bool = False
    ):
        """
        Format and send verification response

        Args:
            update: Telegram update object
            verification: Verification result (dict or VerificationResult)
            from_cache: Whether result is from cache
        """
        # Handle both dict and VerificationResult
        if isinstance(verification, dict):
            status = verification['status']
            confidence = verification['confidence_score']
            explanation = verification['explanation']
            sources = verification.get('sources', [])
        else:
            status = verification.status
            confidence = verification.confidence_score
            explanation = verification.explanation
            sources = verification.sources

        # Get emoji for status
        emoji_map = {
            'true': '✅',
            'false': '❌',
            'misleading': '⚠️',
            'unverified': '🔍',
            'outdated': '📅'
        }
        emoji = emoji_map.get(status.lower(), '❓')

        # Build response
        response = f"{emoji} **{status.upper()}**\n\n"
        response += f"**Confidence**: {confidence:.0f}%\n\n"
        response += f"**Explanation**:\n{explanation}\n\n"

        # Add sources (top 2)
        if sources:
            response += "**Sources**:\n"
            for i, source in enumerate(sources[:2], 1):
                title = source.get('title', 'Unknown') if isinstance(source, dict) else source.title
                url = source.get('url', '') if isinstance(source, dict) else source.url
                if url:
                    response += f"{i}. [{title}]({url})\n"
                else:
                    response += f"{i}. {title}\n"

        if from_cache:
            response += "\n💾 _Cached result_"

        response += "\n\n🤖 _Powered by KnowInfo_"

        # Send response
        await update.message.reply_text(
            response,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    async def start(self):
        """Start the bot"""
        logger.info("Starting Telegram bot")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        logger.info("Telegram bot running")

    async def stop(self):
        """Stop the bot"""
        logger.info("Stopping Telegram bot")
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()


# Simple runner
async def run_telegram_bot(
    token: str,
    knowledge_base_path: str = "./data/knowledge_base",
    vector_db_path: str = "./data/vector_db"
):
    """
    Run Telegram bot

    Args:
        token: Telegram bot token
        knowledge_base_path: Path to knowledge base
        vector_db_path: Path to vector database
    """
    from ..database.mongodb import init_mongo
    from ..database.redis_cache import init_redis
    from ..utils.model_manager import init_model_manager
    from config import settings

    # Initialize dependencies
    await init_mongo(settings.mongodb_uri, settings.mongodb_db_name)
    await init_redis(settings.redis_url)
    init_model_manager(
        ollama_base_url=settings.ollama_base_url,
        gemini_api_key=settings.gemini_api_key,
        use_local_first=settings.use_local_models_first
    )

    # Create and start bot
    bot = TelegramFactCheckBot(token, knowledge_base_path, vector_db_path)

    try:
        await bot.start()
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bot.stop()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python telegram_bot.py <bot_token>")
        sys.exit(1)

    token = sys.argv[1]
    asyncio.run(run_telegram_bot(token))
