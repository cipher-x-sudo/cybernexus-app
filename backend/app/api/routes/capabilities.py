"""
Capabilities API Routes

User-facing capability endpoints. Users interact with WHAT they want to achieve,
not HOW it's done. Underlying tools are completely abstracted.

Capabilities:
- Exposure Discovery: "What can attackers find about us online?"
- Dark Web Intelligence: "Are we mentioned on the dark web?"
- Email Security: "Can our email be spoofed?"
- Infrastructure Testing: "Are our servers misconfigured?"
- Authentication Testing: "Are our credentials weak?"
- Network Security: "Can attackers tunnel into our network?"
- Investigation: "Analyze this suspicious target"
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, AsyncGenerator
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from loguru import logger
import json
import asyncio

from app.services.orchestrator import (
    get_orchestrator, 
    Capability, 
    JobStatus, 
    JobPriority
)
from app.services.risk_engine import get_risk_engine


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class CapabilityResponse(BaseModel):
    """Capability information"""
    id: str
    name: str
    description: str
    question: str
    icon: str
    supports_scheduling: bool
    requires_tor: bool
    default_config: Dict[str, Any]


class JobCreateRequest(BaseModel):
    """Request to start a capability job"""
    capability: str = Field(..., description="Capability ID to execute")
    target: str = Field(..., description="Target domain, URL, or identifier")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Custom configuration")
    priority: str = Field(default="normal", description="Job priority: critical, high, normal, low")


class JobResponse(BaseModel):
    """Job information"""
    id: str
    capability: str
    target: str
    status: str
    progress: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    findings_count: int
    error: Optional[str]


class FindingResponse(BaseModel):
    """Security finding"""
    id: str
    capability: str
    severity: str
    title: str
    description: str
    evidence: Dict[str, Any]
    affected_assets: List[str]
    recommendations: List[str]
    discovered_at: str
    risk_score: float


class RiskScoreResponse(BaseModel):
    """Risk score information"""
    target: str
    overall_score: float
    risk_level: str
    factors: List[Dict[str, Any]]
    issues: Dict[str, int]
    last_updated: str
    trend: str


class QuickScanRequest(BaseModel):
    """Quick scan request"""
    domain: str = Field(..., description="Domain to scan")


class QuickScanResponse(BaseModel):
    """Quick scan results"""
    domain: str
    started_at: str
    completed_at: str
    jobs: List[JobResponse]
    summary: Dict[str, Any]
    risk_score: Optional[RiskScoreResponse]


# ============================================================================
# Capability Endpoints
# ============================================================================

@router.get("/", response_model=List[CapabilityResponse])
async def list_capabilities():
    """
    List all available security capabilities.
    
    Returns capabilities the user can execute, with user-friendly names
    and descriptions. Underlying tools are not exposed.
    """
    orchestrator = get_orchestrator()
    return orchestrator.get_capabilities()


@router.get("/{capability_id}", response_model=CapabilityResponse)
async def get_capability(capability_id: str):
    """
    Get details for a specific capability.
    """
    orchestrator = get_orchestrator()
    capability = orchestrator.get_capability(capability_id)
    
    if not capability:
        raise HTTPException(
            status_code=404,
            detail=f"Capability '{capability_id}' not found"
        )
    
    return capability


# ============================================================================
# Job Endpoints
# ============================================================================

@router.post("/jobs", response_model=JobResponse)
async def create_job(request: JobCreateRequest, background_tasks: BackgroundTasks):
    """
    Create and start a capability job.
    
    The job will execute the appropriate capability against the target.
    Results are available via the job status endpoint.
    """
    try:
        logger.info(f"[API] Creating job: capability={request.capability}, target={request.target}, priority={request.priority}")
        orchestrator = get_orchestrator()
        
        # Validate capability
        try:
            capability = Capability(request.capability)
        except ValueError as e:
            logger.warning(f"[API] Invalid capability: {request.capability}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid capability: {request.capability}"
            )
        
        # Map priority
        priority_map = {
            "critical": JobPriority.CRITICAL,
            "high": JobPriority.HIGH,
            "normal": JobPriority.NORMAL,
            "low": JobPriority.LOW,
            "background": JobPriority.BACKGROUND
        }
        priority = priority_map.get(request.priority.lower(), JobPriority.NORMAL)
        
        # Create job
        try:
            job = await orchestrator.create_job(
                capability=capability,
                target=request.target,
                config=request.config,
                priority=priority
            )
            logger.info(f"[API] Job created successfully: job_id={job.id}")
        except Exception as e:
            logger.error(f"[API] Failed to create job object: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")
        
        # Execute in background
        try:
            background_tasks.add_task(orchestrator.execute_job, job.id)
            logger.debug(f"[API] Background task added for job_id={job.id}")
        except Exception as e:
            logger.error(f"[API] Failed to add background task: {e}", exc_info=True)
            # Don't fail the request if background task fails, job is still created
        
        return JobResponse(
            id=job.id,
            capability=job.capability.value,
            target=job.target,
            status=job.status.value,
            progress=job.progress,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            findings_count=len(job.findings),
            error=job.error
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"[API] Unexpected error in create_job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    capability: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """
    List jobs with optional filtering.
    """
    orchestrator = get_orchestrator()
    
    # Parse filters
    cap_filter = None
    if capability:
        try:
            cap_filter = Capability(capability)
        except ValueError:
            pass
    
    status_filter = None
    if status:
        try:
            status_filter = JobStatus(status)
        except ValueError:
            pass
    
    jobs = orchestrator.get_jobs(
        capability=cap_filter,
        status=status_filter,
        limit=limit
    )
    
    return [
        JobResponse(
            id=job.id,
            capability=job.capability.value,
            target=job.target,
            status=job.status.value,
            progress=job.progress,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            findings_count=len(job.findings),
            error=job.error
        )
        for job in jobs
    ]


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """
    Get job status and details.
    """
    orchestrator = get_orchestrator()
    job = orchestrator.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(
        id=job.id,
        capability=job.capability.value,
        target=job.target,
        status=job.status.value,
        progress=job.progress,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        findings_count=len(job.findings),
        error=job.error
    )


@router.get("/jobs/{job_id}/findings", response_model=List[FindingResponse])
async def get_job_findings(
    job_id: str,
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of findings to return"),
    offset: int = Query(default=0, ge=0, description="Number of findings to skip")
):
    """
    Get findings from a completed job with pagination support.
    
    Returns findings in batches, allowing clients to retrieve data incrementally
    to avoid timeout issues with large result sets.
    """
    orchestrator = get_orchestrator()
    job = orchestrator.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Apply pagination
    total_findings = len(job.findings)
    paginated_findings = job.findings[offset:offset + limit]
    
    logger.debug(f"[API] get_job_findings: job_id={job_id}, total={total_findings}, offset={offset}, limit={limit}, returning={len(paginated_findings)}")
    
    findings_response = [
        FindingResponse(
            id=f.id,
            capability=f.capability.value,
            severity=f.severity,
            title=f.title,
            description=f.description,
            evidence=f.evidence,
            affected_assets=f.affected_assets,
            recommendations=f.recommendations,
            discovered_at=f.discovered_at.isoformat(),
            risk_score=f.risk_score
        )
        for f in paginated_findings
    ]
    
    # Add pagination metadata as response headers (FastAPI allows this via response model)
    # For now, we'll include it in a custom response format
    return findings_response


@router.get("/jobs/{job_id}/findings/stream")
async def stream_job_findings(job_id: str):
    """
    Stream findings from a job as they become available using Server-Sent Events (SSE).
    
    This endpoint allows real-time streaming of findings as they are discovered,
    preventing timeouts for long-running dark web intelligence jobs.
    
    The stream sends:
    - Findings as they are created (event: finding)
    - Progress updates (event: progress)
    - Completion status (event: complete)
    """
    from app.config import settings
    
    if not settings.DARKWEB_STREAMING_ENABLED:
        raise HTTPException(status_code=503, detail="Streaming is not enabled")
    
    orchestrator = get_orchestrator()
    job = orchestrator.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger.debug(f"[API] Starting SSE stream for job_id={job_id}")
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate SSE events for findings stream"""
        last_finding_count = 0
        check_interval = 1.0  # Check every second
        max_wait_time = 300  # Wait up to 5 minutes for job completion
        elapsed_time = 0
        
        # Send initial connection event
        yield f"event: connected\ndata: {json.dumps({'job_id': job_id, 'status': job.status.value})}\n\n"
        
        while True:
            # Refresh job data
            current_job = orchestrator.get_job(job_id)
            if not current_job:
                yield f"event: error\ndata: {json.dumps({'message': 'Job not found'})}\n\n"
                break
            
            current_findings_count = len(current_job.findings)
            
            # Send new findings
            if current_findings_count > last_finding_count:
                new_findings = current_job.findings[last_finding_count:]
                logger.debug(f"[API] Streaming {len(new_findings)} new findings for job_id={job_id}")
                
                for finding in new_findings:
                    finding_data = {
                        "id": finding.id,
                        "capability": finding.capability.value,
                        "severity": finding.severity,
                        "title": finding.title,
                        "description": finding.description,
                        "evidence": finding.evidence,
                        "affected_assets": finding.affected_assets,
                        "recommendations": finding.recommendations,
                        "discovered_at": finding.discovered_at.isoformat(),
                        "risk_score": finding.risk_score
                    }
                    yield f"event: finding\ndata: {json.dumps(finding_data)}\n\n"
                
                last_finding_count = current_findings_count
            
            # Send progress update
            progress_data = {
                "job_id": job_id,
                "status": current_job.status.value,
                "findings_count": current_findings_count,
                "progress": current_job.progress,
                "elapsed_time": elapsed_time
            }
            yield f"event: progress\ndata: {json.dumps(progress_data)}\n\n"
            
            # Check if job is complete
            if current_job.status.value in ["completed", "failed", "cancelled"]:
                completion_data = {
                    "job_id": job_id,
                    "status": current_job.status.value,
                    "total_findings": current_findings_count,
                    "error": current_job.error
                }
                yield f"event: complete\ndata: {json.dumps(completion_data)}\n\n"
                logger.debug(f"[API] SSE stream completed for job_id={job_id}, total findings={current_findings_count}")
                break
            
            # Check timeout
            if elapsed_time >= max_wait_time:
                timeout_data = {
                    "job_id": job_id,
                    "message": "Stream timeout reached",
                    "findings_count": current_findings_count
                }
                yield f"event: timeout\ndata: {json.dumps(timeout_data)}\n\n"
                logger.debug(f"[API] SSE stream timeout for job_id={job_id}")
                break
            
            await asyncio.sleep(check_interval)
            elapsed_time += check_interval
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )


