"""
Data models for verification results
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class VerificationStatus(str, Enum):
    """Verification status"""
    TRUE = "true"
    FALSE = "false"
    MISLEADING = "misleading"
    UNVERIFIED = "unverified"
    OUTDATED = "outdated"


class SourceCredibility(str, Enum):
    """Source credibility levels"""
    HIGH = "high"  # WHO, CDC, Reuters, AP
    MEDIUM = "medium"  # Reputable news, government sites
    LOW = "low"  # Social media, blogs
    UNKNOWN = "unknown"


class VerificationSource(BaseModel):
    """Source document used in verification"""
    source_id: str
    title: str
    url: Optional[str] = None
    source_type: str  # "news", "government", "medical", "fact_check"
    credibility: SourceCredibility
    publication_date: Optional[datetime] = None
    relevant_excerpt: Optional[str] = None
    supports_claim: bool  # True if supports, False if contradicts
    relevance_score: float = Field(ge=0.0, le=1.0)

    class Config:
        use_enum_values = True


class VerificationResult(BaseModel):
    """Complete verification result for a claim"""
    verification_id: Optional[str] = None
    claim_id: Optional[str] = None
    claim_text: str
    status: VerificationStatus
    confidence_score: float = Field(ge=0.0, le=100.0)
    sources: List[VerificationSource] = Field(default_factory=list)
    explanation: str  # 3-sentence explanation
    detailed_analysis: Optional[str] = None
    supporting_sources_count: int = 0
    contradicting_sources_count: int = 0
    consensus_type: str  # "unanimous", "majority", "split"
    fact_check_urls: List[str] = Field(default_factory=list)
    verification_timestamp: datetime = Field(default_factory=datetime.utcnow)
    verified_by: str = "automated"  # "automated" or "expert"
    expert_review_required: bool = False
    temporal_context: Optional[str] = None  # If info is outdated
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True

    def get_emoji_status(self) -> str:
        """Get emoji representation of status"""
        emoji_map = {
            VerificationStatus.TRUE: "✅",
            VerificationStatus.FALSE: "❌",
            VerificationStatus.MISLEADING: "⚠️",
            VerificationStatus.UNVERIFIED: "🔍",
            VerificationStatus.OUTDATED: "📅"
        }
        return emoji_map.get(self.status, "❓")

    def to_whatsapp_response(self) -> str:
        """Format verification result for WhatsApp"""
        emoji = self.get_emoji_status()
        response = f"{emoji} {self.status.upper()}\n\n"
        response += f"{self.explanation}\n\n"

        if self.sources[:2]:  # Top 2 sources
            response += "Sources:\n"
            for source in self.sources[:2]:
                if source.url:
                    response += f"• {source.title}: {source.url}\n"

        return response


class PatientZeroInfo(BaseModel):
    """Information about the origin of misinformation"""
    post_id: str
    platform: str
    user_id: str
    username: str
    followers_count: int
    post_text: str
    post_timestamp: datetime
    current_spread_count: int = 0
    total_reach: int = 0
    amplifiers: List[Dict[str, Any]] = Field(default_factory=list)
    propagation_depth: int = 0


class PropagationNode(BaseModel):
    """Node in the propagation tree"""
    post_id: str
    user_id: str
    username: str
    followers_count: int
    timestamp: datetime
    depth: int  # Distance from patient zero
    parent_post_id: Optional[str] = None
    children_count: int = 0
