# KnowInfo - Quick Reference Guide

## 🚀 Getting Started (5 Minutes)

### 1. One-Command Setup
```bash
./scripts/quickstart.sh
```

### 2. Manual Setup
```bash
# 1. Environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# 2. Start services
docker-compose up -d

# 3. Setup Ollama (optional, for local models)
./scripts/setup_ollama.sh

# 4. Seed knowledge base
python scripts/seed_knowledge_base.py

# 5. Start API
python main.py
```

### 3. Verify Installation
```bash
# Check health
curl http://localhost:8000/health

# Should return: {"status": "healthy", "components": {...}}
```

## 📁 Project Structure (30 Second Overview)

```
KnowInfo/
├── main.py                      # Start here - FastAPI app
├── config.py                    # All configuration
│
├── src/
│   ├── database/                # MongoDB, Neo4j, Redis managers
│   ├── models/                  # Data models (content, verification, report)
│   ├── utils/                   # Logger, metrics, guardrails, model_manager
│   ├── stage1_ingestion/        # Social media monitors
│   ├── stage2_extraction/       # Claim extraction (AI)
│   ├── stage3_verification/     # RAG verification engine
│   ├── stage4_tracking/         # Patient zero tracking
│   ├── stage5_response/         # WhatsApp bot, dashboard
│   └── stage6_learning/         # Feedback and learning
│
├── scripts/
│   ├── quickstart.sh            # Automated setup
│   ├── setup_ollama.sh          # Download AI models
│   └── seed_knowledge_base.py   # Load initial data
│
└── Documentation:
    ├── README.md                # User guide
    ├── IMPLEMENTATION_GUIDE.md  # Developer guide
    ├── ARCHITECTURE.md          # System design
    └── QUICK_REFERENCE.md       # This file
```

## 🔑 Key Configuration (.env)

### Minimum Configuration
```bash
# Choose ONE:
GEMINI_API_KEY=your_key        # Recommended (cost-effective)
# OR
# Use Ollama (free, local) - no key needed
```

### Full Configuration
```bash
# AI Models
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key        # Optional
USE_LOCAL_MODELS_FIRST=true    # Try Ollama first

# Social Media (for monitoring)
TWITTER_BEARER_TOKEN=your_token
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token

# WhatsApp Bot
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
```

## 🎯 Core Components (What Does What)

### Database Managers
```python
# MongoDB - Content storage
from src.database.mongodb import get_mongo
mongo = await get_mongo()
await mongo.store_content(content_dict)

# Neo4j - Graph tracking
from src.database.neo4j_db import get_neo4j
neo4j = await get_neo4j()
patient_zero = await neo4j.find_patient_zero(claim_text)

# Redis - Caching
from src.database.redis_cache import get_redis
redis = await get_redis()
await redis.cache_verification(claim_text, result)
```

### Model Manager
```python
from src.utils.model_manager import get_model_manager

model_manager = get_model_manager()

# Generate text (auto-fallback: Ollama → Gemini → OpenAI)
text = await model_manager.generate_text(
    prompt="Extract claims from this text...",
    temperature=0.7
)

# Generate embeddings
embeddings = await model_manager.generate_embeddings(["text1", "text2"])

# Classify text
categories = await model_manager.classify_text(
    text="This is a health claim...",
    categories=["health", "political", "economic"]
)
```

### Claim Extraction
```python
from src.stage2_extraction.claim_extractor import ClaimExtractor
from src.models.content import Content, SourcePlatform

extractor = ClaimExtractor()
content = Content(
    source=SourcePlatform.TWITTER,
    text="Your text here...",
    # ... other fields
)
claims = await extractor.extract_claims(content)
```

### Verification
```python
from src.stage3_verification.rag_engine import RAGEngine

rag = RAGEngine(
    knowledge_base_path="./data/knowledge_base",
    vector_db_path="./data/vector_db"
)
verification = await rag.verify_claim(claim)

print(verification.status)           # TRUE, FALSE, MISLEADING, UNVERIFIED
print(verification.confidence_score) # 0-100
print(verification.explanation)      # 3-sentence explanation
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f mongodb

# Restart a service
docker-compose restart api

# Scale workers
docker-compose up -d --scale worker=3

# Access Neo4j browser
# http://localhost:7474 (user: neo4j, pass: knowinfo_password)

# Access MongoDB shell
docker-compose exec mongodb mongosh

# Access Redis CLI
docker-compose exec redis redis-cli
```

## 🔍 Testing & Debugging