# ============================================================================
# Findings Endpoints
# ============================================================================

@router.get("/findings", response_model=List[FindingResponse])
async def list_findings(
    capability: Optional[str] = None,
    severity: Optional[str] = None,
    target: Optional[str] = None,
    min_risk_score: float = Query(default=0, ge=0, le=100),
    limit: int = Query(default=100, le=500)
):
    """
    List all findings with optional filtering.
    """
    orchestrator = get_orchestrator()
    
    # Parse capability filter
    cap_filter = None
    if capability:
        try:
            cap_filter = Capability(capability)
        except ValueError:
            pass
    
    findings = orchestrator.get_findings(
        capability=cap_filter,
        severity=severity,
        target=target,
        min_risk_score=min_risk_score,
        limit=limit
    )
    
    return [
        FindingResponse(
            id=f.id,
            capability=f.capability.value,
            severity=f.severity,
            title=f.title,
            description=f.description,
            evidence=f.evidence,
            affected_assets=f.affected_assets,
            recommendations=f.recommendations,
            discovered_at=f.discovered_at.isoformat(),
            risk_score=f.risk_score
        )
        for f in findings
    ]


@router.get("/findings/critical", response_model=List[FindingResponse])
async def get_critical_findings(limit: int = Query(default=10, le=50)):
    """
    Get critical and high severity findings that need immediate attention.
    """
    orchestrator = get_orchestrator()
    findings = orchestrator.get_critical_findings(limit=limit)
    
    return [
        FindingResponse(
            id=f.id,
            capability=f.capability.value,
            severity=f.severity,
            title=f.title,
            description=f.description,
            evidence=f.evidence,
            affected_assets=f.affected_assets,
            recommendations=f.recommendations,
            discovered_at=f.discovered_at.isoformat(),
            risk_score=f.risk_score
        )
        for f in findings
    ]


