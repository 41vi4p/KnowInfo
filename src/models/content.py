"""
Data models for content and claims
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SourcePlatform(str, Enum):
    """Supported source platforms"""
    TWITTER = "twitter"
    REDDIT = "reddit"
    TELEGRAM = "telegram"
    RSS = "rss"
    WHATSAPP = "whatsapp"


class ContentStatus(str, Enum):
    """Content processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    VERIFIED = "verified"
    COMPLETED = "completed"
    FAILED = "failed"


class Content(BaseModel):
    """Raw content from social media monitoring"""
    content_id: Optional[str] = None
    source: SourcePlatform
    platform_id: str  # Original post/tweet ID from platform
    text: str
    author_id: str
    author_username: str
    author_followers: int = 0
    url: Optional[str] = None
    media_urls: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    engagement_count: int = 0  # likes + shares + comments
    reach: int = 0
    created_at: datetime
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    status: ContentStatus = ContentStatus.PENDING
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class ClaimCategory(str, Enum):
    """Claim categories"""
    HEALTH_MEDICAL = "health_medical"
    POLITICAL_GEOPOLITICAL = "political_geopolitical"
    ENVIRONMENTAL_CLIMATE = "environmental_climate"
    ECONOMIC = "economic"
    SAFETY_SECURITY = "safety_security"
    OTHER = "other"


class ClaimPriority(str, Enum):
    """Claim priority levels"""
    P0 = "P0"  # Imminent physical harm
    P1 = "P1"  # Medical misinformation during health crises
    P2 = "P2"  # False attribution to authorities
    P3 = "P3"  # Other verifiable false claims


class Claim(BaseModel):
    """Extracted claim from content"""
    claim_id: Optional[str] = None
    content_id: str  # Reference to source content
    claim_text: str
    category: ClaimCategory
    priority: ClaimPriority
    entities: List[Dict[str, str]] = Field(default_factory=list)  # Named entities
    keywords: List[str] = Field(default_factory=list)
    context: Optional[str] = None
    is_image_based: bool = False
    image_analysis: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class MediaType(str, Enum):
    """Media types"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class MediaAnalysis(BaseModel):
    """Results from image/video analysis"""
    media_url: str
    media_type: MediaType
    reverse_search_results: List[Dict[str, Any]] = Field(default_factory=list)
    earliest_occurrence: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)  # EXIF, creation date, etc.
    deepfake_probability: Optional[float] = None
    ocr_text: Optional[str] = None
    detected_objects: List[str] = Field(default_factory=list)
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
