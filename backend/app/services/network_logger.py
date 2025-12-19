"""
Network Log Storage Service

Provides methods to query and manage network logs stored in Redis.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.config import settings
from app.core.database.redis_client import get_redis_client


class NetworkLogStorage:
    """Service for querying network logs."""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.ttl_seconds = settings.NETWORK_LOG_TTL_DAYS * 24 * 60 * 60
    
    async def get_log(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a single log entry by ID."""
        try:
            key = f"network:logs:{request_id}"
            return self.redis.get_json(key)
        except Exception as e:
            logger.error(f"Error getting log {request_id}: {e}")
            return None
    
    async def get_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        ip: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        status: Optional[int] = None,
        has_tunnel: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Get logs with filtering.
        
        Args:
            limit: Maximum number of logs to return
            offset: Offset for pagination
            start_time: Start time filter
            end_time: End time filter
            ip: Filter by IP address
            endpoint: Filter by endpoint path
            method: Filter by HTTP method
            status: Filter by status code
            has_tunnel: Filter by tunnel detection (True/False)
        """
        try:
            # Get request IDs from index
            request_ids = await self._get_filtered_request_ids(
                start_time, end_time, ip, endpoint, method, status, has_tunnel
            )
            
            # Apply pagination
            paginated_ids = request_ids[offset:offset + limit]
            
            # Fetch log entries
            logs = []
            for request_id in paginated_ids:
                log = await self.get_log(request_id)
                if log:
                    logs.append(log)
            
            return logs
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return []
    
    async def _get_filtered_request_ids(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        ip: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        status: Optional[int] = None,
        has_tunnel: Optional[bool] = None
    ) -> List[str]:
        """Get filtered request IDs."""
        # Start with all request IDs from index
        if start_time or end_time:
            # Use time range
            min_score = start_time.timestamp() if start_time else 0
            max_score = end_time.timestamp() if end_time else float('inf')
            request_ids = [
                rid for rid, _ in self.redis.zrangebyscore(
                    "network:logs:index",
                    min_score,
                    max_score,
                    withscores=True
                )
            ]
        else:
            # Get recent logs (last 1000)
            request_ids = [
                rid for rid in self.redis.zrange("network:logs:index", -1000, -1)
            ]
        
        # Apply filters
        filtered_ids = []
        for request_id in request_ids:
            log = await self.get_log(request_id)
            if not log:
                continue
            
            # IP filter
            if ip and log.get("ip") != ip:
                continue
            
            # Endpoint filter
            if endpoint and log.get("path") != endpoint:
                continue
            
            # Method filter
            if method and log.get("method") != method.upper():
                continue
            
            # Status filter
            if status is not None and log.get("status") != status:
                continue
            
            # Tunnel filter
            if has_tunnel is not None:
                has_tunnel_detection = "tunnel_detection" in log
                if has_tunnel != has_tunnel_detection:
                    continue
            
            filtered_ids.append(request_id)
        
        # Sort by timestamp (newest first)
        filtered_ids.reverse()
        return filtered_ids
    
    async def search_logs(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search logs by query string (searches URL, headers, body)."""
        try:
            query_lower = query.lower()
            matching_logs = []
            
            # Get recent logs to search
            request_ids = self.redis.zrange("network:logs:index", -1000, -1)
            
            for request_id in request_ids:
                log = await self.get_log(request_id)
                if not log:
                    continue
                
                # Search in various fields
                searchable_text = " ".join([
                    log.get("path", ""),
                    log.get("query", ""),
                    log.get("body", ""),
                    str(log.get("headers", {})),
                    log.get("user_agent", ""),
                ]).lower()
                
                if query_lower in searchable_text:
                    matching_logs.append(log)
                    if len(matching_logs) >= limit:
                        break
            
            return matching_logs
        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            return []
    
    async def get_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get network statistics."""
        try:
            # Get logs in time range
            request_ids = []
            if start_time or end_time:
                min_score = start_time.timestamp() if start_time else 0
                max_score = end_time.timestamp() if end_time else float('inf')
                request_ids = [
                    rid for rid, _ in self.redis.zrangebyscore(
                        "network:logs:index",
                        min_score,
                        max_score,
                        withscores=True
                    )
                ]
            else:
                # Last hour
                hour_ago = datetime.utcnow() - timedelta(hours=1)
                min_score = hour_ago.timestamp()
                request_ids = [
                    rid for rid, _ in self.redis.zrangebyscore(
                        "network:logs:index",
                        min_score,
                        float('inf'),
                        withscores=True
                    )
                ]
            
            # Calculate statistics
            total_requests = len(request_ids)
            status_counts = {}
            method_counts = {}
            ip_counts = {}
            endpoint_counts = {}
            tunnel_count = 0
            total_response_time = 0
            response_count = 0
            
            for request_id in request_ids[:1000]:  # Limit to 1000 for performance
                log = await self.get_log(request_id)
                if not log:
                    continue
                
                # Status codes
                status = log.get("status", 0)
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Methods
                method = log.get("method", "UNKNOWN")
                method_counts[method] = method_counts.get(method, 0) + 1
                
                # IPs
                ip = log.get("ip", "unknown")
                ip_counts[ip] = ip_counts.get(ip, 0) + 1
                
                # Endpoints
                path = log.get("path", "unknown")
                endpoint_counts[path] = endpoint_counts.get(path, 0) + 1
                
                # Tunnels
                if "tunnel_detection" in log:
                    tunnel_count += 1
                
                # Response time
                response_time = log.get("response_time_ms", 0)
                if response_time > 0:
                    total_response_time += response_time
                    response_count += 1
            
            avg_response_time = total_response_time / response_count if response_count > 0 else 0
            
            # Get top IPs
            top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Get top endpoints
            top_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "total_requests": total_requests,
                "status_counts": status_counts,
                "method_counts": method_counts,
                "top_ips": [{"ip": ip, "count": count} for ip, count in top_ips],
                "top_endpoints": [{"endpoint": endpoint, "count": count} for endpoint, count in top_endpoints],
                "tunnel_detections": tunnel_count,
                "average_response_time_ms": round(avg_response_time, 2),
                "time_range": {
                    "start": start_time.isoformat() if start_time else None,
                    "end": end_time.isoformat() if end_time else None
                }
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    async def get_tunnel_detections(
        self,
        limit: int = 100,
        min_confidence: str = "medium"
    ) -> List[Dict[str, Any]]:
        """Get tunnel detections sorted by risk score."""
        try:
            # Get tunnel detections from sorted set
            request_ids = self.redis.zrange("network:logs:tunnels", -limit, -1, withscores=True)
            
            detections = []
            confidence_levels = {"low": 1, "medium": 2, "high": 3, "confirmed": 4}
            min_level = confidence_levels.get(min_confidence.lower(), 2)
            
            for request_id, risk_score in request_ids:
                log = await self.get_log(request_id)
                if not log or "tunnel_detection" not in log:
                    continue
                
                detection = log["tunnel_detection"]
                confidence = detection.get("confidence", "low")
                confidence_level = confidence_levels.get(confidence.lower(), 1)
                
                if confidence_level >= min_level:
                    detections.append({
                        "request_id": request_id,
                        "log": log,
                        "detection": detection
                    })
            
            return detections
        except Exception as e:
            logger.error(f"Error getting tunnel detections: {e}")
            return []
    
    async def export_logs(
        self,
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export logs in specified format (json, csv, har)."""
        try:
            logs = await self.get_logs(
                limit=10000,
                start_time=start_time,
                end_time=end_time,
                ip=filters.get("ip") if filters else None,
                endpoint=filters.get("endpoint") if filters else None,
                method=filters.get("method") if filters else None,
                status=filters.get("status") if filters else None
            )
            
            if format == "json":
                import json
                return json.dumps(logs, indent=2, default=str)
            
            elif format == "csv":
                import csv
                import io
                output = io.StringIO()
                if logs:
                    writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                    writer.writeheader()
                    writer.writerows(logs)
                return output.getvalue()
            
            elif format == "har":
                # Convert to HAR format
                har = {
                    "log": {
                        "version": "1.2",
                        "creator": {"name": "CyberNexus", "version": "1.0"},
                        "entries": []
                    }
                }
                
                for log in logs:
                    entry = {
                        "request": {
                            "method": log.get("method", "GET"),
                            "url": f"{log.get('path', '')}?{log.get('query', '')}",
                            "headers": [
                                {"name": k, "value": v} for k, v in log.get("headers", {}).items()
                            ],
                            "postData": {"text": log.get("body", "")} if log.get("body") else None
                        },
                        "response": {
                            "status": log.get("status", 200),
                            "headers": [
                                {"name": k, "value": v} for k, v in log.get("response_headers", {}).items()
                            ],
                            "content": {"text": log.get("response_body", "")}
                        },
                        "time": log.get("response_time_ms", 0),
                        "timestamp": log.get("timestamp", "")
                    }
                    har["log"]["entries"].append(entry)
                
                import json
                return json.dumps(har, indent=2, default=str)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
        except Exception as e:
            logger.error(f"Error exporting logs: {e}")
            return ""


# Global network log storage instance
_network_log_storage: Optional[NetworkLogStorage] = None


def get_network_log_storage() -> NetworkLogStorage:
    """Get or create global network log storage instance."""
    global _network_log_storage
    if _network_log_storage is None:
        _network_log_storage = NetworkLogStorage()
    return _network_log_storage

