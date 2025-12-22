from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from loguru import logger

from app.core.database.models import Job
from app.services.orchestrator import Job as JobDataclass, Capability, JobStatus, JobPriority


class DBJobStorage:
    """Service for querying jobs from database."""
    
    def __init__(self, db: AsyncSession, user_id: Optional[str] = None, is_admin: bool = False):
        """
        Initialize database job storage.
        
        Args:
            db: Database session
            user_id: User ID for scoping (None for admin access to all)
            is_admin: Whether user is admin (can access all data)
        """
        self.db = db
        self.user_id = user_id
        self.is_admin = is_admin
    
    async def save_job(self, job: JobDataclass, user_id: Optional[str] = None) -> str:
        owner_id = user_id or self.user_id
        if not owner_id:
            raise ValueError("user_id must be provided")
        
        result = await self.db.execute(
            select(Job).where(Job.id == job.id)
        )
        existing = result.scalar_one_or_none()
        
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
                meta_data=job.metadata or {},  # Map from dataclass metadata to DB meta_data
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
        """
        Update a job with partial updates.
        
        Args:
            job_id: Job ID
            updates: Dictionary of fields to update
            
        Returns:
            True if updated
        """
        query = select(Job).where(Job.id == job_id)
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Job.user_id == self.user_id)
        
        result = await self.db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            return False
        
        # Update fields
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
            job.meta_data = updates['metadata']  # Map to meta_data column
        if 'execution_logs' in updates:
            job.execution_logs = updates['execution_logs']
        
        await self.db.commit()
        return True
    
    async def get_job(self, job_id: str) -> Optional[JobDataclass]:
        """
        Get a single job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job dataclass instance or None
        """
        query = select(Job).where(Job.id == job_id)
        
        # Apply user filter if not admin
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
        """
        List jobs with filtering and pagination.
        
        Args:
            capability: Filter by capability
            status: Filter by status
            limit: Maximum results
            offset: Number of results to skip
            start_date: Filter jobs created after this date
            end_date: Filter jobs created before this date
            
        Returns:
            List of job dataclass instances
        """
        query = select(Job)
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Job.user_id == self.user_id)
        
        # Apply filters
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
        
        # Order by created_at descending
        query = query.order_by(desc(Job.created_at))
        
        # Apply pagination
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
        """
        Count jobs matching filters.
        
        Args:
            capability: Filter by capability
            status: Filter by status
            start_date: Filter jobs created after this date
            end_date: Filter jobs created before this date
            
        Returns:
            Count of matching jobs
        """
        query = select(func.count(Job.id))
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Job.user_id == self.user_id)
        
        # Apply filters
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
        """Convert Job model to Job dataclass."""
        # Note: We don't load findings here as they're stored separately
        # Findings will be loaded separately when needed
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
            findings=[],  # Findings loaded separately
            error=job.error,
            metadata=job.meta_data or {},  # Map from DB meta_data to dataclass metadata
            execution_logs=job.execution_logs or []  # Include execution logs from database
        )

