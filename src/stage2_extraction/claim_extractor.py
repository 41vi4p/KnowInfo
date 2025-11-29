"""
Claim extraction using NLP and LLMs
"""
import structlog
from typing import List, Dict, Any
from ..models.content import Content, Claim, ClaimCategory, ClaimPriority
from ..utils.model_manager import get_model_manager

logger = structlog.get_logger(__name__)


class ClaimExtractor:
    """Extract verifiable claims from content"""

    def __init__(self):
        self.model_manager = get_model_manager()

        # P0 priority keywords (imminent harm)
        self.p0_keywords = [
            "evacuation", "poisoned", "contaminated", "imminent",
            "shelter in place", "lockdown", "immediate danger"
        ]

        # P1 priority keywords (medical)
        self.p1_keywords = [
            "vaccine", "cure", "treatment", "outbreak", "pandemic",
            "virus", "disease", "medication"
        ]

        # P2 priority keywords (authority attribution)
        self.p2_keywords = [
            "government says", "officials announce", "cdc reports",
            "who confirms", "president declares"
        ]

    async def extract_claims(self, content: Content) -> List[Claim]:
        """Extract all verifiable claims from content"""
        prompt = f"""Extract all factual, verifiable claims from the following text.
A claim should be a specific statement that can be fact-checked (not opinions or questions).

Text: {content.text}

For each claim, identify:
1. The exact claim text
2. Key entities mentioned (people, places, organizations)
3. Keywords

Respond in JSON format:
[{{
  "claim_text": "exact claim statement",
  "entities": [{{"entity": "name", "type": "PERSON/ORG/LOCATION"}}],
  "keywords": ["keyword1", "keyword2"]
}}]"""

        try:
            from ..utils.model_manager import ModelProvider
            response = await self.model_manager.generate_text(
                prompt=prompt,
                temperature=0.2,
                max_tokens=1000,
                preferred_provider=ModelProvider.GEMINI  # Force Gemini for reliable JSON
            )

            import json
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            claims_data = json.loads(response.strip())

            claims = []
            for claim_data in claims_data:
                from datetime import datetime
                claim = Claim(
                    content_id=content.content_id or f"content_{int(datetime.utcnow().timestamp())}",
                    claim_text=claim_data["claim_text"],
                    category=await self._categorize_claim(claim_data["claim_text"]),
                    priority=self._determine_priority(claim_data["claim_text"]),
                    entities=claim_data.get("entities", []),
                    keywords=claim_data.get("keywords", [])
                )
                claims.append(claim)

            logger.info("Claims extracted", count=len(claims), content_id=content.content_id)
            return claims

        except Exception as e:
            logger.error("Claim extraction failed", error=str(e), content_id=content.content_id)
            return []

    async def _categorize_claim(self, claim_text: str) -> ClaimCategory:
        """Categorize claim using LLM"""
        categories = [c.value for c in ClaimCategory]
        scores = await self.model_manager.classify_text(claim_text, categories)

        # Get highest scoring category
        best_category = max(scores.items(), key=lambda x: x[1])[0]
        return ClaimCategory(best_category)

    def _determine_priority(self, claim_text: str) -> ClaimPriority:
        """Determine claim priority based on keywords"""
        claim_lower = claim_text.lower()

        # P0: Imminent harm
        if any(keyword in claim_lower for keyword in self.p0_keywords):
            return ClaimPriority.P0

        # P1: Medical misinformation
        if any(keyword in claim_lower for keyword in self.p1_keywords):
            return ClaimPriority.P1

        # P2: Authority attribution
        if any(keyword in claim_lower for keyword in self.p2_keywords):
            return ClaimPriority.P2

        # P3: Everything else
        return ClaimPriority.P3
