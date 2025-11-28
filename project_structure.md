# KnowInfo - Crisis Misinformation Detection System

## Project Structure

```
KnowInfo/
├── README.md
├── requirements.txt
├── .env.example
├── config.py
├── main.py                          # FastAPI application entry point
│
├── src/
│   ├── __init__.py
│   │
│   ├── stage1_ingestion/            # STAGE 1: Ingestion & Monitoring
│   │   ├── __init__.py
│   │   ├── monitors.py              # Base monitor class
│   │   ├── twitter_monitor.py       # Twitter/X API monitoring
│   │   ├── reddit_monitor.py        # Reddit monitoring
│   │   ├── telegram_monitor.py      # Telegram monitoring
│   │   ├── rss_monitor.py           # RSS feed aggregation
│   │   ├── trend_detector.py        # Velocity-based trend detection
│   │   └── filters.py               # Language, sentiment, relevance filters
│   │
│   ├── stage2_extraction/           # STAGE 2: Claim Extraction & Categorization
│   │   ├── __init__.py
│   │   ├── claim_extractor.py       # NLP-based claim extraction
│   │   ├── categorizer.py           # Claim category classification
│   │   ├── priority_ranker.py       # P0-P3 priority assignment
│   │   └── media_analyzer.py        # Image/video analysis
│   │
│   ├── stage3_verification/         # STAGE 3: Verification (NotebookLM RAG)
│   │   ├── __init__.py
│   │   ├── rag_engine.py            # NotebookLM RAG implementation
│   │   ├── source_manager.py        # Manage authoritative sources
│   │   ├── cross_reference.py       # Cross-referencing logic
│   │   └── confidence_scorer.py     # Consensus confidence calculation
│   │
│   ├── stage4_tracking/             # STAGE 4: Patient Zero Tracking
│   │   ├── __init__.py
│   │   ├── graph_manager.py         # Neo4j graph database operations
│   │   ├── backtracking.py          # Patient zero identification
│   │   ├── propagation_mapper.py    # Spread visualization
│   │   └── bot_detector.py          # Inauthentic behavior detection
│   │
│   ├── stage5_response/             # STAGE 5: Response Generation
│   │   ├── __init__.py
│   │   ├── whatsapp_bot.py          # WhatsApp bot interface
│   │   ├── dashboard_api.py         # Dashboard API endpoints
│   │   ├── report_generator.py      # Deep-dive portal reports
│   │   └── formatters.py            # Response formatting utilities
│   │
│   ├── stage6_learning/             # STAGE 6: Continuous Learning
│   │   ├── __init__.py
│   │   ├── feedback_processor.py    # User feedback integration
│   │   ├── ab_testing.py            # Explanation format experiments
│   │   ├── pattern_library.py       # Successful debunk templates
│   │   └── adversarial_training.py  # Adversarial simulation
│   │
│   ├── database/                    # Database Management
│   │   ├── __init__.py
│   │   ├── mongodb.py               # MongoDB connection & operations
│   │   ├── neo4j_db.py              # Neo4j connection & operations
│   │   └── redis_cache.py           # Redis caching layer
│   │
│   ├── models/                      # Data Models
│   │   ├── __init__.py
│   │   ├── content.py               # Content model (posts, claims)
│   │   ├── verification.py          # Verification result model
│   │   ├── user.py                  # User/account model
│   │   └── report.py                # Report model
│   │
│   ├── utils/                       # Utilities
│   │   ├── __init__.py
│   │   ├── logger.py                # Structured logging
│   │   ├── metrics.py               # Prometheus metrics
│   │   └── guardrails.py            # Safety guardrails
│   │
│   └── api/                         # API Routes
│       ├── __init__.py
│       ├── whatsapp.py              # WhatsApp webhook
│       ├── dashboard.py             # Dashboard endpoints
│       └── public.py                # Public API endpoints
│
├── data/                            # Data Storage
│   ├── vector_db/                   # Vector database for RAG
│   ├── knowledge_base/              # Authoritative source documents
│   └── models/                      # Downloaded ML models
│
├── tests/                           # Tests
│   ├── __init__.py
│   ├── test_stage1/
│   ├── test_stage2/
│   ├── test_stage3/
│   ├── test_stage4/
│   ├── test_stage5/
│   └── test_stage6/
│
├── scripts/                         # Utility Scripts
│   ├── setup_databases.py           # Initialize databases
│   ├── seed_knowledge_base.py       # Populate knowledge base
│   └── download_models.py           # Download NLP models
│
└── docker/                          # Docker Configuration
    ├── Dockerfile
    ├── docker-compose.yml
    └── .dockerignore
```

## Implementation Phases

### Phase 1: Core Infrastructure
- Project setup and dependencies
- Database connections (MongoDB, Neo4j, Redis)
- Logging and monitoring setup
- Basic API structure

### Phase 2: Stage 1 - Ingestion
- Social media monitors (Twitter, Reddit, Telegram)
- RSS feed aggregation
- Trend detection algorithm
- Content filtering pipeline

### Phase 3: Stage 2 - Claim Extraction
- NLP claim extraction
- Category classification
- Priority ranking
- Media analysis (images/videos)

### Phase 4: Stage 3 - Verification
- NotebookLM RAG implementation
- Source management system
- Cross-referencing engine
- Confidence scoring

### Phase 5: Stage 4 - Patient Zero
- Neo4j graph modeling
- Backtracking algorithm
- Propagation visualization
- Bot detection

### Phase 6: Stage 5 - Response
- WhatsApp bot implementation
- Dashboard API
- Report generation
- Multi-format output

### Phase 7: Stage 6 - Learning
- Feedback integration
- A/B testing framework
- Pattern library
- Adversarial training

### Phase 8: Testing & Deployment
- Comprehensive testing
- Performance optimization
- Docker containerization
- Production deployment
