import asyncio
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dsa import MinHeap, HashMap, CircularBuffer
from app.core.database.models import Notification as NotificationModel


class NotificationPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


class NotificationService:
    def __init__(self):
        self._notification_queue = MinHeap()
        self._subscriptions = HashMap()
        self._history = CircularBuffer(capacity=1000)
        self._rate_limits = HashMap()
        self._handlers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, channel: str, callback: Callable):
        callbacks = self._subscriptions.get(channel, [])
        callbacks.append(callback)
        self._subscriptions.put(channel, callbacks)
        logger.info(f"Subscribed to channel: {channel}")
    
    def unsubscribe(self, channel: str, callback: Callable):
        callbacks = self._subscriptions.get(channel, [])
        if callback in callbacks:
            callbacks.remove(callback)
            self._subscriptions.put(channel, callbacks)
    
    async def notify(self, channel: str, message: Dict[str, Any], 
                    priority: NotificationPriority = NotificationPriority.MEDIUM):
        notification = {
            "id": f"notif-{datetime.utcnow().timestamp()}",
            "channel": channel,
            "message": message,
            "priority": priority.name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._notification_queue.push(priority.value, notification)
        
        self._history.push(notification)
        
        if priority.value <= NotificationPriority.HIGH.value:
            await self._process_notification(notification)
        
        logger.debug(f"Notification queued: {channel} - {priority.name}")
    
    async def _process_notification(self, notification: Dict[str, Any]):
        channel = notification["channel"]
        callbacks = self._subscriptions.get(channel, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification)
                else:
                    callback(notification)
            except Exception as e:
                logger.error(f"Notification callback error: {e}")
    
    async def process_queue(self):
        while self._notification_queue:
            result = self._notification_queue.pop()
            if result:
                _, notification = result
                await self._process_notification(notification)
    
    def get_recent_notifications(self, n: int = 20) -> List[Dict[str, Any]]:
        return self._history.get_last_n(n)
    
    def get_notifications_by_channel(self, channel: str, n: int = 50) -> List[Dict[str, Any]]:
        all_notifications = self._history.get_all()
        filtered = [n for n in all_notifications if n["channel"] == channel]
        return filtered[-n:]
    
    def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        now = datetime.utcnow().timestamp()
        state = self._rate_limits.get(key)
        
        if state:
            count, reset_time = state
            if now < reset_time:
                if count >= limit:
                    return False
                self._rate_limits.put(key, (count + 1, reset_time))
            else:
                self._rate_limits.put(key, (1, now + window_seconds))
        else:
            self._rate_limits.put(key, (1, now + window_seconds))
        
        return True
    
    def stats(self) -> Dict[str, Any]:
        return {
            "queue_size": len(self._notification_queue),
            "subscriptions": {ch: len(cb) for ch, cb in self._subscriptions.items()},
            "history_size": len(self._history),
            "history_capacity": self._history.capacity
        }
    
    async def create_notification(
        self,
        db: AsyncSession,
        user_id: str,
        channel: str,
        priority: NotificationPriority,
        title: str,
        message: str,
        severity: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationModel:
        """
        Create a notification in the database.
        
        Args:
            db: Database session
            user_id: User ID to send notification to
            channel: Notification channel (threats, findings, scans, system, etc.)
            priority: Notification priority level
            title: Notification title
            message: Notification message
            severity: Severity level (critical, high, medium, low, info)
            metadata: Optional metadata dictionary
            
        Returns:
            Created Notification model instance
        """
        notification = NotificationModel(
            user_id=user_id,
            channel=channel,
            priority=priority.name,
            title=title,
            message=message,
            severity=severity,
            read=False,
            read_at=None,
            meta_data=metadata or {},
            timestamp=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        logger.info(f"Created notification for user {user_id}: {channel} - {priority.name}")
        
        # Also add to in-memory queue for immediate processing
        notification_dict = {
            "id": notification.id,
            "channel": channel,
            "message": {"title": title, "message": message},
            "priority": priority.name,
            "timestamp": notification.timestamp.isoformat()
        }
        self._notification_queue.push(priority.value, notification_dict)
        self._history.push(notification_dict)
        
        # Process immediately if high priority
        if priority.value <= NotificationPriority.HIGH.value:
            await self._process_notification(notification_dict)
        
        return notification


