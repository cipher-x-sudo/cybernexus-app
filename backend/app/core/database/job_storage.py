"""Job storage and management system.

This module provides database-backed storage for job execution records.
Uses PostgreSQL for persistence without custom DSA structures.

This module does not use custom DSA concepts from app.core.dsa.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from loguru import logger

from app.core.database.models import Job
from app.services.orchestrator import Job as JobDataclass, Capability, JobStatus, JobPriority


class DBJobStorage:
    def __init__(self, db: AsyncSession, user_id: Optional[str] = None, is_admin: bool = False):
        self.db = db
        self.user_id = user_id
        self.is_admin = is_admin
    
    async def save_job(self, job: JobDataclass, user_id: Optional[str] = None) -> str:
        """Save or update a job in the database.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            job: The job dataclass to save or update
            user_id: Optional user ID to override the instance user_id
        
        Returns:
            The ID of the saved job
        
        Raises:
            ValueError: If user_id is not provided and instance user_id is None
        """
        owner_id = user_id or self.user_id
        if not owner_id:
            raise ValueError("user_id must be provided")
        
        result = await self.db.execute(
            select(Job).where(Job.id == job.id)
        )
        existing = result.scalar_one_or_none()
        
        # Extract execution logs from job (may be in execution_logs or metadata)
        execution_logs = []
        if hasattr(job, 'execution_logs') and job.execution_logs:
            execution_logs = job.execution_logs
        elif hasattr(job, 'metadata') and job.metadata:
            execution_logs = job.metadata.get('execution_logs', [])
        
        if existing:
            existing.capability = job.capability.value
            existing.target = job.target
            existing.status = job.status.value
            existing.priority = job.priority.value
            existing.progress = job.progress
            existing.config = job.config or {}
            existing.meta_data = job.metadata or {}
            existing.error = job.error
            existing.execution_logs = execution_logs
            existing.started_at = job.started_at
            existing.completed_at = job.completed_at
        else:
            db_job = Job(
                id=job.id,
                user_id=owner_id,
                capability=job.capability.value,
                target=job.target,
                status=job.status.value,
                priority=job.priority.value,
                progress=job.progress,
                config=job.config or {},
                meta_data=job.metadata or {},
                error=job.error,
                execution_logs=execution_logs,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at
            )
            self.db.add(db_job)
        
        await self.db.commit()
        return job.id
    
    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update a job with the provided fields.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            job_id: The unique identifier of the job to update
            updates: Dictionary of fields to update (status, progress, error, etc.)
        
        Returns:
            True if the job was updated, False if not found
        """
        query = select(Job).where(Job.id == job_id)
        
        if not self.is_admin:
            query = query.where(Job.user_id == self.user_id)
        
        result = await self.db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            return False
        
        if 'status' in updates:
            job.status = updates['status']
        if 'progress' in updates:
            job.progress = updates['progress']
        if 'error' in updates:
            job.error = updates['error']
        if 'started_at' in updates:
            job.started_at = updates['started_at']
        if 'completed_at' in updates:
            job.completed_at = updates['completed_at']
        if 'config' in updates:
            job.config = updates['config']
        if 'metadata' in updates:
            job.meta_data = updates['metadata']
        if 'execution_logs' in updates:
            job.execution_logs = updates['execution_logs']
        
        await self.db.commit()
        return True
    
    async def get_job(self, job_id: str) -> Optional[JobDataclass]:
        """Retrieve a job by its ID.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            job_id: The unique identifier of the job
        
        Returns:
            The job dataclass if found, None otherwise
        """
        query = select(Job).where(Job.id == job_id)
        
        if not self.is_admin:
            query = query.where(Job.user_id == self.user_id)
        
        result = await self.db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            return None
        
        return self._job_to_dataclass(job)
    
    async def list_jobs(
        self,
        capability: Optional[Capability] = None,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[JobDataclass]:
        """List jobs with optional filters.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            capability: Optional capability filter
            status: Optional job status filter
            limit: Maximum number of jobs to return (default: 50)
            offset: Number of jobs to skip for pagination (default: 0)
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            List of job dataclasses matching the filters, ordered by creation time
        """
        query = select(Job)
        
        if not self.is_admin:
            query = query.where(Job.user_id == self.user_id)
        
        conditions = []
        
        if capability:
            conditions.append(Job.capability == capability.value)
        if status:
            conditions.append(Job.status == status.value)
        if start_date:
            conditions.append(Job.created_at >= start_date)
        if end_date:
            conditions.append(Job.created_at <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(Job.created_at))
        
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        jobs = result.scalars().all()
        
        return [self._job_to_dataclass(job) for job in jobs]
    
    async def count_jobs(
        self,
        capability: Optional[Capability] = None,
        status: Optional[JobStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Count jobs matching the provided filters.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            capability: Optional capability filter
            status: Optional job status filter
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            The count of jobs matching the filters
        """
        query = select(func.count(Job.id))
        
        if not self.is_admin:
            query = query.where(Job.user_id == self.user_id)
        
        conditions = []
        
        if capability:
            conditions.append(Job.capability == capability.value)
        if status:
            conditions.append(Job.status == status.value)
        if start_date:
            conditions.append(Job.created_at >= start_date)
        if end_date:
            conditions.append(Job.created_at <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    def _job_to_dataclass(self, job: Job) -> JobDataclass:
        """Convert a database Job model to a JobDataclass.
        
        Internal helper method to convert SQLAlchemy model to dataclass.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            job: The SQLAlchemy Job model instance
        
        Returns:
            A JobDataclass instance with data from the model
        """
        # Convert enum strings to enum types, handle None values and defaults
        return JobDataclass(
            id=job.id,
            capability=Capability(job.capability),
            target=job.target,
            status=JobStatus(job.status),
            priority=JobPriority(job.priority),
            config=job.config or {},
            progress=job.progress,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            findings=[],  # Findings loaded separately if needed
            error=job.error,
            metadata=job.meta_data or {},
            execution_logs=job.execution_logs or []
        )

