# KnowInfo - Crisis Misinformation Detection System

A real-time AI-powered system for detecting, verifying, and correcting misinformation during global crises.

## 🎯 Features

- **Multi-Source Monitoring**: Ingests content from Twitter/X, Reddit, Telegram, and RSS feeds
- **AI-Powered Claim Extraction**: Uses LLMs (Ollama, Gemini, OpenAI) to extract verifiable claims
- **RAG-Based Verification**: Cross-references claims against authoritative sources (WHO, CDC, Reuters, etc.)
- **Patient Zero Tracking**: Graph-based analysis to trace misinformation origins and spread
- **WhatsApp Bot**: Instant fact-checking via WhatsApp
- **Real-Time Dashboard**: Live monitoring of trending false claims
- **Continuous Learning**: A/B testing and feedback integration

## 🏗️ Architecture

### 6-Stage Pipeline

```
Stage 1: Ingestion → Stage 2: Extraction → Stage 3: Verification
                                              ↓
Stage 6: Learning ← Stage 5: Response ← Stage 4: Tracking
```

1. **Ingestion & Monitoring**: Stream content from social media platforms
2. **Claim Extraction**: NLP-based extraction and categorization (P0-P3 priority)
3. **Verification**: RAG engine with vector database for fact-checking
4. **Patient Zero Tracking**: Neo4j graph for propagation analysis
5. **Response Generation**: WhatsApp bot, Dashboard API, Deep-dive reports
6. **Continuous Learning**: Feedback loops and adversarial training

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- (Optional) NVIDIA GPU for local models
- API Keys (optional): Gemini, OpenAI, or Anthropic

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd KnowInfo
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. **Start services with Docker Compose**
```bash
docker-compose up -d
```

This will start:
- MongoDB (port 27017)
- Neo4j (ports 7474, 7687)
- Redis (port 6379)
- Ollama (port 11434)
- KnowInfo API (port 8000)

4. **Setup Ollama models** (if using local models)
```bash
chmod +x scripts/setup_ollama.sh
./scripts/setup_ollama.sh
```

5. **Seed the knowledge base**
```bash
docker-compose exec api python scripts/seed_knowledge_base.py
```

6. **Access the system**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474
- Health Check: http://localhost:8000/health

## 🔧 Configuration

### Model Selection

KnowInfo supports multiple LLM providers. Configure in `.env`:

```bash
# Use local models first (free, private)
USE_LOCAL_MODELS_FIRST=true

# Ollama (local, free)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_EMBEDDING=nomic-embed-text
OLLAMA_MODEL_EXTRACTION=llama3.2

# Gemini (recommended for API)
GEMINI_API_KEY=your_key_here

# OpenAI (alternative)
OPENAI_API_KEY=your_key_here
```

### Social Media APIs

Configure social media monitoring:

```bash
# Twitter/X
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_BEARER_TOKEN=your_token

# Reddit
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret

# Telegram
TELEGRAM_BOT_TOKEN=your_token

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
```

## 📊 Usage Examples

### Verifying a Claim (Python)

```python
import asyncio
from src.stage2_extraction.claim_extractor import ClaimExtractor
from src.stage3_verification.rag_engine import RAGEngine
from src.models.content import Content, SourcePlatform
from datetime import datetime

async def verify_claim_example():
    # Create content
    content = Content(
        content_id="test123",
        source=SourcePlatform.TWITTER,
        platform_id="12345",
        text="Breaking: WHO announces new miracle cure for COVID-19",
        author_id="user123",
        author_username="newsbot",
        created_at=datetime.utcnow()
    )

    # Extract claims
    extractor = ClaimExtractor()
    claims = await extractor.extract_claims(content)

    # Verify first claim
    if claims:
        rag_engine = RAGEngine(
            knowledge_base_path="./data/knowledge_base",
            vector_db_path="./data/vector_db"
        )
        verification = await rag_engine.verify_claim(claims[0])

        print(f"Status: {verification.status}")
        print(f"Confidence: {verification.confidence_score}%")
        print(f"Explanation: {verification.explanation}")

asyncio.run(verify_claim_example())
```

### API Usage

```bash
# Check system health
curl http://localhost:8000/health

# Get metrics
curl http://localhost:8000/metrics

# Verify claim via API (when implemented)
curl -X POST http://localhost:8000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"claim_text": "WHO says vaccines cause autism"}'
```

## 🗄️ Database Schema

### MongoDB Collections

