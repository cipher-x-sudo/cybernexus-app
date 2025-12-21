"""
Capabilities API Routes

User-facing capability endpoints. Users interact with WHAT they want to achieve,
not HOW it's done. Underlying tools are completely abstracted.

Capabilities:
- Exposure Discovery: "What can attackers find about us online?"
- Dark Web Intelligence: "Are we mentioned on the dark web?"
- Email Security: "Can our email be spoofed?"
- Infrastructure Testing: "Are our servers misconfigured?"
- Network Security: "Can attackers tunnel into our network?"
- Investigation: "Analyze this suspicious target"
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, AsyncGenerator
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field
from loguru import logger
import json
import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor

from app.services.orchestrator import (
    get_orchestrator, 
    Capability, 
    JobStatus, 
    JobPriority
)
from app.services.risk_engine import get_risk_engine
from app.api.routes.auth import get_current_active_user, User
from app.core.database.database import get_db
from app.core.database.job_storage import DBJobStorage


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
    priority: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_logs: Optional[List[Dict[str, Any]]] = None


class JobHistoryResponse(BaseModel):
    """Job history response with pagination"""
    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


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
            # Initialize database within this thread's event loop context
            # This ensures the engine is created in the correct event loop
            async def init_and_execute():
                from app.core.database.database import init_db, close_db
                from app.services.browser_capture import get_browser_capture_service
                # Initialize database in this event loop's context
                init_db()
                try:
                    # Execute the job
                    await orchestrator_instance.execute_job(job_id)
                finally:
                    # Clean up thread-local database engine
                    await close_db()
                    # Clean up browser service for this thread before event loop closes
                    try:
                        browser_service = get_browser_capture_service()
                        await browser_service.close()
                    except Exception as e:
                        logger.warning(f"[API] Error cleaning up browser service in thread: {e}")
            
            loop.run_until_complete(init_and_execute())
        finally:
            # Clean up any pending tasks before closing the loop
            pending = asyncio.all_tasks(loop)
            if pending:
                for task in pending:
                    task.cancel()
                # Wait for tasks to complete cancellation
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
    except Exception as e:
        logger.error(
            f"[API] [create_job] Error in background job thread for {job_id}: {e}",
            exc_info=True
        )


@router.post("/jobs", response_model=JobResponse)
async def create_job(
    request: JobCreateRequest,
    current_user: User = Depends(get_current_active_user)
):
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
            f"config={request.config}, user_id={current_user.id}"
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
        
        # Create job with user_id
        job_creation_start = time.time()
        try:
            job = await orchestrator.create_job(
                capability=capability,
                target=request.target,
                config=request.config,
                priority=priority,
                user_id=current_user.id
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
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    List jobs with optional filtering.
    Queries jobs from database, filtered by current user.
    """
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
    
    # Parse date filters
    start_date_obj = None
    end_date_obj = None
    if start_date:
        try:
            start_date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    if end_date:
        try:
            end_date_obj = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    
    # Query from database
    storage = DBJobStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    jobs = await storage.list_jobs(
        capability=cap_filter,
        status=status_filter,
        limit=limit,
        offset=offset,
        start_date=start_date_obj,
        end_date=end_date_obj
    )
    
    # Get findings count for each job from database
    from app.core.database.finding_storage import DBFindingStorage
    finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    
    result = []
    for job in jobs:
        # Get findings count for this job
        findings = await finding_storage.get_findings_for_job(job.id)
        findings_count = len(findings)
        
        result.append(JobResponse(
            id=job.id,
            capability=job.capability.value,
            target=job.target,
            status=job.status.value,
            progress=job.progress,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            findings_count=findings_count,
            error=job.error
        ))
    
    return result


