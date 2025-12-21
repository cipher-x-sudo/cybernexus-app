"""
Dashboard API Routes

Provides aggregated data for the main dashboard overview.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query, HTTPException, Depends
from loguru import logger

from app.services.orchestrator import get_orchestrator, Capability, JobStatus
from app.services.risk_engine import get_risk_engine
from app.api.routes.auth import get_current_active_user, User
from app.core.database.database import get_db
from app.core.database.job_storage import DBJobStorage
from app.core.database.finding_storage import DBFindingStorage

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def calculate_risk_score(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate risk score from findings.
    
    Args:
        findings: List of finding dictionaries
        
    Returns:
        Dictionary with risk_score, risk_level, critical_count, high_count
    """
    if not findings:
        return {
            "risk_score": 100,
            "risk_level": "minimal",
            "critical_count": 0,
            "high_count": 0
        }
    
    critical_count = sum(1 for f in findings if f.get("severity") == "critical")
    high_count = sum(1 for f in findings if f.get("severity") == "high")
    medium_count = sum(1 for f in findings if f.get("severity") == "medium")
    low_count = sum(1 for f in findings if f.get("severity") == "low")
    
    # Calculate risk score (0-100, higher is better)
    # Critical: -20 points each, High: -10, Medium: -5, Low: -2
    base_score = 100
    score = base_score - (critical_count * 20) - (high_count * 10) - (medium_count * 5) - (low_count * 2)
    score = max(0, min(100, score))
    
    # Determine risk level
    if score >= 80:
        risk_level = "minimal"
    elif score >= 60:
        risk_level = "low"
    elif score >= 40:
        risk_level = "medium"
    elif score >= 20:
        risk_level = "high"
    else:
        risk_level = "critical"
    
    return {
        "risk_score": score,
        "risk_level": risk_level,
        "critical_count": critical_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count
    }


def calculate_trend(current_score: int, previous_score: Optional[int]) -> str:
    """Calculate trend based on score comparison.
    
    Args:
        current_score: Current risk score
        previous_score: Previous period risk score (if available)
        
    Returns:
        "improving", "worsening", or "stable"
    """
    if previous_score is None:
        return "stable"
    
    diff = current_score - previous_score
    if diff > 5:
        return "improving"
    elif diff < -5:
        return "worsening"
    else:
        return "stable"


