"""
RAG (Retrieval Augmented Generation) engine for claim verification
"""
import structlog
from typing import List, Optional
from datetime import datetime
from ..models.content import Claim
from ..models.verification import (
    VerificationResult, VerificationStatus, VerificationSource, SourceCredibility
)
from ..utils.model_manager import get_model_manager

logger = structlog.get_logger(__name__)


class RAGEngine:
    """RAG engine for retrieving authoritative sources and verifying claims"""

    def __init__(self, knowledge_base_path: str, vector_db_path: str):
        self.knowledge_base_path = knowledge_base_path
        self.vector_db_path = vector_db_path
        self.model_manager = get_model_manager()

        # Initialize vector store
        self.vector_store = None
        self._init_vector_store()

    def _init_vector_store(self):
        """Initialize ChromaDB vector store"""
        try:
            import chromadb
            self.chroma_client = chromadb.PersistentClient(path=self.vector_db_path)
            self.vector_store = self.chroma_client.get_or_create_collection(
                name="authoritative_sources",
                metadata={"description": "Fact-checking knowledge base"}
            )
            logger.info("Vector store initialized", path=self.vector_db_path)
        except Exception as e:
            logger.error("Failed to initialize vector store", error=str(e))

    async def verify_claim(self, claim: Claim) -> VerificationResult:
        """Verify a claim against authoritative sources"""
        logger.info("Starting verification", claim_text=claim.claim_text[:100])

        # 1. Retrieve relevant sources
        sources = await self._retrieve_sources(claim.claim_text)

        if not sources:
            return VerificationResult(
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                status=VerificationStatus.UNVERIFIED,
                confidence_score=0.0,
                explanation="No authoritative sources found to verify this claim.",
                consensus_type="none"
            )

        # 2. Cross-reference sources
        consensus = self._calculate_consensus(sources)

        # 3. Generate explanation
        explanation = await self._generate_explanation(claim, sources, consensus)

        # 4. Determine verification status
        status = self._determine_status(consensus)

        # 5. Calculate confidence score
        confidence = self._calculate_confidence(sources, consensus)

        verification = VerificationResult(
            claim_id=claim.claim_id,
            claim_text=claim.claim_text,
            status=status,
            confidence_score=confidence,
            sources=sources,
            explanation=explanation,
            supporting_sources_count=len([s for s in sources if s.supports_claim]),
            contradicting_sources_count=len([s for s in sources if not s.supports_claim]),
            consensus_type=consensus["type"],
            expert_review_required=confidence < 60.0
        )

        logger.info(
            "Verification completed",
            status=status,
            confidence=confidence,
            sources_count=len(sources)
        )

        return verification

    async def _retrieve_sources(
        self,
        claim_text: str,
        top_k: int = 5
    ) -> List[VerificationSource]:
        """Retrieve relevant sources from knowledge base"""
        if not self.vector_store:
            return []

        try:
            # Generate embedding for claim
            embeddings = await self.model_manager.generate_embeddings([claim_text])

            # Query vector store
            results = self.vector_store.query(
                query_embeddings=embeddings,
                n_results=top_k
            )

            sources = []
            for i, doc_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                # Calculate relevance score (ensure it's between 0 and 1)
                distance = results['distances'][0][i]
                relevance_score = max(0.0, min(1.0, 1.0 / (1.0 + distance)))

                source = VerificationSource(
                    source_id=doc_id,
                    title=metadata.get('title', 'Unknown'),
                    url=metadata.get('url'),
                    source_type=metadata.get('source_type', 'unknown'),
                    credibility=SourceCredibility(metadata.get('credibility', 'unknown')),
                    relevant_excerpt=results['documents'][0][i],
                    supports_claim=False,  # Will be determined by LLM
                    relevance_score=relevance_score
                )

                # Use LLM to determine if source supports or contradicts claim
                supports = await self._check_support(claim_text, source.relevant_excerpt)
                source.supports_claim = supports

                sources.append(source)

            return sources

        except Exception as e:
            logger.error("Source retrieval failed", error=str(e))
            return []

    async def _check_support(self, claim: str, source_text: str) -> bool:
        """Check if source supports or contradicts claim"""
        prompt = f"""Does the following source text support or contradict the claim?

Claim: {claim}

Source: {source_text}

Respond with only: SUPPORTS or CONTRADICTS"""

        response = await self.model_manager.generate_text(
            prompt=prompt,
            temperature=0.1,
            max_tokens=10
        )

        return "SUPPORTS" in response.upper()

    def _calculate_consensus(self, sources: List[VerificationSource]) -> dict:
        """Calculate consensus from sources"""
        if not sources:
            return {"type": "none", "confidence": 0.0}

        supporting = sum(1 for s in sources if s.supports_claim)
        total = len(sources)
        ratio = supporting / total

        if ratio >= 0.9 or ratio <= 0.1:
            consensus_type = "unanimous"
            confidence = 95.0
        elif ratio >= 0.7 or ratio <= 0.3:
            consensus_type = "majority"
            confidence = 70.0
        else:
            consensus_type = "split"
            confidence = 40.0

        return {
            "type": consensus_type,
            "confidence": confidence,
            "supporting_ratio": ratio
        }

    async def _generate_explanation(
        self,
        claim: Claim,
        sources: List[VerificationSource],
        consensus: dict
    ) -> str:
        """Generate 3-sentence explanation"""
        sources_text = "\n".join([
            f"- {s.title}: {s.relevant_excerpt[:200]}"
            for s in sources[:3]
        ])

        prompt = f"""Generate a clear, 3-sentence explanation for this fact-check.

Claim: {claim.claim_text}

Sources:
{sources_text}

Consensus: {consensus['type']} ({consensus['supporting_ratio']:.0%} supporting)

Requirements:
- Exactly 3 sentences
- Empathetic, non-condescending tone
- Explain WHY the claim is true/false/misleading
- No jargon, active voice
- Start with "We understand this is confusing."
"""

        explanation = await self.model_manager.generate_text(
            prompt=prompt,
            temperature=0.7,
            max_tokens=200
        )

        return explanation.strip()

    def _determine_status(self, consensus: dict) -> VerificationStatus:
        """Determine verification status from consensus"""
        ratio = consensus["supporting_ratio"]

        if ratio >= 0.8:
            return VerificationStatus.TRUE
        elif ratio <= 0.2:
            return VerificationStatus.FALSE
        elif 0.3 <= ratio <= 0.7:
            return VerificationStatus.MISLEADING
        else:
            return VerificationStatus.UNVERIFIED

    def _calculate_confidence(
        self,
        sources: List[VerificationSource],
        consensus: dict
    ) -> float:
        """Calculate overall confidence score"""
        base_confidence = consensus["confidence"]

        # Boost confidence for high-credibility sources
        high_cred_count = sum(
            1 for s in sources
            if s.credibility == SourceCredibility.HIGH
        )
        credibility_boost = min(high_cred_count * 5, 20)

        # Reduce confidence for low relevance
        avg_relevance = sum(s.relevance_score for s in sources) / len(sources) if sources else 0
        relevance_factor = avg_relevance

        final_confidence = (base_confidence + credibility_boost) * relevance_factor
        return min(final_confidence, 100.0)

    async def add_source_to_knowledge_base(
        self,
        title: str,
        content: str,
        url: str,
        source_type: str,
        credibility: str
    ):
        """Add a new source document to the knowledge base"""
        if not self.vector_store:
            return

        try:
            # Generate embedding
            embeddings = await self.model_manager.generate_embeddings([content])

            # Add to vector store
            self.vector_store.add(
                embeddings=embeddings,
                documents=[content],
                metadatas=[{
                    "title": title,
                    "url": url,
                    "source_type": source_type,
                    "credibility": credibility,
                    "added_at": datetime.utcnow().isoformat()
                }],
                ids=[f"{source_type}_{title}_{datetime.utcnow().timestamp()}"]
            )

            logger.info("Source added to knowledge base", title=title)

        except Exception as e:
            logger.error("Failed to add source", error=str(e))
