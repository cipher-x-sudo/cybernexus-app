"""
Notifications Routes

Handles HTTP endpoints for user notifications with read/unread status.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database.database import get_db
from app.core.database.models import Notification as NotificationModel
from app.api.routes.auth import get_current_active_user, User

router = APIRouter()


class Notification(BaseModel):
    """Notification response model."""
    id: str
    user_id: str
    channel: str
    priority: str
    title: str
    message: str
    severity: str
    read: bool
    read_at: Optional[str] = None
    metadata: dict = {}
    timestamp: str
    created_at: str

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Response model for notification list."""
    notifications: List[Notification]
    unread_count: int


class UnreadCountResponse(BaseModel):
    """Response model for unread count."""
    unread_count: int


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = Query(default=50, ge=1, le=500),
    unread_only: bool = Query(default=False),
    channel: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notifications for the current user."""
    # Build query
    query = select(NotificationModel).where(
        NotificationModel.user_id == current_user.id
    )
    
    # Apply filters
    if unread_only:
        query = query.where(NotificationModel.read == False)
    
    if channel:
        query = query.where(NotificationModel.channel == channel)
    
    # Order by created_at descending (newest first)
    query = query.order_by(NotificationModel.created_at.desc())
    
    # Apply limit
    query = query.limit(limit)
    
    # Execute query
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    # Get unread count
    unread_count_query = select(func.count(NotificationModel.id)).where(
        and_(
            NotificationModel.user_id == current_user.id,
            NotificationModel.read == False
        )
    )
    unread_count_result = await db.execute(unread_count_query)
    unread_count = unread_count_result.scalar() or 0
    
    # Convert to response models
    notification_list = []
    for notif in notifications:
        notification_list.append(Notification(
            id=notif.id,
            user_id=notif.user_id,
            channel=notif.channel,
            priority=notif.priority,
            title=notif.title,
            message=notif.message,
            severity=notif.severity,
            read=notif.read,
            read_at=notif.read_at.isoformat() if notif.read_at else None,
            metadata=notif.metadata or {},
            timestamp=notif.timestamp.isoformat(),
            created_at=notif.created_at.isoformat()
        ))
    
    return NotificationListResponse(
        notifications=notification_list,
        unread_count=unread_count
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get unread notification count for the current user."""
    query = select(func.count(NotificationModel.id)).where(
        and_(
            NotificationModel.user_id == current_user.id,
            NotificationModel.read == False
        )
    )
    result = await db.execute(query)
    unread_count = result.scalar() or 0
    
    return UnreadCountResponse(unread_count=unread_count)


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a notification as read."""
    # Get notification
    query = select(NotificationModel).where(
        and_(
            NotificationModel.id == notification_id,
            NotificationModel.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Mark as read
    notification.read = True
    notification.read_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Notification marked as read", "id": notification_id}


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark all notifications as read for the current user."""
    # Get all unread notifications
    query = select(NotificationModel).where(
        and_(
            NotificationModel.user_id == current_user.id,
            NotificationModel.read == False
        )
    )
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    # Mark all as read
    now = datetime.utcnow()
    count = 0
    for notification in notifications:
        notification.read = True
        notification.read_at = now
        count += 1
    
    await db.commit()
    
    return {"message": f"Marked {count} notifications as read", "count": count}
