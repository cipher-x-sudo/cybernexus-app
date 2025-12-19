"""
Network Logging Middleware

Captures all API requests and responses for real-time monitoring.
Integrates with TunnelDetector for tunnel pattern detection.
Uses database storage with user scoping.
"""

import uuid
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Message
from loguru import logger
import asyncio
from jose import JWTError, jwt

from app.config import settings
from app.core.database.database import get_db
from app.core.database.network_log_storage import DBNetworkLogStorage


# Global reference to middleware instance for WebSocket handler
_global_middleware_instance = None


class NetworkLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware to capture and log all API requests/responses."""
    
    def __init__(self, app, tunnel_analyzer=None):
        super().__init__(app)
        global _global_middleware_instance
        _global_middleware_instance = self
        self.tunnel_analyzer = tunnel_analyzer
        self.websocket_clients = set()  # Will be set by WebSocket handler
        
    async def dispatch(self, request: Request, call_next):
        """Process request and capture logs."""
        if not settings.NETWORK_ENABLE_LOGGING:
            return await call_next(request)
        
        # Skip logging for health checks and static files
        if request.url.path in ["/health", "/api/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Extract user_id from JWT token if available
        user_id = await self._extract_user_id(request)
        
        # Capture request data
        client_ip = self._get_client_ip(request)
        request_data = await self._capture_request(request, request_id, client_ip)
        
        # Process request
        response = await call_next(request)
        
        # Capture response data
        response_time_ms = (time.time() - start_time) * 1000
        log_entry = await self._capture_response(
            request_data, response, request_id, response_time_ms
        )
        
        # Store log entry asynchronously (don't block response)
        asyncio.create_task(self._store_log(log_entry, user_id))
        
        # Broadcast to WebSocket clients
        asyncio.create_task(self._broadcast_log(log_entry))
        
        return response
    
    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user_id from JWT token in Authorization header."""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username = payload.get("sub")
            
            if username:
                # Get user_id from database
                from app.core.database.database import init_db, _async_session_maker
                from app.core.database.models import User as UserModel
                from sqlalchemy import select
                
                # Ensure database is initialized
                init_db()
                
                # Access session maker directly (it's needed for middleware context)
                if _async_session_maker:
                    async with _async_session_maker() as db:
                        try:
                            result = await db.execute(
                                select(UserModel).where(UserModel.username == username)
                            )
                            user = result.scalar_one_or_none()
                            if user:
                                return user.id
                        except Exception as e:
                            logger.debug(f"Error querying user: {e}")
        except (JWTError, Exception) as e:
            # Token invalid or user not found - log as unauthenticated
            logger.debug(f"Could not extract user_id from request: {e}")
        
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded IP (common in proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def _capture_request(self, request: Request, request_id: str, client_ip: str) -> Dict[str, Any]:
        """Capture request data."""
        # Read body
        body = b""
        try:
            body = await request.body()
        except Exception as e:
            logger.warning(f"Failed to read request body: {e}")
        
        # Truncate large bodies
        max_size = settings.NETWORK_MAX_BODY_SIZE
        body_truncated = len(body) > max_size
        if body_truncated:
            body = body[:max_size]
        
        # Parse query string
        query_string = str(request.url.query) if request.url.query else ""
        
        # Get headers (sanitize sensitive ones)
        headers = dict(request.headers)
        headers = self._sanitize_headers(headers)
        
        request_data = {
            "id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "query": query_string,
            "headers": headers,
            "body": body.decode("utf-8", errors="replace") if body else "",
            "body_size": len(body),
            "body_truncated": body_truncated,
            "user_agent": headers.get("user-agent", ""),
            "referer": headers.get("referer", ""),
        }
        
        return request_data
    
    async def _capture_response(
        self, 
        request_data: Dict[str, Any], 
        response: Response, 
        request_id: str,
        response_time_ms: float
    ) -> Dict[str, Any]:
        """Capture response data and create complete log entry."""
        # Read response body
        response_body = b""
        response_body_truncated = False
        
        # For streaming responses, we can't easily read the body
        # We'll capture what we can from the response
        # Note: Full body capture requires wrapping the response, which is complex
        # For now, we'll capture headers and status, and note that body capture is limited
        try:
            # Check if response has a body attribute we can read
            if hasattr(response, "body") and response.body:
                body_bytes = response.body
                if isinstance(body_bytes, bytes):
                    response_body = body_bytes
                elif isinstance(body_bytes, str):
                    response_body = body_bytes.encode("utf-8")
        except Exception:
            pass
        
        # Truncate if needed
        if len(response_body) > settings.NETWORK_MAX_BODY_SIZE:
            response_body = response_body[:settings.NETWORK_MAX_BODY_SIZE]
            response_body_truncated = True
        
        # Get response headers (sanitize)
        response_headers = dict(response.headers)
        response_headers = self._sanitize_headers(response_headers)
        
        log_entry = {
            **request_data,
            "status": response.status_code,
            "response_headers": response_headers,
            "response_body": response_body.decode("utf-8", errors="replace") if response_body else "",
            "response_body_size": len(response_body),
            "response_body_truncated": response_body_truncated,
            "response_time_ms": round(response_time_ms, 2),
        }
        
        # Run tunnel detection if enabled
        if settings.NETWORK_ENABLE_TUNNEL_DETECTION and self.tunnel_analyzer:
            try:
                tunnel_detection = await self.tunnel_analyzer.analyze_request(log_entry)
                if tunnel_detection:
                    log_entry["tunnel_detection"] = tunnel_detection
            except Exception as e:
                logger.error(f"Tunnel detection error: {e}")
        
        return log_entry
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize sensitive headers."""
        sensitive_keys = [
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "api-key",
            "access-token",
            "password",
        ]
        
        sanitized = {}
        for key, value in headers.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    async def _store_log(self, log_entry: Dict[str, Any], user_id: Optional[str] = None):
        """Store log entry in database."""
        try:
            from app.core.database.database import init_db, _async_session_maker
            from app.core.database.network_log_storage import DBNetworkLogStorage
            
            # Ensure database is initialized
            init_db()
            
            # Access session maker directly (needed for middleware context)
            if _async_session_maker:
                async with _async_session_maker() as db:
                    try:
                        storage = DBNetworkLogStorage(db, user_id=user_id, is_admin=False)
                        await storage.save_log(log_entry, user_id=user_id)
                        await db.commit()
                    except Exception as e:
                        await db.rollback()
                        logger.error(f"Failed to save log in database: {e}")
        except Exception as e:
            logger.error(f"Failed to store network log: {e}", exc_info=True)
    
    async def _broadcast_log(self, log_entry: Dict[str, Any]):
        """Broadcast log entry to WebSocket clients."""
        if not self.websocket_clients:
            return
        
        try:
            message = {
                "type": "log",
                "data": log_entry
            }
            
            # If tunnel detected, also send tunnel alert
            if "tunnel_detection" in log_entry:
                tunnel_message = {
                    "type": "tunnel_alert",
                    "data": log_entry["tunnel_detection"]
                }
                await self._send_to_clients(tunnel_message)
            
            await self._send_to_clients(message)
        except Exception as e:
            logger.error(f"Failed to broadcast log: {e}")
    
    async def _send_to_clients(self, message: Dict[str, Any]):
        """Send message to all connected WebSocket clients."""
        if not self.websocket_clients:
            return
        
        disconnected = set()
        for client in self.websocket_clients:
            try:
                await client.send_json(message)
            except Exception:
                disconnected.add(client)
        
        # Remove disconnected clients
        self.websocket_clients -= disconnected
    
    def register_websocket_client(self, client):
        """Register a WebSocket client for real-time updates."""
        self.websocket_clients.add(client)
    
    def unregister_websocket_client(self, client):
        """Unregister a WebSocket client."""
        self.websocket_clients.discard(client)


def get_network_logger_middleware() -> Optional[NetworkLoggerMiddleware]:
    """Get the global network logger middleware instance."""
    return _global_middleware_instance