@router.get("/jobs/history", response_model=JobHistoryResponse)
async def get_job_history(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=200, description="Number of jobs per page"),
    capability: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get job history with pagination support.
    Uses page/page_size parameters (converts to offset/limit internally).
    Queries jobs from database, filtered by current user.
    """
    # Convert page/page_size to offset/limit
    offset = (page - 1) * page_size
    limit = page_size
    
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
    
    # Parse date filters
    start_date_obj = None
    end_date_obj = None
    if start_date:
        try:
            start_date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    if end_date:
        try:
            end_date_obj = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    
    # Query from database
    storage = DBJobStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    
    # Get total count for pagination
    total_count = await storage.count_jobs(
        capability=cap_filter,
        status=status_filter,
        start_date=start_date_obj,
        end_date=end_date_obj
    )
    
    # Get jobs
    jobs = await storage.list_jobs(
        capability=cap_filter,
        status=status_filter,
        limit=limit,
        offset=offset,
        start_date=start_date_obj,
        end_date=end_date_obj
    )
    
    # Get findings count for each job from database
    from app.core.database.finding_storage import DBFindingStorage
    finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    
    result = []
    for job in jobs:
        # Get findings count for this job
        findings = await finding_storage.get_findings_for_job(job.id)
        findings_count = len(findings)
        
        result.append(JobResponse(
            id=job.id,
            capability=job.capability.value,
            target=job.target,
            status=job.status.value,
            progress=job.progress,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            findings_count=findings_count,
            error=job.error,
            priority=job.priority.value if hasattr(job.priority, 'value') else job.priority,
            config=job.config or {},
            metadata=job.metadata or {},
            execution_logs=job.execution_logs or []
        ))
    
    # Calculate total pages
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
    
    return JobHistoryResponse(
        jobs=result,
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/jobs/recent")
async def get_recent_jobs(
    limit: int = Query(default=5, ge=1, le=50, description="Number of recent jobs to return"),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get recent jobs for the current user.
    Returns the most recently created jobs, ordered by creation date descending.
    """
    from datetime import datetime, timezone
    
    # Query from database
    storage = DBJobStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    jobs = await storage.list_jobs(limit=limit, offset=0)
    
    # Get total count
    total_count = await storage.count_jobs()
    
    # Get findings count for each job from database
    from app.core.database.finding_storage import DBFindingStorage
    finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    
    result = []
    now = datetime.now(timezone.utc)
    for job in jobs:
        # Get findings count for this job
        findings = await finding_storage.get_findings_for_job(job.id)
        findings_count = len(findings)
        
        # Calculate time_ago
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
        
        result.append({
            "id": job.id,
            "capability": job.capability.value,
            "target": job.target,
            "status": job.status.value,
            "progress": job.progress,
            "findings_count": findings_count,
            "time_ago": time_ago,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error": job.error
        })
    
    return {
        "jobs": result,
        "count": len(result)
    }


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get job status and details.
    Queries job from database, ensures user can only access their own jobs.
    """
    # Query from database
    storage = DBJobStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    job = await storage.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get findings count for this job from database
    from app.core.database.finding_storage import DBFindingStorage
    finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    findings = await finding_storage.get_findings_for_job(job_id)
    findings_count = len(findings)
    
    return JobResponse(
        id=job.id,
        capability=job.capability.value,
        target=job.target,
        status=job.status.value,
        progress=job.progress,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        findings_count=findings_count,
        error=job.error,
        priority=job.priority.value if hasattr(job.priority, 'value') else job.priority,
        config=job.config or {},
        metadata=job.metadata or {},  # JobDataclass uses 'metadata', not 'meta_data'
        execution_logs=job.execution_logs or []
    )


@router.post("/jobs/{job_id}/restart", response_model=JobResponse)
async def restart_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Restart the same job by resetting its status and re-executing it.
    Resets progress, clears error, and re-queues the job for execution.
    """
    from datetime import datetime
    
    # Get the job from database
    storage = DBJobStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    job = await storage.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    orchestrator = get_orchestrator()
    
    # Check if job exists in orchestrator (in-memory)
    orchestrator_job = orchestrator.get_job(job_id)
    
    if orchestrator_job:
        # Job is in memory, reset it directly
        orchestrator_job.status = JobStatus.PENDING
        orchestrator_job.progress = 0
        orchestrator_job.error = None
        orchestrator_job.started_at = None
        orchestrator_job.completed_at = None
        # Add restart log
        orchestrator._add_execution_log(orchestrator_job, "info", "Job restarted", {
            "capability": orchestrator_job.capability.value,
            "target": orchestrator_job.target
        })
        # Update status indexes
        orchestrator._update_job_status(orchestrator_job, JobStatus.PENDING)
        # Re-add to queue
        orchestrator._job_queue.push((orchestrator_job.priority.value, datetime.now().timestamp(), job_id))
        # Save to database
        await orchestrator._save_job_to_db(orchestrator_job, user_id=current_user.id)
        job_to_return = orchestrator_job
    else:
        # Job only exists in database, reset it there
        # Get current execution logs and add restart log
        current_logs = job.execution_logs or []
        from datetime import datetime
        restart_log = {
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "message": "Job restarted",
            "data": {
                "capability": job.capability.value,
                "target": job.target
            }
        }
        current_logs.append(restart_log)
        
        await storage.update_job(job_id, {
            'status': 'pending',
            'progress': 0,
            'error': None,
            'started_at': None,
            'completed_at': None,
            'execution_logs': current_logs
        })
        # Reload job to get updated data
        job = await storage.get_job(job_id)
        job_to_return = job
        
        # Add job to orchestrator for execution
        from app.services.orchestrator import Job as JobDataclass
        orchestrator_job = JobDataclass(
            id=job.id,
            capability=job.capability,
            target=job.target,
            status=JobStatus.PENDING,
            priority=job.priority,
            config=job.config or {},
            progress=0,
            created_at=job.created_at,
            started_at=None,
            completed_at=None,
            findings=[],
            error=None,
            metadata=job.metadata or {},
            execution_logs=job.execution_logs or []
        )
        # Add restart log
        orchestrator._add_execution_log(orchestrator_job, "info", "Job restarted", {
            "capability": job.capability.value,
            "target": job.target
        })
        # Store in orchestrator
        orchestrator._jobs.put(job_id, orchestrator_job)
        # Add to queue
        orchestrator._job_queue.push((orchestrator_job.priority.value, datetime.now().timestamp(), job_id))
        # Update indexes
        status_jobs = orchestrator._jobs_by_status.get(JobStatus.PENDING.value) or []
        status_jobs.append(job_id)
        orchestrator._jobs_by_status.put(JobStatus.PENDING.value, status_jobs)
    
    # Start execution in background
    import threading
    thread = threading.Thread(
        target=run_job_in_thread,
        args=(job_id, orchestrator),
        daemon=True
    )
    thread.start()
    
    # Get findings count
    from app.core.database.finding_storage import DBFindingStorage
    finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    findings = await finding_storage.get_findings_for_job(job_id)
    findings_count = len(findings)
    
    return JobResponse(
        id=job_to_return.id,
        capability=job_to_return.capability.value,
        target=job_to_return.target,
        status=job_to_return.status.value if hasattr(job_to_return.status, 'value') else job_to_return.status,
        progress=job_to_return.progress,
        created_at=job_to_return.created_at.isoformat(),
        started_at=job_to_return.started_at.isoformat() if job_to_return.started_at else None,
        completed_at=job_to_return.completed_at.isoformat() if job_to_return.completed_at else None,
        findings_count=findings_count,
        error=job_to_return.error,
        priority=job_to_return.priority.value if hasattr(job_to_return.priority, 'value') else job_to_return.priority,
        config=job_to_return.config or {},
        metadata=job_to_return.metadata or {},
        execution_logs=job_to_return.execution_logs or []
    )


