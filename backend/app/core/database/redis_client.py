"""
Redis Client Module

Provides Redis connection management and utilities for the storage layer.
"""

import json
from typing import Optional, Any, Dict, List
from urllib.parse import urlparse
import redis
from redis.connection import ConnectionPool
from loguru import logger

from app.config import settings


class RedisClient:
    """
    Redis client wrapper with connection pooling and health checks.
    
    Features:
    - Connection pooling for performance
    - Automatic reconnection
    - Health check utilities
    - JSON serialization helpers
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis client.
        
        Args:
            redis_url: Redis connection URL (defaults to settings.REDIS_URL)
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._connected = False
        
        # Parse URL to extract components
        parsed = urlparse(self.redis_url)
        self.host = parsed.hostname or "localhost"
        self.port = parsed.port or 6379
        self.db = settings.REDIS_DB
        self.password = parsed.password
        
        # Initialize connection (non-blocking - don't raise on failure)
        self._connect()
    
    def _connect(self):
        """Establish Redis connection with connection pooling."""
        try:
            # Create connection pool
            self._pool = ConnectionPool.from_url(
                self.redis_url,
                db=self.db,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                decode_responses=True,
                max_connections=50
            )
            
            # Create client from pool
            self._client = redis.Redis(connection_pool=self._pool)
            
            # Test connection
            self._client.ping()
            self._connected = True
            logger.info(f"Redis connected: {self.host}:{self.port}/{self.db}")
            
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Redis features will be disabled.")
            self._connected = False
            # Don't raise - allow app to start without Redis
            self._pool = None
            self._client = None
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """Get Redis client instance."""
        if not self._connected or self._client is None:
            try:
                self._connect()
            except Exception:
                return None
        return self._client
    
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self._connected or self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except Exception:
            self._connected = False
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Redis connection.
        
        Returns:
            Dictionary with health status
        """
        try:
            if not self.is_connected():
                return {
                    "status": "unhealthy",
                    "error": "Not connected to Redis"
                }
            
            # Test basic operations
            test_key = "__health_check__"
            self._client.set(test_key, "ok", ex=1)
            value = self._client.get(test_key)
            
            if value != "ok":
                return {
                    "status": "unhealthy",
                    "error": "Health check test failed"
                }
            
            # Get Redis info
            info = self._client.info()
            
            return {
                "status": "healthy",
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "redis_version": info.get("redis_version", "unknown")
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    # ==================== JSON Serialization Helpers ====================
    
    def set_json(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Store JSON-serializable value in Redis.
        
        Args:
            key: Redis key
            value: Value to serialize (must be JSON-serializable)
            ex: Expiration time in seconds
            
        Returns:
            True if successful
        """
        try:
            json_str = json.dumps(value, default=str)
            return self.client.set(key, json_str, ex=ex)
        except Exception as e:
            logger.error(f"Failed to set JSON key {key}: {e}")
            raise
    
    def get_json(self, key: str) -> Optional[Any]:
        """Retrieve and deserialize JSON value from Redis.
        
        Args:
            key: Redis key
            
        Returns:
            Deserialized value or None if not found
        """
        try:
            json_str = self.client.get(key)
            if json_str is None:
                return None
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON for key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get JSON key {key}: {e}")
            return None
    
    # ==================== Hash Operations ====================
    
    def hset_json(self, name: str, key: str, value: Any) -> int:
        """Set JSON value in Redis hash.
        
        Args:
            name: Hash name
            key: Hash key
            value: Value to serialize
            
        Returns:
            Number of fields added
        """
        try:
            json_str = json.dumps(value, default=str)
            return self.client.hset(name, key, json_str)
        except Exception as e:
            logger.error(f"Failed to hset JSON {name}:{key}: {e}")
            raise
    
    def hget_json(self, name: str, key: str) -> Optional[Any]:
        """Get JSON value from Redis hash.
        
        Args:
            name: Hash name
            key: Hash key
            
        Returns:
            Deserialized value or None
        """
        try:
            json_str = self.client.hget(name, key)
            if json_str is None:
                return None
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON for hash {name}:{key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to hget JSON {name}:{key}: {e}")
            return None
    
    def hgetall_json(self, name: str) -> Dict[str, Any]:
        """Get all JSON values from Redis hash.
        
        Args:
            name: Hash name
            
        Returns:
            Dictionary of deserialized values
        """
        try:
            data = self.client.hgetall(name)
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except json.JSONDecodeError:
                    result[k] = v  # Fallback to raw string
            return result
        except Exception as e:
            logger.error(f"Failed to hgetall JSON {name}: {e}")
            return {}
    
    def hdel(self, name: str, *keys: str) -> int:
        """Delete keys from Redis hash.
        
        Args:
            name: Hash name
            *keys: Keys to delete
            
        Returns:
            Number of keys deleted
        """
        return self.client.hdel(name, *keys)
    
    # ==================== Set Operations ====================
    
    def sadd(self, name: str, *values: str) -> int:
        """Add values to Redis set.
        
        Args:
            name: Set name
            *values: Values to add
            
        Returns:
            Number of values added
        """
        return self.client.sadd(name, *values)
    
    def srem(self, name: str, *values: str) -> int:
        """Remove values from Redis set.
        
        Args:
            name: Set name
            *values: Values to remove
            
        Returns:
            Number of values removed
        """
        return self.client.srem(name, *values)
    
    def smembers(self, name: str) -> set:
        """Get all members of Redis set.
        
        Args:
            name: Set name
            
        Returns:
            Set of members
        """
        return self.client.smembers(name)
    
    def sismember(self, name: str, value: str) -> bool:
        """Check if value is member of Redis set.
        
        Args:
            name: Set name
            value: Value to check
            
        Returns:
            True if member
        """
        return bool(self.client.sismember(name, value))
    
    # ==================== Sorted Set Operations ====================
    
    def zadd(self, name: str, mapping: Dict[str, float]) -> int:
        """Add members with scores to Redis sorted set.
        
        Args:
            name: Sorted set name
            mapping: Dictionary of member -> score
            
        Returns:
            Number of members added
        """
        return self.client.zadd(name, mapping)
    
    def zrem(self, name: str, *members: str) -> int:
        """Remove members from Redis sorted set.
        
        Args:
            name: Sorted set name
            *members: Members to remove
            
        Returns:
            Number of members removed
        """
        return self.client.zrem(name, *members)
    
    def zrange(self, name: str, start: int = 0, end: int = -1, withscores: bool = False) -> List:
        """Get range of members from Redis sorted set.
        
        Args:
            name: Sorted set name
            start: Start index
            end: End index
            withscores: Include scores in result
            
        Returns:
            List of members (or tuples if withscores=True)
        """
        return self.client.zrange(name, start, end, withscores=withscores)
    
    def zrangebyscore(self, name: str, min_score: float, max_score: float, 
                     withscores: bool = False, limit: Optional[tuple] = None) -> List:
        """Get members by score range from Redis sorted set.
        
        Args:
            name: Sorted set name
            min_score: Minimum score
            max_score: Maximum score
            withscores: Include scores in result
            limit: Optional (offset, count) tuple
            
        Returns:
            List of members (or tuples if withscores=True)
        """
        # Call underlying Redis client - handle limit parameter carefully
        # Some redis-py versions don't support limit as keyword argument
        if limit is not None:
            try:
                # Try with limit as keyword (newer redis-py)
                return self.client.zrangebyscore(name, min_score, max_score, 
                                                withscores=withscores, limit=limit)
            except TypeError:
                # Fallback: get all and slice manually
                result = self.client.zrangebyscore(name, min_score, max_score, 
                                                  withscores=withscores)
                offset, count = limit
                return result[offset:offset + count] if result else []
        else:
            return self.client.zrangebyscore(name, min_score, max_score, 
                                           withscores=withscores)
    
    # ==================== List Operations ====================
    
    def lpush(self, name: str, *values: str) -> int:
        """Push values to left of Redis list.
        
        Args:
            name: List name
            *values: Values to push
            
        Returns:
            New length of list
        """
        return self.client.lpush(name, *values)
    
    def rpush(self, name: str, *values: str) -> int:
        """Push values to right of Redis list.
        
        Args:
            name: List name
            *values: Values to push
            
        Returns:
            New length of list
        """
        return self.client.rpush(name, *values)
    
    def lrange(self, name: str, start: int = 0, end: int = -1) -> List[str]:
        """Get range of values from Redis list.
        
        Args:
            name: List name
            start: Start index
            end: End index
            
        Returns:
            List of values
        """
        return self.client.lrange(name, start, end)
    
    def ltrim(self, name: str, start: int, end: int) -> bool:
        """Trim Redis list to specified range.
        
        Args:
            name: List name
            start: Start index
            end: End index
            
        Returns:
            True if successful
        """
        return self.client.ltrim(name, start, end)
    
    def llen(self, name: str) -> int:
        """Get length of Redis list.
        
        Args:
            name: List name
            
        Returns:
            Length of list
        """
        return self.client.llen(name)
    
    # ==================== Key Operations ====================
    
    def delete(self, *keys: str) -> int:
        """Delete keys from Redis.
        
        Args:
            *keys: Keys to delete
            
        Returns:
            Number of keys deleted
        """
        return self.client.delete(*keys)
    
    def exists(self, *keys: str) -> int:
        """Check if keys exist in Redis.
        
        Args:
            *keys: Keys to check
            
        Returns:
            Number of keys that exist
        """
        return self.client.exists(*keys)
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "entity:*")
            
        Returns:
            List of matching keys
        """
        return self.client.keys(pattern)
    
    def close(self):
        """Close Redis connection."""
        if self._pool:
            self._pool.disconnect()
        self._connected = False
        logger.info("Redis connection closed")


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Get or create global Redis client instance.
    
    Returns:
        RedisClient instance
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


def close_redis_client():
    """Close global Redis client connection."""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None



