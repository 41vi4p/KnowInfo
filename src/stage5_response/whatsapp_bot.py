"""
WhatsApp Bot using PyWhatKit (100% FREE - No Twilio needed!)

PyWhatKit uses WhatsApp Web - completely free, no limits!
"""
import asyncio
from typing import Optional
import structlog
import pywhatkit as kit
from datetime import datetime, timedelta
import time
import re

from ..stage2_extraction.claim_extractor import ClaimExtractor
from ..stage3_verification.rag_engine import RAGEngine
from ..models.content import Content, SourcePlatform
from ..models.verification import VerificationResult
from ..database.redis_cache import get_redis
from ..utils.metrics import whatsapp_queries_total, whatsapp_response_duration_seconds

logger = structlog.get_logger(__name__)


class WhatsAppBot:
    """
    FREE WhatsApp bot using PyWhatKit

    No API costs, no Twilio - uses WhatsApp Web!

    How it works:
    1. User sends message to your WhatsApp number
    2. You forward it to the bot's monitoring system
    3. Bot verifies claim
    4. Bot sends response via WhatsApp Web

    Requirements:
    - WhatsApp Web logged in on the server
    - Python with GUI access (for automation)
    """

    def __init__(
        self,
        knowledge_base_path: str,
        vector_db_path: str,
        phone_number: str = None
    ):
        """
        Initialize WhatsApp bot

        Args:
            knowledge_base_path: Path to knowledge base
            vector_db_path: Path to vector database
            phone_number: Your WhatsApp number (with country code, e.g., +1234567890)
        """
        self.phone_number = phone_number
        self.claim_extractor = ClaimExtractor()
        self.rag_engine = RAGEngine(knowledge_base_path, vector_db_path)

        logger.info("WhatsApp bot initialized (PyWhatKit)", phone=phone_number)

    async def send_message(
        self,
        phone_number: str,
        message: str,
        wait_time: int = 15,
        tab_close: bool = True
    ):
        """
        Send WhatsApp message using PyWhatKit

        Args:
            phone_number: Recipient's phone number (with country code)
            message: Message to send
            wait_time: Seconds to wait before sending (default 15)
            tab_close: Close tab after sending (default True)
        """
        try:
            # Calculate send time (current time + wait_time seconds)
            send_time = datetime.now() + timedelta(seconds=wait_time)
            hour = send_time.hour
            minute = send_time.minute

            logger.info(
                "Scheduling WhatsApp message",
                to=phone_number,
                send_at=f"{hour}:{minute}",
                preview=message[:50]
            )

            # Send via WhatsApp Web
            kit.sendwhatmsg(
                phone_number,
                message,
                hour,
                minute,
                wait_time=wait_time,
                tab_close=tab_close
            )

            logger.info("Message sent", to=phone_number)

        except Exception as e:
            logger.error("Failed to send WhatsApp message", error=str(e))
            raise

    async def send_instant_message(
        self,
        phone_number: str,
        message: str
    ):
        """
        Send message instantly (requires WhatsApp Web already open)

        Args:
            phone_number: Recipient's phone number
            message: Message to send
        """
        try:
            logger.info(
                "Sending instant WhatsApp message",
                to=phone_number,
                preview=message[:50]
            )

            # Send instantly (WhatsApp Web must be open)
            kit.sendwhatmsg_instantly(
                phone_number,
                message,
                wait_time=10,
                tab_close=True
            )

            logger.info("Instant message sent", to=phone_number)

        except Exception as e:
            logger.error("Failed to send instant message", error=str(e))
            raise

    async def verify_and_respond(
        self,
        phone_number: str,
        claim_text: str
    ) -> VerificationResult:
        """
        Verify a claim and send response via WhatsApp

        Args:
            phone_number: User's phone number
            claim_text: Claim to verify

        Returns:
            VerificationResult
        """
        start_time = time.time()

        # Log query
        whatsapp_queries_total.inc()

        try:
            # Check cache first
            redis = await get_redis()
            cached_result = await redis.get_cached_verification(claim_text)

            if cached_result:
                logger.info(
                    "Cache hit",
                    phone=phone_number,
                    claim=claim_text[:50]
                )
                verification = VerificationResult(**cached_result)
                response = verification.to_whatsapp_response()
                response += "\n\n💾 Cached result"
                await self.send_instant_message(phone_number, response)
                return verification

            # Send "processing" message
            await self.send_instant_message(
                phone_number,
                "🔍 Analyzing your claim...\n"
                "⏳ Checking authoritative sources...\n"
                "⏱️ This usually takes < 60 seconds"
            )

            # Create content object
            content = Content(
                source=SourcePlatform.WHATSAPP,
                platform_id=f"whatsapp_{phone_number}_{int(time.time())}",
                text=claim_text,
                author_id=phone_number,
                author_username=phone_number,
                created_at=datetime.utcnow()
            )

            # Extract claims
            claims = await self.claim_extractor.extract_claims(content)

            if not claims:
                await self.send_instant_message(
                    phone_number,
                    "❓ *No verifiable claims found*\n\n"
                    "I couldn't identify any specific factual claims to verify. "
                    "Try rephrasing as a clear statement.\n\n"
                    "Example: 'WHO says vaccines cause autism'"
                )
                return None

            # Verify first claim
            verification = await self.rag_engine.verify_claim(claims[0])

            # Cache result
            await redis.cache_verification(claim_text, verification.dict())

            # Format and send response
            response = verification.to_whatsapp_response()
            await self.send_instant_message(phone_number, response)

            # Record metrics
            duration = time.time() - start_time
            whatsapp_response_duration_seconds.observe(duration)

            logger.info(
                "Verification completed",
                phone=phone_number,
                status=verification.status,
                confidence=verification.confidence_score,
                duration=duration
            )

            return verification

        except Exception as e:
            logger.error(
                "Verification failed",
                phone=phone_number,
                error=str(e)
            )

            await self.send_instant_message(
                phone_number,
                "❌ *Error*\n\n"
                "Sorry, something went wrong while verifying your claim. "
                "Please try again in a moment."
            )
            raise


