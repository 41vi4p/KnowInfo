"""
MongoDB connection and operations for content storage
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
from typing import Optional, Dict, Any, List
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class MongoDBManager:
    """Manages MongoDB connections and operations"""

    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.uri)
            self.db = self.client[self.db_name]
            # Test connection
            await self.client.admin.command('ping')
            logger.info("MongoDB connected successfully", db_name=self.db_name)
        except ConnectionFailure as e:
            logger.error("MongoDB connection failed", error=str(e))
            raise

    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB disconnected")

    # Content Collection Operations
    async def store_content(self, content: Dict[str, Any]) -> str:
        """Store raw content from social media monitoring"""
        content["created_at"] = datetime.utcnow()
        content["updated_at"] = datetime.utcnow()
        result = await self.db.contents.insert_one(content)
        logger.info("Content stored", content_id=str(result.inserted_id))
        return str(result.inserted_id)

    async def get_content_by_id(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve content by ID"""
        from bson import ObjectId
        return await self.db.contents.find_one({"_id": ObjectId(content_id)})

    async def search_contents(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search contents with filters"""
        cursor = self.db.contents.find(filters).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def update_content_status(self, content_id: str, status: str):
        """Update content processing status"""
        from bson import ObjectId
        await self.db.contents.update_one(
            {"_id": ObjectId(content_id)},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow()
                }
            }
        )

    # Claims Collection Operations
    async def store_claim(self, claim: Dict[str, Any]) -> str:
        """Store extracted claim"""
        claim["created_at"] = datetime.utcnow()
        claim["updated_at"] = datetime.utcnow()
        result = await self.db.claims.insert_one(claim)
        logger.info("Claim stored", claim_id=str(result.inserted_id))
        return str(result.inserted_id)

    async def get_claim_by_id(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve claim by ID"""
        from bson import ObjectId
        return await self.db.claims.find_one({"_id": ObjectId(claim_id)})

    async def search_similar_claims(
        self,
        claim_text: str,
        similarity_threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """Search for similar claims using text search"""
        # Note: For production, use vector similarity search
        cursor = self.db.claims.find(
            {"$text": {"$search": claim_text}}
        ).limit(10)
        return await cursor.to_list(length=10)

    # Verifications Collection Operations
    async def store_verification(self, verification: Dict[str, Any]) -> str:
        """Store verification result"""
        verification["created_at"] = datetime.utcnow()
        result = await self.db.verifications.insert_one(verification)
        logger.info("Verification stored", verification_id=str(result.inserted_id))
        return str(result.inserted_id)

    async def get_verification_by_claim_id(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get verification result for a claim"""
        return await self.db.verifications.find_one({"claim_id": claim_id})

    # Trending Analysis
    async def get_trending_claims(
        self,
        hours: int = 24,
        min_velocity: int = 500
    ) -> List[Dict[str, Any]]:
        """Get trending claims based on velocity"""
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        pipeline = [
            {"$match": {"created_at": {"$gte": cutoff_time}}},
            {"$group": {
                "_id": "$claim_text",
                "count": {"$sum": 1},
                "first_seen": {"$min": "$created_at"},
                "sources": {"$push": "$source"}
            }},
            {"$match": {"count": {"$gte": min_velocity}}},
            {"$sort": {"count": -1}},
            {"$limit": 50}
        ]

        cursor = self.db.contents.aggregate(pipeline)
        return await cursor.to_list(length=50)

    # Create indexes for performance
    async def create_indexes(self):
        """Create database indexes for optimal performance"""
        # Content indexes
        await self.db.contents.create_index("source")
        await self.db.contents.create_index("created_at")
        await self.db.contents.create_index("status")
        await self.db.contents.create_index([("text", "text")])

        # Claims indexes
        await self.db.claims.create_index("claim_text")
        await self.db.claims.create_index("category")
        await self.db.claims.create_index("priority")
        await self.db.claims.create_index("created_at")
        await self.db.claims.create_index([("claim_text", "text")])

        # Verifications indexes
        await self.db.verifications.create_index("claim_id")
        await self.db.verifications.create_index("status")
        await self.db.verifications.create_index("confidence_score")

        logger.info("Database indexes created")


# Global instance
mongo_manager: Optional[MongoDBManager] = None


async def get_mongo() -> MongoDBManager:
    """Get MongoDB manager instance"""
    global mongo_manager
    if mongo_manager is None:
        raise RuntimeError("MongoDB not initialized")
    return mongo_manager


async def init_mongo(uri: str, db_name: str):
    """Initialize MongoDB connection"""
    global mongo_manager
    mongo_manager = MongoDBManager(uri, db_name)
    await mongo_manager.connect()
    await mongo_manager.create_indexes()
