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
        try:
            return ip in self._ip_blocks
        except Exception as e:
            logger.error(f"Error checking IP block: {e}")
            return False
    
    async def get_blocked_ips(self) -> List[Dict[str, Any]]:
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
        try:
            return list(self._pattern_blocks.values())
        except Exception as e:
            logger.error(f"Error getting blocked patterns: {e}")
            return []
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        try:
            return bool(re.match(f"^{regex_pattern}$", path))
        except Exception:
            return False
    
    def _check_pattern_match(self, request, pattern_type: str, pattern_str: str) -> bool:
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

