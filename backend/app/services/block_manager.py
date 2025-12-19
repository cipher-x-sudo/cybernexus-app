"""
Block Manager Service

Manages blocking rules for IPs, endpoints, and patterns.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from app.config import settings
from app.core.database.redis_client import get_redis_client


class BlockManager:
    """Service for managing network blocking rules."""
    
    def __init__(self):
        self.redis = get_redis_client()
    
    # ==================== IP Blocking ====================
    
    async def block_ip(self, ip: str, reason: str = "", created_by: str = "") -> bool:
        """Block an IP address."""
        try:
            block_data = {
                "ip": ip,
                "reason": reason,
                "created_at": datetime.utcnow().isoformat(),
                "created_by": created_by
            }
            
            key = f"network:blocks:ip:{ip}"
            self.redis.set_json(key, block_data)
            
            logger.info(f"IP blocked: {ip} - {reason}")
            return True
        except Exception as e:
            logger.error(f"Failed to block IP {ip}: {e}")
            return False
    
    async def unblock_ip(self, ip: str) -> bool:
        """Unblock an IP address."""
        try:
            key = f"network:blocks:ip:{ip}"
            deleted = self.redis.delete(key)
            
            if deleted:
                logger.info(f"IP unblocked: {ip}")
            return bool(deleted)
        except Exception as e:
            logger.error(f"Failed to unblock IP {ip}: {e}")
            return False
    
    async def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked."""
        if not self.redis or not self.redis.is_connected():
            return False
        try:
            key = f"network:blocks:ip:{ip}"
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Error checking IP block: {e}")
            return False
    
    async def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get all blocked IPs."""
        try:
            pattern = "network:blocks:ip:*"
            keys = self.redis.keys(pattern)
            
            blocked = []
            for key in keys:
                block_data = self.redis.get_json(key)
                if block_data:
                    blocked.append(block_data)
            
            return blocked
        except Exception as e:
            logger.error(f"Error getting blocked IPs: {e}")
            return []
    
    # ==================== Endpoint Blocking ====================
    
    async def block_endpoint(
        self, 
        pattern: str, 
        method: str = "ALL", 
        reason: str = "",
        created_by: str = ""
    ) -> bool:
        """Block an endpoint pattern."""
        try:
            block_data = {
                "pattern": pattern,
                "method": method.upper(),
                "reason": reason,
                "created_at": datetime.utcnow().isoformat(),
                "created_by": created_by
            }
            
            # Use pattern as part of key (sanitize for Redis key)
            pattern_key = pattern.replace("/", "_").replace("*", "star")
            key = f"network:blocks:endpoint:{pattern_key}"
            self.redis.set_json(key, block_data)
            
            logger.info(f"Endpoint blocked: {method} {pattern} - {reason}")
            return True
        except Exception as e:
            logger.error(f"Failed to block endpoint {pattern}: {e}")
            return False
    
    async def unblock_endpoint(self, pattern: str) -> bool:
        """Unblock an endpoint pattern."""
        try:
            pattern_key = pattern.replace("/", "_").replace("*", "star")
            key = f"network:blocks:endpoint:{pattern_key}"
            deleted = self.redis.delete(key)
            
            if deleted:
                logger.info(f"Endpoint unblocked: {pattern}")
            return bool(deleted)
        except Exception as e:
            logger.error(f"Failed to unblock endpoint {pattern}: {e}")
            return False
    
    async def is_endpoint_blocked(self, path: str, method: str) -> bool:
        """Check if endpoint is blocked."""
        if not self.redis or not self.redis.is_connected():
            return False
        try:
            # Get all endpoint blocks
            pattern = "network:blocks:endpoint:*"
            keys = self.redis.keys(pattern)
            
            for key in keys:
                block_data = self.redis.get_json(key)
                if not block_data:
                    continue
                
                block_pattern = block_data.get("pattern", "")
                block_method = block_data.get("method", "ALL")
                
                # Check method
                if block_method != "ALL" and block_method != method.upper():
                    continue
                
                # Check pattern match (support wildcards)
                if self._match_pattern(path, block_pattern):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking endpoint block: {e}")
            return False
    
    async def get_blocked_endpoints(self) -> List[Dict[str, Any]]:
        """Get all blocked endpoints."""
        try:
            pattern = "network:blocks:endpoint:*"
            keys = self.redis.keys(pattern)
            
            blocked = []
            for key in keys:
                block_data = self.redis.get_json(key)
                if block_data:
                    blocked.append(block_data)
            
            return blocked
        except Exception as e:
            logger.error(f"Error getting blocked endpoints: {e}")
            return []
    
    # ==================== Pattern Blocking ====================
    
    async def block_pattern(
        self,
        pattern_type: str,
        pattern: str,
        reason: str = "",
        created_by: str = ""
    ) -> str:
        """
        Block a pattern (user-agent, header, etc.).
        
        Returns:
            Block ID
        """
        try:
            import uuid
            block_id = str(uuid.uuid4())
            
            block_data = {
                "id": block_id,
                "type": pattern_type,
                "pattern": pattern,
                "reason": reason,
                "created_at": datetime.utcnow().isoformat(),
                "created_by": created_by
            }
            
            key = f"network:blocks:pattern:{block_id}"
            self.redis.set_json(key, block_data)
            
            logger.info(f"Pattern blocked: {pattern_type} - {pattern} - {reason}")
            return block_id
        except Exception as e:
            logger.error(f"Failed to block pattern: {e}")
            return ""
    
    async def unblock_pattern(self, block_id: str) -> bool:
        """Unblock a pattern by ID."""
        try:
            key = f"network:blocks:pattern:{block_id}"
            deleted = self.redis.delete(key)
            
            if deleted:
                logger.info(f"Pattern unblocked: {block_id}")
            return bool(deleted)
        except Exception as e:
            logger.error(f"Failed to unblock pattern {block_id}: {e}")
            return False
    
    async def is_pattern_blocked(self, request) -> bool:
        """Check if request matches blocked pattern."""
        if not self.redis or not self.redis.is_connected():
            return False
        try:
            # Get all pattern blocks
            pattern = "network:blocks:pattern:*"
            keys = self.redis.keys(pattern)
            
            for key in keys:
                block_data = self.redis.get_json(key)
                if not block_data:
                    continue
                
                pattern_type = block_data.get("type", "")
                pattern_str = block_data.get("pattern", "")
                
                if self._check_pattern_match(request, pattern_type, pattern_str):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking pattern block: {e}")
            return False
    
    async def get_blocked_patterns(self) -> List[Dict[str, Any]]:
        """Get all blocked patterns."""
        try:
            pattern = "network:blocks:pattern:*"
            keys = self.redis.keys(pattern)
            
            blocked = []
            for key in keys:
                block_data = self.redis.get_json(key)
                if block_data:
                    blocked.append(block_data)
            
            return blocked
        except Exception as e:
            logger.error(f"Error getting blocked patterns: {e}")
            return []
    
    # ==================== Helper Methods ====================
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern (supports wildcards)."""
        # Convert pattern to regex
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        try:
            return bool(re.match(f"^{regex_pattern}$", path))
        except Exception:
            return False
    
    def _check_pattern_match(self, request, pattern_type: str, pattern_str: str) -> bool:
        """Check if request matches pattern."""
        if pattern_type == "user_agent":
            user_agent = request.headers.get("user-agent", "")
            return self._match_pattern(user_agent.lower(), pattern_str.lower())
        
        elif pattern_type == "header":
            # Check all headers
            for header_name, header_value in request.headers.items():
                if self._match_pattern(header_value.lower(), pattern_str.lower()):
                    return True
        
        elif pattern_type == "path":
            path = request.url.path
            return self._match_pattern(path, pattern_str)
        
        elif pattern_type == "query":
            query = str(request.url.query)
            return self._match_pattern(query.lower(), pattern_str.lower())
        
        return False
    
    async def get_all_blocks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all blocks grouped by type."""
        return {
            "ips": await self.get_blocked_ips(),
            "endpoints": await self.get_blocked_endpoints(),
            "patterns": await self.get_blocked_patterns()
        }


# Global block manager instance
_block_manager: Optional[BlockManager] = None


def get_block_manager() -> BlockManager:
    """Get or create global block manager instance."""
    global _block_manager
    if _block_manager is None:
        _block_manager = BlockManager()
    return _block_manager

