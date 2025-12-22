from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.orm import selectinload
from loguru import logger
import json
import csv
import io

from app.core.database.models import NetworkLog
from app.config import settings


class DBNetworkLogStorage:
    def __init__(self, db: AsyncSession, user_id: Optional[str] = None, is_admin: bool = False):
        self.db = db
        self.user_id = user_id
        self.is_admin = is_admin
        self.ttl_days = settings.NETWORK_LOG_TTL_DAYS
    
    async def save_log(self, log_entry: Dict[str, Any], user_id: Optional[str] = None) -> str:
        request_id = log_entry.get("id")
        if not request_id:
            raise ValueError("Log entry must have an 'id' field")
        
        owner_id = user_id or self.user_id
        
        result = await self.db.execute(
            select(NetworkLog).where(NetworkLog.request_id == request_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.ip = log_entry.get("ip")
            existing.method = log_entry.get("method")
            existing.path = log_entry.get("path")
            existing.query = log_entry.get("query")
            existing.status = log_entry.get("status")
            existing.response_time_ms = log_entry.get("response_time_ms", 0.0)
            existing.tunnel_detection = log_entry.get("tunnel_detection")
            existing.request_headers = log_entry.get("headers")
            existing.response_headers = log_entry.get("response_headers")
            existing.request_body = log_entry.get("body", "")
            existing.response_body = log_entry.get("response_body", "")
            
            if "timestamp" in log_entry:
                try:
                    existing.timestamp = datetime.fromisoformat(log_entry["timestamp"].replace('Z', '+00:00'))
                except:
                    pass
            
            if owner_id:
                existing.user_id = owner_id
        else:
            timestamp = datetime.utcnow()
            if "timestamp" in log_entry:
                try:
                    timestamp = datetime.fromisoformat(log_entry["timestamp"].replace('Z', '+00:00'))
                except:
                    pass
            
            db_log = NetworkLog(
                id=log_entry.get("id", f"log-{request_id}"),
                user_id=owner_id,
                request_id=request_id,
                ip=log_entry.get("ip"),
                method=log_entry.get("method", "GET"),
                path=log_entry.get("path", ""),
                query=log_entry.get("query"),
                status=log_entry.get("status", 200),
                response_time_ms=log_entry.get("response_time_ms", 0.0),
                tunnel_detection=log_entry.get("tunnel_detection"),
                request_headers=log_entry.get("headers"),
                response_headers=log_entry.get("response_headers"),
                request_body=log_entry.get("body", ""),
                response_body=log_entry.get("response_body", ""),
                timestamp=timestamp
            )
            self.db.add(db_log)
        
        await self.db.commit()
        return request_id
    
    async def get_log(self, request_id: str) -> Optional[Dict[str, Any]]:
        query = select(NetworkLog).where(NetworkLog.request_id == request_id)
        
        if not self.is_admin and self.user_id:
            query = query.where(NetworkLog.user_id == self.user_id)
        
        result = await self.db.execute(query)
        log = result.scalar_one_or_none()
        
        if not log:
            return None
        
        return self._log_to_dict(log)
    
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
        query = select(NetworkLog)
        
        if not self.is_admin and self.user_id:
            query = query.where(NetworkLog.user_id == self.user_id)
        
        conditions = []
        
        if start_time:
            conditions.append(NetworkLog.timestamp >= start_time)
        if end_time:
            conditions.append(NetworkLog.timestamp <= end_time)
        if ip:
            conditions.append(NetworkLog.ip == ip)
        if endpoint:
            conditions.append(NetworkLog.path == endpoint)
        if method:
            conditions.append(NetworkLog.method == method.upper())
        if status is not None:
            conditions.append(NetworkLog.status == status)
        if has_tunnel is not None:
            if has_tunnel:
                conditions.append(NetworkLog.tunnel_detection.isnot(None))
            else:
                conditions.append(NetworkLog.tunnel_detection.is_(None))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(NetworkLog.timestamp.desc())
        
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return [self._log_to_dict(log) for log in logs]
    
    async def search_logs(self, q: str, limit: int = 100) -> List[Dict[str, Any]]:
        query = select(NetworkLog).where(
            or_(
                NetworkLog.path.ilike(f"%{q}%"),
                NetworkLog.query.ilike(f"%{q}%"),
                NetworkLog.request_body.ilike(f"%{q}%"),
                NetworkLog.response_body.ilike(f"%{q}%")
            )
        )
        
        if not self.is_admin and self.user_id:
            query = query.where(NetworkLog.user_id == self.user_id)
        
        query = query.order_by(NetworkLog.timestamp.desc()).limit(limit)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return [self._log_to_dict(log) for log in logs]
    
    async def get_stats(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        query = select(
            func.count(NetworkLog.id).label("total_requests"),
            func.avg(NetworkLog.response_time_ms).label("avg_response_time"),
            func.min(NetworkLog.response_time_ms).label("min_response_time"),
            func.max(NetworkLog.response_time_ms).label("max_response_time"),
            func.count(func.distinct(NetworkLog.ip)).label("unique_ips"),
            func.count(func.distinct(NetworkLog.path)).label("unique_endpoints")
        )
        
        if not self.is_admin and self.user_id:
            query = query.where(NetworkLog.user_id == self.user_id)
        
        conditions = []
        if start_time:
            conditions.append(NetworkLog.timestamp >= start_time)
        if end_time:
            conditions.append(NetworkLog.timestamp <= end_time)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        stats = result.one()
        
        status_query = select(
            NetworkLog.status,
            func.count(NetworkLog.id).label("count")
        )
        
        if not self.is_admin and self.user_id:
            status_query = status_query.where(NetworkLog.user_id == self.user_id)
        
        if conditions:
            status_query = status_query.where(and_(*conditions))
        
        status_query = status_query.group_by(NetworkLog.status)
        status_result = await self.db.execute(status_query)
        status_dist = {row[0]: row[1] for row in status_result.fetchall()}
        
        tunnel_query = select(func.count(NetworkLog.id))
        if not self.is_admin and self.user_id:
            tunnel_query = tunnel_query.where(NetworkLog.user_id == self.user_id)
        tunnel_query = tunnel_query.where(NetworkLog.tunnel_detection.isnot(None))
        if conditions:
            tunnel_query = tunnel_query.where(and_(*conditions))
        
        tunnel_result = await self.db.execute(tunnel_query)
        tunnel_count = tunnel_result.scalar_one()
        
        return {
            "total_requests": stats.total_requests or 0,
            "avg_response_time_ms": float(stats.avg_response_time or 0),
            "min_response_time_ms": float(stats.min_response_time or 0),
            "max_response_time_ms": float(stats.max_response_time or 0),
            "unique_ips": stats.unique_ips or 0,
            "unique_endpoints": stats.unique_endpoints or 0,
            "status_distribution": status_dist,
            "tunnel_detections": tunnel_count
        }
    
    async def export_logs(
        self,
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
            filters: Optional[Dict[str, Any]] = None
    ) -> str:
        query = select(NetworkLog)
        
        if not self.is_admin and self.user_id:
            query = query.where(NetworkLog.user_id == self.user_id)
        
        conditions = []
        if start_time:
            conditions.append(NetworkLog.timestamp >= start_time)
        if end_time:
            conditions.append(NetworkLog.timestamp <= end_time)
        
        if filters:
            if filters.get("ip"):
                conditions.append(NetworkLog.ip == filters["ip"])
            if filters.get("endpoint"):
                conditions.append(NetworkLog.path == filters["endpoint"])
            if filters.get("method"):
                conditions.append(NetworkLog.method == filters["method"].upper())
            if filters.get("status") is not None:
                conditions.append(NetworkLog.status == filters["status"])
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(NetworkLog.timestamp.desc())
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        if format == "json":
            return json.dumps([self._log_to_dict(log) for log in logs], indent=2, default=str)
        elif format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                "id", "request_id", "timestamp", "ip", "method", "path", "status",
                "response_time_ms", "has_tunnel"
            ])
            writer.writeheader()
            for log in logs:
                writer.writerow({
                    "id": log.id,
                    "request_id": log.request_id,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else "",
                    "ip": log.ip or "",
                    "method": log.method,
                    "path": log.path,
                    "status": log.status,
                    "response_time_ms": log.response_time_ms,
                    "has_tunnel": "yes" if log.tunnel_detection else "no"
                })
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def get_tunnel_detections(
        self,
        limit: int = 100,
        min_confidence: str = "medium"
    ) -> List[Dict[str, Any]]:
        query = select(NetworkLog).where(NetworkLog.tunnel_detection.isnot(None))
        
        if not self.is_admin and self.user_id:
            query = query.where(NetworkLog.user_id == self.user_id)
        
        query = query.order_by(NetworkLog.timestamp.desc()).limit(limit * 2)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        detections = []
        confidence_map = {"low": 0, "medium": 1, "high": 2, "confirmed": 3}
        min_conf_level = confidence_map.get(min_confidence, 1)
        
        for log in logs:
            if not log.tunnel_detection:
                continue
            
            detection = log.tunnel_detection
            conf = detection.get("confidence", "medium")
            conf_level = confidence_map.get(conf, 1)
            
            if conf_level >= min_conf_level:
                detections.append({
                    "id": detection.get("detection_id", log.request_id),
                    "request_id": log.request_id,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "ip": log.ip,
                    "path": log.path,
                    "method": log.method,
                    "confidence": conf,
                    "risk_score": detection.get("risk_score", 0.0),
                    "indicators": detection.get("indicators", []),
                    "description": detection.get("description", "")
                })
                
                if len(detections) >= limit:
                    break
        
        return detections
    
    async def cleanup_old_logs(self) -> int:
        cutoff_date = datetime.utcnow() - timedelta(days=self.ttl_days)
        
        query = delete(NetworkLog).where(NetworkLog.timestamp < cutoff_date)
        
        if not self.is_admin and self.user_id:
            query = query.where(NetworkLog.user_id == self.user_id)
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount or 0
    
    def _log_to_dict(self, log: NetworkLog) -> Dict[str, Any]:
        return {
            "id": log.id,
            "request_id": log.request_id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "ip": log.ip,
            "method": log.method,
            "path": log.path,
            "query": log.query,
            "status": log.status,
            "response_time_ms": log.response_time_ms,
            "tunnel_detection": log.tunnel_detection,
            "headers": log.request_headers,
            "response_headers": log.response_headers,
            "body": log.request_body,
            "body_size": len(log.request_body) if log.request_body else 0,
            "body_truncated": False,
            "response_body": log.response_body,
            "response_body_size": len(log.response_body) if log.response_body else 0,
            "response_body_truncated": False,
            "user_agent": log.request_headers.get("user-agent", "") if log.request_headers else "",
            "referer": log.request_headers.get("referer", "") if log.request_headers else "",
        }

