"""
Reddit Monitor using PRAW (Reddit API)
"""
import asyncio
from typing import List, AsyncGenerator
import structlog
from datetime import datetime
import praw

from .base_monitor import BaseMonitor
from ..models.content import Content, SourcePlatform

logger = structlog.get_logger(__name__)


class RedditMonitor(BaseMonitor):
    """Monitor Reddit for crisis-related posts"""

    def __init__(
        self,
        keywords: List[str],
        client_id: str,
        client_secret: str,
        user_agent: str,
        subreddits: List[str] = None
    ):
        """
        Initialize Reddit monitor

        Args:
            keywords: Keywords to filter for
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
            subreddits: List of subreddits to monitor (default: news+worldnews)
        """
        super().__init__("Reddit", keywords)

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

        self.subreddits = subreddits or ["news", "worldnews", "breaking"]
        self.seen_post_ids = set()

    async def start(self):
        """Start monitoring"""
        self.is_running = True
        logger.info(
            "Reddit monitor started",
            keywords=self.keywords,
            subreddits=self.subreddits
        )

    async def stop(self):
        """Stop monitoring"""
        self.is_running = False
        logger.info("Reddit monitor stopped")

    async def stream_content(self) -> AsyncGenerator[Content, None]:
        """
        Stream content from Reddit

        Yields:
            Content objects from Reddit
        """
        subreddit_str = "+".join(self.subreddits)
        subreddit = self.reddit.subreddit(subreddit_str)

        while self.is_running:
            try:
                # Get new posts
                for submission in subreddit.new(limit=100):
                    # Skip if already seen
                    if submission.id in self.seen_post_ids:
                        continue

                    self.seen_post_ids.add(submission.id)

                    # Convert to Content object
                    content = self._submission_to_content(submission)

                    # Filter by keywords
                    if await self.filter_content(content):
                        logger.info(
                            "Reddit post matched",
                            post_id=content.platform_id,
                            title=content.text[:50]
                        )
                        yield content

                # Wait before next check (to avoid rate limits)
                await asyncio.sleep(60)

            except Exception as e:
                logger.error("Reddit streaming error", error=str(e))
                await asyncio.sleep(120)

    def _submission_to_content(self, submission) -> Content:
        """
        Convert Reddit submission to Content object

        Args:
            submission: PRAW submission object

        Returns:
            Content object
        """
        # Combine title and selftext for full content
        text = submission.title
        if submission.selftext:
            text += "\n\n" + submission.selftext

        # Extract media URLs
        media_urls = []
        if hasattr(submission, "url") and submission.url:
            if any(
                ext in submission.url.lower()
                for ext in [".jpg", ".jpeg", ".png", ".gif", ".mp4"]
            ):
                media_urls.append(submission.url)

        # Get top comments for context
        try:
            submission.comments.replace_more(limit=0)
            top_comments = []
            for comment in submission.comments[:5]:  # Top 5 comments
                if hasattr(comment, "body") and comment.score > 5:
                    top_comments.append(comment.body)

            if top_comments:
                text += "\n\nTop Comments:\n" + "\n".join(top_comments)
        except:
            pass

        content = Content(
            source=SourcePlatform.REDDIT,
            platform_id=submission.id,
            text=text,
            author_id=str(submission.author) if submission.author else "[deleted]",
            author_username=str(submission.author) if submission.author else "[deleted]",
            author_followers=0,  # Reddit doesn't have follower count easily accessible
            url=f"https://reddit.com{submission.permalink}",
            media_urls=media_urls,
            hashtags=[],  # Reddit doesn't use hashtags
            mentions=[],
            engagement_count=submission.score + submission.num_comments,
            reach=submission.score * 10,  # Rough estimate
            created_at=datetime.fromtimestamp(submission.created_utc),
            metadata={
                "subreddit": submission.subreddit.display_name,
                "num_comments": submission.num_comments,
                "upvote_ratio": submission.upvote_ratio,
                "awards": submission.total_awards_received
            }
        )

        return content
