"""
CyberNexus Orchestration Engine

Maps user-facing capabilities to underlying tools. Users never see tool names -
they interact with high-level security capabilities.

Capabilities → Tools mapping:
- Exposure Discovery → oxdork + lookyloo
- Dark Web Intelligence → freshonions + VigilantOnion
- Email Security → espoofer
- Infrastructure Testing → nginxpwner
- Authentication Testing → RDPassSpray
- Network Security → Tunna
- Investigation → lookyloo + correlation
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
from loguru import logger

from app.core.dsa import HashMap, MinHeap, AVLTree


class Capability(str, Enum):
    """User-facing security capabilities"""
    EXPOSURE_DISCOVERY = "exposure_discovery"
    DARK_WEB_INTELLIGENCE = "dark_web_intelligence"
    EMAIL_SECURITY = "email_security"
    INFRASTRUCTURE_TESTING = "infrastructure_testing"
    AUTHENTICATION_TESTING = "authentication_testing"
    NETWORK_SECURITY = "network_security"
    INVESTIGATION = "investigation"


class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(int, Enum):
    """Job priority levels"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class Finding:
    """A security finding from capability execution"""
    id: str
    capability: Capability
    severity: str  # critical, high, medium, low, info
    title: str
    description: str
    evidence: Dict[str, Any]
    affected_assets: List[str]
    recommendations: List[str]
    discovered_at: datetime
    risk_score: float  # 0-100
    target: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "capability": self.capability.value,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "affected_assets": self.affected_assets,
            "recommendations": self.recommendations,
            "discovered_at": self.discovered_at.isoformat(),
            "risk_score": self.risk_score,
            "target": self.target
        }


@dataclass
class Job:
    """A capability execution job"""
    id: str
    capability: Capability
    target: str
    status: JobStatus
    priority: JobPriority
    config: Dict[str, Any]
    progress: int  # 0-100
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    findings: List[Finding] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "capability": self.capability.value,
            "target": self.target,
            "status": self.status.value,
            "priority": self.priority.value,
            "config": self.config,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "findings_count": len(self.findings),
            "error": self.error
        }


# Capability metadata for user display
CAPABILITY_METADATA = {
    Capability.EXPOSURE_DISCOVERY: {
        "id": "exposure_discovery",
        "name": "Exposure Discovery",
        "description": "Discover what attackers can find about your organization online",
        "question": "What can attackers find about us online?",
        "icon": "search",
        "supports_scheduling": True,
        "requires_tor": False,
        "default_config": {
            "depth": "standard",
            "include_subdomains": True
        }
    },
    Capability.DARK_WEB_INTELLIGENCE: {
        "id": "dark_web_intelligence",
        "name": "Dark Web Intelligence",
        "description": "Monitor dark web for mentions, leaks, and threats targeting your organization",
        "question": "Are we mentioned on the dark web?",
        "icon": "globe",
        "supports_scheduling": True,
        "requires_tor": True,
        "default_config": {
            "monitor_keywords": True,
            "check_credentials": True,
            "scan_marketplaces": True
        }
    },
    Capability.EMAIL_SECURITY: {
        "id": "email_security",
        "name": "Email Security Assessment",
        "description": "Test email authentication configuration and spoofing vulnerabilities",
        "question": "Can our email be spoofed?",
        "icon": "mail",
        "supports_scheduling": True,
        "requires_tor": False,
        "default_config": {
            "test_spf": True,
            "test_dkim": True,
            "test_dmarc": True,
            "comprehensive": True
        }
    },
    Capability.INFRASTRUCTURE_TESTING: {
        "id": "infrastructure_testing",
        "name": "Infrastructure Testing",
        "description": "Scan for server misconfigurations and vulnerabilities",
        "question": "Are our servers misconfigured?",
        "icon": "server",
        "supports_scheduling": True,
        "requires_tor": False,
        "default_config": {
            "check_headers": True,
            "check_paths": True,
            "check_cves": True
        }
    },
    Capability.AUTHENTICATION_TESTING: {
        "id": "authentication_testing",
        "name": "Authentication Testing",
        "description": "Test for weak credentials and authentication vulnerabilities",
        "question": "Are our credentials weak?",
        "icon": "key",
        "supports_scheduling": False,
        "requires_tor": False,
        "default_config": {
            "smart_throttling": True,
            "respect_lockouts": True
        }
    },
    Capability.NETWORK_SECURITY: {
        "id": "network_security",
        "name": "Network Security",
        "description": "Detect tunneling attempts and covert channel vulnerabilities",
        "question": "Can attackers tunnel into our network?",
        "icon": "shield",
        "supports_scheduling": True,
        "requires_tor": False,
        "default_config": {
            "detect_http_tunnels": True,
            "detect_dns_tunnels": True
        }
    },
    Capability.INVESTIGATION: {
        "id": "investigation",
        "name": "Investigation Mode",
        "description": "Deep analysis of suspicious URLs, domains, or artifacts",
        "question": "Analyze this suspicious target",
        "icon": "search",
        "supports_scheduling": False,
        "requires_tor": False,
        "default_config": {
            "capture_screenshot": True,
            "map_resources": True,
            "check_reputation": True
        }
    }
}


