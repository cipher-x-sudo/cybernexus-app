"""
Network Log Storage Service

Provides methods to query and manage network logs stored in PostgreSQL database.
This is a legacy service wrapper - new code should use DBNetworkLogStorage directly.

NOTE: This service is currently unused. The application uses DBNetworkLogStorage
directly in routes and middleware. This file is kept for reference/compatibility.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.config import settings
from app.core.database.database import _async_session_maker


class NetworkLogStorage:
    """Service for querying network logs from database."""
    
    def __init__(self):
        """Initialize network log storage service."""
        self.ttl_seconds = settings.NETWORK_LOG_TTL_DAYS * 24 * 60 * 60
    
    async def get_log(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a single log entry by ID."""
        try:
            from app.core.database.network_log_storage import DBNetworkLogStorage
            
            if not _async_session_maker:
                logger.error("Database session maker not initialized")
                return None
            
            async with _async_session_maker() as db:
                storage = DBNetworkLogStorage(db, user_id=None, is_admin=True)
                return await storage.get_log(request_id)
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
        """Get logs with filtering."""
        try:
            from app.core.database.network_log_storage import DBNetworkLogStorage
            
            if not _async_session_maker:
                logger.error("Database session maker not initialized")
                return []
            
            async with _async_session_maker() as db:
                storage = DBNetworkLogStorage(db, user_id=None, is_admin=True)
                return await storage.get_logs(
                    limit=limit,
                    offset=offset,
                    start_time=start_time,
                    end_time=end_time,
                    ip=ip,
                    endpoint=endpoint,
                    method=method,
                    status=status,
                    has_tunnel=has_tunnel
                )
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return []
    
    async def search_logs(self, q: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search logs by query string."""
        try:
            from app.core.database.network_log_storage import DBNetworkLogStorage
            
            if not _async_session_maker:
                logger.error("Database session maker not initialized")
                return []
            
            async with _async_session_maker() as db:
                storage = DBNetworkLogStorage(db, user_id=None, is_admin=True)
                return await storage.search_logs(q, limit=limit)
        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            return []
    
    async def get_stats(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get aggregate statistics for network logs."""
        try:
            from app.core.database.network_log_storage import DBNetworkLogStorage
            
            if not _async_session_maker:
                logger.error("Database session maker not initialized")
                return {}
            
            async with _async_session_maker() as db:
                storage = DBNetworkLogStorage(db, user_id=None, is_admin=True)
                return await storage.get_stats(start_time=start_time, end_time=end_time)
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    async def get_top_ips(self, limit: int = 10, start_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get top IP addresses by request count."""
        try:
            from app.core.database.network_log_storage import DBNetworkLogStorage
            from sqlalchemy import select, func
            from app.core.database.models import NetworkLog
            
            if not _async_session_maker:
                logger.error("Database session maker not initialized")
                return []
            
            async with _async_session_maker() as db:
                query = select(
                    NetworkLog.ip,
                    func.count(NetworkLog.id).label("count")
                ).group_by(NetworkLog.ip)
                
                if start_time:
                    query = query.where(NetworkLog.timestamp >= start_time)
                
                query = query.order_by(func.count(NetworkLog.id).desc()).limit(limit)
                
                result = await db.execute(query)
                rows = result.fetchall()
                
                return [{"ip": row[0], "count": row[1]} for row in rows if row[0]]
        except Exception as e:
            logger.error(f"Error getting top IPs: {e}")
            return []
    
    async def get_top_endpoints(self, limit: int = 10, start_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get top endpoints by request count."""
        try:
            from app.core.database.network_log_storage import DBNetworkLogStorage
            from sqlalchemy import select, func
            from app.core.database.models import NetworkLog
            
            if not _async_session_maker:
                logger.error("Database session maker not initialized")
                return []
            
            async with _async_session_maker() as db:
                query = select(
                    NetworkLog.path,
                    func.count(NetworkLog.id).label("count")
                ).group_by(NetworkLog.path)
                
                if start_time:
                    query = query.where(NetworkLog.timestamp >= start_time)
                
                query = query.order_by(func.count(NetworkLog.id).desc()).limit(limit)
                
                result = await db.execute(query)
                rows = result.fetchall()
                
                return [{"endpoint": row[0], "count": row[1]} for row in rows]
        except Exception as e:
            logger.error(f"Error getting top endpoints: {e}")
            return []
    
    async def get_status_distribution(self, start_time: Optional[datetime] = None) -> Dict[int, int]:
        """Get status code distribution."""
        try:
            from app.core.database.network_log_storage import DBNetworkLogStorage
            
            if not _async_session_maker:
                logger.error("Database session maker not initialized")
                return {}
            
            async with _async_session_maker() as db:
                storage = DBNetworkLogStorage(db, user_id=None, is_admin=True)
                stats = await storage.get_stats(start_time=start_time)
                return stats.get("status_distribution", {})
        except Exception as e:
            logger.error(f"Error getting status distribution: {e}")
            return {}
    
    async def get_tunnel_alerts(
        self,
        limit: int = 100,
        min_confidence: str = "medium"
    ) -> List[Dict[str, Any]]:
        """Get tunnel detection alerts."""
        try:
            from app.core.database.network_log_storage import DBNetworkLogStorage
            
            if not _async_session_maker:
                logger.error("Database session maker not initialized")
                return []
            
            async with _async_session_maker() as db:
                storage = DBNetworkLogStorage(db, user_id=None, is_admin=True)
                return await storage.get_tunnel_detections(limit=limit, min_confidence=min_confidence)
        except Exception as e:
            logger.error(f"Error getting tunnel alerts: {e}")
            return []
    
    async def get_tunnel_alert(self, detection_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific tunnel detection alert."""
        try:
            from app.core.database.network_log_storage import DBNetworkLogStorage
            from sqlalchemy import select
            from app.core.database.models import NetworkLog
            
            if not _async_session_maker:
                logger.error("Database session maker not initialized")
                return None
            
            async with _async_session_maker() as db:
                # Search for log with matching detection_id in tunnel_detection JSONB
                query = select(NetworkLog).where(
                    NetworkLog.tunnel_detection.isnot(None)
                )
                
                result = await db.execute(query)
                logs = result.scalars().all()
                
                for log in logs:
                    if log.tunnel_detection and log.tunnel_detection.get("detection_id") == detection_id:
                        return {
                            "id": detection_id,
                            "request_id": log.request_id,
                            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                            "ip": log.ip,
                            "path": log.path,
                            "method": log.method,
                            "confidence": log.tunnel_detection.get("confidence", "medium"),
                            "risk_score": log.tunnel_detection.get("risk_score", 0.0),
                            "indicators": log.tunnel_detection.get("indicators", []),
                            "description": log.tunnel_detection.get("description", "")
                        }
                
                return None
        except Exception as e:
            logger.error(f"Error getting tunnel alert {detection_id}: {e}")
            return None
    
    async def export_logs(
        self,
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export logs in various formats."""
        try:
            from app.core.database.network_log_storage import DBNetworkLogStorage
            
            if not _async_session_maker:
                logger.error("Database session maker not initialized")
                return ""
            
            async with _async_session_maker() as db:
                storage = DBNetworkLogStorage(db, user_id=None, is_admin=True)
                return await storage.export_logs(
                    format=format,
                    start_time=start_time,
                    end_time=end_time,
                    filters=filters or {}
                )
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

