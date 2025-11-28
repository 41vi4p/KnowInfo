# KnowInfo - Step-by-Step Implementation Guide

This guide will help you complete the remaining components of the KnowInfo system.

## Current Status

✅ **Completed:**
- Project structure and configuration
- Database managers (MongoDB, Neo4j, Redis)
- Pydantic data models
- Utilities (logging, metrics, guardrails)
- Multi-model manager (Gemini/Ollama/OpenAI/Anthropic)
- Core components for Stages 2 & 3
- FastAPI application scaffold
- Docker configuration

⏳ **To Be Implemented:**
- Complete Stage 1 monitors (Twitter, Reddit, Telegram, RSS)
- Stage 4 tracking (Patient Zero)
- Stage 5 response (WhatsApp bot, Dashboard)
- Stage 6 learning (Feedback, A/B testing)
- API endpoints
- Full integration and testing

## Phase 1: Set Up Development Environment

### 1.1 Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 1.2 Start Infrastructure

```bash
# Start databases
docker-compose up -d mongodb neo4j redis ollama

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 1.3 Configure Ollama

```bash
# Pull models
./scripts/setup_ollama.sh

# Or manually:
ollama pull nomic-embed-text
ollama pull llama3.2

# Verify
ollama list
```

### 1.4 Configure Environment

```bash
# Copy example
cp .env.example .env

# Edit with your keys (at minimum set GEMINI_API_KEY or configure Ollama)
nano .env
```

## Phase 2: Implement Remaining Monitors (Stage 1)

### 2.1 Twitter Monitor

Create `src/stage1_ingestion/twitter_monitor.py`:

```python
from .base_monitor import BaseMonitor
from ..models.content import Content, SourcePlatform
import tweepy
from datetime import datetime

class TwitterMonitor(BaseMonitor):
    def __init__(self, keywords, bearer_token):
        super().__init__("Twitter", keywords)
        self.client = tweepy.StreamingClient(bearer_token)

    async def stream_content(self):
        # Implement Twitter streaming
        # Use tweepy.StreamingClient to filter by keywords
        # Convert tweets to Content objects
        pass
```

### 2.2 Reddit Monitor

Create `src/stage1_ingestion/reddit_monitor.py`:

```python
from .base_monitor import BaseMonitor
import praw
import asyncio

class RedditMonitor(BaseMonitor):
    def __init__(self, keywords, client_id, client_secret, user_agent):
        super().__init__("Reddit", keywords)
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

    async def stream_content(self):
        # Monitor r/news, r/worldnews
        subreddit = self.reddit.subreddit("news+worldnews")
        for submission in subreddit.stream.submissions():
            # Convert to Content object
            yield content
```

### 2.3 RSS Monitor

Create `src/stage1_ingestion/rss_monitor.py`:

```python
import feedparser
import asyncio

class RSSMonitor(BaseMonitor):
    def __init__(self, keywords, feed_urls):
        super().__init__("RSS", keywords)
        self.feed_urls = feed_urls

    async def stream_content(self):
        while self.is_running:
            for url in self.feed_urls:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    # Convert to Content object
                    yield content
            await asyncio.sleep(300)  # Check every 5 minutes
```

### 2.4 Content Ingestion Pipeline

Create `src/stage1_ingestion/pipeline.py`:

```python
import asyncio
from ..database.mongodb import get_mongo
from ..database.redis_cache import get_redis

class IngestionPipeline:
    def __init__(self, monitors):
        self.monitors = monitors

    async def start(self):
        tasks = []
        for monitor in self.monitors:
            tasks.append(self._process_monitor(monitor))
        await asyncio.gather(*tasks)

    async def _process_monitor(self, monitor):
        await monitor.start()
        async for content in monitor.stream_content():
            # Filter
            if await monitor.filter_content(content):
                # Store in MongoDB
                mongo = await get_mongo()
                content_id = await mongo.store_content(content.dict())

                # Track velocity in Redis
                redis = await get_redis()
                velocity = await redis.increment_claim_velocity(content.text)

                # Queue for extraction
                await redis.enqueue_task("extraction", {"content_id": content_id})