@router.get("/jobs/{job_id}/findings", response_model=List[FindingResponse])
async def get_job_findings(
    job_id: str,
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of findings to return"),
    offset: int = Query(default=0, ge=0, description="Number of findings to skip"),
    since: Optional[str] = Query(None, description="Return findings after this timestamp (ISO format) or finding ID for incremental polling"),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
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
    
    # First try to get job from database
    job_storage = DBJobStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    db_job = await job_storage.get_job(job_id)
    
    if not db_job:
        # Fallback to orchestrator (in-memory) for running jobs
        orchestrator = get_orchestrator()
        orchestrator_job = orchestrator.get_job(job_id)
        if not orchestrator_job:
            raise HTTPException(status_code=404, detail="Job not found")
        job = orchestrator_job
        
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
    else:
        # Job exists in database, get findings from database
        from app.core.database.finding_storage import DBFindingStorage
        finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
        db_findings = await finding_storage.get_findings_for_job(job_id)
        
        # Convert database findings to Finding objects for compatibility
        from app.services.orchestrator import Finding
        from datetime import datetime
        
        filtered_findings = []
        for db_f in db_findings:
            # Parse discovered_at
            discovered_at = db_f.discovered_at if isinstance(db_f.discovered_at, datetime) else datetime.fromisoformat(db_f.discovered_at.replace('Z', '+00:00'))
            
            # db_f.capability is already a Capability enum from FindingDataclass
            finding = Finding(
                id=db_f.id,
                capability=db_f.capability,
                severity=db_f.severity,
                title=db_f.title,
                description=db_f.description or "",
                evidence=db_f.evidence or {},
                affected_assets=db_f.affected_assets or [],
                recommendations=db_f.recommendations or [],
                discovered_at=discovered_at,
                risk_score=db_f.risk_score or 0.0
            )
            filtered_findings.append(finding)
        
        # Apply 'since' filtering if provided
        if since:
            try:
                try:
                    since_timestamp = dt.fromisoformat(since.replace('Z', '+00:00'))
                    filtered_findings = [f for f in filtered_findings if f.discovered_at > since_timestamp]
                    logger.debug(
                        f"[API] get_job_findings: job_id={job_id}, incremental mode (timestamp), "
                        f"since={since}, found={len(filtered_findings)} new findings"
                    )
                except (ValueError, AttributeError):
                    # If not a timestamp, treat as finding ID
                    since_index = next((i for i, f in enumerate(filtered_findings) if f.id == since), -1)
                    if since_index >= 0:
                        filtered_findings = filtered_findings[since_index + 1:]
                        logger.debug(
                            f"[API] get_job_findings: job_id={job_id}, incremental mode (finding_id), "
                            f"since={since}, found={len(filtered_findings)} new findings"
                        )
                    else:
                        # Finding ID not found, return all findings
                        logger.debug(
                            f"[API] get_job_findings: job_id={job_id}, finding_id '{since}' not found, "
                            f"returning all findings"
                        )
            except Exception as e:
                logger.warning(
                    f"[API] get_job_findings: Error parsing 'since' parameter '{since}': {e}. "
                    f"Falling back to all findings."
                )
    
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
    limit: int = Query(default=100, le=500),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    List all findings with optional filtering.
    Queries from database, filtered by current user.
    """
    # Parse capability filter
    cap_filter = None
    if capability:
        try:
            cap_filter = Capability(capability)
        except ValueError:
            pass
    
    # Query from database
    from app.core.database.finding_storage import DBFindingStorage
    finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    findings = await finding_storage.get_findings(
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


@router.patch("/findings/{finding_id}/resolve")
async def resolve_finding(
    finding_id: str,
    status: str = Query(default="resolved", description="Status: resolved, false_positive, or accepted_risk"),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Mark a finding as resolved.
    
    Args:
        finding_id: Finding ID to resolve
        status: Resolution status (resolved, false_positive, accepted_risk)
        
    Returns:
        Success message
    """
    if status not in ["resolved", "false_positive", "accepted_risk"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be: resolved, false_positive, or accepted_risk")
    
    from app.core.database.finding_storage import DBFindingStorage
    finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    
    success = await finding_storage.mark_finding_resolved(finding_id, current_user.id, status)
    
    if not success:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    return {"message": f"Finding marked as {status}", "finding_id": finding_id, "status": status}


@router.get("/findings/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get a single finding by ID.
    Queries from database, ensures user can only access their own findings.
    """
    # Query from database
    from app.core.database.finding_storage import DBFindingStorage
    finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    finding = await finding_storage.get_finding(finding_id)
    
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    return FindingResponse(
        id=finding.id,
        capability=finding.capability.value,
        severity=finding.severity,
        title=finding.title,
        description=finding.description,
        evidence=finding.evidence,
        affected_assets=finding.affected_assets,
        recommendations=finding.recommendations,
        discovered_at=finding.discovered_at.isoformat(),
        risk_score=finding.risk_score
    )


@router.get("/findings/critical", response_model=List[FindingResponse])
async def get_critical_findings(
    limit: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get critical and high severity findings that need immediate attention.
    Queries from database, filtered by current user.
    """
    # Query from database
    from app.core.database.finding_storage import DBFindingStorage
    finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
    findings = await finding_storage.get_critical_findings(limit=limit)
    
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
async def get_recent_events(
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get recent capability events for live activity feed.
    Generates events from database (jobs and findings) for current user.
    """
    from datetime import datetime, timezone
    
    events = []
    
    try:
        # Generate events from recent jobs
        job_storage = DBJobStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
        recent_jobs = await job_storage.list_jobs(limit=limit, offset=0)
        
        for job in recent_jobs:
            # Create event for completed jobs
            if job.status.value == "completed" and job.completed_at:
                events.append({
                    "id": f"job-{job.id}",
                    "type": "job_completed",
                    "message": f"Scan completed: {job.capability.value} on {job.target}",
                    "timestamp": job.completed_at.isoformat(),
                    "capability": job.capability.value,
                    "target": job.target
                })
            # Create event for running jobs
            elif job.status.value == "running" and job.started_at:
                events.append({
                    "id": f"job-{job.id}",
                    "type": "job_started",
                    "message": f"Scan started: {job.capability.value} on {job.target}",
                    "timestamp": job.started_at.isoformat(),
                    "capability": job.capability.value,
                    "target": job.target
                })
        
        # Generate events from recent findings (all severities, not just critical/high)
        from app.core.database.finding_storage import DBFindingStorage
        finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
        # Get recent findings of all severities to show more activity
        recent_findings = await finding_storage.get_findings(limit=limit * 2)  # Get more to have variety
        
        for finding in recent_findings:
            events.append({
                "id": f"finding-{finding.id}",
                "type": "finding",
                "message": f"{finding.title} - {finding.target or 'Unknown target'}",
                "timestamp": finding.discovered_at.isoformat(),
                "severity": finding.severity,
                "capability": finding.capability.value
            })
        
        # Sort by timestamp descending (most recent first)
        events.sort(key=lambda e: e["timestamp"], reverse=True)
        
        # Limit results
        events = events[:limit]
        
    except Exception as e:
        logger.error(f"Error generating capability events from database: {e}", exc_info=True)
        # Fall back to orchestrator if database fails
        orchestrator = get_orchestrator()
        orchestrator_events = orchestrator.get_recent_events(limit=limit)
        events = orchestrator_events
    
    return {
        "events": events,
        "count": len(events)
    }


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@router.websocket("/ws/darkweb/{job_id}")
async def websocket_darkweb_job(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time streaming of darkweb intelligence job results.
    
    Connect to this endpoint after creating a darkweb job to receive findings
    as they are discovered in real-time.
    
    Message format:
    - type: "finding" | "progress" | "complete" | "error"
    - data: Finding object, progress info, completion summary, or error message
    - timestamp: ISO format timestamp
    """
    await websocket.accept()
    orchestrator = get_orchestrator()
    
    try:
        # Verify job exists
        job = orchestrator.get_job(job_id)
        if not job:
            await websocket.send_json({
                "type": "error",
                "data": {"error": f"Job {job_id} not found"},
                "timestamp": datetime.now().isoformat()
            })
            await websocket.close()
            return
        
        # Verify job is for darkweb capability
        if job.capability != Capability.DARK_WEB_INTELLIGENCE:
            await websocket.send_json({
                "type": "error",
                "data": {"error": f"Job {job_id} is not a darkweb intelligence job"},
                "timestamp": datetime.now().isoformat()
            })
            await websocket.close()
            return
        
        logger.info(f"[WebSocket] Client connected to darkweb job {job_id}")
        
        # Register WebSocket connection
        await orchestrator.register_websocket(job_id, websocket)
        
        # Send initial connection message
        await websocket.send_json({
            "type": "progress",
            "data": {
                "progress": job.progress,
                "message": f"Connected to job {job_id}. Status: {job.status.value}"
            },
            "timestamp": datetime.now().isoformat()
        })
        
        # If job is already running or completed, send existing findings
        if job.status in [JobStatus.RUNNING, JobStatus.COMPLETED]:
            # Refresh job to get latest findings (in case they were just added)
            job = orchestrator.get_job(job_id)
            existing_findings = job.findings or []
            logger.info(f"[WebSocket] Job {job_id} is {job.status.value}, found {len(existing_findings)} existing findings")
            
            # Send progress update first
            await websocket.send_json({
                "type": "progress",
                "data": {
                    "progress": job.progress,
                    "message": f"Job {job.status.value}. Found {len(existing_findings)} findings."
                },
                "timestamp": datetime.now().isoformat()
            })
            
            # Send all existing findings one by one
            for idx, finding in enumerate(existing_findings):
                try:
                    finding_dict = finding.to_dict() if hasattr(finding, 'to_dict') else finding
                    await websocket.send_json({
                        "type": "finding",
                        "data": finding_dict,
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.debug(f"[WebSocket] Sent finding {idx+1}/{len(existing_findings)}: {finding.id}")
                except Exception as e:
                    logger.error(f"[WebSocket] Error sending finding {finding.id if hasattr(finding, 'id') else idx}: {e}", exc_info=True)
            
            logger.info(f"[WebSocket] Sent {len(existing_findings)} findings to client for job {job_id}")
            
            # If job is completed, send completion message and close
            if job.status == JobStatus.COMPLETED:
                logger.info(f"[WebSocket] Job {job_id} is completed, sending completion message with {len(existing_findings)} findings")
                await websocket.send_json({
                    "type": "complete",
                    "data": {
                        "total_findings": len(existing_findings),
                        "urls_crawled": len(job.metadata.get("crawled_urls", [])) if job.metadata else 0,
                        "status": "completed"
                    },
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"[WebSocket] Sent completion message for job {job_id}, closing connection")
                # Give a moment for the message to be sent before closing
                await asyncio.sleep(0.5)
                await websocket.close()
                await orchestrator.unregister_websocket(job_id)
                return
            
            # Track how many findings we've already sent
            last_findings_count = len(existing_findings)
        else:
            # Job is pending, start with 0 findings sent
            last_findings_count = 0
        
        # Keep connection alive and wait for job to complete
        # The job execution will send messages via the registered WebSocket
        # We just need to keep the connection open and handle disconnections
        try:
            while True:
                # Wait for messages from client (ping/pong or close)
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    # Handle ping/pong if needed
                    if data == "ping":
                        await websocket.send_text("pong")
                except asyncio.TimeoutError:
                    # Refresh job status to check for completion or new findings
                    job = orchestrator.get_job(job_id)
                    if not job:
                        logger.warning(f"[WebSocket] Job {job_id} not found during keepalive")
                        break
                    
                    current_findings = job.findings or []
                    current_findings_count = len(current_findings)
                    
                    # Check if job completed
                    if job.status == JobStatus.COMPLETED:
                        # Send any new findings that weren't sent before
                        if current_findings_count > last_findings_count:
                            new_findings = current_findings[last_findings_count:]
                            logger.info(f"[WebSocket] Job {job_id} completed, sending {len(new_findings)} new findings")
                            for finding in new_findings:
                                try:
                                    finding_dict = finding.to_dict() if hasattr(finding, 'to_dict') else finding
                                    await websocket.send_json({
                                        "type": "finding",
                                        "data": finding_dict,
                                        "timestamp": datetime.now().isoformat()
                                    })
                                except Exception as e:
                                    logger.error(f"[WebSocket] Error sending finding {finding.id if hasattr(finding, 'id') else 'unknown'}: {e}", exc_info=True)
                        
                        # Send completion message
                        logger.info(f"[WebSocket] Job {job_id} completed, sending completion message with {current_findings_count} total findings")
                        await websocket.send_json({
                            "type": "complete",
                            "data": {
                                "total_findings": current_findings_count,
                                "urls_crawled": len(job.metadata.get("crawled_urls", [])) if job.metadata else 0,
                                "status": "completed"
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                        await asyncio.sleep(0.5)
                        await websocket.close()
                        break
                    elif current_findings_count > last_findings_count:
                        # Send new findings that appeared while job is running
                        new_findings = current_findings[last_findings_count:]
                        logger.info(f"[WebSocket] Found {len(new_findings)} new findings for running job {job_id}")
                        for finding in new_findings:
                            try:
                                finding_dict = finding.to_dict() if hasattr(finding, 'to_dict') else finding
                                await websocket.send_json({
                                    "type": "finding",
                                    "data": finding_dict,
                                    "timestamp": datetime.now().isoformat()
                                })
                            except Exception as e:
                                logger.error(f"[WebSocket] Error sending finding {finding.id if hasattr(finding, 'id') else 'unknown'}: {e}", exc_info=True)
                        last_findings_count = current_findings_count
                    else:
                        # Send periodic keepalive
                        await websocket.send_json({
                            "type": "progress",
                            "data": {
                                "progress": job.progress,
                                "message": "Connection alive"
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                except WebSocketDisconnect:
                    logger.info(f"[WebSocket] Client disconnected from job {job_id}")
                    break
        except Exception as e:
            logger.error(f"[WebSocket] Error in WebSocket connection for job {job_id}: {e}", exc_info=True)
        finally:
            # Unregister WebSocket connection
            await orchestrator.unregister_websocket(job_id)
            logger.info(f"[WebSocket] Unregistered WebSocket connection for job {job_id}")
    
    except Exception as e:
        logger.error(f"[WebSocket] Error setting up WebSocket for job {job_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"error": str(e)},
                "timestamp": datetime.now().isoformat()
            })
            await websocket.close()
        except:
            pass
        finally:
            await orchestrator.unregister_websocket(job_id)


@router.websocket("/ws/exposure/{job_id}")
async def websocket_exposure_job(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time streaming of exposure discovery job results.
    
    Connect to this endpoint after creating an exposure discovery job to receive findings
    as they are discovered in real-time.
    
    Message format:
    - type: "finding" | "progress" | "complete" | "error"
    - data: Finding object, progress info, completion summary, or error message
    - timestamp: ISO format timestamp
    """
    logger.info(f"[WebSocket] [exposure] [job_id={job_id}] Client attempting to connect")
    await websocket.accept()
    logger.debug(f"[WebSocket] [exposure] [job_id={job_id}] WebSocket connection accepted")
    orchestrator = get_orchestrator()
    
    try:
        # Verify job exists
        logger.debug(f"[WebSocket] [exposure] [job_id={job_id}] Verifying job exists")
        job = orchestrator.get_job(job_id)
        if not job:
            logger.warning(f"[WebSocket] [exposure] [job_id={job_id}] Job not found")
            await websocket.send_json({
                "type": "error",
                "data": {"error": f"Job {job_id} not found"},
                "timestamp": datetime.now().isoformat()
            })
            await websocket.close()
            return
        
        # Verify job is for exposure discovery capability
        logger.debug(f"[WebSocket] [exposure] [job_id={job_id}] Verifying capability (current: {job.capability.value})")
        if job.capability != Capability.EXPOSURE_DISCOVERY:
            await websocket.send_json({
                "type": "error",
                "data": {"error": f"Job {job_id} is not an exposure discovery job"},
                "timestamp": datetime.now().isoformat()
            })
            logger.warning(f"[WebSocket] [exposure] [job_id={job_id}] Job is not exposure discovery (capability: {job.capability.value})")
            await websocket.close()
            return
        
        logger.info(f"[WebSocket] [exposure] [job_id={job_id}] Client connected to exposure discovery job (target: {job.target}, status: {job.status.value})")
        
        # Register WebSocket connection
        logger.debug(f"[WebSocket] [exposure] [job_id={job_id}] Registering WebSocket connection")
        await orchestrator.register_websocket(job_id, websocket)
        logger.debug(f"[WebSocket] [exposure] [job_id={job_id}] WebSocket connection registered")
        
        # Send initial connection message
        await websocket.send_json({
            "type": "progress",
            "data": {
                "progress": job.progress,
                "message": f"Connected to job {job_id}. Status: {job.status.value}"
            },
            "timestamp": datetime.now().isoformat()
        })
        
        # If job is already running or completed, send existing findings
        if job.status in [JobStatus.RUNNING, JobStatus.COMPLETED]:
            # Refresh job to get latest findings
            job = orchestrator.get_job(job_id)
            existing_findings = job.findings or []
            logger.info(f"[WebSocket] Job {job_id} is {job.status.value}, found {len(existing_findings)} existing findings")
            
            # Send progress update first
            await websocket.send_json({
                "type": "progress",
                "data": {
                    "progress": job.progress,
                    "message": f"Job {job.status.value}. Found {len(existing_findings)} findings."
                },
                "timestamp": datetime.now().isoformat()
            })
            
            # Send all existing findings one by one
            for idx, finding in enumerate(existing_findings):
                try:
                    finding_dict = finding.to_dict() if hasattr(finding, 'to_dict') else finding
                    await websocket.send_json({
                        "type": "finding",
                        "data": finding_dict,
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.debug(f"[WebSocket] Sent finding {idx+1}/{len(existing_findings)}: {finding.id}")
                except Exception as e:
                    logger.error(f"[WebSocket] Error sending finding {finding.id if hasattr(finding, 'id') else idx}: {e}", exc_info=True)
            
            logger.info(f"[WebSocket] Sent {len(existing_findings)} findings to client for job {job_id}")
            
            # If job is completed, send completion message and close
            if job.status == JobStatus.COMPLETED:
                logger.info(f"[WebSocket] Job {job_id} is completed, sending completion message with {len(existing_findings)} findings")
                await websocket.send_json({
                    "type": "complete",
                    "data": {
                        "total_findings": len(existing_findings),
                        "status": "completed"
                    },
                    "timestamp": datetime.now().isoformat()
                })
                await asyncio.sleep(0.5)
                await websocket.close()
                await orchestrator.unregister_websocket(job_id)
                return
            
            # Track how many findings we've already sent
            last_findings_count = len(existing_findings)
        else:
            # Job is pending, start with 0 findings sent
            last_findings_count = 0
        
        # Keep connection alive and wait for job to complete
        try:
            while True:
                # Wait for messages from client (ping/pong or close)
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    # Handle ping/pong if needed
                    if data == "ping":
                        await websocket.send_text("pong")
                except asyncio.TimeoutError:
                    # Refresh job status to check for completion or new findings
                    job = orchestrator.get_job(job_id)
                    if not job:
                        logger.warning(f"[WebSocket] Job {job_id} not found during keepalive")
                        break
                    
                    current_findings = job.findings or []
                    current_findings_count = len(current_findings)
                    
                    # Check if job completed
                    if job.status == JobStatus.COMPLETED:
                        # Send any new findings that weren't sent before
                        if current_findings_count > last_findings_count:
                            new_findings = current_findings[last_findings_count:]
                            logger.info(f"[WebSocket] Job {job_id} completed, sending {len(new_findings)} new findings")
                            for finding in new_findings:
                                try:
                                    finding_dict = finding.to_dict() if hasattr(finding, 'to_dict') else finding
                                    await websocket.send_json({
                                        "type": "finding",
                                        "data": finding_dict,
                                        "timestamp": datetime.now().isoformat()
                                    })
                                except Exception as e:
                                    logger.error(f"[WebSocket] Error sending finding {finding.id if hasattr(finding, 'id') else 'unknown'}: {e}", exc_info=True)
                        
                        # Send completion message
                        logger.info(f"[WebSocket] Job {job_id} completed, sending completion message with {current_findings_count} total findings")
                        await websocket.send_json({
                            "type": "complete",
                            "data": {
                                "total_findings": current_findings_count,
                                "status": "completed"
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                        await asyncio.sleep(0.5)
                        await websocket.close()
                        break
                    elif current_findings_count > last_findings_count:
                        # Send new findings that appeared while job is running
                        new_findings = current_findings[last_findings_count:]
                        logger.info(f"[WebSocket] Found {len(new_findings)} new findings for running job {job_id}")
                        for finding in new_findings:
                            try:
                                finding_dict = finding.to_dict() if hasattr(finding, 'to_dict') else finding
                                await websocket.send_json({
                                    "type": "finding",
                                    "data": finding_dict,
                                    "timestamp": datetime.now().isoformat()
                                })
                            except Exception as e:
                                logger.error(f"[WebSocket] Error sending finding {finding.id if hasattr(finding, 'id') else 'unknown'}: {e}", exc_info=True)
                        last_findings_count = current_findings_count
                    else:
                        # Send periodic keepalive
                        await websocket.send_json({
                            "type": "progress",
                            "data": {
                                "progress": job.progress,
                                "message": "Connection alive"
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                except WebSocketDisconnect:
                    logger.info(f"[WebSocket] Client disconnected from job {job_id}")
                    break
        except Exception as e:
            logger.error(f"[WebSocket] Error in WebSocket connection for job {job_id}: {e}", exc_info=True)
        finally:
            # Unregister WebSocket connection
            await orchestrator.unregister_websocket(job_id)
            logger.info(f"[WebSocket] Unregistered WebSocket connection for job {job_id}")
    
    except Exception as e:
        logger.error(f"[WebSocket] Error setting up WebSocket for job {job_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"error": str(e)},
                "timestamp": datetime.now().isoformat()
            })
            await websocket.close()
        except:
            pass
        finally:
            await orchestrator.unregister_websocket(job_id)


# ============================================================================
# Email Security Specific Endpoints
# ============================================================================

@router.get("/email/{domain}/history")
async def get_email_history(
    domain: str,
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    Get historical email security scan data for a domain.
    
    Returns list of past scans with timestamps and scores.
    """
    try:
        orchestrator = get_orchestrator()
        
        # Get all email security jobs for this domain
        jobs = orchestrator.get_jobs(
            capability=Capability.EMAIL_SECURITY,
            limit=limit * 2  # Get more to filter by target
        )
        
        # Filter by domain and get most recent
        domain_jobs = [j for j in jobs if j.target.lower() == domain.lower()]
        domain_jobs.sort(key=lambda x: x.created_at, reverse=True)
        domain_jobs = domain_jobs[:limit]
        
        history = []
        for job in domain_jobs:
            findings = job.findings
            score = 0
            if findings:
                # Calculate average risk score (inverted to get security score)
                avg_risk = sum(f.risk_score for f in findings) / len(findings)
                score = max(0, 100 - avg_risk)
            
            history.append({
                "job_id": job.id,
                "timestamp": job.created_at.isoformat(),
                "score": score,
                "findings_count": len(findings),
                "status": job.status.value
            })
        
        return {"domain": domain, "history": history}
    except Exception as e:
        logger.error(f"Error getting email history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/email/{domain}/compliance")
async def get_email_compliance(domain: str):
    """
    Get compliance report for a domain's email security configuration.
    
    Returns compliance scores for RFC standards and M3AAWG best practices.
    """
    try:
        orchestrator = get_orchestrator()
        
        # Get most recent email security job for this domain
        jobs = orchestrator.get_jobs(
            capability=Capability.EMAIL_SECURITY,
            limit=50
        )
        
        domain_jobs = [j for j in jobs if j.target.lower() == domain.lower()]
        if not domain_jobs:
            raise HTTPException(status_code=404, detail=f"No email security scan found for {domain}")
        
        latest_job = sorted(domain_jobs, key=lambda x: x.created_at, reverse=True)[0]
        
        # Get job results (we need to access the audit results)
        # For now, return a message that compliance is calculated during scan
        # In a full implementation, we'd store compliance data with jobs
        return {
            "domain": domain,
            "message": "Compliance data is included in scan results. Run a new scan to get latest compliance scores.",
            "last_scan": latest_job.created_at.isoformat() if latest_job else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/email/{domain}/bypass-test")
async def run_email_bypass_test(
    domain: str,
    background_tasks: BackgroundTasks
):
    """
    Run bypass vulnerability tests for a domain.
    
    Creates a new email security job with bypass testing enabled.
    """
    try:
        orchestrator = get_orchestrator()
        
        # Create job with bypass testing enabled
        job = orchestrator.create_job(
            capability=Capability.EMAIL_SECURITY,
            target=domain,
            config={"run_bypass_tests": True},
            priority=JobPriority.NORMAL
        )
        
        # Execute in background
        background_tasks.add_task(orchestrator.execute_job, job.id)
        
        return {
            "job_id": job.id,
            "domain": domain,
            "message": "Bypass testing job created. Check job status for results.",
            "status": job.status.value
        }
    except Exception as e:
        logger.error(f"Error creating bypass test job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/email/{domain}/infrastructure")
async def get_email_infrastructure(domain: str):
    """
    Get email infrastructure graph data for a domain.
    
    Returns graph representation of email infrastructure (MX, SPF includes, etc.)
    """
    try:
        orchestrator = get_orchestrator()
        
        # Get most recent email security job
        jobs = orchestrator.get_jobs(
            capability=Capability.EMAIL_SECURITY,
            limit=50
        )
        
        domain_jobs = [j for j in jobs if j.target.lower() == domain.lower()]
        if not domain_jobs:
            raise HTTPException(status_code=404, detail=f"No email security scan found for {domain}")
        
        latest_job = sorted(domain_jobs, key=lambda x: x.created_at, reverse=True)[0]
        findings = latest_job.findings
        
        # Extract infrastructure data from findings
        nodes = [{"id": domain, "type": "domain", "label": domain}]
        edges = []
        
        for finding in findings:
            evidence = finding.evidence or {}
            
            # Extract MX records
            if "mx_records" in evidence:
                for mx in evidence.get("mx_records", []):
                    mx_host = mx.get("exchange", "")
                    if mx_host:
                        nodes.append({"id": mx_host, "type": "mx", "label": mx_host})
                        edges.append({"from": domain, "to": mx_host, "relation": "mx_record"})
            
            # Extract SPF includes
            if "includes" in evidence:
                for include in evidence.get("includes", []):
                    nodes.append({"id": include, "type": "spf_include", "label": include})
                    edges.append({"from": domain, "to": include, "relation": "spf_include"})
        
        # Remove duplicate nodes
        unique_nodes = {}
        for node in nodes:
            if node["id"] not in unique_nodes:
                unique_nodes[node["id"]] = node
        
        return {
            "domain": domain,
            "nodes": list(unique_nodes.values()),
            "edges": edges
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email infrastructure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/email/{domain}/export")
async def export_email_report(
    domain: str,
    format: str = Query(default="json", regex="^(json|csv)$")
):
    """
    Export email security report for a domain.
    
    Supports JSON and CSV formats.
    """
    try:
        orchestrator = get_orchestrator()
        
        # Get most recent email security job
        jobs = orchestrator.get_jobs(
            capability=Capability.EMAIL_SECURITY,
            limit=50
        )
        
        domain_jobs = [j for j in jobs if j.target.lower() == domain.lower()]
        if not domain_jobs:
            raise HTTPException(status_code=404, detail=f"No email security scan found for {domain}")
        
        latest_job = sorted(domain_jobs, key=lambda x: x.created_at, reverse=True)[0]
        findings = latest_job.findings
        
        if format == "csv":
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["ID", "Severity", "Title", "Description", "Risk Score", "Discovered At"])
            
            # Write findings
            for finding in findings:
                writer.writerow([
                    finding.id,
                    finding.severity,
                    finding.title,
                    finding.description,
                    finding.risk_score,
                    finding.discovered_at.isoformat()
                ])
            
            from fastapi.responses import Response
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=email_report_{domain}.csv"}
            )
        else:
            # JSON format
            return {
                "domain": domain,
                "scan_date": latest_job.created_at.isoformat(),
                "findings": [f.to_dict() for f in findings],
                "summary": {
                    "total_findings": len(findings),
                    "by_severity": {
                        "critical": len([f for f in findings if f.severity == "critical"]),
                        "high": len([f for f in findings if f.severity == "high"]),
                        "medium": len([f for f in findings if f.severity == "medium"]),
                        "low": len([f for f in findings if f.severity == "low"]),
                        "info": len([f for f in findings if f.severity == "info"])
                    }
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting email report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/email/{domain}/compare")
async def compare_email_scans(
    domain: str,
    job_id1: str = Query(..., description="First job ID to compare"),
    job_id2: str = Query(..., description="Second job ID to compare")
):
    """
    Compare two email security scans for a domain.
    
    Returns differences between the two scans.
    """
    try:
        orchestrator = get_orchestrator()
        
        job1 = orchestrator.get_job(job_id1)
        job2 = orchestrator.get_job(job_id2)
        
        if not job1 or not job2:
            raise HTTPException(status_code=404, detail="One or both jobs not found")
        
        if job1.target.lower() != domain.lower() or job2.target.lower() != domain.lower():
            raise HTTPException(status_code=400, detail="Jobs do not match the specified domain")
        
        findings1 = job1.findings
        findings2 = job2.findings
        
        # Compare findings
        findings1_ids = {f.id for f in findings1}
        findings2_ids = {f.id for f in findings2}
        
        new_findings = [f.to_dict() for f in findings2 if f.id not in findings1_ids]
        resolved_findings = [f.to_dict() for f in findings1 if f.id not in findings2_ids]
        
        # Calculate score changes
        score1 = 100 - (sum(f.risk_score for f in findings1) / len(findings1) if findings1 else 0)
        score2 = 100 - (sum(f.risk_score for f in findings2) / len(findings2) if findings2 else 0)
        
        return {
            "domain": domain,
            "job1": {
                "id": job_id1,
                "timestamp": job1.created_at.isoformat(),
                "score": score1,
                "findings_count": len(findings1)
            },
            "job2": {
                "id": job_id2,
                "timestamp": job2.created_at.isoformat(),
                "score": score2,
                "findings_count": len(findings2)
            },
            "comparison": {
                "score_change": score2 - score1,
                "new_findings": new_findings,
                "resolved_findings": resolved_findings,
                "findings_count_change": len(findings2) - len(findings1)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing email scans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Investigation Endpoints
# ============================================================================

@router.get("/investigation/{job_id}/screenshot")
async def get_investigation_screenshot(job_id: str):
    """
    Get screenshot from an investigation job.
    
    Returns the captured screenshot as PNG image.
    """
    try:
        orchestrator = get_orchestrator()
        job = orchestrator.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.capability != Capability.INVESTIGATION:
            raise HTTPException(status_code=400, detail="Job is not an investigation job")
        
        # Get screenshot from job metadata
        capture_data = getattr(job, 'metadata', {}).get('capture', {})
        screenshot_b64 = capture_data.get('screenshot')
        
        if not screenshot_b64:
            raise HTTPException(status_code=404, detail="Screenshot not available for this job. The investigation may not have captured a screenshot.")
        
        # Decode and return as image
        try:
            screenshot_bytes = base64.b64decode(screenshot_b64)
        except Exception as e:
            logger.error(f"Error decoding screenshot: {e}")
            raise HTTPException(status_code=500, detail="Failed to decode screenshot data")
        return Response(
            content=screenshot_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=investigation_{job_id}_screenshot.png"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving screenshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investigation/{job_id}/har")
async def get_investigation_har(job_id: str):
    """
    Get HAR file from an investigation job.
    
    Returns the captured HAR file as JSON.
    """
    try:
        orchestrator = get_orchestrator()
        job = orchestrator.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.capability != Capability.INVESTIGATION:
            raise HTTPException(status_code=400, detail="Job is not an investigation job")
        
        # Get HAR from job metadata
        capture_data = getattr(job, 'metadata', {}).get('capture', {})
        har_data = capture_data.get('har')
        
        if not har_data:
            raise HTTPException(status_code=404, detail="HAR file not available for this job. The investigation may not have captured network traffic.")
        
        return Response(
            content=json.dumps(har_data, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=investigation_{job_id}.har"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving HAR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investigation/{job_id}/domain-tree")
async def get_investigation_domain_tree(job_id: str):
    """
    Get domain tree graph from an investigation job.
    
    Returns the domain tree structure as JSON for visualization.
    """
    try:
        orchestrator = get_orchestrator()
        job = orchestrator.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.capability != Capability.INVESTIGATION:
            raise HTTPException(status_code=400, detail="Job is not an investigation job")
        
        # Get domain tree from job metadata
        capture_data = getattr(job, 'metadata', {}).get('capture', {})
        domain_tree_data = capture_data.get('domain_tree')
        
        if not domain_tree_data:
            # Fallback: try to extract from findings
            findings = job.findings
            domain_tree_data = {
                "nodes": [],
                "edges": [],
                "summary": {}
            }
            
            # Extract domain information from findings
            for finding in findings:
                evidence = finding.evidence or {}
                if 'domain_tree' in evidence:
                    domain_tree_data = evidence['domain_tree']
                    break
                elif 'domains' in evidence:
                    # Build simple tree from domain list
                    domains = evidence.get('domains', [])
                    for i, domain in enumerate(domains):
                        domain_tree_data['nodes'].append({
                            "id": domain,
                            "label": domain,
                            "type": "domain"
                        })
                        if i > 0:
                            domain_tree_data['edges'].append({
                                "source": domains[0],
                                "target": domain
                            })
        
        # Add summary if available
        summary = capture_data.get('domain_tree_summary', {})
        if summary:
            domain_tree_data['summary'] = summary
        
        return domain_tree_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving domain tree: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/investigation/compare")
async def compare_investigations(
    job_id1: str = Query(..., description="First investigation job ID"),
    job_id2: str = Query(..., description="Second investigation job ID")
):
    """
    Compare two investigation results.
    
    Returns comparison data including visual similarity, domain differences, etc.
    """
    try:
        orchestrator = get_orchestrator()
        
        job1 = orchestrator.get_job(job_id1)
        job2 = orchestrator.get_job(job_id2)
        
        if not job1 or not job2:
            raise HTTPException(status_code=404, detail="One or both jobs not found")
        
        if job1.capability != Capability.INVESTIGATION or job2.capability != Capability.INVESTIGATION:
            raise HTTPException(status_code=400, detail="Both jobs must be investigation jobs")
        
        # Get capture data
        capture1 = getattr(job1, 'metadata', {}).get('capture', {})
        capture2 = getattr(job2, 'metadata', {}).get('capture', {})
        
        comparison = {
            "job1": job_id1,
            "job2": job_id2,
            "target1": job1.target,
            "target2": job2.target,
            "visual_similarity": None,
            "domain_differences": {},
            "findings_comparison": {}
        }
        
        # Visual similarity comparison
        screenshot1 = capture1.get('screenshot')
        screenshot2 = capture2.get('screenshot')
        
        if screenshot1 and screenshot2:
            from app.services.visual_similarity import get_visual_similarity_service
            visual_similarity = get_visual_similarity_service()
            
            img1_data = base64.b64decode(screenshot1)
            img2_data = base64.b64decode(screenshot2)
            
            similarity_result = visual_similarity.compare_images(img1_data, img2_data)
            comparison['visual_similarity'] = similarity_result
        
        # Domain differences
        har1 = capture1.get('har', {})
        har2 = capture2.get('har', {})
        
        if har1 and har2:
            domains1 = set()
            domains2 = set()
            
            for entry in har1.get('entries', []):
                url = entry.get('request', {}).get('url', '')
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if parsed.netloc:
                    domains1.add(parsed.netloc)
            
            for entry in har2.get('entries', []):
                url = entry.get('request', {}).get('url', '')
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if parsed.netloc:
                    domains2.add(parsed.netloc)
            
            comparison['domain_differences'] = {
                "added_domains": list(domains2 - domains1),
                "removed_domains": list(domains1 - domains2),
                "common_domains": list(domains1 & domains2)
            }
        
        # Findings comparison
        findings1 = job1.findings
        findings2 = job2.findings
        
        comparison['findings_comparison'] = {
            "count1": len(findings1),
            "count2": len(findings2),
            "new_findings": len([f for f in findings2 if f.id not in [f2.id for f2 in findings1]]),
            "resolved_findings": len([f for f in findings1 if f.id not in [f2.id for f2 in findings2]])
        }
        
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing investigations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investigation/{job_id}/export")
async def export_investigation(
    job_id: str,
    format: str = Query(default="json", regex="^(json|html)$")
):
    """
    Export complete investigation results.
    
    Returns investigation data in specified format (json or html).
    """
    try:
        orchestrator = get_orchestrator()
        job = orchestrator.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.capability != Capability.INVESTIGATION:
            raise HTTPException(status_code=400, detail="Job is not an investigation job")
        
        findings = job.findings
        capture_data = getattr(job, 'metadata', {}).get('capture', {})
        
        export_data = {
            "job_id": job_id,
            "target": job.target,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "findings": [f.to_dict() for f in findings],
            "capture": {
                "final_url": capture_data.get('final_url'),
                "title": capture_data.get('title'),
                "redirect_chain": capture_data.get('redirect_chain', []),
                "capture_time": capture_data.get('capture_time')
            }
        }
        
        if format == "json":
            return Response(
                content=json.dumps(export_data, indent=2),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=investigation_{job_id}.json"
                }
            )
        elif format == "html":
            # Generate HTML report
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Investigation Report - {job.target}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a2e; color: #fff; }}
        .header {{ background: #16213e; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .finding {{ background: #0f3460; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #e94560; }}
        .severity-critical {{ border-left-color: #e94560; }}
        .severity-high {{ border-left-color: #f39c12; }}
        .severity-medium {{ border-left-color: #f1c40f; }}
        .severity-low {{ border-left-color: #3498db; }}
        .severity-info {{ border-left-color: #95a5a6; }}
        .evidence {{ background: #16213e; padding: 10px; margin: 10px 0; border-radius: 5px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Investigation Report</h1>
        <p><strong>Target:</strong> {job.target}</p>
        <p><strong>Job ID:</strong> {job_id}</p>
        <p><strong>Status:</strong> {job.status.value}</p>
        <p><strong>Findings:</strong> {len(findings)}</p>
    </div>
    
    <h2>Findings</h2>
    {''.join([f'''
    <div class="finding severity-{f.severity}">
        <h3>{f.title}</h3>
        <p>{f.description}</p>
        <div class="evidence">
            <strong>Evidence:</strong><br>
            <pre>{json.dumps(f.evidence, indent=2)}</pre>
        </div>
        <p><strong>Risk Score:</strong> {f.risk_score}</p>
        <p><strong>Recommendations:</strong></p>
        <ul>
            {''.join([f'<li>{rec}</li>' for rec in f.recommendations])}
        </ul>
    </div>
    ''' for f in findings])}
</body>
</html>
            """
            return Response(
                content=html_content,
                media_type="text/html",
                headers={
                    "Content-Disposition": f"attachment; filename=investigation_{job_id}.html"
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting investigation: {e}")
        raise HTTPException(status_code=500, detail=str(e))



