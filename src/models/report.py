"""
Data models for reports and responses
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from .content import Claim
from .verification import VerificationResult, PatientZeroInfo


class DashboardStats(BaseModel):
    """Real-time dashboard statistics"""
    total_claims_processed: int = 0
    claims_last_24h: int = 0
    false_claims_detected: int = 0
    unverified_claims: int = 0
    average_verification_time: float = 0.0  # seconds
    trending_claims_count: int = 0
    active_crises: List[str] = Field(default_factory=list)
    top_categories: Dict[str, int] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TrendingClaim(BaseModel):
    """Trending claim information for dashboard"""
    claim_text: str
    category: str
    priority: str
    velocity: int  # Mentions in last hour
    verification_status: Optional[str] = None
    first_seen: datetime
    platforms: List[str] = Field(default_factory=list)
    geographic_spread: List[str] = Field(default_factory=list)


class DeepDiveReport(BaseModel):
    """Comprehensive deep-dive report"""
    report_id: Optional[str] = None
    claim: Claim
    verification: VerificationResult
    patient_zero: Optional[PatientZeroInfo] = None

    # Executive Summary
    executive_summary: str

    # Claim Analysis
    claim_first_detected: datetime
    claim_volume_trend: List[Dict[str, Any]] = Field(default_factory=list)
    geographic_distribution: Dict[str, int] = Field(default_factory=dict)
    platform_distribution: Dict[str, int] = Field(default_factory=dict)

    # Evidence Review
    evidence_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    contradicting_facts: List[str] = Field(default_factory=list)
    supporting_context: List[str] = Field(default_factory=list)

    # Impact Assessment
    estimated_total_reach: int = 0
    unique_sharers: int = 0
    bot_activity_percentage: float = 0.0
    high_influence_amplifiers: List[Dict[str, Any]] = Field(default_factory=list)
    potential_harm_level: str = "low"  # low, medium, high, critical

    # Recommendations
    recommended_actions: List[str] = Field(default_factory=list)
    target_audiences: List[str] = Field(default_factory=list)
    correction_strategy: Optional[str] = None

    # Multimedia
    related_images: List[str] = Field(default_factory=list)
    propagation_graph_url: Optional[str] = None
    timeline_visualization_url: Optional[str] = None

    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = "KnowInfo System"


class WhatsAppQuery(BaseModel):
    """WhatsApp bot query"""
    query_id: Optional[str] = None
    user_phone: str
    message_text: Optional[str] = None
    media_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WhatsAppResponse(BaseModel):
    """WhatsApp bot response"""
    query_id: str
    response_text: str
    verification_result: Optional[VerificationResult] = None
    response_time_seconds: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FeedbackEntry(BaseModel):
    """User feedback on verification"""
    feedback_id: Optional[str] = None
    verification_id: str
    user_id: Optional[str] = None
    rating: int = Field(ge=1, le=5)  # 1-5 stars
    is_accurate: Optional[bool] = None
    is_helpful: Optional[bool] = None
    comments: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ABTestVariant(BaseModel):
    """A/B test variant for explanation formats"""
    variant_id: str
    variant_name: str
    explanation_template: str
    user_count: int = 0
    avg_rating: float = 0.0
    comprehension_score: float = 0.0
    engagement_rate: float = 0.0
