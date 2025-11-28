"""
Base monitor class for content ingestion
"""
from abc import ABC, abstractmethod
from typing import List, AsyncGenerator
import structlog
from ..models.content import Content

logger = structlog.get_logger(__name__)


class BaseMonitor(ABC):
    """Abstract base class for social media monitors"""

    def __init__(self, name: str, keywords: List[str]):
        self.name = name
        self.keywords = keywords
        self.is_running = False

    @abstractmethod
    async def start(self):
        """Start monitoring"""
        pass

    @abstractmethod
    async def stop(self):
        """Stop monitoring"""
        pass

    @abstractmethod
    async def stream_content(self) -> AsyncGenerator[Content, None]:
        """Stream content from the platform"""
        pass

    async def filter_content(self, content: Content) -> bool:
        """Filter content based on crisis keywords"""
        text_lower = content.text.lower()
        return any(keyword.lower() in text_lower for keyword in self.keywords)