```

## Phase 3: Implement Patient Zero Tracking (Stage 4)

### 3.1 Backtracking Algorithm

Create `src/stage4_tracking/backtracking.py`:

```python
from ..database.neo4j_db import get_neo4j
from ..models.verification import PatientZeroInfo

class PatientZeroTracker:
    async def track_origin(self, claim_text: str):
        neo4j = await get_neo4j()

        # Find patient zero
        patient_zero = await neo4j.find_patient_zero(claim_text)

        if not patient_zero:
            return None

        # Get propagation tree
        tree = await neo4j.get_propagation_tree(patient_zero["post_id"])

        # Identify amplifiers
        amplifiers = await neo4j.identify_amplifiers(patient_zero["post_id"])

        # Get statistics
        stats = await neo4j.get_spread_statistics(patient_zero["post_id"])

        return PatientZeroInfo(
            post_id=patient_zero["post_id"],
            platform=patient_zero["platform"],
            user_id=patient_zero["user_id"],
            username=patient_zero["username"],
            # ... fill in other fields
        )
```

### 3.2 Bot Detection

Create `src/stage4_tracking/bot_detector.py`:

```python
class BotDetector:
    async def detect_bots(self):
        neo4j = await get_neo4j()

        # Detect coordinated behavior
        coordinated = await neo4j.detect_coordinated_behavior()

        # Find clusters
        clusters = await neo4j.find_coordinated_clusters()

        return {
            "coordinated_accounts": coordinated,
            "bot_clusters": clusters
        }
```

## Phase 4: Implement Response Generation (Stage 5)

### 4.1 WhatsApp Bot

Create `src/stage5_response/whatsapp_bot.py`:

```python
from twilio.rest import Client
from ..stage2_extraction.claim_extractor import ClaimExtractor
from ..stage3_verification.rag_engine import RAGEngine

class WhatsAppBot:
    def __init__(self, account_sid, auth_token, from_number):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        self.claim_extractor = ClaimExtractor()
        self.rag_engine = RAGEngine(...)

    async def process_message(self, from_number: str, message_text: str):
        # Extract claim
        # Verify
        # Format response
        # Send via Twilio
        pass

    def send_message(self, to_number: str, message: str):
        self.client.messages.create(
            from_=self.from_number,
            to=to_number,
            body=message
        )
```

### 4.2 Dashboard API

Create `src/api/dashboard.py`:

```python
from fastapi import APIRouter, Depends
from ..database.mongodb import get_mongo
from ..models.report import DashboardStats, TrendingClaim

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    mongo = await get_mongo()
    # Aggregate statistics
    return stats

@router.get("/trending", response_model=list[TrendingClaim])
async def get_trending_claims():
    redis = await get_redis()
    trending = await redis.get_trending_claims()
    return trending

@router.get("/heatmap")
async def get_geographic_heatmap():
    # Return geographic distribution data
    pass
```

### 4.3 Public API

Create `src/api/public.py`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class VerifyRequest(BaseModel):
    claim_text: str

@router.post("/verify")
async def verify_claim(request: VerifyRequest):
    # Create content object
    # Extract claims
    # Verify
    # Return result
    pass

@router.get("/claim/{claim_id}")
async def get_claim(claim_id: str):
    mongo = await get_mongo()
    claim = await mongo.get_claim_by_id(claim_id)
    return claim
```

## Phase 5: Implement Continuous Learning (Stage 6)

### 5.1 Feedback System

Create `src/stage6_learning/feedback_processor.py`:

```python
from ..models.report import FeedbackEntry

class FeedbackProcessor:
    async def process_feedback(self, feedback: FeedbackEntry):
        # Store feedback
        mongo = await get_mongo()
        await mongo.db.feedback.insert_one(feedback.dict())

        # Update verification confidence if needed
        if not feedback.is_accurate:
            # Flag for review
            pass
```

### 5.2 A/B Testing

Create `src/stage6_learning/ab_testing.py`:

