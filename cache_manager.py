"""
Redis cache manager for user data.
Provides centralized caching logic for user-related operations.
"""
import json
from typing import Optional, Any
from redis.asyncio import Redis


class UserCacheManager:
    """Manage user data caching in Redis."""
    
    def __init__(self, redis_client: Redis):
        """Initialize cache manager with Redis client.
        
        Args:
            redis_client: Redis async client instance.
        """
        self.redis = redis_client
        self.prefix = "user"
    
    def _get_key(self, identifier: str) -> str:
        """Generate cache key for user.
        
        Args:
            identifier: User identifier (email or user_id).
            
        Returns:
            Cache key string.
        """
        return f"{self.prefix}:{identifier}"
    
    async def get_user(self, identifier: str) -> Optional[dict]:
        """Get user data from cache.
        
        Args:
            identifier: User identifier (email or user_id).
            
        Returns:
            User data dict or None if not found.
        """
        key = self._get_key(identifier)
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def set_user(
        self, 
        identifier: str, 
        user_data: dict, 
        ttl: int = 300
    ) -> None:
        """Cache user data with TTL.
        
        Args:
            identifier: User identifier (email or user_id).
            user_data: User data dict to cache.
            ttl: Time to live in seconds (default: 300).
        """
        key = self._get_key(identifier)
        await self.redis.setex(key, ttl, json.dumps(user_data))
    
    async def delete_user(self, identifier: str) -> None:
        """Delete user data from cache.
        
        Args:
            identifier: User identifier (email or user_id).
        """
        key = self._get_key(identifier)
        await self.redis.delete(key)
    
    async def invalidate_all_user_caches(self) -> None:
        """Invalidate all user caches (use with caution).
        
        Warning: This will delete all user cache entries.
        Use only when necessary (e.g., bulk user updates).
        """
        pattern = self._get_key("*")
        async for key in self.redis.scan_iter(pattern):
            await self.redis.delete(key)
