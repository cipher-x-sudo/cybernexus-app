"""Network blocking and filtering service.

This module provides IP, endpoint, and pattern-based blocking functionality.
Uses standard Python data structures for block management.

This module does not use custom DSA concepts from app.core.dsa.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
from loguru import logger

from app.config import settings


class BlockManager:
    
    def __init__(self):
        self._ip_blocks: Dict[str, Dict[str, Any]] = {}
        self._endpoint_blocks: Dict[str, Dict[str, Any]] = {}
        self._pattern_blocks: Dict[str, Dict[str, Any]] = {}
    
    async def block_ip(self, ip: str, reason: str = "", created_by: str = "") -> bool:
        """Block an IP address from accessing the system.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            ip: The IP address to block
            reason: Optional reason for blocking
            created_by: Optional identifier of who created the block
        
        Returns:
            True if the IP was successfully blocked
        """
        try:
            block_data = {
                "ip": ip,
                "reason": reason,
                "created_at": datetime.utcnow().isoformat(),
                "created_by": created_by
            }
            
            self._ip_blocks[ip] = block_data
            
            logger.info(f"IP blocked: {ip} - {reason}")
            return True
        except Exception as e:
            logger.error(f"Failed to block IP {ip}: {e}")
            return False
    
    async def unblock_ip(self, ip: str) -> bool:
        """Unblock a previously blocked IP address.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            ip: The IP address to unblock
        
        Returns:
            True if the IP was unblocked, False if it wasn't blocked
        """
        try:
            if ip in self._ip_blocks:
                del self._ip_blocks[ip]
                logger.info(f"IP unblocked: {ip}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unblock IP {ip}: {e}")
            return False
    
    async def is_ip_blocked(self, ip: str) -> bool:
        """Check if an IP address is currently blocked.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            ip: The IP address to check
        
        Returns:
            True if the IP is blocked, False otherwise
        """
        try:
            return ip in self._ip_blocks
        except Exception as e:
            logger.error(f"Error checking IP block: {e}")
            return False
    
    async def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get all blocked IP addresses.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Returns:
            List of dictionaries containing blocked IP information
        """
        try:
            return list(self._ip_blocks.values())
        except Exception as e:
            logger.error(f"Error getting blocked IPs: {e}")
            return []
    
    async def block_endpoint(
        self, 
        pattern: str, 
        method: str = "ALL", 
        reason: str = "",
        created_by: str = ""
    ) -> bool:
        """Block an endpoint pattern from being accessed.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            pattern: Endpoint pattern to block (supports * and ? wildcards)
            method: HTTP method to block (default: "ALL" for all methods)
            reason: Optional reason for blocking
            created_by: Optional identifier of who created the block
        
        Returns:
            True if the endpoint was successfully blocked
        """
        try:
            block_data = {
                "pattern": pattern,
                "method": method.upper(),
                "reason": reason,
                "created_at": datetime.utcnow().isoformat(),
                "created_by": created_by
            }
            
            pattern_key = pattern.replace("/", "_").replace("*", "star")
            self._endpoint_blocks[pattern_key] = block_data
            
            logger.info(f"Endpoint blocked: {method} {pattern} - {reason}")
            return True
        except Exception as e:
            logger.error(f"Failed to block endpoint {pattern}: {e}")
            return False
    
    async def unblock_endpoint(self, pattern: str) -> bool:
        """Unblock a previously blocked endpoint pattern.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            pattern: The endpoint pattern to unblock
        
        Returns:
            True if the endpoint was unblocked, False if it wasn't blocked
        """
        try:
            pattern_key = pattern.replace("/", "_").replace("*", "star")
            if pattern_key in self._endpoint_blocks:
                del self._endpoint_blocks[pattern_key]
                logger.info(f"Endpoint unblocked: {pattern}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unblock endpoint {pattern}: {e}")
            return False
    
    async def is_endpoint_blocked(self, path: str, method: str) -> bool:
        """Check if an endpoint path and method combination is blocked.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            path: The endpoint path to check
            method: The HTTP method to check
        
        Returns:
            True if the endpoint is blocked, False otherwise
        """
        try:
            for block_data in self._endpoint_blocks.values():
                block_pattern = block_data.get("pattern", "")
                block_method = block_data.get("method", "ALL")
                
                if block_method != "ALL" and block_method != method.upper():
                    continue
                
                if self._match_pattern(path, block_pattern):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking endpoint block: {e}")
            return False
    
    async def get_blocked_endpoints(self) -> List[Dict[str, Any]]:
        """Get all blocked endpoint patterns.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Returns:
            List of dictionaries containing blocked endpoint information
        """
        try:
            return list(self._endpoint_blocks.values())
        except Exception as e:
            logger.error(f"Error getting blocked endpoints: {e}")
            return []
    
    async def block_pattern(
        self,
        pattern_type: str,
        pattern: str,
        reason: str = "",
        created_by: str = ""
    ) -> str:
        """Block a request pattern (user agent, header, path, or query).
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            pattern_type: Type of pattern ('user_agent', 'header', 'path', 'query')
            pattern: The pattern string to match against
            reason: Optional reason for blocking
            created_by: Optional identifier of who created the block
        
        Returns:
            Block ID string if successful, empty string on failure
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
            
            self._pattern_blocks[block_id] = block_data
            
            logger.info(f"Pattern blocked: {pattern_type} - {pattern} - {reason}")
            return block_id
        except Exception as e:
            logger.error(f"Failed to block pattern: {e}")
            return ""
    
    async def unblock_pattern(self, block_id: str) -> bool:
        """Unblock a previously blocked pattern by its block ID.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            block_id: The unique identifier of the block to remove
        
        Returns:
            True if the pattern was unblocked, False if it wasn't blocked
        """
        try:
            if block_id in self._pattern_blocks:
                del self._pattern_blocks[block_id]
                logger.info(f"Pattern unblocked: {block_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unblock pattern {block_id}: {e}")
            return False
    
    async def is_pattern_blocked(self, request) -> bool:
        """Check if a request matches any blocked pattern.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            request: The request object to check against blocked patterns
        
        Returns:
            True if the request matches a blocked pattern, False otherwise
        """
        try:
            for block_data in self._pattern_blocks.values():
                pattern_type = block_data.get("type", "")
                pattern_str = block_data.get("pattern", "")
                
                if self._check_pattern_match(request, pattern_type, pattern_str):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking pattern block: {e}")
            return False
    
    async def get_blocked_patterns(self) -> List[Dict[str, Any]]:
        """Get all blocked patterns.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Returns:
            List of dictionaries containing blocked pattern information
        """
        try:
            return list(self._pattern_blocks.values())
        except Exception as e:
            logger.error(f"Error getting blocked patterns: {e}")
            return []
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Match a path against a pattern with wildcards.
        
        Internal helper method that converts wildcard pattern to regex.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            path: The path string to match
            pattern: The pattern with * and ? wildcards
        
        Returns:
            True if the path matches the pattern, False otherwise
        """
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        try:
            return bool(re.match(f"^{regex_pattern}$", path))
        except Exception:
            return False
    
    def _check_pattern_match(self, request, pattern_type: str, pattern_str: str) -> bool:
        """Check if a request matches a specific pattern type and string.
        
        Internal helper method for pattern matching based on type.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            request: The request object to check
            pattern_type: Type of pattern ('user_agent', 'header', 'path', 'query')
            pattern_str: The pattern string to match against
        
        Returns:
            True if the request matches the pattern, False otherwise
        """
        if pattern_type == "user_agent":
            user_agent = request.headers.get("user-agent", "")
            return self._match_pattern(user_agent.lower(), pattern_str.lower())
        
        elif pattern_type == "header":
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
        """Get all blocks grouped by type.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Returns:
            Dictionary with keys 'ips', 'endpoints', and 'patterns', each containing lists of block information
        """
        return {
            "ips": await self.get_blocked_ips(),
            "endpoints": await self.get_blocked_endpoints(),
            "patterns": await self.get_blocked_patterns()
        }


_block_manager: Optional[BlockManager] = None


def get_block_manager() -> BlockManager:
    global _block_manager
    if _block_manager is None:
        _block_manager = BlockManager()
    return _block_manager

