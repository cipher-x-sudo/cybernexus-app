"""
Task Scheduler Service

Background task scheduling using custom Heap-based priority queue.
"""

import asyncio
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger

from app.core.dsa import MinHeap, HashMap


@dataclass
class ScheduledTask:
    """A scheduled task."""
    id: str
    name: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    interval: Optional[timedelta] = None
    next_run: datetime = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.next_run is None:
            self.next_run = datetime.utcnow()


class Scheduler:
    """
    Task Scheduler using custom Min-Heap.
    
    Features:
    - Priority-based task scheduling
    - One-time and recurring tasks
    - Async task support
    
    DSA Usage:
    - MinHeap: Task queue ordered by next run time
    - HashMap: Task lookup by ID
    """
    
    def __init__(self):
        """Initialize scheduler."""
        self._task_queue = MinHeap()
        self._tasks = HashMap()
        self._running = False
        self._task_counter = 0
    
    def schedule(self, name: str, func: Callable, 
                delay: timedelta = None, interval: timedelta = None,
                args: tuple = (), kwargs: dict = None) -> str:
        """Schedule a task.
        
        Args:
            name: Task name
            func: Function to execute
            delay: Initial delay before first run
            interval: Repeat interval (None for one-time)
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Task ID
        """
        self._task_counter += 1
        task_id = f"task-{self._task_counter}"
        
        next_run = datetime.utcnow()
        if delay:
            next_run += delay
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs or {},
            interval=interval,
            next_run=next_run
        )
        
        self._tasks.put(task_id, task)
        self._task_queue.push(next_run.timestamp(), task_id)
        
        logger.info(f"Scheduled task: {name} ({task_id})")
        return task_id
    
    def cancel(self, task_id: str) -> bool:
        """Cancel a scheduled task.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if cancelled
        """
        if self._tasks.remove(task_id):
            logger.info(f"Cancelled task: {task_id}")
            return True
        return False
    
    async def run(self):
        """Run the scheduler loop."""
        self._running = True
        logger.info("Scheduler started")
        
        while self._running:
            await self._process_due_tasks()
            await asyncio.sleep(1)  # Check every second
    
    def stop(self):
        """Stop the scheduler."""
        self._running = False
        logger.info("Scheduler stopped")
    
    async def _process_due_tasks(self):
        """Process tasks that are due to run."""
        now = datetime.utcnow().timestamp()
        
        while self._task_queue:
            # Peek at next task
            next_item = self._task_queue.peek()
            if not next_item:
                break
            
            next_time, task_id = next_item
            
            if next_time > now:
                break  # No more due tasks
            
            # Pop and execute
            self._task_queue.pop()
            task = self._tasks.get(task_id)
            
            if not task:
                continue  # Task was cancelled
            
            # Execute task
            try:
                logger.debug(f"Executing task: {task.name}")
                if asyncio.iscoroutinefunction(task.func):
                    await task.func(*task.args, **task.kwargs)
                else:
                    task.func(*task.args, **task.kwargs)
            except Exception as e:
                logger.error(f"Task error ({task.name}): {e}")
            
            # Reschedule if recurring
            if task.interval:
                task.next_run = datetime.utcnow() + task.interval
                self._task_queue.push(task.next_run.timestamp(), task_id)
            else:
                self._tasks.remove(task_id)
    
    def get_pending_tasks(self) -> list:
        """Get list of pending tasks.
        
        Returns:
            List of pending task info
        """
        pending = []
        for task_id in self._tasks.keys():
            task = self._tasks.get(task_id)
            if task:
                pending.append({
                    "id": task.id,
                    "name": task.name,
                    "next_run": task.next_run.isoformat(),
                    "recurring": task.interval is not None
                })
        return pending
    
    def stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "running": self._running,
            "pending_tasks": len(self._tasks),
            "queue_size": len(self._task_queue)
        }


