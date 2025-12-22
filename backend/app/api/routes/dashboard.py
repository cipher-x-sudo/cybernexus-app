from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query, HTTPException, Depends
from loguru import logger

from app.services.orchestrator import get_orchestrator, Capability, JobStatus
from app.services.risk_engine import get_risk_engine
from app.services.positive_scorer import get_positive_scorer
from app.api.routes.auth import get_current_active_user, User
from app.core.database.database import get_db
from app.core.database.job_storage import DBJobStorage
from app.core.database.finding_storage import DBFindingStorage

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def calculate_risk_score(
    findings: List[Dict[str, Any]], 
    resolved_findings: Optional[Dict[str, int]] = None,
    positive_indicators: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    critical_count = sum(1 for f in findings if f.get("severity", "").lower() == "critical")
    high_count = sum(1 for f in findings if f.get("severity", "").lower() == "high")
    medium_count = sum(1 for f in findings if f.get("severity", "").lower() == "medium")
    low_count = sum(1 for f in findings if f.get("severity", "").lower() == "low")
    
    base_score = 100
    deductions = (critical_count * 20) + (high_count * 10) + (medium_count * 5) + (low_count * 2)
    
    resolved_points = 0
    resolved_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    if resolved_findings:
        resolved_counts = resolved_findings
        resolved_points = (
            resolved_counts.get("critical", 0) * 25 +
            resolved_counts.get("high", 0) * 12 +
            resolved_counts.get("medium", 0) * 6 +
            resolved_counts.get("low", 0) * 3
        )
    
    indicator_points = 0
    if positive_indicators:
        indicator_points = sum(ind.get("points_awarded", 0) for ind in positive_indicators)
    
    score = base_score - deductions + resolved_points + indicator_points
    score = max(0, min(100, score))
    
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
        "low_count": low_count,
        "resolved_critical_count": resolved_counts.get("critical", 0),
        "resolved_high_count": resolved_counts.get("high", 0),
        "resolved_medium_count": resolved_counts.get("medium", 0),
        "resolved_low_count": resolved_counts.get("low", 0),
        "positive_points": {
            "resolved": resolved_points,
            "indicators": indicator_points,
            "total": resolved_points + indicator_points
        },
        "deductions": deductions
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
        
        finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
        all_findings = await finding_storage.get_findings(limit=1000)
        
        findings_data = [{
            "id": f.id,
            "title": f.title,
            "severity": f.severity,
            "capability": f.capability.value,
            "target": f.target,
            "risk_score": f.risk_score,
            "status": getattr(f, 'status', 'active'),
            "discovered_at": f.discovered_at.isoformat() if f.discovered_at else datetime.now(timezone.utc).isoformat()
        } for f in all_findings]
        
        resolved_findings = await finding_storage.get_resolved_findings()
        
        positive_indicators = await finding_storage.get_positive_indicators(limit=100)
        
        risk_data = calculate_risk_score(findings_data, resolved_findings, positive_indicators)
        
        critical_findings = [f for f in findings_data if f.get("severity", "").lower() in ["critical", "high"]]
        critical_findings = sorted(critical_findings, key=lambda x: x.get("risk_score", 0), reverse=True)[:10]
        
        job_storage = DBJobStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
        recent_jobs = await job_storage.list_jobs(limit=10, offset=0)
        jobs_data = []
        for job in recent_jobs:
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
        
        recent_events = orchestrator.get_recent_events(limit=20)
        
        stats = orchestrator.get_stats()
        
        total_jobs_count = await job_storage.count_jobs()
        
        capability_stats = {}
        for capability in Capability:
            cap_jobs = await job_storage.list_jobs(capability=capability, limit=100)
            cap_findings = await finding_storage.get_findings(capability=capability, limit=100)
            
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
        
        timeline_stats = {
            "total_events": len(recent_events),
            "events_24h": len([e for e in recent_events if _is_within_24h(e.get("timestamp", ""))])
        }
        
        previous_score = None
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
        finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
        findings = await finding_storage.get_critical_findings(limit=limit)
        
        findings_data = []
        now = datetime.now(timezone.utc)
        for finding in findings:
            time_diff = now - finding.discovered_at
            if time_diff.days > 0:
                time_ago = f"{time_diff.days}d ago"
            elif time_diff.seconds > 3600:
                time_ago = f"{time_diff.seconds // 3600}h ago"
            else:
                time_ago = f"{time_diff.seconds // 60}m ago"
            
            finding_status = getattr(finding, 'status', 'active')
            resolved_at = getattr(finding, 'resolved_at', None)
            
            resolved_time_ago = None
            if finding_status == "resolved" and resolved_at:
                resolved_diff = now - resolved_at
                if resolved_diff.days > 0:
                    resolved_time_ago = f"{resolved_diff.days}d ago"
                elif resolved_diff.seconds > 3600:
                    resolved_time_ago = f"{resolved_diff.seconds // 3600}h ago"
                else:
                    resolved_time_ago = f"{resolved_diff.seconds // 60}m ago"
            
            findings_data.append({
                "id": finding.id,
                "title": finding.title,
                "severity": finding.severity,
                "capability": finding.capability.value,
                "target": finding.target,
                "time_ago": time_ago,
                "risk_score": finding.risk_score,
                "discovered_at": finding.discovered_at.isoformat(),
                "status": finding_status,
                "resolved_at": resolved_at.isoformat() if resolved_at else None,
                "resolved_time_ago": resolved_time_ago
            })
        
        return {
            "findings": findings_data,
            "count": len(findings_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting critical findings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching critical findings: {str(e)}")


@router.get("/risk-breakdown")
async def get_risk_breakdown(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get detailed risk score breakdown aggregated across all targets.
    
    Returns:
    - Overall score and risk level
    - Category-wise breakdown (exposure, dark_web, email_security, etc.)
    - Severity distribution per category
    - Calculation details
    - Recommendations
    """
    try:        
        finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
        all_findings = await finding_storage.get_findings(limit=1000)
        
        active_findings = list(all_findings)
        
        if not active_findings and not all_findings:
            return {
                "overall_score": 100,
                "risk_level": "minimal",
                "trend": "stable",
                "categories": {},
                "severity_distribution": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                },
                "calculation": {
                    "base_score": 100,
                    "deductions": {
                        "critical": 0,
                        "high": 0,
                        "medium": 0,
                        "low": 0
                    },
                    "additions": {
                        "resolved": 0,
                        "indicators": 0,
                        "total": 0
                    },
                    "formula": "Base Score (100) - Deductions + Positive Points"
                },
                "positive_points": {
                    "resolved": 0,
                    "indicators": 0,
                    "total": 0
                },
                "recommendations": []
            }
        
        findings_data = [{
            "id": f.id,
            "title": f.title,
            "severity": f.severity,
            "capability": f.capability.value,
            "target": f.target,
            "risk_score": f.risk_score,
        } for f in active_findings]
        
        resolved_findings = await finding_storage.get_resolved_findings()
        positive_indicators = await finding_storage.get_positive_indicators(limit=100)
        
        risk_data = calculate_risk_score(findings_data, resolved_findings, positive_indicators)
        
        capability_names = {
            "exposure_discovery": "Exposure Discovery",
            "dark_web_intelligence": "Dark Web Intel",
            "email_security": "Email Security",
            "infrastructure_testing": "Infrastructure",
            "network_security": "Network Security",
            "investigation": "Investigation"
        }
        
        findings_by_capability: Dict[str, List[Dict[str, Any]]] = {}
        for finding in findings_data:
            capability = finding.get("capability", "unknown")
            if capability not in findings_by_capability:
                findings_by_capability[capability] = []
            findings_by_capability[capability].append(finding)
        
        categories = {}
        total_deductions = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        for capability, findings in findings_by_capability.items():
            critical_count = sum(1 for f in findings if f.get("severity", "").lower() == "critical")
            high_count = sum(1 for f in findings if f.get("severity", "").lower() == "high")
            medium_count = sum(1 for f in findings if f.get("severity", "").lower() == "medium")
            low_count = sum(1 for f in findings if f.get("severity", "").lower() == "low")
            
            category_score = 100
            category_score -= (critical_count * 20)
            category_score -= (high_count * 10)
            category_score -= (medium_count * 5)
            category_score -= (low_count * 2)
            category_score = max(0, min(100, category_score))
            
            total_findings = len(findings)
            contribution = (critical_count * 20) + (high_count * 10) + (medium_count * 5) + (low_count * 2)
            
            total_deductions["critical"] += critical_count
            total_deductions["high"] += high_count
            total_deductions["medium"] += medium_count
            total_deductions["low"] += low_count
            
            categories[capability] = {
                "name": capability_names.get(capability, capability.replace("_", " ").title()),
                "score": category_score,
                "findings_count": total_findings,
                "contribution": contribution,
                "severity_breakdown": {
                    "critical": critical_count,
                    "high": high_count,
                    "medium": medium_count,
                    "low": low_count
                }
            }
        
        recommendations = []
        
        if risk_data["critical_count"] > 0:
            recommendations.append({
                "priority": "critical",
                "title": f"Address {risk_data['critical_count']} Critical Finding(s)",
                "description": "Critical findings pose immediate security risks and should be addressed immediately.",
                "action": "Review and remediate all critical findings as soon as possible."
            })
        
        if risk_data["high_count"] > 0:
            recommendations.append({
                "priority": "high",
                "title": f"Review {risk_data['high_count']} High Severity Finding(s)",
                "description": "High severity findings require prompt attention to prevent potential security incidents.",
                "action": "Schedule remediation for high severity findings within 7 days."
            })
        
        for capability, cat_data in categories.items():
            if cat_data["severity_breakdown"]["critical"] > 0 or cat_data["severity_breakdown"]["high"] > 0:
                recommendations.append({
                    "priority": "high" if cat_data["severity_breakdown"]["critical"] > 0 else "medium",
                    "title": f"Improve {cat_data['name']} Security",
                    "description": f"{cat_data['name']} has {cat_data['severity_breakdown']['critical']} critical and {cat_data['severity_breakdown']['high']} high findings.",
                    "action": f"Focus on addressing findings in {cat_data['name']} to improve overall security posture."
                })
        
        if risk_data["risk_score"] < 60:
            recommendations.append({
                "priority": "high",
                "title": "Overall Security Posture Needs Improvement",
                "description": f"Your security score of {risk_data['risk_score']}/100 indicates significant security risks.",
                "action": "Prioritize remediation of critical and high severity findings across all categories."
            })
        
        previous_score = None
        trend = calculate_trend(risk_data["risk_score"], previous_score)
        
        return {
            "overall_score": risk_data["risk_score"],
            "risk_level": risk_data["risk_level"],
            "trend": trend,
            "categories": categories,
            "severity_distribution": {
                "critical": risk_data["critical_count"],
                "high": risk_data["high_count"],
                "medium": risk_data["medium_count"],
                "low": risk_data["low_count"]
            },
            "calculation": {
                "base_score": 100,
                "deductions": total_deductions,
                "total_deduction": sum([
                    total_deductions["critical"] * 20,
                    total_deductions["high"] * 10,
                    total_deductions["medium"] * 5,
                    total_deductions["low"] * 2
                ]),
                "additions": risk_data.get("positive_points", {"resolved": 0, "indicators": 0, "total": 0}),
                "formula": "Base Score (100) - Deductions + Positive Points (Resolved + Indicators)"
            },
            "positive_points": risk_data.get("positive_points", {"resolved": 0, "indicators": 0, "total": 0}),
            "recommendations": recommendations[:10]  # Limit to top 10
        }
        
    except Exception as e:
        logger.error(f"Error getting risk breakdown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching risk breakdown: {str(e)}")


@router.get("/positive-indicators")
async def get_positive_indicators(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get positive security indicators for the current user.
    """
    try:
        finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
        indicators = await finding_storage.get_positive_indicators(limit=100)
        
        return {
            "indicators": indicators,
            "count": len(indicators),
            "total_points": sum(ind.get("points_awarded", 0) for ind in indicators)
        }
    except Exception as e:
        logger.error(f"Error getting positive indicators: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching positive indicators: {str(e)}")


@router.post("/positive-indicators")
async def create_positive_indicator(
    indicator_type: str,
    category: str,
    points_awarded: int,
    description: str,
    target: Optional[str] = None,
    evidence: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Manually create a positive indicator.
    
    Args:
        indicator_type: Type of indicator (strong_config, no_vulnerabilities, improvement, etc.)
        category: Category (exposure, dark_web, email_security, etc.)
        points_awarded: Points to award
        description: Description of the indicator
        target: Target domain/IP (optional)
        evidence: Additional evidence (optional)
    """
    try:
        from app.core.database.models import PositiveIndicator
        import uuid
        
        indicator = PositiveIndicator(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            indicator_type=indicator_type,
            category=category,
            points_awarded=points_awarded,
            description=description,
            target=target,
            evidence=evidence or {},
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(indicator)
        await db.commit()
        await db.refresh(indicator)
        
        return {
            "id": indicator.id,
            "indicator_type": indicator.indicator_type,
            "category": indicator.category,
            "points_awarded": indicator.points_awarded,
            "description": indicator.description,
            "created_at": indicator.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating positive indicator: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating positive indicator: {str(e)}")

