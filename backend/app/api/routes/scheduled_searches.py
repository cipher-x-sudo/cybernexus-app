"""
Scheduled Searches API Routes

Handles listing of scheduled automated searches.
Scheduled searches are created automatically via company automation sync.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.api.routes.auth import get_current_active_user, User
from app.core.database.database import get_db
from app.core.database.models import ScheduledSearch as ScheduledSearchModel


router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class ScheduledSearchResponse(BaseModel):
    """Scheduled search response"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    capabilities: List[str]  # List of capabilities
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


# ============================================================================
# Helper Functions
# ============================================================================

def get_capabilities_list(scheduled_search: ScheduledSearchModel) -> List[str]:
    """Get capabilities list from scheduled search (supports both old and new format)."""
    if hasattr(scheduled_search, 'capabilities') and scheduled_search.capabilities:
        if isinstance(scheduled_search.capabilities, list):
            return scheduled_search.capabilities
        return [scheduled_search.capabilities]
    elif hasattr(scheduled_search, 'capability') and scheduled_search.capability:
        # Backward compatibility: convert single capability to list
        return [scheduled_search.capability]
    return []


def scheduled_search_to_response(scheduled_search: ScheduledSearchModel) -> ScheduledSearchResponse:
    """Convert ScheduledSearchModel to ScheduledSearchResponse."""
    capabilities_list = get_capabilities_list(scheduled_search)
    return ScheduledSearchResponse(
        id=scheduled_search.id,
        user_id=scheduled_search.user_id,
        name=scheduled_search.name,
        description=scheduled_search.description,
        capabilities=capabilities_list,
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


# ============================================================================
# API Endpoints
# ============================================================================

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
        
        return [scheduled_search_to_response(ss) for ss in scheduled_searches]
    except Exception as e:
        logger.error(f"Error listing scheduled searches: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list scheduled searches: {str(e)}")

