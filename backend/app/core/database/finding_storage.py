from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete, column
from loguru import logger

from app.core.database.models import Finding, PositiveIndicator
from app.services.orchestrator import Finding as FindingDataclass, Capability


class DBFindingStorage:
    def __init__(self, db: AsyncSession, user_id: Optional[str] = None, is_admin: bool = False):
        self.db = db
        self.user_id = user_id
        self.is_admin = is_admin
    
    async def save_finding(self, finding: FindingDataclass, user_id: Optional[str] = None) -> str:
        owner_id = user_id or self.user_id
        if not owner_id:
            raise ValueError("user_id must be provided")
        
        result = await self.db.execute(
            select(Finding).where(Finding.id == finding.id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.capability = finding.capability.value
            existing.severity = finding.severity
            existing.title = finding.title
            existing.description = finding.description
            existing.evidence = finding.evidence or {}
            existing.affected_assets = finding.affected_assets or []
            existing.recommendations = finding.recommendations or []
            existing.risk_score = finding.risk_score
            existing.target = finding.target
            existing.discovered_at = finding.discovered_at
        else:
            db_finding = Finding(
                id=finding.id,
                user_id=owner_id,
                capability=finding.capability.value,
                severity=finding.severity,
                title=finding.title,
                description=finding.description,
                evidence=finding.evidence or {},
                affected_assets=finding.affected_assets or [],
                recommendations=finding.recommendations or [],
                risk_score=finding.risk_score,
                target=finding.target or "",
                discovered_at=finding.discovered_at
            )
            self.db.add(db_finding)
        
        await self.db.commit()
        return finding.id
    
    async def get_finding(self, finding_id: str) -> Optional[FindingDataclass]:
        """
        Get a single finding by ID.
        
        Args:
            finding_id: Finding ID
            
        Returns:
            Finding dataclass instance or None
        """
        query = select(Finding).where(Finding.id == finding_id)
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Finding.user_id == self.user_id)
        
        result = await self.db.execute(query)
        finding = result.scalar_one_or_none()
        
        if not finding:
            return None
        
        return self._finding_to_dataclass(finding)
    
    async def get_findings(
        self,
        capability: Optional[Capability] = None,
        severity: Optional[str] = None,
        target: Optional[str] = None,
        min_risk_score: float = 0.0,
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> List[FindingDataclass]:
        """
        Get findings with filtering.
        
        Args:
            capability: Filter by capability
            severity: Filter by severity
            target: Filter by target
            min_risk_score: Minimum risk score
            limit: Maximum results
            status_filter: Filter by status (e.g., 'active' to exclude resolved)
            
        Returns:
            List of finding dataclass instances
        """
        query = select(Finding)
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Finding.user_id == self.user_id)
        
        # Apply filters
        conditions = []
        
        if capability:
            conditions.append(Finding.capability == capability.value)
        if severity:
            conditions.append(Finding.severity == severity)
        if target:
            conditions.append(Finding.target == target)
        if min_risk_score > 0:
            conditions.append(Finding.risk_score >= min_risk_score)
        
        # Filter by status (default to only active/unresolved)
        if status_filter:
            conditions.append(Finding.status == status_filter)
        else:
            # Default: only show active findings (exclude resolved)
            conditions.append(
                or_(
                    Finding.status == "active",
                    Finding.status.is_(None)
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Order by risk score descending, then discovered_at descending
        query = query.order_by(Finding.risk_score.desc(), Finding.discovered_at.desc())
        
        # Apply limit
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        findings = result.scalars().all()
        
        return [self._finding_to_dataclass(f) for f in findings]
    
    async def get_critical_findings(self, limit: int = 10) -> List[FindingDataclass]:
        """
        Get critical and high severity findings (only unresolved).
        
        Args:
            limit: Maximum results
            
        Returns:
            List of finding dataclass instances
        """
        query = select(Finding).where(
            Finding.severity.in_(["critical", "high"])
        )
        
        # Only show unresolved findings (status is 'active' or doesn't exist)
        # Filter out resolved, false_positive, and accepted_risk findings
        query = query.where(
            or_(
                Finding.status == "active",
                Finding.status.is_(None)
            )
        )
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Finding.user_id == self.user_id)
        
        query = query.order_by(Finding.risk_score.desc(), Finding.discovered_at.desc())
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        findings = result.scalars().all()
        
        return [self._finding_to_dataclass(f) for f in findings]
    
    async def get_findings_for_target(self, target: str) -> List[FindingDataclass]:
        """
        Get all findings for a specific target.
        
        Args:
            target: Target domain/IP
            
        Returns:
            List of finding dataclass instances
        """
        query = select(Finding).where(Finding.target == target)
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Finding.user_id == self.user_id)
        
        query = query.order_by(Finding.risk_score.desc(), Finding.discovered_at.desc())
        
        result = await self.db.execute(query)
        findings = result.scalars().all()
        
        return [self._finding_to_dataclass(f) for f in findings]
    
    async def get_findings_for_job(self, job_id: str) -> List[FindingDataclass]:
        """
        Get all findings for a specific job.
        
        Note: Job ID is stored in finding metadata/evidence, so we search there.
        This is a workaround until we add job_id to Finding model.
        
        Args:
            job_id: Job ID
            
        Returns:
            List of finding dataclass instances
        """
        # Search in evidence metadata for job_id
        # This is a temporary solution - ideally we'd have a job_id column
        query = select(Finding)
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Finding.user_id == self.user_id)
        
        # Search in evidence JSONB for job_id
        # PostgreSQL JSONB path query: evidence->>'job_id' = job_id
        # Using SQLAlchemy's JSONB operators
        from sqlalchemy.dialects.postgresql import JSONB
        query = query.where(
            Finding.evidence['job_id'].astext == job_id
        )
        
        query = query.order_by(Finding.discovered_at.desc())
        
        result = await self.db.execute(query)
        findings = result.scalars().all()
        
        # Filter more precisely (JSONB contains might match partial strings)
        filtered = []
        for f in findings:
            evidence = f.evidence or {}
            if evidence.get("job_id") == job_id:
                filtered.append(f)
        
        return [self._finding_to_dataclass(f) for f in filtered]
    
    async def delete_finding(self, finding_id: str) -> bool:
        """
        Delete a finding.
        
        Args:
            finding_id: Finding ID
            
        Returns:
            True if deleted
        """
        query = select(Finding).where(Finding.id == finding_id)
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Finding.user_id == self.user_id)
        
        result = await self.db.execute(query)
        finding = result.scalar_one_or_none()
        
        if not finding:
            return False
        
        # Delete the finding using delete statement
        delete_query = delete(Finding).where(Finding.id == finding_id)
        if not self.is_admin:
            delete_query = delete_query.where(Finding.user_id == self.user_id)
        
        await self.db.execute(delete_query)
        await self.db.commit()
        
        return True
    
    async def mark_finding_resolved(self, finding_id: str, user_id: str, status: str = "resolved") -> bool:
        """
        Mark a finding as resolved.
        
        Args:
            finding_id: Finding ID
            user_id: User ID who resolved it
            status: Status to set (resolved, false_positive, accepted_risk)
            
        Returns:
            True if updated
        """
        query = select(Finding).where(Finding.id == finding_id)
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Finding.user_id == self.user_id)
        
        result = await self.db.execute(query)
        finding = result.scalar_one_or_none()
        
        if not finding:
            return False
        
        finding.status = status
        finding.resolved_at = datetime.now(timezone.utc)
        finding.resolved_by = user_id
        
        await self.db.commit()
        return True
    
    async def get_resolved_findings(self) -> Dict[str, int]:
        """
        Get count of resolved findings by severity.
        
        Returns:
            Dictionary with counts per severity
        """
        query = select(Finding).where(Finding.status.in_(["resolved", "false_positive", "accepted_risk"]))
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Finding.user_id == self.user_id)
        
        result = await self.db.execute(query)
        findings = result.scalars().all()
        
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in findings:
            severity = finding.severity.lower()
            if severity in counts:
                counts[severity] += 1
        
        return counts
    
    async def get_positive_indicators(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get positive security indicators.
        
        Args:
            limit: Maximum results
            
        Returns:
            List of positive indicator dictionaries
        """
        query = select(PositiveIndicator)
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(PositiveIndicator.user_id == self.user_id)
        
        query = query.order_by(PositiveIndicator.created_at.desc())
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        indicators = result.scalars().all()
        
        return [{
            "id": ind.id,
            "indicator_type": ind.indicator_type,
            "category": ind.category,
            "points_awarded": ind.points_awarded,
            "description": ind.description,
            "evidence": ind.evidence or {},
            "target": ind.target,
            "created_at": ind.created_at.isoformat() if ind.created_at else None
        } for ind in indicators]
    
    def _finding_to_dataclass(self, finding: Finding) -> FindingDataclass:
        """Convert Finding model to Finding dataclass."""
        return FindingDataclass(
            id=finding.id,
            capability=Capability(finding.capability),
            severity=finding.severity,
            title=finding.title,
            description=finding.description or "",
            evidence=finding.evidence or {},
            affected_assets=finding.affected_assets or [],
            recommendations=finding.recommendations or [],
            discovered_at=finding.discovered_at,
            risk_score=finding.risk_score or 0.0,
            target=finding.target or ""
        )
