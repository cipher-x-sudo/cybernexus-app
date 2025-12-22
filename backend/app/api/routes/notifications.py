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
    notifications: List[Notification]
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int


@router.get("", response_model=NotificationListResponse)
@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = Query(default=50, ge=1, le=500),
    unread_only: bool = Query(default=False),
    channel: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        query = select(NotificationModel).where(
            NotificationModel.user_id == current_user.id
        )
        
        if unread_only:
            query = query.where(NotificationModel.read == False)
        
        if channel:
            query = query.where(NotificationModel.channel == channel)
        
        query = query.order_by(NotificationModel.created_at.desc())
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        notifications = result.scalars().all()
        
        unread_count_query = select(func.count(NotificationModel.id)).where(
            and_(
                NotificationModel.user_id == current_user.id,
                NotificationModel.read == False
            )
        )
        unread_count_result = await db.execute(unread_count_query)
        unread_count = unread_count_result.scalar() or 0
        
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
                metadata=notif.meta_data or {},
                timestamp=notif.timestamp.isoformat(),
                created_at=notif.created_at.isoformat()
            ))
        
        return NotificationListResponse(
            notifications=notification_list,
            unread_count=unread_count
        )
    except Exception as e:
        from loguru import logger
        logger.error(f"Error fetching notifications: {e}", exc_info=True)
        return NotificationListResponse(
            notifications=[],
            unread_count=0
        )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
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
    
    notification.read = True
    notification.read_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Notification marked as read", "id": notification_id}


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(NotificationModel).where(
        and_(
            NotificationModel.user_id == current_user.id,
            NotificationModel.read == False
        )
    )
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    now = datetime.utcnow()
    count = 0
    for notification in notifications:
        notification.read = True
        notification.read_at = now
        count += 1
    
    await db.commit()
    
    return {"message": f"Marked {count} notifications as read", "count": count}
