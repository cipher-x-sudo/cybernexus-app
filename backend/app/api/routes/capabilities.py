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
from concurrent.futures import ThreadPoolExecutor

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


class IncrementalFindingsResponse(BaseModel):
    """Incremental findings response with metadata"""
    findings: List[FindingResponse]
    has_more: bool
    total_findings: int
    new_count: int
    last_finding_id: Optional[str] = None
    last_finding_timestamp: Optional[str] = None


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

def run_job_in_thread(job_id: str, orchestrator_instance):
    """
    Synchronous wrapper to run async job execution in a separate thread.
    Creates a new event loop for the thread to avoid conflicts.
    """
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(orchestrator_instance.execute_job(job_id))
        finally:
            loop.close()
    except Exception as e:
        logger.error(
            f"[API] [create_job] Error in background job thread for {job_id}: {e}",
            exc_info=True
        )


@router.post("/jobs", response_model=JobResponse)
async def create_job(request: JobCreateRequest):
    """
    Create and start a capability job.
    
    The job will execute the appropriate capability against the target in the background.
    This endpoint returns immediately with the job ID. To get results:
    
    1. Poll job status via GET /api/v1/capabilities/jobs/{job_id} every 3 seconds
    2. Check the 'status' field: "pending" → "running" → "completed" or "failed"
    3. When status is "completed", fetch findings via GET /api/v1/capabilities/jobs/{job_id}/findings
    """
    import time
    request_start_time = time.time()
    
    try:
        logger.info(
            f"[API] [create_job] Request received - capability={request.capability}, "
            f"target={request.target}, priority={request.priority}, "
            f"config={request.config}"
        )
        orchestrator = get_orchestrator()
        
        # Validate capability
        validation_start = time.time()
        try:
            capability = Capability(request.capability)
            validation_time = time.time() - validation_start
            logger.debug(f"[API] [create_job] Capability validation completed in {validation_time:.3f}s")
        except ValueError as e:
            validation_time = time.time() - validation_start
            logger.warning(
                f"[API] [create_job] Invalid capability after {validation_time:.3f}s: "
                f"{request.capability}, error={e}"
            )
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
        logger.debug(f"[API] [create_job] Mapped priority: {request.priority} -> {priority.value}")
        
        # Create job
        job_creation_start = time.time()
        try:
            job = await orchestrator.create_job(
                capability=capability,
                target=request.target,
                config=request.config,
                priority=priority
            )
            job_creation_time = time.time() - job_creation_start
            logger.info(
                f"[API] [create_job] Job created successfully in {job_creation_time:.3f}s - "
                f"job_id={job.id}, status={job.status.value}, "
                f"capability={job.capability.value}, target={job.target}"
            )
        except Exception as e:
            job_creation_time = time.time() - job_creation_start
            logger.error(
                f"[API] [create_job] Failed to create job object after {job_creation_time:.3f}s: {e}",
                exc_info=True
            )
            raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")
        
        # Execute job in background using thread pool executor
        # This completely isolates job execution from the API event loop
        bg_task_start = time.time()
        try:
            # Use a shared executor (or create per-request, but shared is more efficient)
            # Store executor as module-level or in a singleton pattern
            if not hasattr(run_job_in_thread, '_executor'):
                run_job_in_thread._executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="job-executor")
            
            executor = run_job_in_thread._executor
            future = executor.submit(run_job_in_thread, job.id, orchestrator)
            
            # Optional: Add callback for completion (non-blocking)
            def log_thread_completion(future):
                try:
                    future.result()  # This will raise if task failed
                except Exception as e:
                    logger.error(
                        f"[API] [create_job] Background job thread error for job {job.id}: {e}",
                        exc_info=True
                    )
            
            # Note: add_done_callback is for concurrent.futures.Future, not asyncio.Task
            future.add_done_callback(log_thread_completion)
            
            bg_task_time = time.time() - bg_task_start
            logger.info(
                f"[API] [create_job] Background job scheduled in thread pool in {bg_task_time:.3f}s - "
                f"job_id={job.id}, will execute {capability.value} against {request.target}"
            )
        except Exception as e:
            bg_task_time = time.time() - bg_task_start
            logger.error(
                f"[API] [create_job] Failed to schedule background job after {bg_task_time:.3f}s: {e}",
                exc_info=True
            )
            # Don't fail the request if background task scheduling fails, job is still created
        
        total_request_time = time.time() - request_start_time
        logger.info(
            f"[API] [create_job] Request completed in {total_request_time:.3f}s - "
            f"job_id={job.id}, returning response"
        )
        
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
        total_request_time = time.time() - request_start_time
        logger.warning(f"[API] [create_job] Request failed after {total_request_time:.3f}s (HTTPException)")
        raise
    except Exception as e:
        total_request_time = time.time() - request_start_time
        logger.error(
            f"[API] [create_job] Unexpected error after {total_request_time:.3f}s: {e}",
            exc_info=True
        )
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
    offset: int = Query(default=0, ge=0, description="Number of findings to skip"),
    since: Optional[str] = Query(None, description="Return findings after this timestamp (ISO format) or finding ID for incremental polling")
):
    """
    Get findings from a job with pagination and incremental polling support.
    
    Supports two modes:
    1. Full pagination: Use offset/limit to paginate through all findings
    2. Incremental polling: Use 'since' parameter to get only new findings since last poll
       - 'since' can be an ISO timestamp (e.g., "2024-01-01T00:00:00") or a finding ID
       - Returns only findings discovered after the specified timestamp or finding ID
    
    Returns findings in batches, allowing clients to retrieve data incrementally
    to avoid timeout issues with large result sets.
    """
    from datetime import datetime as dt
    
    orchestrator = get_orchestrator()
    job = orchestrator.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get findings based on 'since' parameter for incremental polling
    if since:
        try:
            # Try parsing as ISO timestamp first
            try:
                since_timestamp = dt.fromisoformat(since.replace('Z', '+00:00'))
                filtered_findings = job.get_findings_since(since_timestamp=since_timestamp)
                logger.debug(
                    f"[API] get_job_findings: job_id={job_id}, incremental mode (timestamp), "
                    f"since={since}, found={len(filtered_findings)} new findings"
                )
            except (ValueError, AttributeError):
                # If not a timestamp, treat as finding ID
                filtered_findings = job.get_findings_since(since_id=since)
                logger.debug(
                    f"[API] get_job_findings: job_id={job_id}, incremental mode (finding_id), "
                    f"since={since}, found={len(filtered_findings)} new findings"
                )
        except Exception as e:
            logger.warning(
                f"[API] get_job_findings: Error parsing 'since' parameter '{since}': {e}. "
                f"Falling back to all findings."
            )
            filtered_findings = job.findings
    else:
        # No 'since' parameter, return all findings (backward compatible)
        filtered_findings = job.findings
    
    # Apply pagination to filtered results
    total_findings = len(filtered_findings)
    paginated_findings = filtered_findings[offset:offset + limit]
    
    logger.debug(
        f"[API] get_job_findings: job_id={job_id}, total={total_findings}, "
        f"offset={offset}, limit={limit}, returning={len(paginated_findings)}"
    )
    
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
    
    return findings_response


