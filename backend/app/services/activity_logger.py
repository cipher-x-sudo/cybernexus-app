"""
User Activity Logger

Logs user activities for audit trail.
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid

from app.core.database.models import UserActivityLog


async def log_activity(
    db: AsyncSession,
    user_id: str,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> UserActivityLog:
    """
    Log a user activity.
    
    Args:
        db: Database session
        user_id: User ID performing the action
        action: Action name (e.g., "create", "update", "delete", "login", "logout")
        resource_type: Type of resource (e.g., "entity", "graph_node", "finding")
        resource_id: ID of the resource
        ip_address: IP address of the user
        user_agent: User agent string
        metadata: Additional metadata
    
    Returns:
        Created activity log entry
    """
    log_entry = UserActivityLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata or {}
    )
    
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    
    return log_entry


async def get_user_activities(
    db: AsyncSession,
    user_id: str,
    limit: int = 100,
    offset: int = 0,
    action: Optional[str] = None,
    resource_type: Optional[str] = None
) -> list[UserActivityLog]:
    """
    Get user activity logs with optional filtering.
    
    Args:
        db: Database session
        user_id: User ID
        limit: Maximum number of results
        offset: Offset for pagination
        action: Filter by action
        resource_type: Filter by resource type
    
    Returns:
        List of activity log entries
    """
    query = select(UserActivityLog).where(UserActivityLog.user_id == user_id)
    
    if action:
        query = query.where(UserActivityLog.action == action)
    if resource_type:
        query = query.where(UserActivityLog.resource_type == resource_type)
    
    query = query.order_by(UserActivityLog.timestamp.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    return list(result.scalars().all())





