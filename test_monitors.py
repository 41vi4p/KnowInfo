#!/usr/bin/env python3
"""
Test script for monitors - verify Twitter, Reddit, RSS scraping works
"""
import asyncio
import sys
import argparse
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.stage1_ingestion.twitter_monitor import TwitterMonitor, TwitterSingleTweetScraper
from src.stage1_ingestion.reddit_monitor import RedditMonitor
from src.stage1_ingestion.rss_monitor import RSSMonitor
from src.stage1_ingestion.telegram_monitor import TelegramMonitor
from src.utils.logger import setup_logging
from config import settings

logger = setup_logging()


async def test_twitter_search():
    """Test Twitter keyword search"""
    print("\n" + "="*80)
    print("Testing Twitter Monitor (Playwright scraping)")
    print("="*80 + "\n")

    monitor = TwitterMonitor(
        keywords=["breaking news"],
        check_interval=60
    )

    await monitor.start()

    # Get first 5 tweets
    count = 0
    async for content in monitor.stream_content():
        print(f"\n--- Tweet {count + 1} ---")
        print(f"Author: {content.author_username}")
        print(f"Text: {content.text[:200]}...")
        print(f"Engagement: {content.engagement_count}")
        print(f"URL: {content.url}")

        count += 1
        if count >= 5:
            break

    await monitor.stop()
    print("\n✅ Twitter monitor test complete!\n")


async def test_twitter_single_tweet():
    """Test scraping a single tweet"""
    print("\n" + "="*80)
    print("Testing Single Tweet Scraper")
    print("="*80 + "\n")

    # Example tweet URL (replace with any public tweet)
    tweet_url = input("Enter a tweet URL (or press Enter to skip): ").strip()

    if tweet_url:
        scraper = TwitterSingleTweetScraper()
        try:
            content = await scraper.scrape_tweet(tweet_url)
            print(f"\nAuthor: {content.author_username}")
            print(f"Text: {content.text}")
            print(f"Engagement: {content.engagement_count}")
            print(f"Created: {content.created_at}")
            print("\n✅ Single tweet scraping works!\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


async def test_reddit():
    """Test Reddit monitor"""
    print("\n" + "="*80)
    print("Testing Reddit Monitor")
    print("="*80 + "\n")

    try:
        monitor = RedditMonitor(
            keywords=["breaking", "emergency", "crisis"],
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
            subreddits=["news", "worldnews"]
        )

        await monitor.start()

        # Get first 3 posts
        count = 0
        async for content in monitor.stream_content():
            print(f"\n--- Reddit Post {count + 1} ---")
            print(f"Subreddit: {content.metadata.get('subreddit')}")
            print(f"Author: {content.author_username}")
            print(f"Title: {content.text[:200]}...")
            print(f"Engagement: {content.engagement_count}")
            print(f"URL: {content.url}")

            count += 1
            if count >= 3:
                break

        await monitor.stop()
        print("\n✅ Reddit monitor test complete!\n")

    except Exception as e:
        print(f"\n❌ Reddit test failed: {e}")
        print("Make sure you've set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env\n")


async def test_rss():
    """Test RSS monitor"""
    print("\n" + "="*80)
    print("Testing RSS Monitor")
    print("="*80 + "\n")

    feeds = settings.rss_feeds

    monitor = RSSMonitor(
        keywords=["breaking", "emergency", "crisis", "disaster"],
        feed_urls=feeds,
        check_interval=60
    )

    await monitor.start()

    # Get first 5 entries
    count = 0
    async for content in monitor.stream_content():
        print(f"\n--- RSS Entry {count + 1} ---")
        print(f"Source: {content.metadata.get('feed_title')}")
        print(f"Title: {content.text[:200]}...")
        print(f"URL: {content.url}")

        count += 1
        if count >= 5:
            break

    await monitor.stop()
    print("\n✅ RSS monitor test complete!\n")


async def test_telegram():
    """Test Telegram monitor"""
    print("\n" + "="*80)
    print("Testing Telegram Monitor")
    print("="*80 + "\n")

    if not settings.telegram_api_id or not settings.telegram_api_hash:
        print("❌ Telegram API credentials not set in .env")
        print("Please set TELEGRAM_API_ID and TELEGRAM_API_HASH")
        return

    monitor = TelegramMonitor(
        api_id=settings.telegram_api_id,
        api_hash=settings.telegram_api_hash,
        channels=settings.telegram_monitor_channels,
        keywords=["breaking", "news", "emergency", "update"]
    )

    print(f"Monitoring channels: {settings.telegram_monitor_channels}")
    await monitor.start()

    # Get first 3 messages
    count = 0
    print("\nWaiting for messages (this might take a while depending on channel activity)...")
    
    try:
        async for content in monitor.stream_content():
            print(f"\n--- Telegram Message {count + 1} ---")
            print(f"Channel: {content.metadata.get('channel')}")
            print(f"Author: {content.author_username}")
            print(f"Text: {content.text[:200]}...")
            print(f"URL: {content.url}")

            count += 1
            if count >= 3:
                break
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        await monitor.stop()
        print("\n✅ Telegram monitor test complete!\n")


async def main():
    """Run all tests"""
    parser = argparse.ArgumentParser(description="Test monitors")
    parser.add_argument("--test", choices=["twitter", "tweet", "reddit", "rss", "telegram", "all"], help="Test to run")
    args = parser.parse_args()

    if args.test:
        choice = args.test
        # Map choice to number for compatibility with existing logic or just run directly
        if choice == "twitter":
            await test_twitter_search()
        elif choice == "tweet":
            await test_twitter_single_tweet()
        elif choice == "reddit":
            await test_reddit()
        elif choice == "rss":
            await test_rss()
        elif choice == "telegram":
            await test_telegram()
        elif choice == "all":
            await test_twitter_search()
            await test_reddit()
            await test_rss()
        return

    print("\n" + "="*80)
    print("KnowInfo Monitor Testing")
    print("="*80)

    print("\nWhat would you like to test?")
    print("1. Twitter keyword search (Playwright)")
    print("2. Single tweet scraper")
    print("3. Reddit monitor")
    print("4. RSS monitor")
    print("5. Telegram monitor")
    print("6. All monitors")

    choice = input("\nEnter choice (1-5): ").strip()

    if choice == "1":
        await test_twitter_search()
    elif choice == "2":
        await test_twitter_single_tweet()
    elif choice == "3":
        await test_reddit()
    elif choice == "4":
        await test_rss()
    elif choice == "5":
        await test_telegram()
    elif choice == "6":
        await test_twitter_search()
        await test_reddit()
        await test_rss()
        # Telegram skipped in 'all' to avoid interactive login prompts during automated runs
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