```python
import random
from ..models.report import ABTestVariant

class ABTestManager:
    def __init__(self):
        self.variants = []

    def assign_variant(self, user_id: str) -> ABTestVariant:
        # Assign user to variant
        return random.choice(self.variants)

    async def record_result(self, variant_id: str, rating: int):
        # Update variant metrics
        pass
```

## Phase 6: Integration & Background Processing

### 6.1 Create Background Worker

Create `src/worker.py`:

```python
import asyncio
from .database.redis_cache import get_redis, init_redis
from .stage2_extraction.claim_extractor import ClaimExtractor
from .stage3_verification.rag_engine import RAGEngine

async def extraction_worker():
    """Process extraction queue"""
    redis = await get_redis()
    extractor = ClaimExtractor()

    while True:
        task = await redis.dequeue_task("extraction")
        if task:
            # Extract claims
            pass
        await asyncio.sleep(1)

async def verification_worker():
    """Process verification queue"""
    redis = await get_redis()
    rag_engine = RAGEngine(...)

    while True:
        task = await redis.dequeue_task("verification")
        if task:
            # Verify claim
            pass
        await asyncio.sleep(1)

async def main():
    await init_redis(...)
    await asyncio.gather(
        extraction_worker(),
        verification_worker()
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### 6.2 Update Docker Compose

Add worker service to `docker-compose.yml`:

```yaml
  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: python -m src.worker
    depends_on:
      - mongodb
      - neo4j
      - redis
      - ollama
```

## Phase 7: Testing

### 7.1 Create Unit Tests

```bash
# Create test structure
mkdir -p tests/test_stage{1..6}

# Example test
# tests/test_stage3/test_rag_engine.py
import pytest
from src.stage3_verification.rag_engine import RAGEngine

@pytest.mark.asyncio
async def test_verify_claim():
    rag = RAGEngine(...)
    result = await rag.verify_claim(claim)
    assert result.confidence_score > 0
```

### 7.2 Integration Tests

Create `tests/integration/test_pipeline.py`:

```python
@pytest.mark.asyncio
async def test_full_pipeline():
    # Create content
    # Extract claims
    # Verify
    # Check Neo4j graph
    # Verify response
    pass
```

## Phase 8: Deployment

### 8.1 Production Configuration

Create `.env.production`:

```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
# Add production credentials
```

### 8.2 Deploy with Docker

```bash
# Build
docker-compose build

# Start in production mode
docker-compose --env-file .env.production up -d

# Scale workers
docker-compose up -d --scale worker=3
```

### 8.3 Set Up Monitoring

```bash
# Access metrics
curl http://localhost:8000/metrics

# Set up Prometheus (optional)
# Add prometheus.yml configuration
```

## Next Steps

1. **Week 1**: Implement Stage 1 monitors (Twitter, Reddit, RSS)
2. **Week 2**: Complete Stage 4 (Patient Zero tracking)
3. **Week 3**: Build Stage 5 (WhatsApp bot, Dashboard)
4. **Week 4**: Add Stage 6 (Learning mechanisms)
5. **Week 5**: Testing and integration
6. **Week 6**: Deployment and documentation

## Troubleshooting

### Ollama Connection Issues

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart if needed
docker-compose restart ollama
```

### Database Connection Issues

```bash
# Check MongoDB
docker-compose exec mongodb mongosh

# Check Neo4j
docker-compose exec neo4j cypher-shell

# Check Redis
docker-compose exec redis redis-cli ping
```

### Model Loading Issues

```bash
# Check available models
ollama list

# Pull missing models
ollama pull llama3.2
ollama pull nomic-embed-text
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Motor](https://motor.readthedocs.io/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/)
- [ChromaDB](https://docs.trychroma.com/)
- [Ollama](https://ollama.ai/)
- [Gemini API](https://ai.google.dev/)

## Getting Help

For implementation questions:
1. Check existing code examples in `src/`
2. Review data models in `src/models/`
3. Consult this guide and README.md
4. Test individual components before integration

Happy coding! 🚀
