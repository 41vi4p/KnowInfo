#!/usr/bin/env python3
"""
Seed knowledge base with authoritative sources
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stage3_verification.rag_engine import RAGEngine
from src.utils.model_manager import init_model_manager
from src.utils.logger import setup_logging
from config import settings

logger = setup_logging()


SEED_SOURCES = [
    {
        "title": "WHO COVID-19 Fact Sheet",
        "content": """
        The World Health Organization (WHO) provides evidence-based information about COVID-19.
        COVID-19 vaccines are safe and effective. They have undergone rigorous testing and continue
        to be monitored. Common side effects are mild and temporary. Vaccines significantly reduce
        the risk of severe illness and death. Multiple vaccines have been approved by regulatory
        authorities worldwide after thorough evaluation.
        """,
        "url": "https://www.who.int/emergencies/diseases/novel-coronavirus-2019",
        "source_type": "medical",
        "credibility": "high"
    },
    {
        "title": "CDC Emergency Preparedness",
        "content": """
        The Centers for Disease Control and Prevention (CDC) provides guidelines for emergency
        preparedness. During emergencies, follow official evacuation orders from local authorities.
        Do not rely on social media for emergency instructions. Monitor official channels including
        Emergency Alert System, local news, and government websites. Have an emergency kit prepared
        with water, food, medications, and important documents.
        """,
        "url": "https://www.cdc.gov/cpr/",
        "source_type": "government",
        "credibility": "high"
    },
    {
        "title": "Reuters Fact Check Database",
        "content": """
        Reuters Fact Check verifies viral claims and misinformation. Common types of misinformation
        include manipulated images, out-of-context videos, false attribution of quotes to officials,
        and recycled photos from unrelated events. Always verify information from multiple credible
        sources before sharing. Check image metadata and reverse image search for verification.
        """,
        "url": "https://www.reuters.com/fact-check",
        "source_type": "fact_check",
        "credibility": "high"
    }
]


async def seed_knowledge_base():
    """Seed the knowledge base with initial sources"""
    logger.info("Initializing model manager...")
    init_model_manager(
        ollama_base_url=settings.ollama_base_url,
        gemini_api_key=settings.gemini_api_key,
        use_local_first=True
    )

    logger.info("Initializing RAG engine...")
    rag_engine = RAGEngine(
        knowledge_base_path=settings.knowledge_base_path,
        vector_db_path=settings.vector_db_path
    )

    logger.info(f"Adding {len(SEED_SOURCES)} sources to knowledge base...")
    for source in SEED_SOURCES:
        await rag_engine.add_source_to_knowledge_base(
            title=source["title"],
            content=source["content"],
            url=source["url"],
            source_type=source["source_type"],
            credibility=source["credibility"]
        )
        logger.info(f"Added: {source['title']}")

    logger.info("Knowledge base seeding completed!")


if __name__ == "__main__":
    asyncio.run(seed_knowledge_base())