- **contents**: Raw social media posts
- **claims**: Extracted verifiable claims
- **verifications**: Verification results

### Neo4j Graph Model

```
(User)-[:POSTED]->(Post)-[:CONTAINS]->(Claim)
(Post)-[:SHARED_FROM]->(OriginalPost)
```

### Redis Keys

- `verification:{hash}`: Cached verification results
- `velocity:{claim_hash}`: Trending claim counters
- `rate_limit:{user_id}`: Rate limiting
- `queue:{queue_name}`: Background task queues

## 📈 Monitoring & Metrics

### Prometheus Metrics

- `content_ingested_total`: Total content items by source
- `claims_extracted_total`: Claims by category/priority
- `verifications_completed_total`: Verifications by status
- `verification_duration_seconds`: Verification latency
- `whatsapp_queries_total`: WhatsApp bot usage

Access metrics at: `http://localhost:8000/metrics`

## 🛡️ Safety Guardrails

### Built-in Protections

1. **Confidence Thresholds**: Won't declare claims false with <80% confidence
2. **Precautionary Principle**: Flags potentially harmful claims even without full verification
3. **Privacy Compliance**: Automatically redacts PII
4. **Bias Mitigation**: Audits source diversity and political balance
5. **Expert Review**: Flags low-confidence and P0 claims for human review

### Priority Levels

- **P0**: Imminent physical harm (evacuation orders, poisoned supplies)
- **P1**: Medical misinformation during health crises
- **P2**: False attribution to authorities
- **P3**: Other verifiable false claims

## 🔌 Extending the System

### Adding New Sources

Create a new monitor in `src/stage1_ingestion/`:

```python
from .base_monitor import BaseMonitor
from ..models.content import Content, SourcePlatform

class MyPlatformMonitor(BaseMonitor):
    async def stream_content(self):
        # Implement platform-specific streaming
        while self.is_running:
            # Fetch content
            yield Content(...)
```

### Adding Knowledge Sources

```python
from src.stage3_verification.rag_engine import RAGEngine

rag = RAGEngine(...)
await rag.add_source_to_knowledge_base(
    title="New Authoritative Source",
    content="Content text...",
    url="https://example.com",
    source_type="government",
    credibility="high"
)
```

## 🧪 Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=src tests/

# Specific stage
pytest tests/test_stage3/
```

## 📁 Project Structure

```
KnowInfo/
├── config.py                    # Configuration management
├── main.py                      # FastAPI application
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Docker services
│
├── src/
│   ├── database/                # Database managers
│   ├── models/                  # Pydantic data models
│   ├── utils/                   # Utilities (logging, metrics, etc.)
│   ├── stage1_ingestion/        # Content monitoring
│   ├── stage2_extraction/       # Claim extraction
│   ├── stage3_verification/     # RAG verification
│   ├── stage4_tracking/         # Patient zero tracking
│   ├── stage5_response/         # WhatsApp bot, dashboard
│   └── stage6_learning/         # Continuous learning
│
├── scripts/                     # Setup and utility scripts
├── tests/                       # Test suites
└── data/                        # Data storage
    ├── vector_db/               # ChromaDB vector database
    └── knowledge_base/          # Source documents
```

## 🔒 Security Considerations

- Store API keys in `.env` (never commit)
- Use environment-specific configurations
- Implement rate limiting (included)
- Sanitize user inputs
- Audit source selection for bias
- Regular security updates

## 📝 Roadmap

### Phase 1: Core Infrastructure ✅
- [x] Database setup
- [x] Model manager with Gemini/Ollama support
- [x] Basic claim extraction
- [x] RAG verification engine

### Phase 2: Full Pipeline (In Progress)
- [ ] Twitter/Reddit/Telegram monitors
- [ ] Complete WhatsApp bot
- [ ] Dashboard API
- [ ] Patient zero tracking

### Phase 3: Advanced Features
- [ ] Image/video analysis (deepfake detection)
- [ ] Multi-language support
- [ ] Mobile apps
- [ ] Browser extension

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📜 License

[Add your license here]

## 🙏 Acknowledgments

- Authoritative sources: WHO, CDC, Reuters, AP
- Open-source tools: FastAPI, MongoDB, Neo4j, ChromaDB, Ollama
- LLM providers: Google (Gemini), Meta (LLaMA), OpenAI

## 📧 Contact

[Add contact information]

---

**Note**: This system is designed for authorized crisis response use. Ensure compliance with platform terms of service and local regulations when deploying