@router.get("/overview")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get comprehensive dashboard overview data.
    
    Returns aggregated data including:
    - Risk score and metrics
    - Recent jobs
    - Recent events
    - Capability statistics
    - Threat map data
    """
    try:
        orchestrator = get_orchestrator()
        risk_engine = get_risk_engine()
        
        # Get all findings from database
        finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
        all_findings = await finding_storage.get_findings(limit=1000)
        findings_data = [{
            "id": f.id,
            "title": f.title,
            "severity": f.severity,
            "capability": f.capability.value,
            "target": f.target,
            "risk_score": f.risk_score,
            "discovered_at": f.discovered_at.isoformat() if f.discovered_at else datetime.now(timezone.utc).isoformat()
        } for f in all_findings]
        
        # Calculate risk score
        risk_data = calculate_risk_score(findings_data)
        
        # Get critical and high findings for dashboard
        critical_findings = [f for f in findings_data if f.get("severity") in ["critical", "high"]]
        critical_findings = sorted(critical_findings, key=lambda x: x.get("risk_score", 0), reverse=True)[:10]
        
        # Get recent jobs from database (last 10)
        job_storage = DBJobStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
        recent_jobs = await job_storage.list_jobs(limit=10, offset=0)
        jobs_data = []
        for job in recent_jobs:
            # Calculate time ago
            now = datetime.now(timezone.utc)
            if job.completed_at:
                time_diff = now - job.completed_at
                if time_diff.days > 0:
                    time_ago = f"{time_diff.days}d ago"
                elif time_diff.seconds > 3600:
                    time_ago = f"{time_diff.seconds // 3600}h ago"
                else:
                    time_ago = f"{time_diff.seconds // 60}m ago"
            elif job.started_at:
                time_diff = now - job.started_at
                time_ago = f"Started {time_diff.seconds // 60}m ago"
            else:
                time_ago = "Just created"
            
            # Get findings count from database
            findings = await finding_storage.get_findings_for_job(job.id)
            findings_count = len(findings)
            
            jobs_data.append({
                "id": job.id,
                "capability": job.capability.value,
                "target": job.target,
                "status": job.status.value,
                "progress": job.progress,
                "findings_count": findings_count,
                "time_ago": time_ago,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            })
        
        # Get recent events
        recent_events = orchestrator.get_recent_events(limit=20)
        
        # Get orchestrator stats (for total counts, still use orchestrator)
        stats = orchestrator.get_stats()
        
        # Get total jobs count from database
        total_jobs_count = await job_storage.count_jobs()
        
        # Calculate capability statistics from database
        capability_stats = {}
        for capability in Capability:
            cap_jobs = await job_storage.list_jobs(capability=capability, limit=100)
            cap_findings = await finding_storage.get_findings(capability=capability, limit=100)
            
            # Find last run time
            last_run = None
            if cap_jobs:
                completed_jobs = [j for j in cap_jobs if j.status == JobStatus.COMPLETED]
                if completed_jobs:
                    latest = max(completed_jobs, key=lambda j: j.completed_at if j.completed_at else datetime.min.replace(tzinfo=timezone.utc))
                    if latest.completed_at:
                        time_diff = datetime.now(timezone.utc) - latest.completed_at
                        if time_diff.days > 0:
                            last_run = f"{time_diff.days}d ago"
                        elif time_diff.seconds > 3600:
                            last_run = f"{time_diff.seconds // 3600}h ago"
                        else:
                            last_run = f"{time_diff.seconds // 60}m ago"
            
            capability_stats[capability.value] = {
                "scans": len(cap_jobs),
                "findings": len(cap_findings),
                "last_run": last_run or "Never"
            }
        
        # Get threat map data (findings with potential geographic info)
        # For now, we'll use findings as threat map data
        # In the future, this could include actual geographic coordinates
        threat_map_data = []
        for finding in critical_findings[:20]:  # Top 20 for map
            threat_map_data.append({
                "id": finding.get("id"),
                "title": finding.get("title"),
                "severity": finding.get("severity"),
                "risk_score": finding.get("risk_score", 0),
                "target": finding.get("target", ""),
                "capability": finding.get("capability"),
                "discovered_at": finding.get("discovered_at")
            })
        
        # Get timeline stats
        timeline_stats = {
            "total_events": len(recent_events),
            "events_24h": len([e for e in recent_events if _is_within_24h(e.get("timestamp", ""))])
        }
        
        # Calculate trend (simplified - compare with previous period)
        # In a real implementation, you'd store historical scores
        previous_score = None  # TODO: Store and retrieve historical scores
        trend = calculate_trend(risk_data["risk_score"], previous_score)
        
        return {
            "risk_score": risk_data["risk_score"],
            "risk_level": risk_data["risk_level"],
            "trend": trend,
            "critical_findings_count": risk_data["critical_count"],
            "high_findings_count": risk_data["high_count"],
            "total_jobs": total_jobs_count,
            "active_jobs": len([j for j in recent_jobs if j.status == JobStatus.RUNNING]),
            "recent_jobs": jobs_data,
            "recent_events": recent_events,
            "capability_stats": capability_stats,
            "threat_map_data": threat_map_data,
            "timeline_stats": timeline_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")


def _is_within_24h(timestamp_str: str) -> bool:
    """Check if timestamp is within last 24 hours."""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        # Ensure timestamp is timezone-aware
        if not timestamp.tzinfo:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        time_diff = datetime.now(timezone.utc) - timestamp
        return time_diff <= timedelta(hours=24)
    except:
        return False


@router.get("/critical-findings")
async def get_critical_findings(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get critical and high severity findings for dashboard.
    Queries from database, filtered by current user.
    """
    try:
        # Get critical findings from database
        finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
        findings = await finding_storage.get_critical_findings(limit=limit)
        
        findings_data = []
        now = datetime.now(timezone.utc)
        for finding in findings:
            # Calculate time ago
            time_diff = now - finding.discovered_at
            if time_diff.days > 0:
                time_ago = f"{time_diff.days}d ago"
            elif time_diff.seconds > 3600:
                time_ago = f"{time_diff.seconds // 3600}h ago"
            else:
                time_ago = f"{time_diff.seconds // 60}m ago"
            
            findings_data.append({
                "id": finding.id,
                "title": finding.title,
                "severity": finding.severity,
                "capability": finding.capability.value,
                "target": finding.target,
                "time_ago": time_ago,
                "risk_score": finding.risk_score,
                "discovered_at": finding.discovered_at.isoformat()
            })
        
        return {
            "findings": findings_data,
            "count": len(findings_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting critical findings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching critical findings: {str(e)}")

