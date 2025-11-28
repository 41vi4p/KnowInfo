#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Scraper

This script provides functionality to scrape content from various web sources
including news articles, Reddit posts, and Twitter/X posts based on an input URL.
"""

import argparse
import json
import re
import asyncio
import nest_asyncio
from urllib.parse import urlparse
from datetime import datetime

# Import required libraries
from newspaper import Article
import praw
from playwright.async_api import async_playwright
import spacy

# Try to load spaCy model, download if not available
try:
    nlp = spacy.load("en_core_web_sm")
    #trf
except:
    import sys
    import subprocess
    print("Downloading spaCy model...")
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

class WebScraper:
    """Main web scraper class that handles different types of URLs"""
    
    def __init__(self):
        """Initialize the scraper with necessary components"""
        # Initialize Reddit API client
        self.reddit = praw.Reddit(
            client_id='jIVNtBOBarfgQfgWsva2NA',
            client_secret='sBrIiD00Y0Ofk4fi-RzFA9XqkvlEQw',
            user_agent='web:com.cyberkhabar.code_breakers:v0.0.1 (by u/CodeBreakers_)'
        )
        # Apply nest_asyncio to allow nested event loops (needed for Twitter scraping)
        nest_asyncio.apply()
        
    def scrape_url(self, url):
        """
        Scrape content from a URL
        
        Args:
            url (str): URL to scrape
            
        Returns:
            dict: Scraped content
        """
        # Parse URL to determine its type
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Determine the type of URL and use the appropriate scraper
        if "reddit.com" in domain:
            return self.scrape_reddit(url)
        elif "twitter.com" in domain or "x.com" in domain:
            return asyncio.run(self.scrape_twitter(url))
        else:
            # Default to generic article scraper
            return self.scrape_article(url)
    
    def scrape_article(self, url):
        """
        Scrape a news article
        
        Args:
            url (str): URL of the article
            
        Returns:
            dict: Article content
        """
        try:
            # Create Article object and download content
            article = Article(url)
            article.download()
            article.parse()
            article.nlp()
            
            # Extract organizations mentioned in the article
            doc = nlp(article.text)
            organizations = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
            
            # Return structured data
            return {
                "title": article.title,
                "author": article.authors,
                "date": article.publish_date.isoformat() if article.publish_date else None,
                "summary": article.summary,
                "keywords": article.keywords,
                "text": article.text,
                "organizations": organizations,
                "url": url,
                "source_type": "news_article"
            }
        except Exception as e:
            return {"error": str(e), "url": url}
    
    def scrape_reddit(self, url):
        """
        Scrape a Reddit post
        
        Args:
            url (str): URL of the Reddit post
            
        Returns:
            dict: Reddit post content
        """
        try:
            # Extract submission ID from URL
            submission_id = url.split('comments/')[1].split('/')[0]
            submission = self.reddit.submission(id=submission_id)
            
            # Get basic post data
            post_data = {
                'title': submission.title,
                'url': f'https://reddit.com{submission.permalink}',
                'author': str(submission.author) if submission.author else '[deleted]',
                'score': submission.score,
                'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
                'subreddit': submission.subreddit.display_name,
                'post_content': submission.selftext,
                'comments': [],
                'source_type': 'reddit'
            }
            
            # Get comments
            submission.comments.replace_more(limit=None)
            for comment in submission.comments.list():
                if comment.author and comment.score > 0:  # Filter out deleted and low-score comments
                    comment_data = {
                        'author': str(comment.author),
                        'body': comment.body,
                        'score': comment.score,
                        'created_utc': datetime.fromtimestamp(comment.created_utc).isoformat()
                    }
                    post_data['comments'].append(comment_data)
                    
            # Extract full text for analysis
            full_text = submission.title + " " + submission.selftext
            for comment in post_data['comments']:
                full_text += " " + comment['body']
                
            post_data['text'] = full_text
            
            # Extract organizations mentioned
            doc = nlp(full_text)
            post_data['organizations'] = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
            
            return post_data
        except Exception as e:
            return {"error": str(e), "url": url}
    
    async def scrape_twitter(self, url):
        """
        Scrape a Twitter/X post
        
        Args:
            url (str): URL of the tweet
            
        Returns:
            dict: Tweet content
        """
        _xhr_calls = []
        
        def intercept_response(response):
            """Capture background requests"""
            if response.request.resource_type == "xhr":
                _xhr_calls.append(response)
            return response
        
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                context = await browser.new_context(viewport={"width": 1920, "height": 1080})
                page = await context.new_page()
                
                # Enable background request intercepting
                page.on("response", intercept_response)
                
                # Go to URL and wait for tweet to load
                await page.goto(url)
                await page.wait_for_selector("[data-testid='tweet']", timeout=30000)
                
                # Get tweet text and metadata
                tweet_data = {
                    'url': url,
                    'source_type': 'twitter'
                }
                
                # Try to extract tweet content from API calls
                tweet_calls = [f for f in _xhr_calls if "TweetResultByRestId" in f.url]
                for xhr in tweet_calls:
                    try:
                        data = await xhr.json()
                        print(data)
                        tweet = data['data']['tweetResult']['result']
                        tweet_data['text'] = tweet['legacy']['text']
                        tweet_data['created_at'] = tweet['legacy']['created_at']
                        tweet_data['author'] = tweet['core']['user_results']['result']['legacy']['screen_name']
                        tweet_data['retweet_count'] = tweet['legacy']['retweet_count']
                        tweet_data['like_count'] = tweet['legacy']['favorite_count']
                        
                        # Extract organizations mentioned
                        doc = nlp(tweet_data['text'])
                        tweet_data['organizations'] = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
                        
                        break
                    except Exception as e:
                        continue
                
                # If API extraction failed, try direct HTML extraction
                if 'text' not in tweet_data:
                    try:
                        tweet_text = await page.text_content("[data-testid='tweetText']")
                        tweet_data['text'] = tweet_text
                        
                        # Extract organizations mentioned
                        doc = nlp(tweet_text)
                        tweet_data['organizations'] = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
                    except:
                        tweet_data['text'] = "Could not extract tweet text"
                        tweet_data['organizations'] = []
                
                return tweet_data
        except Exception as e:
            return {"error": str(e), "url": url}

def save_to_json(data, output_file=None):
    """
    Save scraped data to a JSON file
    
    Args:
        data (dict): Scraped data
        output_file (str): Path to output file
    """
    if output_file is None:
        # Generate a filename based on URL and timestamp
        source_type = data.get('source_type', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        output_file = f"scraped_{source_type}_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"Data saved to {output_file}")

def main():
    """Main function to handle command line execution"""
    parser = argparse.ArgumentParser(description='Scrape content from a URL')
    parser.add_argument('url', help='URL to scrape')
    parser.add_argument('-o', '--output', help='Output file path')
    args = parser.parse_args()
    
    scraper = WebScraper()
    result = scraper.scrape_url(args.url)
    
    # Print summary of scraped content
    print("\n" + "="*80)
    print(f"Source: {result.get('source_type', 'Unknown')}")
    if 'title' in result:
        print(f"Title: {result.get('title')}")
    if 'author' in result:
        print(f"Author: {result.get('author')}")
    if 'organizations' in result:
        print(f"Organizations mentioned: {', '.join(result.get('organizations', []))}")
    print("="*80 + "\n")
    
    # Save result to file
    save_to_json(result, args.output)
    
    return result

if __name__ == "__main__":
    main()
