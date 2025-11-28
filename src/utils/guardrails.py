"""
Safety guardrails and bias mitigation
"""
import structlog
from typing import Dict, Any, Optional
from ..models.verification import VerificationResult, VerificationStatus

logger = structlog.get_logger(__name__)


class GuardrailsManager:
    """Manages safety checks and bias mitigation"""

    def __init__(
        self,
        confidence_threshold_low: int = 60,
        confidence_threshold_high: int = 80
    ):
        self.confidence_threshold_low = confidence_threshold_low
        self.confidence_threshold_high = confidence_threshold_high

        # Sensitive topics that require extra care
        self.sensitive_topics = {
            "medical", "health", "vaccine", "medication", "treatment",
            "emergency", "evacuation", "disaster", "terror", "attack",
            "election", "voting", "political", "government"
        }

        # Privacy-sensitive patterns
        self.privacy_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{16}\b",  # Credit card
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
        ]

    def check_confidence_threshold(
        self,
        verification: VerificationResult
    ) -> tuple[bool, Optional[str]]:
        """
        Check if verification meets confidence requirements
        Returns: (should_proceed, warning_message)
        """
        if verification.confidence_score < self.confidence_threshold_low:
            return False, "Confidence too low - requires expert review"

        if (
            verification.confidence_score < self.confidence_threshold_high
            and verification.status in [VerificationStatus.FALSE, VerificationStatus.MISLEADING]
        ):
            logger.warning(
                "Low confidence on harmful claim",
                confidence=verification.confidence_score,
                claim=verification.claim_text[:100]
            )
            return True, "Moderate confidence - flagged for review"

        return True, None

    def apply_precautionary_principle(
        self,
        claim_text: str,
        verification: Optional[VerificationResult]
    ) -> bool:
        """
        Apply precautionary principle for potentially harmful claims
        Returns: True if claim should be flagged even without full verification
        """
        # Check for sensitive topics
        claim_lower = claim_text.lower()
        is_sensitive = any(topic in claim_lower for topic in self.sensitive_topics)

        if is_sensitive and (
            verification is None or
            verification.status == VerificationStatus.UNVERIFIED
        ):
            logger.warning(
                "Sensitive claim detected without verification",
                claim=claim_text[:100]
            )
            return True

        # Check for emergency-related keywords
        emergency_keywords = ["evacuation", "emergency", "immediate danger", "poisoned"]
        if any(keyword in claim_lower for keyword in emergency_keywords):
            logger.critical(
                "Emergency claim detected - immediate attention required",
                claim=claim_text[:100]
            )
            return True

        return False

    def check_privacy_compliance(self, text: str) -> tuple[bool, list[str]]:
        """
        Check if text contains personally identifiable information
        Returns: (is_compliant, found_patterns)
        """
        import re
        found_patterns = []

        for pattern in self.privacy_patterns:
            if re.search(pattern, text):
                found_patterns.append(pattern)

        is_compliant = len(found_patterns) == 0
        if not is_compliant:
            logger.warning("PII detected in content", patterns=found_patterns)

        return is_compliant, found_patterns

    def check_bias_in_sources(
        self,
        sources: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Audit sources for potential political or cultural bias
        """
        if not sources:
            return {"bias_detected": False, "warnings": []}

        # Count sources by type
        source_types = {}
        political_leanings = {"left": 0, "center": 0, "right": 0}

        for source in sources:
            source_type = source.get("source_type", "unknown")
            source_types[source_type] = source_types.get(source_type, 0) + 1

            # Note: In production, integrate with media bias databases
            # This is a simplified example
            source_name = source.get("title", "").lower()
            if any(term in source_name for term in ["guardian", "msnbc", "cnn"]):
                political_leanings["left"] += 1
            elif any(term in source_name for term in ["reuters", "ap", "bbc"]):
                political_leanings["center"] += 1
            elif any(term in source_name for term in ["fox", "breitbart"]):
                political_leanings["right"] += 1

        warnings = []

        # Check for political imbalance
        total_political = sum(political_leanings.values())
        if total_political > 0:
            max_leaning = max(political_leanings.values())
            if max_leaning / total_political > 0.7:
                warnings.append("Political bias detected in source selection")

        # Check for source diversity
        if len(source_types) < 2 and len(sources) > 3:
            warnings.append("Low source diversity - consider broader sources")

        return {
            "bias_detected": len(warnings) > 0,
            "warnings": warnings,
            "source_distribution": source_types,
            "political_balance": political_leanings
        }

    def sanitize_output(self, text: str) -> str:
        """Remove or redact sensitive information from output"""
        import re
        sanitized = text

        # Redact email addresses
        sanitized = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL REDACTED]',
            sanitized
        )

        # Redact phone numbers
        sanitized = re.sub(
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            '[PHONE REDACTED]',
            sanitized
        )

        return sanitized

    def require_expert_review(
        self,
        verification: VerificationResult,
        claim_text: str
    ) -> tuple[bool, str]:
        """
        Determine if expert review is required
        Returns: (requires_review, reason)
        """
        # Low confidence
        if verification.confidence_score < self.confidence_threshold_low:
            return True, "Low confidence score"

        # Split consensus
        if verification.consensus_type == "split":
            return True, "Conflicting evidence from sources"

        # High-priority claims
        if "P0" in str(verification.metadata.get("priority", "")):
            return True, "P0 priority claim - potential imminent harm"

        # Medical claims without high-credibility sources
        claim_lower = claim_text.lower()
        if any(term in claim_lower for term in ["medical", "vaccine", "treatment"]):
            high_cred_sources = [
                s for s in verification.sources
                if s.credibility == "high"
            ]
            if len(high_cred_sources) < 2:
                return True, "Medical claim with insufficient high-credibility sources"

        return False, ""


# Global instance
guardrails = GuardrailsManager()
