"""Finding storage and retrieval system.

This module provides database-backed storage for security findings and positive
indicators. Uses PostgreSQL for persistence without custom DSA structures.

This module does not use custom DSA concepts from app.core.dsa.
"""

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
        """Save or update a finding in the database.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            finding: The finding dataclass to save or update
            user_id: Optional user ID to override the instance user_id
        
        Returns:
            The ID of the saved finding
        
        Raises:
            ValueError: If user_id is not provided and instance user_id is None
        """
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
        """Retrieve a finding by its ID.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            finding_id: The unique identifier of the finding
        
        Returns:
            The finding dataclass if found, None otherwise
        """
        query = select(Finding).where(Finding.id == finding_id)
        
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
        """Retrieve findings with optional filters.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            capability: Optional capability filter
            severity: Optional severity filter
            target: Optional target filter
            min_risk_score: Minimum risk score threshold (default: 0.0)
            limit: Maximum number of findings to return (default: 100)
            status_filter: Optional status filter (default: active or None)
        
        Returns:
            List of finding dataclasses matching the filters, ordered by risk score and discovery time
        """
        query = select(Finding)
        
        if not self.is_admin:
            query = query.where(Finding.user_id == self.user_id)
        
        # Build dynamic query conditions
        conditions = []
        
        if capability:
            conditions.append(Finding.capability == capability.value)
        if severity:
            conditions.append(Finding.severity == severity)
        if target:
            conditions.append(Finding.target == target)
        if min_risk_score > 0:
            conditions.append(Finding.risk_score >= min_risk_score)
        
        # Default to active findings if no status filter specified
        if status_filter:
            conditions.append(Finding.status == status_filter)
        else:
            conditions.append(
                or_(
                    Finding.status == "active",
                    Finding.status.is_(None)
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Finding.risk_score.desc(), Finding.discovered_at.desc())
        
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        findings = result.scalars().all()
        
        return [self._finding_to_dataclass(f) for f in findings]
    
    async def get_critical_findings(self, limit: int = 10) -> List[FindingDataclass]:
        """Retrieve critical and high severity findings.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            limit: Maximum number of findings to return (default: 10)
        
        Returns:
            List of critical and high severity findings, ordered by risk score and discovery time
        """
        query = select(Finding).where(
            Finding.severity.in_(["critical", "high"])
        )
        
        query = query.where(
            or_(
                Finding.status == "active",
                Finding.status.is_(None)
            )
        )
        
        if not self.is_admin:
            query = query.where(Finding.user_id == self.user_id)
        
        query = query.order_by(Finding.risk_score.desc(), Finding.discovered_at.desc())
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        findings = result.scalars().all()
        
        return [self._finding_to_dataclass(f) for f in findings]
    
    async def get_findings_for_target(self, target: str) -> List[FindingDataclass]:
        """Retrieve all findings for a specific target.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            target: The target identifier to filter by
        
        Returns:
            List of findings for the specified target, ordered by risk score and discovery time
        """
        query = select(Finding).where(Finding.target == target)
        
        if not self.is_admin:
            query = query.where(Finding.user_id == self.user_id)
        
        query = query.order_by(Finding.risk_score.desc(), Finding.discovered_at.desc())
        
        result = await self.db.execute(query)
        findings = result.scalars().all()
        
        return [self._finding_to_dataclass(f) for f in findings]
    
    async def get_findings_for_job(self, job_id: str) -> List[FindingDataclass]:
        """Retrieve all findings associated with a specific job.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            job_id: The job identifier to filter by
        
        Returns:
            List of findings associated with the job, ordered by discovery time
        """
        query = select(Finding)
        
        if not self.is_admin:
            query = query.where(Finding.user_id == self.user_id)
        
        # Query JSONB field for job_id in evidence
        from sqlalchemy.dialects.postgresql import JSONB
        query = query.where(
            Finding.evidence['job_id'].astext == job_id
        )
        
        query = query.order_by(Finding.discovered_at.desc())
        
        result = await self.db.execute(query)
        findings = result.scalars().all()
        
        # Additional filtering for exact match (JSONB query may have false positives)
        filtered = []
        for f in findings:
            evidence = f.evidence or {}
            if evidence.get("job_id") == job_id:
                filtered.append(f)
        
        return [self._finding_to_dataclass(f) for f in filtered]
    
    async def delete_finding(self, finding_id: str) -> bool:
        """Delete a finding by its ID.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            finding_id: The unique identifier of the finding to delete
        
        Returns:
            True if the finding was deleted, False if not found
        """
        query = select(Finding).where(Finding.id == finding_id)
        
        if not self.is_admin:
            query = query.where(Finding.user_id == self.user_id)
        
        result = await self.db.execute(query)
        finding = result.scalar_one_or_none()
        
        if not finding:
            return False
        
        delete_query = delete(Finding).where(Finding.id == finding_id)
        if not self.is_admin:
            delete_query = delete_query.where(Finding.user_id == self.user_id)
        
        await self.db.execute(delete_query)
        await self.db.commit()
        
        return True
    
    async def mark_finding_resolved(self, finding_id: str, user_id: str, status: str = "resolved") -> bool:
        """Mark a finding as resolved.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            finding_id: The unique identifier of the finding
            user_id: The ID of the user resolving the finding
            status: The resolution status (default: "resolved")
        
        Returns:
            True if the finding was updated, False if not found
        """
        query = select(Finding).where(Finding.id == finding_id)
        
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
        """Get counts of resolved findings grouped by severity.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Returns:
            Dictionary mapping severity levels to counts of resolved findings
        """
        query = select(Finding).where(Finding.status.in_(["resolved", "false_positive", "accepted_risk"]))
        
        if not self.is_admin:
            query = query.where(Finding.user_id == self.user_id)
        
        result = await self.db.execute(query)
        findings = result.scalars().all()
        
        # Aggregate counts by severity level
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in findings:
            severity = finding.severity.lower()
            if severity in counts:
                counts[severity] += 1
        
        return counts
    
    async def get_positive_indicators(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve positive security indicators.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            limit: Maximum number of indicators to return (default: 100)
        
        Returns:
            List of positive indicator dictionaries, ordered by creation time
        """
        query = select(PositiveIndicator)
        
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
        """Convert a database Finding model to a FindingDataclass.
        
        Internal helper method to convert SQLAlchemy model to dataclass.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            finding: The SQLAlchemy Finding model instance
        
        Returns:
            A FindingDataclass instance with data from the model
        """
        # Convert enum strings to Capability enum, handle None values
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