class WhatsAppQueueProcessor:
    """
    Process incoming WhatsApp queries from a queue

    This allows you to:
    1. Receive queries via API/webhook
    2. Queue them in Redis
    3. Process them asynchronously
    """

    def __init__(
        self,
        knowledge_base_path: str,
        vector_db_path: str
    ):
        self.bot = WhatsAppBot(knowledge_base_path, vector_db_path)

    async def process_queue(self):
        """
        Continuously process WhatsApp query queue
        """
        redis = await get_redis()

        logger.info("WhatsApp queue processor started")

        while True:
            try:
                # Get next query from queue
                task = await redis.dequeue_task("whatsapp_queries")

                if task:
                    phone_number = task.get("phone_number")
                    claim_text = task.get("claim_text")

                    logger.info(
                        "Processing WhatsApp query",
                        phone=phone_number,
                        claim=claim_text[:50]
                    )

                    # Verify and respond
                    await self.bot.verify_and_respond(phone_number, claim_text)

                else:
                    # No tasks, wait a bit
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error("Queue processing error", error=str(e))
                await asyncio.sleep(5)


# Helper function to queue a WhatsApp query
async def queue_whatsapp_query(phone_number: str, claim_text: str):
    """
    Queue a WhatsApp query for processing

    Args:
        phone_number: User's phone number (with country code)
        claim_text: Claim to verify
    """
    redis = await get_redis()
    await redis.enqueue_task("whatsapp_queries", {
        "phone_number": phone_number,
        "claim_text": claim_text,
        "timestamp": datetime.utcnow().isoformat()
    })
    logger.info("Query queued", phone=phone_number)


# Simple CLI for testing
async def test_whatsapp_bot():
    """Test WhatsApp bot interactively"""
    from ..database.mongodb import init_mongo
    from ..database.redis_cache import init_redis
    from ..utils.model_manager import init_model_manager
    from config import settings

    print("\n" + "="*80)
    print("WhatsApp Bot Test (PyWhatKit - FREE!)")
    print("="*80 + "\n")

    print("⚠️  Requirements:")
    print("1. WhatsApp Web must be logged in on this computer")
    print("2. GUI environment (not headless server)")
    print("3. Python has permission to control mouse/keyboard\n")

    # Initialize dependencies
    await init_mongo(settings.mongodb_uri, settings.mongodb_db_name)
    await init_redis(settings.redis_url)
    init_model_manager(
        ollama_base_url=settings.ollama_base_url,
        gemini_api_key=settings.gemini_api_key,
        use_local_first=settings.use_local_models_first
    )

    # Create bot
    bot = WhatsAppBot(
        knowledge_base_path="./data/knowledge_base",
        vector_db_path="./data/vector_db"
    )

    # Get user input
    phone = input("Enter recipient phone number (with country code, e.g., +1234567890): ").strip()
    claim = input("Enter claim to verify: ").strip()

    print("\n🔄 Verifying and sending response...")
    print("⏰ WhatsApp Web will open automatically in 15 seconds...\n")

    # Verify and send
    result = await bot.verify_and_respond(phone, claim)

    print("\n✅ Done!")
    print(f"Status: {result.status}")
    print(f"Confidence: {result.confidence_score}%")


if __name__ == "__main__":
    asyncio.run(test_whatsapp_bot())