# ============================================================================
# Risk Score Endpoints
# ============================================================================

@router.get("/risk/{target}", response_model=RiskScoreResponse)
async def get_risk_score(target: str):
    """
    Get the current risk score for a target.
    """
    risk_engine = get_risk_engine()
    orchestrator = get_orchestrator()
    
    # Get findings for target
    findings = orchestrator.get_findings_for_target(target)
    
    if not findings:
        raise HTTPException(
            status_code=404,
            detail=f"No data available for target: {target}"
        )
    
    # Calculate risk score
    findings_dicts = [f.to_dict() for f in findings]
    risk_score = risk_engine.calculate_risk_score(target, findings_dicts)
    
    return RiskScoreResponse(**risk_score.to_dict())


@router.get("/risk/{target}/history")
async def get_risk_history(
    target: str,
    days: int = Query(default=30, ge=1, le=365)
):
    """
    Get risk score history for a target.
    """
    risk_engine = get_risk_engine()
    history = risk_engine.get_risk_history(target, days=days)
    
    return {
        "target": target,
        "period_days": days,
        "history": history
    }


@router.get("/risk/{target}/breakdown")
async def get_risk_breakdown(target: str):
    """
    Get detailed risk category breakdown for a target.
    """
    risk_engine = get_risk_engine()
    breakdown = risk_engine.get_category_breakdown(target)
    
    if not breakdown:
        raise HTTPException(
            status_code=404,
            detail=f"No risk data available for target: {target}"
        )
    
    return breakdown


