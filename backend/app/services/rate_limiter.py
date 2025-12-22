import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger

from app.config import settings


class RateLimiter:
    
    def __init__(self):
        self._ip_counts: Dict[str, list] = defaultdict(list)
        self._endpoint_counts: Dict[str, list] = defaultdict(list)
        self.ip_limit = settings.NETWORK_RATE_LIMIT_IP
        self.endpoint_limit = settings.NETWORK_RATE_LIMIT_ENDPOINT
        self.window_seconds = 60
    
    async def check_rate_limit(self, ip: str, endpoint: str) -> Dict[str, Any]:
        try:
            ip_result = await self._check_ip_limit(ip)
            if not ip_result["allowed"]:
                return ip_result
            
            endpoint_result = await self._check_endpoint_limit(ip, endpoint)
            if not endpoint_result["allowed"]:
                return endpoint_result
            
            return {
                "allowed": True,
                "current": max(ip_result.get("current", 0), endpoint_result.get("current", 0)),
                "limit": max(ip_result.get("limit", 0), endpoint_result.get("limit", 0))
            }
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return {"allowed": True}
    
    async def _check_ip_limit(self, ip: str) -> Dict[str, Any]:
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
        

        await self._increment_sliding_window(key)
        
        return {
            "allowed": True,
            "current": current + 1,
            "limit": self.ip_limit
        }
    
    async def _check_endpoint_limit(self, ip: str, endpoint: str) -> Dict[str, Any]:
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
        

        await self._increment_sliding_window(key)
        
        return {
            "allowed": True,
            "current": current + 1,
            "limit": self.endpoint_limit
        }
    
    async def _get_sliding_window_count(self, key: str) -> int:
        try:
            now = time.time()
            window_start = now - self.window_seconds
            
            if key.startswith("network:ratelimit:ip:"):
                timestamps = self._ip_counts[key]
            else:
                timestamps = self._endpoint_counts[key]
            
            timestamps[:] = [ts for ts in timestamps if ts > window_start]
            
            return len(timestamps)
        except Exception as e:
            logger.error(f"Error getting sliding window count: {e}")
            return 0
    
    async def _increment_sliding_window(self, key: str):
        try:
            now = time.time()
            if key.startswith("network:ratelimit:ip:"):
                self._ip_counts[key].append(now)
            else:
                self._endpoint_counts[key].append(now)
        except Exception as e:
            logger.error(f"Error incrementing sliding window: {e}")
    
    async def get_rate_limit_status(self, ip: str, endpoint: Optional[str] = None) -> Dict[str, Any]:
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


_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

