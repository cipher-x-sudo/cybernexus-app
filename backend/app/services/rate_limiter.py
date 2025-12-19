"""
Rate Limiter Service

Implements sliding window rate limiting using Redis.
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.config import settings
from app.core.database.redis_client import get_redis_client


class RateLimiter:
    """Rate limiting service with sliding window algorithm."""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.ip_limit = settings.NETWORK_RATE_LIMIT_IP
        self.endpoint_limit = settings.NETWORK_RATE_LIMIT_ENDPOINT
        self.window_seconds = 60  # 1 minute window
    
    async def check_rate_limit(self, ip: str, endpoint: str) -> Dict[str, Any]:
        """
        Check if request is within rate limits.
        
        Args:
            ip: Client IP address
            endpoint: Request endpoint path
            
        Returns:
            Dictionary with:
            - allowed: bool - Whether request is allowed
            - current: int - Current request count
            - limit: int - Rate limit
            - reason: str - Reason if blocked
            - retry_after: int - Seconds to wait before retry
        """
        try:
            # Check IP-based rate limit
            ip_result = await self._check_ip_limit(ip)
            if not ip_result["allowed"]:
                return ip_result
            
            # Check endpoint-based rate limit
            endpoint_result = await self._check_endpoint_limit(ip, endpoint)
            if not endpoint_result["allowed"]:
                return endpoint_result
            
            # Both checks passed
            return {
                "allowed": True,
                "current": max(ip_result.get("current", 0), endpoint_result.get("current", 0)),
                "limit": max(ip_result.get("limit", 0), endpoint_result.get("limit", 0))
            }
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # On error, allow the request (fail open)
            return {"allowed": True}
    
    async def _check_ip_limit(self, ip: str) -> Dict[str, Any]:
        """Check IP-based rate limit."""
        key = f"network:ratelimit:ip:{ip}"
        current = await self._get_sliding_window_count(key)
        
        if current >= self.ip_limit:
            return {
                "allowed": False,
                "current": current,
                "limit": self.ip_limit,
                "reason": f"IP rate limit exceeded ({current}/{self.ip_limit} requests per minute)",
                "retry_after": self.window_seconds
            }
        
        # Increment counter
        await self._increment_sliding_window(key)
        
        return {
            "allowed": True,
            "current": current + 1,
            "limit": self.ip_limit
        }
    
    async def _check_endpoint_limit(self, ip: str, endpoint: str) -> Dict[str, Any]:
        """Check endpoint-based rate limit."""
        key = f"network:ratelimit:endpoint:{ip}:{endpoint}"
        current = await self._get_sliding_window_count(key)
        
        if current >= self.endpoint_limit:
            return {
                "allowed": False,
                "current": current,
                "limit": self.endpoint_limit,
                "reason": f"Endpoint rate limit exceeded ({current}/{self.endpoint_limit} requests per minute)",
                "retry_after": self.window_seconds
            }
        
        # Increment counter
        await self._increment_sliding_window(key)
        
        return {
            "allowed": True,
            "current": current + 1,
            "limit": self.endpoint_limit
        }
    
    async def _get_sliding_window_count(self, key: str) -> int:
        """
        Get count of requests in sliding window.
        
        Uses sorted set to track timestamps of requests.
        """
        try:
            now = time.time()
            window_start = now - self.window_seconds
            
            # Remove old entries (outside window)
            self.redis.client.zremrangebyscore(key, 0, window_start)
            
            # Count entries in window
            count = self.redis.client.zcard(key)
            return count
        except Exception as e:
            logger.error(f"Error getting sliding window count: {e}")
            return 0
    
    async def _increment_sliding_window(self, key: str):
        """Increment sliding window counter."""
        try:
            now = time.time()
            # Add current timestamp to sorted set
            self.redis.client.zadd(key, {str(now): now})
            # Set expiration to window size + buffer
            self.redis.client.expire(key, self.window_seconds + 10)
        except Exception as e:
            logger.error(f"Error incrementing sliding window: {e}")
    
    async def get_rate_limit_status(self, ip: str, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get current rate limit status for IP/endpoint."""
        ip_key = f"network:ratelimit:ip:{ip}"
        ip_count = await self._get_sliding_window_count(ip_key)
        
        result = {
            "ip": ip,
            "ip_limit": self.ip_limit,
            "ip_current": ip_count,
            "ip_remaining": max(0, self.ip_limit - ip_count)
        }
        
        if endpoint:
            endpoint_key = f"network:ratelimit:endpoint:{ip}:{endpoint}"
            endpoint_count = await self._get_sliding_window_count(endpoint_key)
            result.update({
                "endpoint": endpoint,
                "endpoint_limit": self.endpoint_limit,
                "endpoint_current": endpoint_count,
                "endpoint_remaining": max(0, self.endpoint_limit - endpoint_count)
            })
        
        return result


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

