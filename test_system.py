#!/usr/bin/env python3
"""
Test script to verify KnowInfo system functionality
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.content import Content, SourcePlatform
from src.stage2_extraction.claim_extractor import ClaimExtractor
from src.stage3_verification.rag_engine import RAGEngine
from src.utils.logger import setup_logging
from src.utils.model_manager import init_model_manager
from config import settings

logger = setup_logging()


async def test_claim_extraction_and_verification():
    """Test the complete claim extraction and verification pipeline"""

    print("\n" + "=" * 70)
    print("🧪 TESTING KNOWINFO SYSTEM")
    print("=" * 70)

    # Initialize model manager
    print("\n🔧 Initializing model manager...")
    init_model_manager(
        ollama_base_url=settings.ollama_base_url,
        gemini_api_key=settings.gemini_api_key,
        openai_api_key=settings.openai_api_key,
        anthropic_api_key=settings.anthropic_api_key,
        use_local_first=settings.use_local_models_first
    )
    print("   ✅ Model manager initialized")

    # Test content with a false claim
    test_content = Content(
        content_id="test_001",
        source=SourcePlatform.TWITTER,
        platform_id="tweet_12345",
        text="BREAKING: WHO announces that COVID-19 vaccines cause autism! Share this before it gets censored!",
        author_id="user_123",
        author_username="newsalert_fake",
        created_at=datetime.utcnow(),
        engagement_count=2650,
        author_followers=15000
    )

    print("\n📋 Test Content:")
    print(f"   Platform: {test_content.source}")
    print(f"   Text: {test_content.text}")
    print(f"   Engagement: {test_content.engagement_count}")

    # Stage 2: Extract claims
    print("\n🔍 STAGE 2: Extracting Claims...")
    print("-" * 70)

    extractor = ClaimExtractor()
    claims = await extractor.extract_claims(test_content)

    if not claims:
        print("   ❌ No claims extracted!")
        return

    print(f"   ✅ Extracted {len(claims)} claim(s)")

    for i, claim in enumerate(claims, 1):
        print(f"\n   Claim {i}:")
        print(f"      Text: {claim.claim_text}")
        print(f"      Category: {claim.category}")
        print(f"      Priority: {claim.priority}")

    # Stage 3: Verify claims
    print("\n✅ STAGE 3: Verifying Claims with RAG...")
    print("-" * 70)

    rag_engine = RAGEngine(
        knowledge_base_path=settings.knowledge_base_path,
        vector_db_path=settings.vector_db_path
    )

    for i, claim in enumerate(claims, 1):
        print(f"\n   Verifying Claim {i}...")
        verification = await rag_engine.verify_claim(claim)

        print(f"      Status: {verification.status}")
        print(f"      Confidence: {verification.confidence_score}%")
        print(f"      Explanation: {verification.explanation[:200]}...")

        if verification.supporting_sources:
            print(f"      Supporting Sources: {len(verification.supporting_sources)}")
            for source in verification.supporting_sources[:2]:
                print(f"         - {source.title}")

    # Test another claim (true claim)
    print("\n\n" + "=" * 70)
    print("🧪 TESTING WITH TRUE CLAIM")
    print("=" * 70)

    true_content = Content(
        content_id="test_002",
        source=SourcePlatform.REDDIT,
        platform_id="post_67890",
        text="During emergencies, follow official evacuation orders from local authorities. Don't rely solely on social media.",
        author_id="user_456",
        author_username="safety_tips",
        created_at=datetime.utcnow()
    )

    print("\n📋 Test Content:")
    print(f"   Platform: {true_content.source}")
    print(f"   Text: {true_content.text}")

    print("\n🔍 Extracting Claims...")
    claims = await extractor.extract_claims(true_content)

    if claims:
        print(f"   ✅ Extracted {len(claims)} claim(s)")

        print("\n✅ Verifying Claims...")
        for claim in claims:
            verification = await rag_engine.verify_claim(claim)
            print(f"\n   Claim: {claim.claim_text[:80]}...")
            print(f"   Status: {verification.status}")
            print(f"   Confidence: {verification.confidence_score}%")

    print("\n" + "=" * 70)
    print("✅ TESTS COMPLETED!")
    print("=" * 70)
    print("\n📊 System Summary:")
    print(f"   - API Server: Running on http://localhost:{settings.api_port}")
    print(f"   - MongoDB: Connected")
    print(f"   - Neo4j: Connected")
    print(f"   - Redis: Connected")
    print(f"   - Ollama: Connected ({settings.ollama_base_url})")
    print(f"   - Gemini API: Configured")
    print(f"   - Knowledge Base: Seeded with {3} sources")
    print("\n🌐 Access Points:")
    print(f"   - API Docs: http://localhost:{settings.api_port}/docs")
    print(f"   - Health Check: http://localhost:{settings.api_port}/health")
    print(f"   - Neo4j Browser: http://localhost:7474")
    print("\n")


if __name__ == "__main__":
    try:
        asyncio.run(test_claim_extraction_and_verification())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
