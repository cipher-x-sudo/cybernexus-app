"""Notification service with priority queuing.

This module provides notification management with priority-based delivery
and history tracking using circular buffers for recent notifications.

This module uses the following DSA concepts from app.core.dsa:
- MinHeap: Priority queue for notification delivery with highest priority first
- HashMap: Channel subscriptions and rate limit tracking for O(1) lookups
- CircularBuffer: Recent notification history with automatic overwrite of oldest entries
"""

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
        """Subscribe to a notification channel.
        
        DSA-USED:
        - HashMap: Channel subscription storage
        
        Args:
            channel: Channel name to subscribe to
            callback: Callback function to invoke on notifications
        """
        callbacks = self._subscriptions.get(channel, [])  # DSA-USED: HashMap
        callbacks.append(callback)
        self._subscriptions.put(channel, callbacks)  # DSA-USED: HashMap
        logger.info(f"Subscribed to channel: {channel}")
    
    def unsubscribe(self, channel: str, callback: Callable):
        """Unsubscribe from a notification channel.
        
        DSA-USED:
        - HashMap: Channel subscription update
        
        Args:
            channel: Channel name
            callback: Callback function to remove
        """
        callbacks = self._subscriptions.get(channel, [])  # DSA-USED: HashMap
        if callback in callbacks:
            callbacks.remove(callback)
            self._subscriptions.put(channel, callbacks)  # DSA-USED: HashMap
    
    async def notify(self, channel: str, message: Dict[str, Any], 
                    priority: NotificationPriority = NotificationPriority.MEDIUM):
        """Queue a notification for delivery.
        
        DSA-USED:
        - MinHeap: Priority queue insertion for ordered delivery
        - CircularBuffer: History storage with automatic overwrite
        
        Args:
            channel: Notification channel
            message: Notification message dictionary
            priority: Notification priority level
        """
        notification = {
            "id": f"notif-{datetime.utcnow().timestamp()}",
            "channel": channel,
            "message": message,
            "priority": priority.name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._notification_queue.push(priority.value, notification)  # DSA-USED: MinHeap
        
        self._history.push(notification)  # DSA-USED: CircularBuffer
        
        if priority.value <= NotificationPriority.HIGH.value:
            await self._process_notification(notification)
        
        logger.debug(f"Notification queued: {channel} - {priority.name}")
    
    async def _process_notification(self, notification: Dict[str, Any]):
        """Process a notification by invoking subscribed callbacks.
        
        DSA-USED:
        - HashMap: Subscription lookup by channel
        
        Args:
            notification: Notification dictionary to process
        """
        channel = notification["channel"]
        callbacks = self._subscriptions.get(channel, [])  # DSA-USED: HashMap
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification)
                else:
                    callback(notification)
            except Exception as e:
                logger.error(f"Notification callback error: {e}")
    
    async def process_queue(self):
        """Process all queued notifications in priority order.
        
        DSA-USED:
        - MinHeap: Priority queue extraction for ordered processing
        """
        while self._notification_queue:  # DSA-USED: MinHeap
            result = self._notification_queue.pop()  # DSA-USED: MinHeap
            if result:
                _, notification = result
                await self._process_notification(notification)
    
    def get_recent_notifications(self, n: int = 20) -> List[Dict[str, Any]]:
        """Get most recent notifications.
        
        DSA-USED:
        - CircularBuffer: Recent notification retrieval
        
        Args:
            n: Number of recent notifications to return
        
        Returns:
            List of recent notification dictionaries
        """
        return self._history.get_last_n(n)  # DSA-USED: CircularBuffer
    
    def get_notifications_by_channel(self, channel: str, n: int = 50) -> List[Dict[str, Any]]:
        all_notifications = self._history.get_all()
        filtered = [n for n in all_notifications if n["channel"] == channel]
        return filtered[-n:]
    
    def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check and update rate limit for a key.
        
        DSA-USED:
        - HashMap: Rate limit state storage and lookup
        
        Args:
            key: Rate limit key (e.g., user ID or IP)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            True if within limit, False if rate limited
        """
        now = datetime.utcnow().timestamp()
        state = self._rate_limits.get(key)  # DSA-USED: HashMap
        
        if state:
            count, reset_time = state
            if now < reset_time:
                if count >= limit:
                    return False
                self._rate_limits.put(key, (count + 1, reset_time))  # DSA-USED: HashMap
            else:
                self._rate_limits.put(key, (1, now + window_seconds))  # DSA-USED: HashMap
        else:
            self._rate_limits.put(key, (1, now + window_seconds))  # DSA-USED: HashMap
        
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
        

        notification_dict = {
            "id": notification.id,
            "channel": channel,
            "message": {"title": title, "message": message},
            "priority": priority.name,
            "timestamp": notification.timestamp.isoformat()
        }
        self._notification_queue.push(priority.value, notification_dict)
        self._history.push(notification_dict)
        

        if priority.value <= NotificationPriority.HIGH.value:
            await self._process_notification(notification_dict)
        
        return notification


