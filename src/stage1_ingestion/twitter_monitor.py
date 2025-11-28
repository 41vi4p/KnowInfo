"""
Twitter/X Monitor using Playwright (no API required)
Scrapes tweets based on search keywords without requiring Twitter API access
"""
import asyncio
from typing import List, AsyncGenerator
import structlog
from datetime import datetime
import nest_asyncio
from playwright.async_api import async_playwright, Page, Response

from .base_monitor import BaseMonitor
from ..models.content import Content, SourcePlatform

logger = structlog.get_logger(__name__)
nest_asyncio.apply()


class TwitterMonitor(BaseMonitor):
    """Monitor Twitter/X using Playwright web scraping"""

    def __init__(self, keywords: List[str], check_interval: int = 300):
        """
        Initialize Twitter monitor

        Args:
            keywords: List of keywords to search for
            check_interval: How often to check for new tweets (seconds)
        """
        super().__init__("Twitter", keywords)
        self.check_interval = check_interval
        self.seen_tweet_ids = set()

    async def start(self):
        """Start monitoring"""
        self.is_running = True
        logger.info("Twitter monitor started", keywords=self.keywords)

    async def stop(self):
        """Stop monitoring"""
        self.is_running = False
        logger.info("Twitter monitor stopped")

    async def stream_content(self) -> AsyncGenerator[Content, None]:
        """
        Stream content from Twitter search

        Yields:
            Content objects from Twitter
        """
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            while self.is_running:
                for keyword in self.keywords:
                    try:
                        # Search for keyword on Twitter
                        async for content in self._search_tweets(page, keyword):
                            if content.platform_id not in self.seen_tweet_ids:
                                self.seen_tweet_ids.add(content.platform_id)
                                yield content
                    except Exception as e:
                        logger.error(
                            "Twitter search error",
                            keyword=keyword,
                            error=str(e)
                        )

                # Wait before next check
                await asyncio.sleep(self.check_interval)

            await browser.close()

    async def _search_tweets(
        self,
        page: Page,
        keyword: str
    ) -> AsyncGenerator[Content, None]:
        """
        Search for tweets with a specific keyword

        Args:
            page: Playwright page object
            keyword: Search keyword

        Yields:
            Content objects
        """
        try:
            # Navigate to Twitter search
            search_url = f"https://twitter.com/search?q={keyword}&f=live"
            logger.info("Searching Twitter", keyword=keyword, url=search_url)

            await page.goto(search_url, wait_until="networkidle", timeout=30000)

            # Wait for tweets to load
            try:
                await page.wait_for_selector(
                    "[data-testid='tweet']",
                    timeout=10000
                )
            except:
                logger.warning("No tweets found", keyword=keyword)
                return

            # Get all tweet elements
            tweet_elements = await page.query_selector_all("[data-testid='tweet']")

            for tweet_elem in tweet_elements[:20]:  # Limit to 20 tweets per keyword
                try:
                    content = await self._extract_tweet_data(tweet_elem, page)
                    if content:
                        yield content
                except Exception as e:
                    logger.error("Tweet extraction error", error=str(e))
                    continue

        except Exception as e:
            logger.error("Twitter search failed", keyword=keyword, error=str(e))

    async def _extract_tweet_data(self, tweet_elem, page: Page) -> Content:
        """
        Extract data from a tweet element

        Args:
            tweet_elem: Playwright element handle for tweet
            page: Playwright page object

        Returns:
            Content object or None
        """
        try:
            # Extract tweet text
            text_elem = await tweet_elem.query_selector("[data-testid='tweetText']")
            text = await text_elem.inner_text() if text_elem else ""

            if not text:
                return None

            # Extract username
            username = ""
            username_elem = await tweet_elem.query_selector("[data-testid='User-Name'] span")
            if username_elem:
                username_text = await username_elem.inner_text()
                # Extract @username from "Name @username · time" format
                parts = username_text.split("@")
                if len(parts) > 1:
                    username = "@" + parts[1].split("·")[0].strip()

            # Extract tweet URL/ID
            link_elem = await tweet_elem.query_selector("a[href*='/status/']")
            tweet_url = ""
            tweet_id = ""
            if link_elem:
                href = await link_elem.get_attribute("href")
                tweet_url = f"https://twitter.com{href}"
                # Extract ID from URL
                if "/status/" in href:
                    tweet_id = href.split("/status/")[1].split("?")[0]

            # Extract time
            time_elem = await tweet_elem.query_selector("time")
            created_at = datetime.utcnow()
            if time_elem:
                datetime_str = await time_elem.get_attribute("datetime")
                if datetime_str:
                    try:
                        created_at = datetime.fromisoformat(
                            datetime_str.replace("Z", "+00:00")
                        )
                    except:
                        pass

            # Extract engagement metrics (if visible)
            engagement = 0
            try:
                # Try to get reply, retweet, like counts
                metrics_elems = await tweet_elem.query_selector_all(
                    "[role='group'] [data-testid*='Count']"
                )
                for metric in metrics_elems:
                    text = await metric.inner_text()
                    # Convert "1.2K" to 1200, etc.
                    count = self._parse_count(text)
                    engagement += count
            except:
                pass

            # Extract media URLs
            media_urls = []
            media_elems = await tweet_elem.query_selector_all("img[src*='pbs.twimg.com']")
            for media in media_elems:
                src = await media.get_attribute("src")
                if src and "profile_images" not in src:
                    media_urls.append(src)

            # Extract hashtags
            hashtags = []
            hashtag_elems = await tweet_elem.query_selector_all("a[href*='/hashtag/']")
            for tag in hashtag_elems:
                tag_text = await tag.inner_text()
                hashtags.append(tag_text.strip())

            # Create Content object
            content = Content(
                source=SourcePlatform.TWITTER,
                platform_id=tweet_id or f"twitter_{hash(text)}",
                text=text,
                author_id=username.replace("@", "") if username else "unknown",
                author_username=username or "unknown",
                author_followers=0,  # Can't get follower count without API
                url=tweet_url,
                media_urls=media_urls,
                hashtags=hashtags,
                engagement_count=engagement,
                created_at=created_at
            )

            logger.info(
                "Tweet extracted",
                tweet_id=content.platform_id,
                username=username,
                text_preview=text[:50]
            )

            return content

        except Exception as e:
            logger.error("Tweet data extraction failed", error=str(e))
            return None

    def _parse_count(self, count_str: str) -> int:
        """
        Parse count strings like "1.2K", "3M" to integers

        Args:
            count_str: Count string from Twitter

        Returns:
            Integer count
        """
        try:
            count_str = count_str.strip().upper()
            if "K" in count_str:
                return int(float(count_str.replace("K", "")) * 1000)
            elif "M" in count_str:
                return int(float(count_str.replace("M", "")) * 1000000)
            else:
                return int(count_str)
        except:
            return 0


