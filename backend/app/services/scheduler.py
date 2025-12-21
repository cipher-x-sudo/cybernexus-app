"""
Scheduler Service for Automated Search Execution

Manages scheduled searches using APScheduler to execute recurring searches
across all security capabilities.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from croniter import croniter
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import _async_session_maker
from app.core.database.models import ScheduledSearch
from app.services.orchestrator import get_orchestrator, Capability, JobPriority


class SchedulerService:
    """Service for managing scheduled searches."""
    
    def __init__(self):
        """Initialize the scheduler service."""
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the scheduler and load existing scheduled searches."""
        async with self._lock:
            if self._initialized:
                logger.warning("Scheduler already initialized")
                return
            
            logger.info("Initializing scheduler service...")
            
            # Create APScheduler instance
            self.scheduler = AsyncIOScheduler(
                timezone=timezone.utc,
                job_defaults={
                    'coalesce': True,
                    'max_instances': 1,
                    'misfire_grace_time': 300  # 5 minutes grace period
                }
            )
            
            # Start scheduler
            self.scheduler.start()
            logger.info("Scheduler started")
            
            # Load all enabled scheduled searches from database
            await self._load_scheduled_searches()
            
            self._initialized = True
            logger.info("Scheduler service initialized successfully")
    
    async def shutdown(self):
        """Shutdown the scheduler service."""
        async with self._lock:
            if not self._initialized:
                return
            
            logger.info("Shutting down scheduler service...")
            
            if self.scheduler:
                self.scheduler.shutdown(wait=True)
                logger.info("Scheduler shut down")
            
            self._initialized = False
    
    async def _load_scheduled_searches(self):
        """Load all enabled scheduled searches from database and schedule them."""
        try:
            async with _async_session_maker() as session:
                # Query all enabled scheduled searches
                result = await session.execute(
                    select(ScheduledSearch).where(ScheduledSearch.enabled == True)
                )
                scheduled_searches = result.scalars().all()
                
                logger.info(f"Loading {len(scheduled_searches)} enabled scheduled searches")
                
                for scheduled_search in scheduled_searches:
                    try:
                        await self._add_scheduled_job(scheduled_search, session)
                    except Exception as e:
                        logger.error(
                            f"Failed to schedule search {scheduled_search.id}: {e}",
                            exc_info=True
                        )
                
                logger.info(f"Successfully loaded {len(scheduled_searches)} scheduled searches")
        except Exception as e:
            logger.error(f"Error loading scheduled searches: {e}", exc_info=True)
    
    async def _add_scheduled_job(self, scheduled_search: ScheduledSearch, session: Optional[AsyncSession] = None):
        """Add a scheduled search job to the scheduler."""
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")
        
        # Calculate next run time if cron expression is provided
        if scheduled_search.cron_expression:
            try:
                # Get timezone
                import pytz
                tz = pytz.timezone(scheduled_search.timezone)
                
                # Calculate next run time
                now = datetime.now(tz)
                cron = croniter(scheduled_search.cron_expression, now)
                next_run = cron.get_next(datetime)
                
                # Update next_run_at in database
                if session:
                    scheduled_search.next_run_at = next_run.astimezone(timezone.utc)
                    await session.commit()
                else:
                    async with _async_session_maker() as db_session:
                        db_search = await db_session.get(ScheduledSearch, scheduled_search.id)
                        if db_search:
                            db_search.next_run_at = next_run.astimezone(timezone.utc)
                            await db_session.commit()
            except Exception as e:
                logger.error(f"Error calculating next run time for {scheduled_search.id}: {e}")
                return
        
        # Create job function
        async def execute_search():
            await self._execute_scheduled_search(scheduled_search.id)
        
        # Add job to scheduler
        try:
            if scheduled_search.cron_expression:
                # Parse cron expression
                cron_parts = scheduled_search.cron_expression.split()
                if len(cron_parts) == 5:
                    # Get timezone object
                    import pytz
                    tz_obj = pytz.timezone(scheduled_search.timezone)
                    
                    trigger = CronTrigger.from_crontab(
                        scheduled_search.cron_expression,
                        timezone=tz_obj
                    )
                else:
                    logger.error(f"Invalid cron expression: {scheduled_search.cron_expression}")
                    return
            else:
                logger.error(f"No cron expression for scheduled search {scheduled_search.id}")
                return
            
            # Add job with unique ID
            job_id = f"scheduled_search_{scheduled_search.id}"
            self.scheduler.add_job(
                execute_search,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
                name=f"Scheduled Search: {scheduled_search.name}",
                max_instances=1
            )
            
            # Format capabilities for logging
            capabilities_str = ", ".join(scheduled_search.capabilities) if scheduled_search.capabilities else "none"
            logger.info(
                f"Added scheduled job {job_id} for search '{scheduled_search.name}' "
                f"(capabilities: {capabilities_str}, target: {scheduled_search.target})"
            )
        except Exception as e:
            logger.error(f"Error adding scheduled job for {scheduled_search.id}: {e}", exc_info=True)
    
    async def _execute_scheduled_search(self, scheduled_search_id: str):
        """Execute a scheduled search."""
        try:
            async with _async_session_maker() as session:
                # Get scheduled search
                scheduled_search = await session.get(ScheduledSearch, scheduled_search_id)
                if not scheduled_search:
                    logger.error(f"Scheduled search {scheduled_search_id} not found")
                    return
                
                if not scheduled_search.enabled:
                    logger.warning(f"Scheduled search {scheduled_search_id} is disabled, skipping")
                    return
                
                # Get capabilities list (support both old single capability and new multiple capabilities)
                if hasattr(scheduled_search, 'capabilities') and scheduled_search.capabilities:
                    capabilities_list = scheduled_search.capabilities if isinstance(scheduled_search.capabilities, list) else [scheduled_search.capabilities]
                elif hasattr(scheduled_search, 'capability') and scheduled_search.capability:
                    # Backward compatibility: convert single capability to list
                    capabilities_list = [scheduled_search.capability]
                else:
                    logger.error(f"Scheduled search {scheduled_search_id} has no capabilities")
                    return
                
                logger.info(
                    f"Executing scheduled search '{scheduled_search.name}' "
                    f"(capabilities: {capabilities_list}, target: {scheduled_search.target})"
                )
                
                # Get orchestrator
                orchestrator = get_orchestrator()
                
                # Execute all capabilities in parallel
                jobs_created = []
                for cap_str in capabilities_list:
                    try:
                        capability = Capability(cap_str)
                    except ValueError:
                        logger.error(f"Invalid capability: {cap_str}, skipping")
                        continue
                    
                    # Get capability-specific config if available
                    cap_config = scheduled_search.config or {}
                    if isinstance(cap_config, dict) and cap_str in cap_config:
                        cap_config = cap_config[cap_str]
                    
                    # Prepare metadata to track that this was created by scheduler
                    metadata = {
                        "scheduled_search_id": scheduled_search_id,
                        "scheduled_search_name": scheduled_search.name,
                        "capability": cap_str
                    }
                    
                    # Merge metadata into config
                    if isinstance(cap_config, dict):
                        cap_config = {**cap_config, "metadata": metadata}
                    else:
                        cap_config = {"metadata": metadata}
                    
                    # Create job via orchestrator
                    # Use background priority for scheduled searches
                    job = await orchestrator.create_job(
                        capability=capability,
                        target=scheduled_search.target,
                        config=cap_config,
                        priority=JobPriority.BACKGROUND,
                        user_id=scheduled_search.user_id
                    )
                    
                    jobs_created.append(job.id)
                
                if not jobs_created:
                    logger.error(f"No jobs created for scheduled search {scheduled_search_id}")
                    return
                
                # Update scheduled search record
                scheduled_search.last_run_at = datetime.now(timezone.utc)
                scheduled_search.run_count = (scheduled_search.run_count or 0) + 1
                
                # Calculate next run time
                if scheduled_search.cron_expression:
                    try:
                        import pytz
                        tz = pytz.timezone(scheduled_search.timezone)
                        cron = croniter(scheduled_search.cron_expression, datetime.now(tz))
                        next_run = cron.get_next(datetime)
                        scheduled_search.next_run_at = next_run.astimezone(timezone.utc)
                    except Exception as e:
                        logger.error(f"Error calculating next run time: {e}")
                
                await session.commit()
                
                logger.info(
                    f"Scheduled search '{scheduled_search.name}' executed successfully. "
                    f"Created {len(jobs_created)} jobs: {', '.join(jobs_created)}"
                )
        except Exception as e:
            logger.error(
                f"Error executing scheduled search {scheduled_search_id}: {e}",
                exc_info=True
            )
    
    async def add_scheduled_search(self, scheduled_search: ScheduledSearch):
        """Add a new scheduled search to the scheduler."""
        if not self._initialized:
            await self.initialize()
        
        async with _async_session_maker() as session:
            session.add(scheduled_search)
            await session.commit()
            await session.refresh(scheduled_search)
            
            await self._add_scheduled_job(scheduled_search, session)
    
    async def update_scheduled_search(self, scheduled_search: ScheduledSearch):
        """Update an existing scheduled search in the scheduler."""
        if not self._initialized:
            await self.initialize()
        
        # Remove old job
        job_id = f"scheduled_search_{scheduled_search.id}"
        if self.scheduler:
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass  # Job might not exist
        
        # Add updated job
        async with _async_session_maker() as session:
            await session.merge(scheduled_search)
            await session.commit()
            await session.refresh(scheduled_search)
            
            if scheduled_search.enabled:
                await self._add_scheduled_job(scheduled_search, session)
    
    async def remove_scheduled_search(self, scheduled_search_id: str):
        """Remove a scheduled search from the scheduler."""
        job_id = f"scheduled_search_{scheduled_search_id}"
        if self.scheduler:
            try:
                self.scheduler.remove_job(job_id)
                logger.info(f"Removed scheduled job {job_id}")
            except Exception as e:
                logger.warning(f"Error removing scheduled job {job_id}: {e}")
    
    async def trigger_scheduled_search(self, scheduled_search_id: str):
        """Manually trigger a scheduled search execution."""
        await self._execute_scheduled_search(scheduled_search_id)


# Global scheduler instance
_scheduler_service: Optional[SchedulerService] = None


def get_scheduler_service() -> SchedulerService:
    """Get the global scheduler service instance."""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service