@router.get("/jobs/{job_id}/findings/incremental", response_model=IncrementalFindingsResponse)
async def get_job_findings_incremental(
    job_id: str,
    last_finding_id: Optional[str] = Query(None, description="Last received finding ID for incremental polling"),
    last_timestamp: Optional[str] = Query(None, description="Last received timestamp (ISO format) for incremental polling"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of findings to return")
):
    """
    Get new findings since last poll (incremental polling endpoint).
    
    This endpoint is optimized for continuous polling. It returns only new findings
    since the last poll, along with metadata to help clients track progress.
    
    Usage:
    1. First call: Don't provide last_finding_id or last_timestamp to get initial findings
    2. Subsequent calls: Use the last_finding_id or last_timestamp from previous response
    3. Continue polling until has_more is False or job status is completed
    
    Returns:
    {
        "findings": [...],           # New findings since last poll
        "has_more": bool,            # Whether there are more findings available
        "total_findings": int,       # Total findings in job
        "new_count": int,            # Number of new findings in this response
        "last_finding_id": str,      # ID of last finding (for next poll)
        "last_finding_timestamp": str # Timestamp of last finding (for next poll)
    }
    """
    from datetime import datetime as dt
    
    orchestrator = get_orchestrator()
    job = orchestrator.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    total_findings = len(job.findings)
    
    # Get new findings based on last_finding_id or last_timestamp
    if last_finding_id:
        new_findings = job.get_findings_since(since_id=last_finding_id)
        logger.debug(
            f"[API] get_job_findings_incremental: job_id={job_id}, "
            f"since_id={last_finding_id}, found={len(new_findings)} new findings"
        )
    elif last_timestamp:
        try:
            since_timestamp = dt.fromisoformat(last_timestamp.replace('Z', '+00:00'))
            new_findings = job.get_findings_since(since_timestamp=since_timestamp)
            logger.debug(
                f"[API] get_job_findings_incremental: job_id={job_id}, "
                f"since_timestamp={last_timestamp}, found={len(new_findings)} new findings"
            )
        except (ValueError, AttributeError) as e:
            logger.warning(
                f"[API] get_job_findings_incremental: Invalid timestamp '{last_timestamp}': {e}. "
                f"Returning all findings."
            )
            new_findings = job.findings
    else:
        # First call - return all findings
        new_findings = job.findings
        logger.debug(
            f"[API] get_job_findings_incremental: job_id={job_id}, "
            f"first call, returning all {len(new_findings)} findings"
        )
    
    # Apply limit
    limited_findings = new_findings[:limit]
    new_count = len(limited_findings)
    has_more = len(new_findings) > limit
    
    # Get last finding metadata for next poll
    last_finding_id_value = None
    last_finding_timestamp_value = None
    if limited_findings:
        last_finding = limited_findings[-1]
        last_finding_id_value = last_finding.id
        last_finding_timestamp_value = last_finding.discovered_at.isoformat()
    
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
        for f in limited_findings
    ]
    
    return IncrementalFindingsResponse(
        findings=findings_response,
        has_more=has_more,
        total_findings=total_findings,
        new_count=new_count,
        last_finding_id=last_finding_id_value,
        last_finding_timestamp=last_finding_timestamp_value
    )


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



