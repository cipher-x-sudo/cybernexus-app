from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Response, Depends
from pydantic import BaseModel
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.core.database.network_log_storage import DBNetworkLogStorage
from app.api.routes.auth import get_current_active_user, User, is_admin
from app.services.block_manager import get_block_manager
from app.services.rate_limiter import get_rate_limiter
from app.services.tunnel_analyzer import get_tunnel_analyzer


router = APIRouter()


class BlockIPRequest(BaseModel):
    """Request model for blocking an IP address."""
    ip: str
    reason: str = ""
    created_by: str = ""


class BlockEndpointRequest(BaseModel):
    """Request model for blocking an endpoint pattern."""
    pattern: str
    method: str = "ALL"
    reason: str = ""
    created_by: str = ""


class BlockPatternRequest(BaseModel):
    """Request model for blocking a request pattern."""
    pattern_type: str
    pattern: str
    reason: str = ""
    created_by: str = ""


class ExportRequest(BaseModel):
    """Request model for exporting network logs."""
    format: str = "json"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


@router.get("/logs")
async def get_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    start_time: Optional[str] = Query(default=None),
    end_time: Optional[str] = Query(default=None),
    ip: Optional[str] = Query(default=None),
    endpoint: Optional[str] = Query(default=None),
    method: Optional[str] = Query(default=None),
    status: Optional[int] = Query(default=None),
    has_tunnel: Optional[bool] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get network logs with optional filtering by time, IP, endpoint, method, status, and tunnel detection."""
    try:
        storage = DBNetworkLogStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        
        # Parse datetime strings
        start_dt = None
        end_dt = None
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
        if end_time:
            end_dt = datetime.fromisoformat(end_time)
        
        logs = await storage.get_logs(
            limit=limit,
            offset=offset,
            start_time=start_dt,
            end_time=end_dt,
            ip=ip,
            endpoint=endpoint,
            method=method,
            status=status,
            has_tunnel=has_tunnel
        )
        
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{request_id}")
async def get_log(
    request_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific network log entry by request ID."""
    try:
        storage = DBNetworkLogStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        log = await storage.get_log(request_id)
        
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")
        
        return log
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/search")
async def search_logs(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Search network logs by query string (searches path, query params, request/response body)."""
    try:
        storage = DBNetworkLogStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        logs = await storage.search_logs(q, limit=limit)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(
    start_time: Optional[str] = Query(default=None),
    end_time: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated statistics about network logs and tunnel detections."""
    try:
        storage = DBNetworkLogStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        
        # Parse datetime strings
        start_dt = None
        end_dt = None
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
        if end_time:
            end_dt = datetime.fromisoformat(end_time)
        
        stats = await storage.get_stats(start_dt, end_dt)
        
        # Add tunnel detector statistics
        analyzer = get_tunnel_analyzer()
        tunnel_stats = analyzer.get_detector_stats()
        stats["tunnel_detector"] = tunnel_stats
        
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tunnels")
async def get_tunnels(
    limit: int = Query(default=100, ge=1, le=1000),
    min_confidence: str = Query(default="medium", regex="^(low|medium|high|confirmed)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tunnel detections filtered by minimum confidence level."""
    try:
        storage = DBNetworkLogStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        detections = await storage.get_tunnel_detections(limit=limit, min_confidence=min_confidence)
        return {"detections": detections, "count": len(detections)}
    except Exception as e:
        logger.error(f"Error getting tunnels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/blocks/ip")
async def block_ip(request: BlockIPRequest):
    """Block an IP address from accessing the system."""
    try:
        block_manager = get_block_manager()
        success = await block_manager.block_ip(
            request.ip,
            reason=request.reason,
            created_by=request.created_by
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to block IP")
        
        return {"message": f"IP {request.ip} blocked", "ip": request.ip}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error blocking IP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/blocks/ip/{ip}")
async def unblock_ip(ip: str):
    """Remove an IP address from the block list."""
    try:
        block_manager = get_block_manager()
        success = await block_manager.unblock_ip(ip)
        
        if not success:
            raise HTTPException(status_code=404, detail="IP not found in block list")
        
        return {"message": f"IP {ip} unblocked", "ip": ip}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unblocking IP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blocks/ip")
async def get_blocked_ips():
    """Get list of all blocked IP addresses."""
    try:
        block_manager = get_block_manager()
        blocked = await block_manager.get_blocked_ips()
        return {"blocked_ips": blocked, "count": len(blocked)}
    except Exception as e:
        logger.error(f"Error getting blocked IPs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/blocks/endpoint")
async def block_endpoint(request: BlockEndpointRequest):
    """Block an endpoint pattern (optionally for specific HTTP method)."""
    try:
        block_manager = get_block_manager()
        success = await block_manager.block_endpoint(
            request.pattern,
            method=request.method,
            reason=request.reason,
            created_by=request.created_by
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to block endpoint")
        
        return {
            "message": f"Endpoint {request.method} {request.pattern} blocked",
            "pattern": request.pattern,
            "method": request.method
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error blocking endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/blocks/endpoint/{pattern}")
async def unblock_endpoint(pattern: str):
    """Remove an endpoint pattern from the block list."""
    try:
        block_manager = get_block_manager()
        success = await block_manager.unblock_endpoint(pattern)
        
        if not success:
            raise HTTPException(status_code=404, detail="Endpoint not found in block list")
        
        return {"message": f"Endpoint {pattern} unblocked", "pattern": pattern}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unblocking endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blocks/endpoint")
async def get_blocked_endpoints():
    """Get list of all blocked endpoint patterns."""
    try:
        block_manager = get_block_manager()
        blocked = await block_manager.get_blocked_endpoints()
        return {"blocked_endpoints": blocked, "count": len(blocked)}
    except Exception as e:
        logger.error(f"Error getting blocked endpoints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/blocks/pattern")
async def block_pattern(request: BlockPatternRequest):
    """Block a request pattern (e.g., user-agent, header pattern)."""
    try:
        block_manager = get_block_manager()
        block_id = await block_manager.block_pattern(
            request.pattern_type,
            request.pattern,
            reason=request.reason,
            created_by=request.created_by
        )
        
        if not block_id:
            raise HTTPException(status_code=500, detail="Failed to block pattern")
        
        return {
            "message": f"Pattern blocked",
            "block_id": block_id,
            "pattern_type": request.pattern_type,
            "pattern": request.pattern
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error blocking pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/blocks/pattern/{block_id}")
async def unblock_pattern(block_id: str):
    """Remove a pattern from the block list by block ID."""
    try:
        block_manager = get_block_manager()
        success = await block_manager.unblock_pattern(block_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Pattern not found in block list")
        
        return {"message": f"Pattern {block_id} unblocked", "block_id": block_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unblocking pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blocks/pattern")
async def get_blocked_patterns():
    """Get list of all blocked request patterns."""
    try:
        block_manager = get_block_manager()
        blocked = await block_manager.get_blocked_patterns()
        return {"blocked_patterns": blocked, "count": len(blocked)}
    except Exception as e:
        logger.error(f"Error getting blocked patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blocks")
async def get_all_blocks():
    """Get all blocks (IPs, endpoints, patterns) in a single response."""
    try:
        block_manager = get_block_manager()
        blocks = await block_manager.get_all_blocks()
        return blocks
    except Exception as e:
        logger.error(f"Error getting all blocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rate-limit/{ip}")
async def get_rate_limit_status(
    ip: str,
    endpoint: Optional[str] = Query(default=None)
):
    """Get current rate limit status for an IP address (optionally for specific endpoint)."""
    try:
        rate_limiter = get_rate_limiter()
        status = await rate_limiter.get_rate_limit_status(ip, endpoint)
        return status
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_logs(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Export network logs in specified format (JSON, CSV, HAR) with optional filtering."""
    try:
        storage = DBNetworkLogStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        
        # Parse datetime strings
        start_dt = None
        end_dt = None
        if request.start_time:
            start_dt = datetime.fromisoformat(request.start_time)
        if request.end_time:
            end_dt = datetime.fromisoformat(request.end_time)
        
        exported = await storage.export_logs(
            format=request.format,
            start_time=start_dt,
            end_time=end_dt,
            filters=request.filters
        )
        
        # Set appropriate content type for download
        content_type = "application/json"
        if request.format == "csv":
            content_type = "text/csv"
        elif request.format == "har":
            content_type = "application/json"
        
        return Response(
            content=exported,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="network_logs.{request.format}"'
            }
        )
    except Exception as e:
        logger.error(f"Error exporting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