class Orchestrator:
    """
    Central orchestration engine for all security capabilities.
    
    Maps high-level capabilities to underlying tools and manages
    job execution, queuing, and result aggregation.
    """
    
    def __init__(self):
        """Initialize the orchestrator"""
        # Job storage (using custom DSA)
        self._jobs = HashMap()  # job_id -> Job
        self._job_queue = MinHeap()  # Priority queue for pending jobs (lower priority value = higher priority)
        self._findings_index = AVLTree()  # Indexed by risk_score for fast retrieval
        
        # Job tracking
        self._jobs_by_capability = HashMap()  # capability -> [job_ids]
        self._jobs_by_target = HashMap()  # target -> [job_ids]
        self._jobs_by_status = HashMap()  # status -> [job_ids]
        
        # All findings
        self._all_findings: List[Finding] = []
        
        # Events for live feed
        self._events: List[Dict[str, Any]] = []
        self._max_events = 1000
        
        # Statistics
        self._stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "total_findings": 0,
            "critical_findings": 0,
            "high_findings": 0
        }
        
        logger.info("Orchestrator initialized")
    
    def get_capabilities(self) -> List[Dict[str, Any]]:
        """Get all available capabilities"""
        return list(CAPABILITY_METADATA.values())
    
    def get_capability(self, capability_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific capability by ID"""
        try:
            cap = Capability(capability_id)
            return CAPABILITY_METADATA.get(cap)
        except ValueError:
            return None
    
    async def create_job(
        self,
        capability: Capability,
        target: str,
        config: Optional[Dict[str, Any]] = None,
        priority: JobPriority = JobPriority.NORMAL
    ) -> Job:
        """Create a new job"""
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        
        # Merge with default config
        default_config = CAPABILITY_METADATA[capability].get("default_config", {})
        merged_config = {**default_config, **(config or {})}
        
        job = Job(
            id=job_id,
            capability=capability,
            target=target,
            status=JobStatus.PENDING,
            priority=priority,
            config=merged_config,
            progress=0,
            created_at=datetime.now()
        )
        
        # Store job
        self._jobs.put(job_id, job)
        
        # Index by capability
        cap_jobs = self._jobs_by_capability.get(capability.value) or []
        cap_jobs.append(job_id)
        self._jobs_by_capability.put(capability.value, cap_jobs)
        
        # Index by target
        target_jobs = self._jobs_by_target.get(target) or []
        target_jobs.append(job_id)
        self._jobs_by_target.put(target, target_jobs)
        
        # Index by status
        status_jobs = self._jobs_by_status.get(JobStatus.PENDING.value) or []
        status_jobs.append(job_id)
        self._jobs_by_status.put(JobStatus.PENDING.value, status_jobs)
        
        # Add to queue
        self._job_queue.push((priority.value, datetime.now().timestamp(), job_id))
        
        self._stats["total_jobs"] += 1
        
        # Add event
        self._add_event("job_created", {
            "job_id": job_id,
            "capability": capability.value,
            "target": target
        })
        
        logger.info(f"Created job {job_id} for {capability.value} on {target}")
        
        return job
    
    async def execute_job(self, job_id: str):
        """Execute a job (called in background)"""
        job = self._jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        try:
            # Update status
            self._update_job_status(job, JobStatus.RUNNING)
            job.started_at = datetime.now()
            
            self._add_event("job_started", {
                "job_id": job_id,
                "capability": job.capability.value
            })
            
            # Simulate capability execution
            findings = await self._execute_capability(job)
            
            # Store findings
            for finding in findings:
                finding.target = job.target
                self._all_findings.append(finding)
                self._findings_index.insert(finding.risk_score, finding)
                
                if finding.severity == "critical":
                    self._stats["critical_findings"] += 1
                elif finding.severity == "high":
                    self._stats["high_findings"] += 1
            
            job.findings = findings
            self._stats["total_findings"] += len(findings)
            
            # Complete job
            self._update_job_status(job, JobStatus.COMPLETED)
            job.completed_at = datetime.now()
            job.progress = 100
            
            self._stats["completed_jobs"] += 1
            
            self._add_event("job_completed", {
                "job_id": job_id,
                "capability": job.capability.value,
                "findings_count": len(findings)
            })
            
            logger.info(f"Job {job_id} completed with {len(findings)} findings")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            self._update_job_status(job, JobStatus.FAILED)
            job.error = str(e)
            self._stats["failed_jobs"] += 1
            
            self._add_event("job_failed", {
                "job_id": job_id,
                "capability": job.capability.value,
                "error": str(e)
            })
    
    async def _execute_capability(self, job: Job) -> List[Finding]:
        """Execute the appropriate capability (simulated for now)"""
        findings = []
        
        # Simulate execution with progress updates
        for i in range(1, 11):
            await asyncio.sleep(0.5)  # Simulate work
            job.progress = i * 10
        
        # Generate sample findings based on capability
        if job.capability == Capability.EMAIL_SECURITY:
            findings = self._generate_email_findings(job)
        elif job.capability == Capability.DARK_WEB_INTELLIGENCE:
            findings = self._generate_darkweb_findings(job)
        elif job.capability == Capability.EXPOSURE_DISCOVERY:
            findings = self._generate_exposure_findings(job)
        elif job.capability == Capability.INFRASTRUCTURE_TESTING:
            findings = self._generate_infra_findings(job)
        elif job.capability == Capability.AUTHENTICATION_TESTING:
            findings = self._generate_auth_findings(job)
        elif job.capability == Capability.NETWORK_SECURITY:
            findings = self._generate_network_findings(job)
        elif job.capability == Capability.INVESTIGATION:
            findings = self._generate_investigation_findings(job)
        
        return findings
    
    def _generate_email_findings(self, job: Job) -> List[Finding]:
        """Generate sample email security findings"""
        return [
            Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.EMAIL_SECURITY,
                severity="high",
                title="SPF Record Too Permissive",
                description=f"The SPF record for {job.target} uses +all mechanism, allowing any server to send email",
                evidence={"spf_record": f"v=spf1 +all", "mechanism": "+all"},
                affected_assets=[job.target],
                recommendations=["Change +all to -all or ~all", "Review authorized senders"],
                discovered_at=datetime.now(),
                risk_score=75.0
            ),
            Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.EMAIL_SECURITY,
                severity="medium",
                title="DMARC Policy Set to None",
                description=f"DMARC policy for {job.target} is set to 'none', not enforcing email authentication",
                evidence={"dmarc_record": "v=DMARC1; p=none;"},
                affected_assets=[job.target],
                recommendations=["Set DMARC policy to quarantine or reject"],
                discovered_at=datetime.now(),
                risk_score=55.0
            )
        ]
    
    def _generate_darkweb_findings(self, job: Job) -> List[Finding]:
        """Generate sample dark web findings"""
        return [
            Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.DARK_WEB_INTELLIGENCE,
                severity="critical",
                title="Credential Dump Detected",
                description=f"Credentials associated with {job.target} found in dark web database",
                evidence={"source": "darkweb_forum", "records_count": 150},
                affected_assets=[job.target],
                recommendations=["Force password reset for affected accounts", "Enable MFA"],
                discovered_at=datetime.now(),
                risk_score=95.0
            )
        ]
    
    def _generate_exposure_findings(self, job: Job) -> List[Finding]:
        """Generate sample exposure findings"""
        return [
            Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.EXPOSURE_DISCOVERY,
                severity="medium",
                title="Admin Panel Exposed",
                description=f"Administrative interface found at {job.target}/admin",
                evidence={"url": f"https://{job.target}/admin", "response_code": 200},
                affected_assets=[f"{job.target}/admin"],
                recommendations=["Restrict access to admin panel", "Implement IP whitelisting"],
                discovered_at=datetime.now(),
                risk_score=60.0
            )
        ]
    
    def _generate_infra_findings(self, job: Job) -> List[Finding]:
        """Generate sample infrastructure findings"""
        return [
            Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.INFRASTRUCTURE_TESTING,
                severity="high",
                title="Missing Security Headers",
                description=f"Critical security headers missing on {job.target}",
                evidence={"missing_headers": ["X-Frame-Options", "Content-Security-Policy"]},
                affected_assets=[job.target],
                recommendations=["Add X-Frame-Options header", "Implement Content-Security-Policy"],
                discovered_at=datetime.now(),
                risk_score=70.0
            )
        ]
    
    def _generate_auth_findings(self, job: Job) -> List[Finding]:
        """Generate sample auth findings"""
        return [
            Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.AUTHENTICATION_TESTING,
                severity="medium",
                title="Weak Password Policy",
                description="Password policy allows common patterns",
                evidence={"policy": "min_length=6, no_complexity"},
                affected_assets=[job.target],
                recommendations=["Enforce minimum 12 characters", "Require complexity"],
                discovered_at=datetime.now(),
                risk_score=50.0
            )
        ]
    
    def _generate_network_findings(self, job: Job) -> List[Finding]:
        """Generate sample network findings"""
        return [
            Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.NETWORK_SECURITY,
                severity="low",
                title="HTTP Tunnel Detection Capability",
                description="Network can detect HTTP tunneling attempts",
                evidence={"detection_enabled": True},
                affected_assets=[job.target],
                recommendations=["Continue monitoring"],
                discovered_at=datetime.now(),
                risk_score=20.0
            )
        ]
    
    def _generate_investigation_findings(self, job: Job) -> List[Finding]:
        """Generate sample investigation findings"""
        return [
            Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.INVESTIGATION,
                severity="info",
                title="Domain Analysis Complete",
                description=f"Investigation of {job.target} completed",
                evidence={"resources_found": 45, "external_connections": 12},
                affected_assets=[job.target],
                recommendations=["Review external connections"],
                discovered_at=datetime.now(),
                risk_score=30.0
            )
        ]
    
    def _update_job_status(self, job: Job, new_status: JobStatus):
        """Update job status and indexes"""
        old_status = job.status
        
        # Remove from old status index
        old_status_jobs = self._jobs_by_status.get(old_status.value) or []
        if job.id in old_status_jobs:
            old_status_jobs.remove(job.id)
        self._jobs_by_status.put(old_status.value, old_status_jobs)
        
        # Add to new status index
        new_status_jobs = self._jobs_by_status.get(new_status.value) or []
        new_status_jobs.append(job.id)
        self._jobs_by_status.put(new_status.value, new_status_jobs)
        
        job.status = new_status
    
    def _add_event(self, event_type: str, data: Dict[str, Any]):
        """Add event for live feed"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self._events.insert(0, event)
        
        # Trim old events
        if len(self._events) > self._max_events:
            self._events = self._events[:self._max_events]
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID"""
        return self._jobs.get(job_id)
    
    def get_jobs(
        self,
        capability: Optional[Capability] = None,
        status: Optional[JobStatus] = None,
        limit: int = 50
    ) -> List[Job]:
        """Get jobs with optional filtering"""
        if capability:
            job_ids = self._jobs_by_capability.get(capability.value) or []
        elif status:
            job_ids = self._jobs_by_status.get(status.value) or []
        else:
            job_ids = list(self._jobs.keys())
        
        jobs = []
        for job_id in job_ids[:limit]:
            job = self._jobs.get(job_id)
            if job:
                # Apply additional filters
                if capability and job.capability != capability:
                    continue
                if status and job.status != status:
                    continue
                jobs.append(job)
        
        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        return jobs[:limit]
    
    def get_findings(
        self,
        capability: Optional[Capability] = None,
        severity: Optional[str] = None,
        target: Optional[str] = None,
        min_risk_score: float = 0,
        limit: int = 100
    ) -> List[Finding]:
        """Get findings with optional filtering"""
        results = []
        
        for finding in self._all_findings:
            if capability and finding.capability != capability:
                continue
            if severity and finding.severity != severity:
                continue
            if target and finding.target != target:
                continue
            if finding.risk_score < min_risk_score:
                continue
            results.append(finding)
            
            if len(results) >= limit:
                break
        
        # Sort by risk_score descending
        results.sort(key=lambda f: f.risk_score, reverse=True)
        
        return results
    
    def get_critical_findings(self, limit: int = 10) -> List[Finding]:
        """Get critical and high severity findings"""
        critical = [f for f in self._all_findings if f.severity in ["critical", "high"]]
        critical.sort(key=lambda f: f.risk_score, reverse=True)
        return critical[:limit]
    
    def get_findings_for_target(self, target: str) -> List[Finding]:
        """Get all findings for a target"""
        return [f for f in self._all_findings if f.target == target]
    
    async def quick_scan(self, domain: str) -> Dict[str, Any]:
        """Perform quick scan of a domain"""
        started_at = datetime.now()
        
        # Run essential capabilities
        capabilities = [
            Capability.EMAIL_SECURITY,
            Capability.EXPOSURE_DISCOVERY,
            Capability.INFRASTRUCTURE_TESTING
        ]
        
        jobs = []
        for cap in capabilities:
            job = await self.create_job(cap, domain, priority=JobPriority.HIGH)
            await self.execute_job(job.id)
            jobs.append(job.to_dict())
        
        completed_at = datetime.now()
        
        # Calculate summary
        total_findings = sum(j["findings_count"] for j in jobs)
        
        return {
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "jobs": jobs,
            "summary": {
                "capabilities_run": len(jobs),
                "total_findings": total_findings,
                "duration_seconds": (completed_at - started_at).total_seconds()
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return self._stats
    
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent events for live feed"""
        return self._events[:limit]


# Global orchestrator instance
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """Get the global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