class TwitterSingleTweetScraper:
    """Scraper for individual tweet URLs (from web_scraper.py approach)"""

    async def scrape_tweet(self, url: str) -> Content:
        """
        Scrape a single tweet by URL

        Args:
            url: Tweet URL

        Returns:
            Content object
        """
        xhr_calls = []

        def intercept_response(response: Response):
            """Capture background XHR requests"""
            if response.request.resource_type == "xhr":
                xhr_calls.append(response)

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080}
                )
                page = await context.new_page()

                # Enable request intercepting
                page.on("response", intercept_response)

                # Navigate to tweet
                await page.goto(url, timeout=30000)
                await page.wait_for_selector(
                    "[data-testid='tweet']",
                    timeout=30000
                )

                # Try to extract from XHR API calls
                tweet_calls = [
                    f for f in xhr_calls
                    if "TweetResultByRestId" in f.url
                ]

                for xhr in tweet_calls:
                    try:
                        data = await xhr.json()
                        tweet = data["data"]["tweetResult"]["result"]
                        legacy = tweet["legacy"]
                        user = tweet["core"]["user_results"]["result"]["legacy"]

                        content = Content(
                            source=SourcePlatform.TWITTER,
                            platform_id=tweet.get("rest_id", ""),
                            text=legacy["full_text"],
                            author_id=user["screen_name"],
                            author_username=f"@{user['screen_name']}",
                            author_followers=user.get("followers_count", 0),
                            url=url,
                            media_urls=[],
                            hashtags=[
                                tag["text"]
                                for tag in legacy.get("entities", {}).get("hashtags", [])
                            ],
                            engagement_count=(
                                legacy.get("retweet_count", 0) +
                                legacy.get("favorite_count", 0)
                            ),
                            created_at=datetime.strptime(
                                legacy["created_at"],
                                "%a %b %d %H:%M:%S %z %Y"
                            )
                        )

                        await browser.close()
                        return content

                    except Exception as e:
                        logger.warning("XHR extraction failed", error=str(e))
                        continue

                # Fallback to HTML extraction
                tweet_text = await page.text_content("[data-testid='tweetText']")
                username_elem = await page.query_selector(
                    "[data-testid='User-Name'] span"
                )
                username = await username_elem.inner_text() if username_elem else "unknown"

                content = Content(
                    source=SourcePlatform.TWITTER,
                    platform_id=url.split("/status/")[1] if "/status/" in url else "",
                    text=tweet_text or "",
                    author_id=username,
                    author_username=username,
                    url=url,
                    created_at=datetime.utcnow()
                )

                await browser.close()
                return content

        except Exception as e:
            logger.error("Tweet scraping failed", url=url, error=str(e))
            raise
