"""
Scheduled Searches API Routes

Handles CRUD operations for scheduled automated searches.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from loguru import logger

from app.api.routes.auth import get_current_active_user, User
from app.core.database.database import get_db
from app.core.database.models import ScheduledSearch as ScheduledSearchModel
from app.services.scheduler import get_scheduler_service
from app.services.orchestrator import Capability


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class ScheduledSearchCreate(BaseModel):
    """Request to create a scheduled search"""
    name: str = Field(..., min_length=1, max_length=200, description="Name for the scheduled search")
    description: Optional[str] = Field(None, description="Optional description")
    capability: str = Field(..., description="Capability to run: exposure_discovery, dark_web_intelligence, email_security, infrastructure_testing")
    target: str = Field(..., min_length=1, max_length=500, description="Target domain, keywords, URL, etc.")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Capability-specific configuration")
    schedule_type: str = Field(default="cron", description="Schedule type: cron")
    cron_expression: str = Field(..., min_length=1, max_length=100, description="Cron expression (e.g., '0 9 * * *' for daily at 9 AM)")
    timezone: str = Field(default="UTC", description="Timezone for scheduling")
    enabled: bool = Field(default=True, description="Whether the scheduled search is enabled")
    
    @field_validator('capability')
    @classmethod
    def validate_capability(cls, v: str) -> str:
        valid_capabilities = [
            "exposure_discovery",
            "dark_web_intelligence",
            "email_security",
            "infrastructure_testing"
        ]
        if v not in valid_capabilities:
            raise ValueError(f"Invalid capability. Must be one of: {', '.join(valid_capabilities)}")
        return v
    
    @field_validator('cron_expression')
    @classmethod
    def validate_cron(cls, v: str) -> str:
        # Basic validation - should be 5 parts separated by spaces
        parts = v.strip().split()
        if len(parts) != 5:
            raise ValueError("Cron expression must have 5 parts: minute hour day month weekday")
        return v


class ScheduledSearchUpdate(BaseModel):
    """Request to update a scheduled search"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    target: Optional[str] = Field(None, min_length=1, max_length=500)
    config: Optional[Dict[str, Any]] = None
    cron_expression: Optional[str] = Field(None, min_length=1, max_length=100)
    timezone: Optional[str] = None
    enabled: Optional[bool] = None


