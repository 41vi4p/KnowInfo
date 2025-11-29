"""
Configuration management for KnowInfo Crisis Misinformation Detection System
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # API Keys (Optional - at least one should be set)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    # Local Models (Ollama)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model_embedding: str = "nomic-embed-text"
    ollama_model_classification: str = "qwen3"
    ollama_model_extraction: str = "qwen3"

    # Model Selection Strategy
    use_local_models_first: bool = True  # Try Ollama first, fallback to API

    # Social Media APIs (No Twitter API needed - uses Playwright)
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str = "KnowInfo/1.0"

    # Messaging Bots (ALL FREE!)
    telegram_bot_token: str  # Get from @BotFather on Telegram (FREE!)
    telegram_api_id: Optional[str] = None  # For monitoring public channels (get from my.telegram.org)
    telegram_api_hash: Optional[str] = None
    telegram_monitor_channels: list[str] = ["telegram", "durov", "cnn", "bbcnews"]

    # WhatsApp via PyWhatKit (FREE - no Twilio!)
    # No configuration needed - uses WhatsApp Web automation

    # Database
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "knowinfo"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str

    redis_url: str = "redis://localhost:6379/0"

    # RAG Configuration
    vector_db_path: str = "./data/vector_db"
    knowledge_base_path: str = "./data/knowledge_base"

    # External Services
    google_custom_search_api_key: Optional[str] = None
    google_custom_search_engine_id: Optional[str] = None

    # Application Settings
    environment: str = "development"
    log_level: str = "INFO"
    api_port: int = 8000

    # Rate Limiting
    max_requests_per_hour_free: int = 1000
    max_requests_per_hour_enterprise: str = "unlimited"

    # Detection Thresholds
    velocity_spike_threshold: int = 500
    similarity_threshold: float = 0.85
    confidence_threshold_low: int = 60
    confidence_threshold_high: int = 80

    # Crisis Keywords for Monitoring
    crisis_keywords: list[str] = [
        "earthquake", "hurricane", "flood", "wildfire", "pandemic",
        "outbreak", "evacuation", "emergency", "disaster", "terror",
        "shooting", "explosion", "crash", "breaking"
    ]

    # Priority Categories
    priority_p0_keywords: list[str] = [
        "evacuation", "poisoned", "contaminated", "imminent threat",
        "shelter in place", "lockdown"
    ]

    # RSS Feed Sources
    rss_feeds: list[str] = [
        "https://feeds.reuters.com/reuters/topNews",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.who.int/rss-feeds/news-english.xml",
        "https://www.cdc.gov/cdcnews/rss/rss.xml",
        "https://www.bbc.com/news/world/rss.xml",
    ]


# Global settings instance
settings = Settings()
