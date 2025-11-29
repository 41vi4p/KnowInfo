"""
WhatsApp API endpoints for claim verification
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
import structlog

# Lazy import to avoid display issues
# from ..stage5_response.whatsapp_bot import WhatsAppBot, queue_whatsapp_query
from ..models.verification import VerificationResult
from ..utils.metrics import whatsapp_queries_total
from config import settings

logger = structlog.get_logger(__name__)

router = APIRouter()

# Global bot instance
whatsapp_bot = None


def get_whatsapp_bot():
    """Get or create WhatsApp bot instance (lazy import)"""
    global whatsapp_bot
    if whatsapp_bot is None:
        # Lazy import to avoid display connection issues on server start
        from ..stage5_response.whatsapp_bot import WhatsAppBot
        whatsapp_bot = WhatsAppBot(
            knowledge_base_path=settings.knowledge_base_path,
            vector_db_path=settings.vector_db_path
        )
    return whatsapp_bot


class WhatsAppVerifyRequest(BaseModel):
    """Request to verify a claim via WhatsApp"""
    phone_number: str = Field(..., description="Phone number with country code (e.g., +1234567890)")
    claim_text: str = Field(..., description="Claim text to verify")
    async_mode: bool = Field(default=False, description="Queue for async processing")


class WhatsAppVerifyResponse(BaseModel):
    """Response from WhatsApp verification"""
    success: bool
    message: str
    verification: Optional[VerificationResult] = None
    queued: bool = False


@router.post("/verify", response_model=WhatsAppVerifyResponse)
async def verify_claim(
    request: WhatsAppVerifyRequest,
    background_tasks: BackgroundTasks
):
    """
    Verify a claim and send response via WhatsApp

    **Modes:**
    - **Synchronous** (async_mode=false): Immediate verification and response
    - **Asynchronous** (async_mode=true): Queue for background processing

    **Example:**
    ```json
    {
        "phone_number": "+1234567890",
        "claim_text": "WHO says vaccines cause autism",
        "async_mode": false
    }
    ```
    """
    try:
        whatsapp_queries_total.inc()

        logger.info(
            "WhatsApp verification request",
            phone=request.phone_number,
            claim=request.claim_text[:50],
            async_mode=request.async_mode
        )

        if request.async_mode:
            # Queue for background processing
            from ..stage5_response.whatsapp_bot import queue_whatsapp_query
            await queue_whatsapp_query(request.phone_number, request.claim_text)
            return WhatsAppVerifyResponse(
                success=True,
                message="Query queued for processing. You will receive a WhatsApp message shortly.",
                queued=True
            )
        else:
            # Immediate processing
            bot = get_whatsapp_bot()
            verification = await bot.verify_and_respond(
                phone_number=request.phone_number,
                claim_text=request.claim_text
            )

            return WhatsAppVerifyResponse(
                success=True,
                message="Verification completed and response sent",
                verification=verification
            )

    except Exception as e:
        logger.error("WhatsApp verification failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-message")
async def send_message(
    phone_number: str,
    message: str
):
    """
    Send a custom WhatsApp message

    **Parameters:**
    - phone_number: Recipient's phone number with country code
    - message: Message text to send
    """
    try:
        bot = get_whatsapp_bot()
        await bot.send_instant_message(phone_number, message)

        return {
            "success": True,
            "message": "WhatsApp message sent"
        }

    except Exception as e:
        logger.error("Failed to send WhatsApp message", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def whatsapp_status():
    """Get WhatsApp bot status"""
    bot = get_whatsapp_bot()

    return {
        "active": bot is not None,
        "provider": "PyWhatKit",
        "features": [
            "Free (no API costs)",
            "Uses WhatsApp Web",
            "Instant messaging",
            "Scheduled messaging"
        ],
        "requirements": [
            "WhatsApp Web logged in",
            "GUI environment",
            "Python automation permissions"
        ]
    }
