"""
RSS Feed Monitor for authoritative news sources
"""
import asyncio
from typing import List, AsyncGenerator
import structlog
from datetime import datetime
import feedparser
from newspaper import Article

from .base_monitor import BaseMonitor
from ..models.content import Content, SourcePlatform

logger = structlog.get_logger(__name__)


class RSSMonitor(BaseMonitor):
    """Monitor RSS feeds from authoritative sources"""

    def __init__(
        self,
        keywords: List[str],
        feed_urls: List[str],
        check_interval: int = 300
    ):
        """
        Initialize RSS monitor

        Args:
            keywords: Keywords to filter for
            feed_urls: List of RSS feed URLs
            check_interval: How often to check feeds (seconds)
        """
        super().__init__("RSS", keywords)
        self.feed_urls = feed_urls
        self.check_interval = check_interval
        self.seen_entry_ids = set()

    async def start(self):
        """Start monitoring"""
        self.is_running = True
        logger.info(
            "RSS monitor started",
            keywords=self.keywords,
            feed_count=len(self.feed_urls)
        )

    async def stop(self):
        """Stop monitoring"""
        self.is_running = False
        logger.info("RSS monitor stopped")

    async def stream_content(self) -> AsyncGenerator[Content, None]:
        """
        Stream content from RSS feeds

        Yields:
            Content objects from RSS feeds
        """
        while self.is_running:
            for feed_url in self.feed_urls:
                try:
                    # Parse feed
                    feed = await asyncio.to_thread(feedparser.parse, feed_url)

                    for entry in feed.entries[:20]:  # Limit per feed
                        # Use link as unique ID
                        entry_id = entry.get("link", entry.get("id", ""))

                        if entry_id in self.seen_entry_ids:
                            continue

                        self.seen_entry_ids.add(entry_id)

                        # Convert to Content
                        content = await self._entry_to_content(entry, feed.feed)

                        if content and await self.filter_content(content):
                            logger.info(
                                "RSS entry matched",
                                title=content.text[:50],
                                source=feed.feed.get("title", "Unknown")
                            )
                            yield content

                except Exception as e:
                    logger.error(
                        "RSS feed error",
                        feed_url=feed_url,
                        error=str(e)
                    )

            # Wait before next check
            await asyncio.sleep(self.check_interval)

    async def _entry_to_content(self, entry, feed_info) -> Content:
        """
        Convert RSS entry to Content object

        Args:
            entry: feedparser entry
            feed_info: Feed metadata

        Returns:
            Content object
        """
        try:
            # Get full article content if possible
            article_url = entry.get("link", "")
            article_text = entry.get("summary", "")
            title = entry.get("title", "")

            # Try to get full article using newspaper3k
            if article_url:
                try:
                    article = Article(article_url)
                    await asyncio.to_thread(article.download)
                    await asyncio.to_thread(article.parse)

                    if article.text:
                        article_text = article.text
                except:
                    pass  # Use summary if article extraction fails

            # Combine title and text
            text = f"{title}\n\n{article_text}" if title != article_text else article_text

            # Parse publication date
            published = datetime.utcnow()
            if "published_parsed" in entry and entry.published_parsed:
                try:
                    from time import mktime
                    published = datetime.fromtimestamp(mktime(entry.published_parsed))
                except:
                    pass

            # Extract author
            author = entry.get("author", feed_info.get("title", "Unknown"))

            # Extract media
            media_urls = []
            if "media_content" in entry:
                for media in entry.media_content:
                    if media.get("url"):
                        media_urls.append(media["url"])
            elif "media_thumbnail" in entry:
                for thumb in entry.media_thumbnail:
                    if thumb.get("url"):
                        media_urls.append(thumb["url"])

            content = Content(
                source=SourcePlatform.RSS,
                platform_id=entry.get("id", article_url),
                text=text,
                author_id=author,
                author_username=author,
                author_followers=0,
                url=article_url,
                media_urls=media_urls,
                hashtags=[],
                mentions=[],
                engagement_count=0,
                created_at=published,
                metadata={
                    "feed_title": feed_info.get("title", "Unknown"),
                    "feed_url": feed_info.get("link", ""),
                    "categories": [tag.term for tag in entry.get("tags", [])]
                }
            )

            return content

        except Exception as e:
            logger.error("RSS entry conversion failed", error=str(e))
            return None
