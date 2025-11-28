"""
Neo4j graph database for Patient Zero tracking and propagation analysis
"""
from neo4j import AsyncGraphDatabase, AsyncDriver
from typing import Optional, Dict, Any, List
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class Neo4jManager:
    """Manages Neo4j graph database operations for tracking misinformation spread"""

    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[AsyncDriver] = None

    async def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connection
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            logger.info("Neo4j connected successfully")
        except Exception as e:
            logger.error("Neo4j connection failed", error=str(e))
            raise

    async def disconnect(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j disconnected")

    # Node Operations
    async def create_user_node(self, user_id: str, user_data: Dict[str, Any]):
        """Create or update a user node"""
        async with self.driver.session() as session:
            query = """
            MERGE (u:User {user_id: $user_id})
            SET u.username = $username,
                u.followers_count = $followers_count,
                u.platform = $platform,
                u.account_created = $account_created,
                u.updated_at = datetime()
            RETURN u
            """
            await session.run(
                query,
                user_id=user_id,
                username=user_data.get("username"),
                followers_count=user_data.get("followers_count", 0),
                platform=user_data.get("platform"),
                account_created=user_data.get("account_created")
            )
            logger.info("User node created", user_id=user_id)

    async def create_post_node(self, post_id: str, post_data: Dict[str, Any]):
        """Create a post node"""
        async with self.driver.session() as session:
            query = """
            MERGE (p:Post {post_id: $post_id})
            SET p.text = $text,
                p.claim_text = $claim_text,
                p.platform = $platform,
                p.created_at = datetime($created_at),
                p.engagement_count = $engagement_count,
                p.reach = $reach
            RETURN p
            """
            await session.run(
                query,
                post_id=post_id,
                text=post_data.get("text"),
                claim_text=post_data.get("claim_text"),
                platform=post_data.get("platform"),
                created_at=post_data.get("created_at", datetime.utcnow().isoformat()),
                engagement_count=post_data.get("engagement_count", 0),
                reach=post_data.get("reach", 0)
            )
            logger.info("Post node created", post_id=post_id)

    # Relationship Operations
    async def create_posted_relationship(self, user_id: str, post_id: str, timestamp: str):
        """Create POSTED relationship between user and post"""
        async with self.driver.session() as session:
            query = """
            MATCH (u:User {user_id: $user_id})
            MATCH (p:Post {post_id: $post_id})
            MERGE (u)-[r:POSTED {timestamp: datetime($timestamp)}]->(p)
            RETURN r
            """
            await session.run(query, user_id=user_id, post_id=post_id, timestamp=timestamp)

    async def create_shared_relationship(
        self,
        user_id: str,
        original_post_id: str,
        shared_post_id: str,
        timestamp: str
    ):
        """Create SHARED relationship (retweet, repost, etc.)"""
        async with self.driver.session() as session:
            query = """
            MATCH (u:User {user_id: $user_id})
            MATCH (original:Post {post_id: $original_post_id})
            MATCH (shared:Post {post_id: $shared_post_id})
            MERGE (u)-[r1:POSTED {timestamp: datetime($timestamp)}]->(shared)
            MERGE (shared)-[r2:SHARED_FROM]->(original)
            RETURN r1, r2
            """
            await session.run(
                query,
                user_id=user_id,
                original_post_id=original_post_id,
                shared_post_id=shared_post_id,
                timestamp=timestamp
            )

    # Patient Zero Tracking
    async def find_patient_zero(self, claim_text: str, similarity_threshold: float = 0.85) -> Optional[Dict[str, Any]]:
        """Find the earliest post containing a specific claim"""
        async with self.driver.session() as session:
            query = """
            MATCH (p:Post)
            WHERE p.claim_text CONTAINS $claim_text
            WITH p, p.created_at AS timestamp
            ORDER BY timestamp ASC
            LIMIT 1
            MATCH (u:User)-[:POSTED]->(p)
            RETURN p.post_id AS post_id,
                   p.text AS text,
                   p.created_at AS created_at,
                   p.platform AS platform,
                   u.user_id AS user_id,
                   u.username AS username,
                   u.followers_count AS followers_count
            """
            result = await session.run(query, claim_text=claim_text)
            record = await result.single()
            if record:
                return dict(record)
            return None

    async def get_propagation_tree(self, original_post_id: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        """Get the propagation tree showing how a post spread"""
        async with self.driver.session() as session:
            query = """
            MATCH path = (original:Post {post_id: $post_id})<-[:SHARED_FROM*0..{max_depth}]-(shared:Post)
            MATCH (u:User)-[:POSTED]->(shared)
            RETURN shared.post_id AS post_id,
                   shared.created_at AS created_at,
                   u.user_id AS user_id,
                   u.username AS username,
                   u.followers_count AS followers_count,
                   length(path) AS depth
            ORDER BY depth, created_at
            """
            result = await session.run(query.replace("{max_depth}", str(max_depth)), post_id=original_post_id)
            records = await result.values()
            return [dict(zip(["post_id", "created_at", "user_id", "username", "followers_count", "depth"], record)) for record in records]

    async def identify_amplifiers(self, original_post_id: str, min_followers: int = 10000) -> List[Dict[str, Any]]:
        """Identify high-influence users who amplified the post"""
        async with self.driver.session() as session:
            query = """
            MATCH (original:Post {post_id: $post_id})<-[:SHARED_FROM*1..3]-(shared:Post)
            MATCH (u:User)-[:POSTED]->(shared)
            WHERE u.followers_count >= $min_followers
            RETURN DISTINCT u.user_id AS user_id,
                   u.username AS username,
                   u.followers_count AS followers_count,
                   u.platform AS platform,
                   count(shared) AS share_count
            ORDER BY u.followers_count DESC
            LIMIT 20
            """
            result = await session.run(query, post_id=original_post_id, min_followers=min_followers)
            records = await result.values()
            return [dict(zip(["user_id", "username", "followers_count", "platform", "share_count"], record)) for record in records]

    # Bot Detection
    async def detect_coordinated_behavior(self, time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        """Detect coordinated posting patterns (potential bot networks)"""
        async with self.driver.session() as session:
            query = """
            MATCH (u:User)-[r:POSTED]->(p:Post)
            WHERE r.timestamp > datetime() - duration({minutes: $time_window})
            WITH u, count(p) AS post_count, collect(p.text) AS texts
            WHERE post_count > 20
            RETURN u.user_id AS user_id,
                   u.username AS username,
                   post_count,
                   u.account_created AS account_age
            ORDER BY post_count DESC
            LIMIT 50
            """
            result = await session.run(query, time_window=time_window_minutes)
            records = await result.values()
            return [dict(zip(["user_id", "username", "post_count", "account_age"], record)) for record in records]

    async def find_coordinated_clusters(self, min_cluster_size: int = 5) -> List[Dict[str, Any]]:
        """Find clusters of users posting identical content (bot networks)"""
        async with self.driver.session() as session:
            query = """
            MATCH (u:User)-[:POSTED]->(p:Post)
            WITH p.text AS text, collect(DISTINCT u) AS users
            WHERE size(users) >= $min_size
            RETURN text,
                   size(users) AS user_count,
                   [u IN users | {user_id: u.user_id, username: u.username}] AS users
            ORDER BY user_count DESC
            LIMIT 20
            """
            result = await session.run(query, min_size=min_cluster_size)
            records = await result.values()
            return [dict(zip(["text", "user_count", "users"], record)) for record in records]

    # Analytics
    async def get_spread_statistics(self, post_id: str) -> Dict[str, Any]:
        """Get statistics about how a post spread"""
        async with self.driver.session() as session:
            query = """
            MATCH (original:Post {post_id: $post_id})
            OPTIONAL MATCH (original)<-[:SHARED_FROM*]-(shared:Post)
            OPTIONAL MATCH (u:User)-[:POSTED]->(shared)
            RETURN count(DISTINCT shared) AS total_shares,
                   count(DISTINCT u) AS unique_sharers,
                   sum(u.followers_count) AS total_reach,
                   max(u.followers_count) AS max_amplifier_followers
            """
            result = await session.run(query, post_id=post_id)
            record = await result.single()
            if record:
                return dict(record)
            return {}

    # Constraints and Indexes
    async def create_constraints(self):
        """Create constraints and indexes for optimal performance"""
        async with self.driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
                "CREATE CONSTRAINT post_id_unique IF NOT EXISTS FOR (p:Post) REQUIRE p.post_id IS UNIQUE",
                "CREATE INDEX user_platform IF NOT EXISTS FOR (u:User) ON (u.platform)",
                "CREATE INDEX post_created IF NOT EXISTS FOR (p:Post) ON (p.created_at)",
                "CREATE INDEX post_claim IF NOT EXISTS FOR (p:Post) ON (p.claim_text)",
            ]
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    logger.warning("Constraint/index already exists", error=str(e))
        logger.info("Neo4j constraints and indexes created")


# Global instance
neo4j_manager: Optional[Neo4jManager] = None


async def get_neo4j() -> Neo4jManager:
    """Get Neo4j manager instance"""
    global neo4j_manager
    if neo4j_manager is None:
        raise RuntimeError("Neo4j not initialized")
    return neo4j_manager


async def init_neo4j(uri: str, user: str, password: str):
    """Initialize Neo4j connection"""
    global neo4j_manager
    neo4j_manager = Neo4jManager(uri, user, password)
    await neo4j_manager.connect()
    await neo4j_manager.create_constraints()