@router.get("/risk/{target}/top-risks")
async def get_top_risks(
    target: str,
    limit: int = Query(default=5, ge=1, le=10)
):
    """
    Get top risk areas for a target with recommendations.
    """
    risk_engine = get_risk_engine()
    top_risks = risk_engine.get_top_risks(target, limit=limit)
    
    return {
        "target": target,
        "top_risks": top_risks
    }


# ============================================================================
# Quick Scan Endpoint
# ============================================================================

@router.post("/quick-scan", response_model=QuickScanResponse)
async def quick_scan(request: QuickScanRequest):
    """
    Perform a quick security assessment of a domain.
    
    This is the recommended starting point for new users. It runs
    essential checks and provides an initial risk score.
    """
    orchestrator = get_orchestrator()
    risk_engine = get_risk_engine()
    
    logger.info(f"Starting quick scan for {request.domain}")
    
    try:
        # Run quick scan
        results = await orchestrator.quick_scan(request.domain)
        
        # Get risk score
        findings = orchestrator.get_findings_for_target(request.domain)
        findings_dicts = [f.to_dict() for f in findings]
        risk_score = risk_engine.calculate_risk_score(request.domain, findings_dicts)
        
        return QuickScanResponse(
            domain=request.domain,
            started_at=results["started_at"],
            completed_at=results["completed_at"],
            jobs=[
                JobResponse(
                    id=j["id"],
                    capability=j["capability"],
                    target=j["target"],
                    status=j["status"],
                    progress=j["progress"],
                    created_at=j["created_at"],
                    started_at=j.get("started_at"),
                    completed_at=j.get("completed_at"),
                    findings_count=j["findings_count"],
                    error=j.get("error")
                )
                for j in results["jobs"]
            ],
            summary=results["summary"],
            risk_score=RiskScoreResponse(**risk_score.to_dict())
        )
        
    except Exception as e:
        logger.error(f"Quick scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Statistics Endpoint
# ============================================================================

@router.get("/stats")
async def get_stats():
    """
    Get overall capability and risk statistics.
    """
    orchestrator = get_orchestrator()
    risk_engine = get_risk_engine()
    
    return {
        "orchestrator": orchestrator.get_stats(),
        "risk": risk_engine.get_global_stats(),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/events")
async def get_recent_events(limit: int = Query(default=50, le=200)):
    """
    Get recent capability events for live activity feed.
    """
    orchestrator = get_orchestrator()
    events = orchestrator.get_recent_events(limit=limit)
    
    return {
        "events": events,
        "count": len(events)
    }



