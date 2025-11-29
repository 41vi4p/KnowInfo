"""
Telegram Monitor for Public Channels (using Telethon)
"""
import asyncio
from typing import List, AsyncGenerator
import structlog
from telethon import TelegramClient, events
from telethon.tl.types import Message

from .base_monitor import BaseMonitor
from ..models.content import Content, SourcePlatform
from datetime import datetime
import time

logger = structlog.get_logger(__name__)


class TelegramMonitor(BaseMonitor):
    """
    Monitor public Telegram channels for crisis information
    """

    def __init__(
        self,
        api_id: str,
        api_hash: str,
        channels: List[str],
        keywords: List[str]
    ):
        """
        Initialize Telegram monitor
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            channels: List of channel usernames to monitor
            keywords: List of keywords to filter by
        """
        super().__init__("telegram", keywords)
        self.api_id = api_id
        self.api_hash = api_hash
        self.channels = channels
        self.client = None
        self.message_queue = asyncio.Queue()

    async def start(self):
        """Start monitoring"""
        if self.is_running:
            return

        logger.info("Starting Telegram monitor", channels=self.channels)
        
        try:
            # Initialize client (session name 'knowinfo_monitor')
            self.client = TelegramClient('knowinfo_monitor', self.api_id, self.api_hash)
            
            # Define event handler
            @self.client.on(events.NewMessage(chats=self.channels))
            async def handler(event):
                try:
                    message = event.message
                    if message.text:
                        # Create content object
                        content = Content(
                            source=SourcePlatform.TELEGRAM,
                            platform_id=str(message.id),
                            text=message.text,
                            author_id=str(message.sender_id) if message.sender_id else "unknown",
                            author_username=await self._get_sender_name(message),
                            created_at=message.date or datetime.utcnow(),
                            url=f"https://t.me/{event.chat.username}/{message.id}" if event.chat.username else "",
                            metadata={
                                "channel": event.chat.title if hasattr(event.chat, 'title') else "Unknown",
                                "views": message.views or 0
                            }
                        )
                        
                        # Filter and queue
                        if await self.filter_content(content):
                            await self.message_queue.put(content)
                            logger.info("Telegram content queued", channel=content.metadata["channel"])
                            
                except Exception as e:
                    logger.error("Error processing Telegram message", error=str(e))

            # Start client
            await self.client.start()
            self.is_running = True
            logger.info("Telegram monitor started")
            
        except Exception as e:
            logger.error("Failed to start Telegram monitor", error=str(e))
            self.is_running = False

    async def stop(self):
        """Stop monitoring"""
        if not self.is_running:
            return
            
        logger.info("Stopping Telegram monitor")
        if self.client:
            await self.client.disconnect()
        self.is_running = False
        logger.info("Telegram monitor stopped")

    async def stream_content(self) -> AsyncGenerator[Content, None]:
        """Stream content from the queue"""
        while self.is_running:
            try:
                # Get content from queue with timeout to allow checking is_running
                try:
                    content = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                    yield content
                except asyncio.TimeoutError:
                    continue
            except Exception as e:
                logger.error("Error streaming Telegram content", error=str(e))
                await asyncio.sleep(1)

    async def _get_sender_name(self, message: Message) -> str:
        """Helper to get sender name safely"""
        try:
            sender = await message.get_sender()
            if hasattr(sender, 'username') and sender.username:
                return sender.username
            if hasattr(sender, 'title'):
                return sender.title
            if hasattr(sender, 'first_name'):
                name = sender.first_name
                if hasattr(sender, 'last_name') and sender.last_name:
                    name += f" {sender.last_name}"
                return name
            return "unknown"
        except:
            return "unknown"
