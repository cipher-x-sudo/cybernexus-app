"""
Network Blocking Middleware

Blocks requests based on IP, endpoint patterns, header patterns, and rate limits.
"""

import re
from typing import Optional, Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from loguru import logger

from app.config import settings
from app.services.block_manager import get_block_manager
from app.services.rate_limiter import get_rate_limiter


class NetworkBlockerMiddleware(BaseHTTPMiddleware):
    """Middleware to block requests based on rules."""
    
    def __init__(self, app):
        super().__init__(app)
        # Initialize block manager and rate limiter (they work without Redis)
        try:
            self.block_manager = get_block_manager()
            self.rate_limiter = get_rate_limiter()
        except Exception as e:
            logger.warning(f"Failed to initialize block manager or rate limiter: {e}")
            self.block_manager = None
            self.rate_limiter = None
    
    async def dispatch(self, request: Request, call_next):
        """Check if request should be blocked."""
        if not settings.NETWORK_ENABLE_BLOCKING:
            return await call_next(request)
        
        # Skip blocking for health checks
        if request.url.path in ["/health", "/api/health"]:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        path = request.url.path
        method = request.method
        
        # Check IP blocking
        if await self._is_ip_blocked(client_ip):
            logger.warning(f"Blocked request from IP: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied", "reason": "IP blocked"}
            )
        
        # Check endpoint blocking
        if await self._is_endpoint_blocked(path, method):
            logger.warning(f"Blocked request to endpoint: {method} {path} from {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied", "reason": "Endpoint blocked"}
            )
        
        # Check pattern blocking (headers, user-agent, etc.)
        if await self._is_pattern_blocked(request):
            logger.warning(f"Blocked request matching pattern from {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied", "reason": "Request pattern blocked"}
            )
        
        # Check rate limits (skip if rate limiter not available)
        if self.rate_limiter:
            try:
                rate_limit_result = await self.rate_limiter.check_rate_limit(client_ip, path)
                if not rate_limit_result["allowed"]:
                    logger.warning(
                        f"Rate limit exceeded: {client_ip} -> {path} "
                        f"({rate_limit_result.get('current', 0)}/{rate_limit_result.get('limit', 0)})"
                    )
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Rate limit exceeded",
                            "reason": rate_limit_result.get("reason", "Too many requests"),
                            "retry_after": rate_limit_result.get("retry_after", 60)
                        },
                        headers={
                            "Retry-After": str(rate_limit_result.get("retry_after", 60))
                        }
                    )
            except Exception as e:
                logger.error(f"Error checking rate limit: {e}")
        
        # Request is allowed
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked."""
        if not self.block_manager:
            return False
        try:
            return await self.block_manager.is_ip_blocked(ip)
        except Exception as e:
            logger.error(f"Error checking IP block: {e}")
            return False
    
    async def _is_endpoint_blocked(self, path: str, method: str) -> bool:
        """Check if endpoint is blocked."""
        if not self.block_manager:
            return False
        try:
            return await self.block_manager.is_endpoint_blocked(path, method)
        except Exception as e:
            logger.error(f"Error checking endpoint block: {e}")
            return False
    
    async def _is_pattern_blocked(self, request: Request) -> bool:
        """Check if request matches blocked pattern."""
        if not self.block_manager:
            return False
        try:
            return await self.block_manager.is_pattern_blocked(request)
        except Exception as e:
            logger.error(f"Error checking pattern block: {e}")
            return False