class ScheduledSearchResponse(BaseModel):
    """Scheduled search response"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    capability: str
    target: str
    config: Dict[str, Any]
    schedule_type: str
    cron_expression: str
    timezone: str
    enabled: bool
    last_run_at: Optional[str]
    next_run_at: Optional[str]
    run_count: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ExecutionHistoryItem(BaseModel):
    """Execution history item"""
    job_id: str
    status: str
    created_at: str
    completed_at: Optional[str]
    findings_count: int
    error: Optional[str]


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("", response_model=ScheduledSearchResponse, status_code=201)
async def create_scheduled_search(
    request: ScheduledSearchCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new scheduled search"""
    try:
        # Validate capability
        try:
            Capability(request.capability)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid capability: {request.capability}")
        
        # Create scheduled search
        scheduled_search = ScheduledSearchModel(
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            capability=request.capability,
            target=request.target,
            config=request.config or {},
            schedule_type=request.schedule_type,
            cron_expression=request.cron_expression,
            timezone=request.timezone,
            enabled=request.enabled
        )
        
        db.add(scheduled_search)
        await db.commit()
        await db.refresh(scheduled_search)
        
        # Add to scheduler if enabled
        if scheduled_search.enabled:
            scheduler = get_scheduler_service()
            await scheduler.add_scheduled_search(scheduled_search)
        
        logger.info(f"Created scheduled search '{scheduled_search.name}' for user {current_user.id}")
        
        return ScheduledSearchResponse(
            id=scheduled_search.id,
            user_id=scheduled_search.user_id,
            name=scheduled_search.name,
            description=scheduled_search.description,
            capability=scheduled_search.capability,
            target=scheduled_search.target,
            config=scheduled_search.config or {},
            schedule_type=scheduled_search.schedule_type,
            cron_expression=scheduled_search.cron_expression,
            timezone=scheduled_search.timezone,
            enabled=scheduled_search.enabled,
            last_run_at=scheduled_search.last_run_at.isoformat() if scheduled_search.last_run_at else None,
            next_run_at=scheduled_search.next_run_at.isoformat() if scheduled_search.next_run_at else None,
            run_count=scheduled_search.run_count or 0,
            created_at=scheduled_search.created_at.isoformat(),
            updated_at=scheduled_search.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating scheduled search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create scheduled search: {str(e)}")


@router.get("", response_model=List[ScheduledSearchResponse])
async def list_scheduled_searches(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status")
):
    """List all scheduled searches for the current user"""
    try:
        query = select(ScheduledSearchModel).where(ScheduledSearchModel.user_id == current_user.id)
        
        if enabled is not None:
            query = query.where(ScheduledSearchModel.enabled == enabled)
        
        query = query.order_by(ScheduledSearchModel.created_at.desc())
        
        result = await db.execute(query)
        scheduled_searches = result.scalars().all()
        
        return [
            ScheduledSearchResponse(
                id=ss.id,
                user_id=ss.user_id,
                name=ss.name,
                description=ss.description,
                capability=ss.capability,
                target=ss.target,
                config=ss.config or {},
                schedule_type=ss.schedule_type,
                cron_expression=ss.cron_expression,
                timezone=ss.timezone,
                enabled=ss.enabled,
                last_run_at=ss.last_run_at.isoformat() if ss.last_run_at else None,
                next_run_at=ss.next_run_at.isoformat() if ss.next_run_at else None,
                run_count=ss.run_count or 0,
                created_at=ss.created_at.isoformat(),
                updated_at=ss.updated_at.isoformat()
            )
            for ss in scheduled_searches
        ]
    except Exception as e:
        logger.error(f"Error listing scheduled searches: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list scheduled searches: {str(e)}")


@router.get("/{scheduled_search_id}", response_model=ScheduledSearchResponse)
async def get_scheduled_search(
    scheduled_search_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific scheduled search"""
    try:
        scheduled_search = await db.get(ScheduledSearchModel, scheduled_search_id)
        
        if not scheduled_search:
            raise HTTPException(status_code=404, detail="Scheduled search not found")
        
        if scheduled_search.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return ScheduledSearchResponse(
            id=scheduled_search.id,
            user_id=scheduled_search.user_id,
            name=scheduled_search.name,
            description=scheduled_search.description,
            capability=scheduled_search.capability,
            target=scheduled_search.target,
            config=scheduled_search.config or {},
            schedule_type=scheduled_search.schedule_type,
            cron_expression=scheduled_search.cron_expression,
            timezone=scheduled_search.timezone,
            enabled=scheduled_search.enabled,
            last_run_at=scheduled_search.last_run_at.isoformat() if scheduled_search.last_run_at else None,
            next_run_at=scheduled_search.next_run_at.isoformat() if scheduled_search.next_run_at else None,
            run_count=scheduled_search.run_count or 0,
            created_at=scheduled_search.created_at.isoformat(),
            updated_at=scheduled_search.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scheduled search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get scheduled search: {str(e)}")


@router.put("/{scheduled_search_id}", response_model=ScheduledSearchResponse)
async def update_scheduled_search(
    scheduled_search_id: str,
    request: ScheduledSearchUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a scheduled search"""
    try:
        scheduled_search = await db.get(ScheduledSearchModel, scheduled_search_id)
        
        if not scheduled_search:
            raise HTTPException(status_code=404, detail="Scheduled search not found")
        
        if scheduled_search.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update fields
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(scheduled_search, field, value)
        
        await db.commit()
        await db.refresh(scheduled_search)
        
        # Update scheduler
        scheduler = get_scheduler_service()
        await scheduler.update_scheduled_search(scheduled_search)
        
        logger.info(f"Updated scheduled search '{scheduled_search.name}' for user {current_user.id}")
        
        return ScheduledSearchResponse(
            id=scheduled_search.id,
            user_id=scheduled_search.user_id,
            name=scheduled_search.name,
            description=scheduled_search.description,
            capability=scheduled_search.capability,
            target=scheduled_search.target,
            config=scheduled_search.config or {},
            schedule_type=scheduled_search.schedule_type,
            cron_expression=scheduled_search.cron_expression,
            timezone=scheduled_search.timezone,
            enabled=scheduled_search.enabled,
            last_run_at=scheduled_search.last_run_at.isoformat() if scheduled_search.last_run_at else None,
            next_run_at=scheduled_search.next_run_at.isoformat() if scheduled_search.next_run_at else None,
            run_count=scheduled_search.run_count or 0,
            created_at=scheduled_search.created_at.isoformat(),
            updated_at=scheduled_search.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scheduled search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update scheduled search: {str(e)}")


@router.delete("/{scheduled_search_id}", status_code=204)
async def delete_scheduled_search(
    scheduled_search_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a scheduled search"""
    try:
        scheduled_search = await db.get(ScheduledSearchModel, scheduled_search_id)
        
        if not scheduled_search:
            raise HTTPException(status_code=404, detail="Scheduled search not found")
        
        if scheduled_search.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Remove from scheduler
        scheduler = get_scheduler_service()
        await scheduler.remove_scheduled_search(scheduled_search_id)
        
        # Delete from database
        await db.delete(scheduled_search)
        await db.commit()
        
        logger.info(f"Deleted scheduled search '{scheduled_search.name}' for user {current_user.id}")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scheduled search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete scheduled search: {str(e)}")


@router.post("/{scheduled_search_id}/enable", response_model=ScheduledSearchResponse)
async def enable_scheduled_search(
    scheduled_search_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Enable a scheduled search"""
    try:
        scheduled_search = await db.get(ScheduledSearchModel, scheduled_search_id)
        
        if not scheduled_search:
            raise HTTPException(status_code=404, detail="Scheduled search not found")
        
        if scheduled_search.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        scheduled_search.enabled = True
        await db.commit()
        await db.refresh(scheduled_search)
        
        # Update scheduler
        scheduler = get_scheduler_service()
        await scheduler.update_scheduled_search(scheduled_search)
        
        logger.info(f"Enabled scheduled search '{scheduled_search.name}' for user {current_user.id}")
        
        return ScheduledSearchResponse(
            id=scheduled_search.id,
            user_id=scheduled_search.user_id,
            name=scheduled_search.name,
            description=scheduled_search.description,
            capability=scheduled_search.capability,
            target=scheduled_search.target,
            config=scheduled_search.config or {},
            schedule_type=scheduled_search.schedule_type,
            cron_expression=scheduled_search.cron_expression,
            timezone=scheduled_search.timezone,
            enabled=scheduled_search.enabled,
            last_run_at=scheduled_search.last_run_at.isoformat() if scheduled_search.last_run_at else None,
            next_run_at=scheduled_search.next_run_at.isoformat() if scheduled_search.next_run_at else None,
            run_count=scheduled_search.run_count or 0,
            created_at=scheduled_search.created_at.isoformat(),
            updated_at=scheduled_search.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling scheduled search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to enable scheduled search: {str(e)}")


@router.post("/{scheduled_search_id}/disable", response_model=ScheduledSearchResponse)
async def disable_scheduled_search(
    scheduled_search_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Disable a scheduled search"""
    try:
        scheduled_search = await db.get(ScheduledSearchModel, scheduled_search_id)
        
        if not scheduled_search:
            raise HTTPException(status_code=404, detail="Scheduled search not found")
        
        if scheduled_search.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        scheduled_search.enabled = False
        await db.commit()
        await db.refresh(scheduled_search)
        
        # Remove from scheduler
        scheduler = get_scheduler_service()
        await scheduler.remove_scheduled_search(scheduled_search_id)
        
        logger.info(f"Disabled scheduled search '{scheduled_search.name}' for user {current_user.id}")
        
        return ScheduledSearchResponse(
            id=scheduled_search.id,
            user_id=scheduled_search.user_id,
            name=scheduled_search.name,
            description=scheduled_search.description,
            capability=scheduled_search.capability,
            target=scheduled_search.target,
            config=scheduled_search.config or {},
            schedule_type=scheduled_search.schedule_type,
            cron_expression=scheduled_search.cron_expression,
            timezone=scheduled_search.timezone,
            enabled=scheduled_search.enabled,
            last_run_at=scheduled_search.last_run_at.isoformat() if scheduled_search.last_run_at else None,
            next_run_at=scheduled_search.next_run_at.isoformat() if scheduled_search.next_run_at else None,
            run_count=scheduled_search.run_count or 0,
            created_at=scheduled_search.created_at.isoformat(),
            updated_at=scheduled_search.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling scheduled search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to disable scheduled search: {str(e)}")


@router.post("/{scheduled_search_id}/run-now", response_model=Dict[str, str])
async def run_scheduled_search_now(
    scheduled_search_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger execution of a scheduled search"""
    try:
        scheduled_search = await db.get(ScheduledSearchModel, scheduled_search_id)
        
        if not scheduled_search:
            raise HTTPException(status_code=404, detail="Scheduled search not found")
        
        if scheduled_search.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Trigger execution
        scheduler = get_scheduler_service()
        await scheduler.trigger_scheduled_search(scheduled_search_id)
        
        logger.info(f"Manually triggered scheduled search '{scheduled_search.name}' for user {current_user.id}")
        
        return {"message": "Scheduled search execution triggered", "scheduled_search_id": scheduled_search_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering scheduled search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to trigger scheduled search: {str(e)}")


@router.get("/{scheduled_search_id}/history", response_model=List[ExecutionHistoryItem])
async def get_execution_history(
    scheduled_search_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of history items to return")
):
    """Get execution history for a scheduled search"""
    try:
        scheduled_search = await db.get(ScheduledSearchModel, scheduled_search_id)
        
        if not scheduled_search:
            raise HTTPException(status_code=404, detail="Scheduled search not found")
        
        if scheduled_search.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Query jobs created by this scheduled search
        from app.core.database.models import Job
        from sqlalchemy import func, cast, String
        
        # Query all jobs for user and filter by scheduled_search_id in Python
        # (JSONB filtering can be complex, so we'll filter in memory)
        query = (
            select(Job)
            .where(Job.user_id == current_user.id)
            .order_by(Job.created_at.desc())
            .limit(limit * 2)  # Get more to filter
        )
        
        result = await db.execute(query)
        all_jobs = result.scalars().all()
        
        # Filter jobs that were created by this scheduled search
        jobs = [
            job for job in all_jobs
            if job.meta_data and job.meta_data.get('scheduled_search_id') == scheduled_search_id
        ][:limit]
        
        # Get findings count from job storage
        from app.core.database.job_storage import DBJobStorage
        job_storage = DBJobStorage(db, current_user.id)
        
        history_items = []
        for job in jobs:
            # Get findings count from job
            findings_count = 0
            if job.meta_data and 'findings' in job.meta_data:
                findings_count = len(job.meta_data['findings'])
            else:
                # Try to get from job storage
                try:
                    db_job = await job_storage.get_job(job.id)
                    if db_job:
                        findings_count = len(db_job.findings) if hasattr(db_job, 'findings') else 0
                except:
                    pass
            
            history_items.append(
                ExecutionHistoryItem(
                    job_id=job.id,
                    status=job.status,
                    created_at=job.created_at.isoformat(),
                    completed_at=job.completed_at.isoformat() if job.completed_at else None,
                    findings_count=findings_count,
                    error=job.error
                )
            )
        
        return history_items
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get execution history: {str(e)}")

