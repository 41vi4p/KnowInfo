"""
Redis cache manager for high-speed caching and rate limiting
"""
import redis.asyncio as redis
from typing import Optional, Any
import json
import structlog
from datetime import timedelta

logger = structlog.get_logger(__name__)


class RedisManager:
    """Manages Redis connections and caching operations"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """Establish connection to Redis"""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error("Redis connection failed", error=str(e))
            raise

    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis disconnected")

    # Caching Operations
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = await self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ):
        """Set value in cache with optional expiration (seconds)"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.client.set(key, value, ex=expire)

    async def delete(self, key: str):
        """Delete key from cache"""
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.client.exists(key) > 0

    # Verification Caching
    async def cache_verification(
        self,
        claim_text: str,
        verification_result: dict,
        expire_seconds: int = 3600
    ):
        """Cache verification result for a claim"""
        cache_key = f"verification:{hash(claim_text)}"
        await self.set(cache_key, verification_result, expire=expire_seconds)
        logger.info("Verification cached", cache_key=cache_key)

    async def get_cached_verification(self, claim_text: str) -> Optional[dict]:
        """Retrieve cached verification result"""
        cache_key = f"verification:{hash(claim_text)}"
        result = await self.get(cache_key)
        if result:
            logger.info("Verification cache hit", cache_key=cache_key)
        return result

    # Rate Limiting
    async def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        Check if request is within rate limit
        Returns: (is_allowed, remaining_requests)
        """
        key = f"rate_limit:{identifier}"
        current = await self.client.get(key)

        if current is None:
            # First request in window
            await self.client.setex(key, window_seconds, 1)
            return True, max_requests - 1

        current_count = int(current)
        if current_count >= max_requests:
            return False, 0

        # Increment counter
        await self.client.incr(key)
        return True, max_requests - current_count - 1

    # Trending Detection
    async def increment_claim_velocity(
        self,
        claim_text: str,
        window_seconds: int = 3600
    ) -> int:
        """Increment claim velocity counter and return current count"""
        key = f"velocity:{hash(claim_text)}"
        count = await self.client.incr(key)

        # Set expiration on first increment
        if count == 1:
            await self.client.expire(key, window_seconds)

        return count

    async def get_claim_velocity(self, claim_text: str) -> int:
        """Get current velocity count for a claim"""
        key = f"velocity:{hash(claim_text)}"
        count = await self.client.get(key)
        return int(count) if count else 0

    async def get_trending_claims(self, min_velocity: int = 500) -> list[tuple[str, int]]:
        """Get all claims exceeding velocity threshold"""
        trending = []
        cursor = 0

        while True:
            cursor, keys = await self.client.scan(
                cursor,
                match="velocity:*",
                count=100
            )

            for key in keys:
                count = int(await self.client.get(key))
                if count >= min_velocity:
                    trending.append((key.replace("velocity:", ""), count))

            if cursor == 0:
                break

        return sorted(trending, key=lambda x: x[1], reverse=True)

    # Session Management
    async def create_session(
        self,
        session_id: str,
        user_data: dict,
        expire_seconds: int = 86400
    ):
        """Create user session"""
        key = f"session:{session_id}"
        await self.set(key, user_data, expire=expire_seconds)

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve session data"""
        key = f"session:{session_id}"
        return await self.get(key)

    async def delete_session(self, session_id: str):
        """Delete session"""
        key = f"session:{session_id}"
        await self.delete(key)

    # Queue Management (for background tasks)
    async def enqueue_task(self, queue_name: str, task_data: dict):
        """Add task to processing queue"""
        queue_key = f"queue:{queue_name}"
        await self.client.rpush(queue_key, json.dumps(task_data))

    async def dequeue_task(self, queue_name: str) -> Optional[dict]:
        """Get next task from queue"""
        queue_key = f"queue:{queue_name}"
        task_json = await self.client.lpop(queue_key)
        if task_json:
            return json.loads(task_json)
        return None

    async def get_queue_length(self, queue_name: str) -> int:
        """Get number of tasks in queue"""
        queue_key = f"queue:{queue_name}"
        return await self.client.llen(queue_key)

    # Pub/Sub for real-time updates
    async def publish(self, channel: str, message: dict):
        """Publish message to channel"""
        await self.client.publish(channel, json.dumps(message))

    async def subscribe(self, channel: str):
        """Subscribe to channel (returns async generator)"""
        pubsub = self.client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub


# Global instance
redis_manager: Optional[RedisManager] = None


async def get_redis() -> RedisManager:
    """Get Redis manager instance"""
    global redis_manager
    if redis_manager is None:
        raise RuntimeError("Redis not initialized")
    return redis_manager


async def init_redis(redis_url: str):
    """Initialize Redis connection"""
    global redis_manager
    redis_manager = RedisManager(redis_url)
    await redis_manager.connect()