### Manual Test: Verify a Claim
```python
import asyncio
from datetime import datetime
from src.models.content import Content, SourcePlatform
from src.stage2_extraction.claim_extractor import ClaimExtractor
from src.stage3_verification.rag_engine import RAGEngine
from src.utils.model_manager import init_model_manager
from config import settings

async def test_verification():
    # Initialize
    init_model_manager(
        ollama_base_url=settings.ollama_base_url,
        gemini_api_key=settings.gemini_api_key,
        use_local_first=True
    )

    # Create test content
    content = Content(
        content_id="test1",
        source=SourcePlatform.TWITTER,
        platform_id="123",
        text="WHO says vaccines are dangerous",
        author_id="user123",
        author_username="testuser",
        author_followers=1000,
        created_at=datetime.utcnow()
    )

    # Extract claims
    extractor = ClaimExtractor()
    claims = await extractor.extract_claims(content)
    print(f"Extracted {len(claims)} claims")

    # Verify first claim
    if claims:
        rag = RAGEngine("./data/knowledge_base", "./data/vector_db")
        result = await rag.verify_claim(claims[0])

        print(f"\nStatus: {result.status}")
        print(f"Confidence: {result.confidence_score}%")
        print(f"Explanation: {result.explanation}")
        print(f"Sources: {len(result.sources)}")

asyncio.run(test_verification())
```

### Check System Health
```bash
# API health
curl http://localhost:8000/health

# Database connectivity
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
docker-compose exec neo4j cypher-shell -u neo4j -p knowinfo_password "RETURN 1"
docker-compose exec redis redis-cli ping

# Ollama models
curl http://localhost:11434/api/tags
```

### View Metrics
```bash
curl http://localhost:8000/metrics

# Look for:
# - content_ingested_total
# - claims_extracted_total
# - verifications_completed_total
# - verification_duration_seconds
```

## 🚨 Common Issues & Solutions

### 1. "Model not found" Error
```bash
# Pull Ollama models
docker-compose exec ollama ollama pull llama3.2
docker-compose exec ollama ollama pull nomic-embed-text

# Or set GEMINI_API_KEY in .env
```

### 2. "MongoDB connection failed"
```bash
# Check MongoDB is running
docker-compose ps mongodb

# Restart if needed
docker-compose restart mongodb

# Check logs
docker-compose logs mongodb
```

### 3. "No module named 'src'"
```bash
# Ensure you're in project root
cd /path/to/KnowInfo

# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### 4. "Port already in use"
```bash
# Find and kill process using port
lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml
```

### 5. "ChromaDB not initialized"
```bash
# Seed knowledge base
python scripts/seed_knowledge_base.py

# Check data directory exists
ls -la data/vector_db/
```

## 📊 API Endpoints (When Fully Implemented)

```bash
# Health check
GET /health

# Metrics
GET /metrics

# Verify claim
POST /api/v1/verify
{
  "claim_text": "Your claim here"
}

# Get claim details
GET /api/v1/claim/{claim_id}

# Dashboard stats
GET /api/dashboard/stats

# Trending claims
GET /api/dashboard/trending

# WhatsApp webhook
POST /api/whatsapp/webhook
```

## 💡 Quick Tips

### 1. Use Local Models First (Save Money)
```bash
# In .env
USE_LOCAL_MODELS_FIRST=true
OLLAMA_BASE_URL=http://localhost:11434
```

### 2. Monitor Performance
```bash
# Watch logs in real-time
docker-compose logs -f api | grep "verification"

# Check metrics
watch -n 5 'curl -s http://localhost:8000/metrics | grep verification'
```

### 3. Add Custom Sources
```python
from src.stage3_verification.rag_engine import RAGEngine

rag = RAGEngine(...)
await rag.add_source_to_knowledge_base(
    title="My Authoritative Source",
    content="Important factual content...",
    url="https://example.com",
    source_type="government",
    credibility="high"
)
```

### 4. Batch Processing
```python
# Queue multiple claims for processing
from src.database.redis_cache import get_redis

redis = await get_redis()
for claim in claims:
    await redis.enqueue_task("verification", {"claim_id": claim.claim_id})
```

## 🎓 Learning Path

### Day 1: Setup & Basics
1. Run quickstart.sh
2. Test verification with example code
3. Explore database in Neo4j browser

### Day 2: Understanding Core
1. Read ARCHITECTURE.md
2. Review data models in src/models/
3. Test different LLM providers

### Day 3: Implementation
1. Follow IMPLEMENTATION_GUIDE.md
2. Implement Twitter monitor
3. Build WhatsApp webhook

### Week 2: Full System
1. Complete all monitors
2. Build dashboard
3. Deploy to production

## 📚 Further Reading

- **README.md**: Comprehensive user guide
- **ARCHITECTURE.md**: System design and data flow
- **IMPLEMENTATION_GUIDE.md**: Step-by-step development guide
- **PROJECT_SUMMARY.md**: What's built and what's left
- **API Docs**: http://localhost:8000/docs (when running)

## 🆘 Getting Help

1. Check this quick reference
2. Review error logs: `docker-compose logs -f`
3. Test individual components in isolation
4. Consult implementation guide for code examples
5. Review source code - it's well-documented!

---

**Remember**: Start simple, test often, scale gradually.

Good luck building! 🚀
