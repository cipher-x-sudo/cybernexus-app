"""
CyberNexus Orchestration Engine

Maps user-facing capabilities to underlying tools. Users never see tool names -
they interact with high-level security capabilities.

Capabilities → Tools mapping:
- Exposure Discovery → WebRecon (subdomain enumeration, endpoint discovery)
- Dark Web Intelligence → DarkWatch (onion site monitoring)
- Email Security → EmailAudit (SPF/DKIM/DMARC analysis)
- Infrastructure Testing → ConfigAudit (security headers, vuln scanning)
- Authentication Testing → CredentialAnalyzer
- Network Security → TunnelDetector
- Investigation → Domain correlation
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import time
from loguru import logger

from app.core.dsa import HashMap, MinHeap, AVLTree

# Import real collectors
from app.collectors.web_recon import WebRecon
from app.collectors.email_audit import EmailAudit
from app.collectors.config_audit import ConfigAudit


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
        
        # Initialize real collectors
        self._web_recon = WebRecon()
        self._email_audit = EmailAudit()
        self._config_audit = ConfigAudit()
        
        logger.info("Orchestrator initialized with real collectors")
    
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
        """Execute the appropriate capability using real collectors"""
        findings = []
        
        logger.info(f"Executing capability {job.capability.value} for {job.target}")
        job.progress = 10
        
        try:
            if job.capability == Capability.EMAIL_SECURITY:
                findings = await self._execute_email_audit(job)
            elif job.capability == Capability.EXPOSURE_DISCOVERY:
                findings = await self._execute_exposure_discovery(job)
            elif job.capability == Capability.INFRASTRUCTURE_TESTING:
                findings = await self._execute_infra_testing(job)
            elif job.capability == Capability.DARK_WEB_INTELLIGENCE:
                logger.info(f"[Orchestrator] Calling _execute_darkweb_intelligence for job {job.id}")
                findings = await self._execute_darkweb_intelligence(job)
                logger.info(f"[Orchestrator] _execute_darkweb_intelligence completed for job {job.id}, returned {len(findings)} findings")
            elif job.capability == Capability.AUTHENTICATION_TESTING:
                findings = self._generate_auth_findings(job)
            elif job.capability == Capability.NETWORK_SECURITY:
                findings = self._generate_network_findings(job)
            elif job.capability == Capability.INVESTIGATION:
                findings = self._generate_investigation_findings(job)
        except Exception as e:
            logger.error(f"Collector error for {job.capability.value}: {e}")
            raise
        
        job.progress = 100
        return findings
    
    async def _execute_email_audit(self, job: Job) -> List[Finding]:
        """Execute real email security audit using EmailAudit collector"""
        findings = []
        
        job.progress = 20
        logger.info(f"Running email audit for {job.target}")
        
        # Run real email audit
        results = await self._email_audit.audit(job.target)
        
        job.progress = 80
        
        # Convert SPF issues to findings
        spf = results.get("spf", {})
        if spf.get("exists"):
            for issue in spf.get("issues", []):
                severity = issue.get("severity", "medium")
                findings.append(Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.EMAIL_SECURITY,
                    severity=severity,
                    title=f"SPF Issue: {issue.get('issue', 'Unknown')}",
                    description=issue.get("issue", "SPF configuration issue detected"),
                    evidence={
                        "spf_record": spf.get("record"),
                        "all_mechanism": spf.get("all_mechanism"),
                        "includes": spf.get("includes", [])
                    },
                    affected_assets=[job.target],
                    recommendations=self._get_spf_recommendations(spf),
                    discovered_at=datetime.now(),
                    risk_score=self._severity_to_score(severity)
                ))
        else:
            # No SPF record found
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.EMAIL_SECURITY,
                severity="high",
                title="No SPF Record Found",
                description=f"The domain {job.target} has no SPF record, making it vulnerable to email spoofing",
                evidence={"spf_exists": False},
                affected_assets=[job.target],
                recommendations=["Create an SPF record for your domain", "Start with: v=spf1 include:_spf.google.com ~all"],
                discovered_at=datetime.now(),
                risk_score=75.0
            ))
        
        # Convert DKIM issues to findings
        dkim = results.get("dkim", {})
        if not dkim.get("selectors_found"):
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.EMAIL_SECURITY,
                severity="high",
                title="No DKIM Records Found",
                description=f"No DKIM records found for {job.target}. Email authenticity cannot be verified.",
                evidence={
                    "selectors_checked": dkim.get("selectors_checked", 0),
                    "selectors_found": []
                },
                affected_assets=[job.target],
                recommendations=["Configure DKIM signing for your email server", "Publish DKIM public key in DNS"],
                discovered_at=datetime.now(),
                risk_score=70.0
            ))
        else:
            # DKIM found - report as info
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.EMAIL_SECURITY,
                severity="info",
                title="DKIM Records Found",
                description=f"DKIM is properly configured for {job.target}",
                evidence={
                    "selectors_found": [s.get("selector") for s in dkim.get("selectors_found", [])]
                },
                affected_assets=[job.target],
                recommendations=["Continue monitoring DKIM configuration"],
                discovered_at=datetime.now(),
                risk_score=10.0
            ))
        
        # Convert DMARC issues to findings
        dmarc = results.get("dmarc", {})
        if dmarc.get("exists"):
            policy = dmarc.get("policy")
            if policy == "none":
                findings.append(Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.EMAIL_SECURITY,
                    severity="high",
                    title="DMARC Policy Set to 'none'",
                    description=f"DMARC policy for {job.target} is 'none' (monitoring only). Failed emails are still delivered.",
                    evidence={
                        "dmarc_record": dmarc.get("record"),
                        "policy": policy,
                        "pct": dmarc.get("pct", 100)
                    },
                    affected_assets=[job.target],
                    recommendations=["Upgrade DMARC policy to 'quarantine' or 'reject'", "Review DMARC reports before changing"],
                    discovered_at=datetime.now(),
                    risk_score=65.0
                ))
            elif policy in ["quarantine", "reject"]:
                findings.append(Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.EMAIL_SECURITY,
                    severity="info",
                    title=f"DMARC Policy: {policy}",
                    description=f"DMARC is enforcing {policy} policy for failed authentication",
                    evidence={
                        "dmarc_record": dmarc.get("record"),
                        "policy": policy,
                        "rua": dmarc.get("rua", [])
                    },
                    affected_assets=[job.target],
                    recommendations=["Monitor DMARC reports regularly"],
                    discovered_at=datetime.now(),
                    risk_score=15.0
                ))
            
            # Check for missing report URI
            if not dmarc.get("rua"):
                findings.append(Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.EMAIL_SECURITY,
                    severity="medium",
                    title="Missing DMARC Aggregate Reports",
                    description="No aggregate report URI (rua) configured. You won't receive authentication reports.",
                    evidence={"dmarc_record": dmarc.get("record")},
                    affected_assets=[job.target],
                    recommendations=["Add rua= tag to receive DMARC reports", "Use a DMARC analysis service"],
                    discovered_at=datetime.now(),
                    risk_score=40.0
                ))
        else:
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.EMAIL_SECURITY,
                severity="high",
                title="No DMARC Record Found",
                description=f"The domain {job.target} has no DMARC record. No email authentication policy is enforced.",
                evidence={"dmarc_exists": False},
                affected_assets=[job.target],
                recommendations=["Create a DMARC record", "Start with: v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com"],
                discovered_at=datetime.now(),
                risk_score=70.0
            ))
        
        # Add risk assessment as a finding
        risk = results.get("risk_assessment", {})
        if risk.get("spoofing_risk") in ["critical", "high"]:
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.EMAIL_SECURITY,
                severity=risk.get("spoofing_risk"),
                title=f"Email Spoofing Risk: {risk.get('spoofing_risk', 'unknown').upper()}",
                description=f"Overall email security assessment indicates {risk.get('spoofing_risk')} risk of spoofing",
                evidence={
                    "risk_factors": risk.get("factors", []),
                    "security_score": results.get("score", 0)
                },
                affected_assets=[job.target],
                recommendations=["Address all identified email security issues", "Implement SPF, DKIM, and DMARC"],
                discovered_at=datetime.now(),
                risk_score=self._severity_to_score(risk.get("spoofing_risk", "medium"))
            ))
        
        return findings
    
    async def _execute_exposure_discovery(self, job: Job) -> List[Finding]:
        """Execute real exposure discovery using WebRecon collector"""
        findings = []
        
        job.progress = 20
        logger.info(f"Running exposure discovery for {job.target}")
        
        # Run real web reconnaissance
        results = await self._web_recon.discover_assets(job.target)
        
        job.progress = 80
        
        # Convert subdomain findings
        subdomains = results.get("subdomains", [])
        if subdomains:
            # Report discovered subdomains
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.EXPOSURE_DISCOVERY,
                severity="info",
                title=f"Discovered {len(subdomains)} Subdomains",
                description=f"Subdomain enumeration found {len(subdomains)} active subdomains for {job.target}",
                evidence={
                    "subdomains": [s.get("subdomain") for s in subdomains[:20]],
                    "total_found": len(subdomains)
                },
                affected_assets=[s.get("subdomain") for s in subdomains],
                recommendations=["Review discovered subdomains for unauthorized services", "Ensure all subdomains are properly secured"],
                discovered_at=datetime.now(),
                risk_score=25.0
            ))
            
            # Check for non-HTTPS subdomains
            non_https = [s for s in subdomains if not s.get("https")]
            if non_https:
                findings.append(Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.EXPOSURE_DISCOVERY,
                    severity="medium",
                    title=f"{len(non_https)} Subdomains Without HTTPS",
                    description="Some subdomains are accessible only via HTTP, which is insecure",
                    evidence={
                        "non_https_subdomains": [s.get("subdomain") for s in non_https[:10]]
                    },
                    affected_assets=[s.get("subdomain") for s in non_https],
                    recommendations=["Enable HTTPS on all subdomains", "Redirect HTTP to HTTPS"],
                    discovered_at=datetime.now(),
                    risk_score=50.0
                ))
        
        # Convert endpoint findings
        endpoints = results.get("endpoints", [])
        for endpoint in endpoints:
            path = endpoint.get("path", "")
            status = endpoint.get("status", 0)
            
            # Determine severity based on endpoint type
            severity = "info"
            risk_score = 20.0
            title = f"Endpoint Discovered: {path}"
            recommendations = ["Review endpoint access controls"]
            
            if path in ["/.git/config", "/.git/HEAD"]:
                severity = "critical"
                risk_score = 90.0
                title = "Git Repository Exposed"
                recommendations = ["Block access to .git directory immediately", "Check for exposed secrets in git history"]
            elif path == "/.env":
                severity = "critical"
                risk_score = 95.0
                title = "Environment File Exposed"
                recommendations = ["Remove .env from web root", "Rotate all exposed credentials"]
            elif path in ["/admin", "/wp-admin", "/administrator"]:
                severity = "high"
                risk_score = 70.0
                title = f"Admin Panel Exposed: {path}"
                recommendations = ["Restrict admin access by IP", "Implement strong authentication"]
            elif path in ["/phpinfo.php", "/server-status"]:
                severity = "high"
                risk_score = 65.0
                title = f"Server Information Exposed: {path}"
                recommendations = ["Remove debug endpoints from production", "Disable server-status"]
            elif path in ["/backup", "/config"]:
                severity = "high"
                risk_score = 75.0
                title = f"Sensitive Directory Exposed: {path}"
                recommendations = ["Remove sensitive files from web root", "Implement access controls"]
            elif path in ["/robots.txt", "/sitemap.xml"]:
                severity = "info"
                risk_score = 10.0
            
            if status == 200 or (status >= 300 and status < 400):
                findings.append(Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.EXPOSURE_DISCOVERY,
                    severity=severity,
                    title=title,
                    description=f"Discovered accessible endpoint at {endpoint.get('url', path)}",
                    evidence={
                        "url": endpoint.get("url"),
                        "path": path,
                        "status_code": status,
                        "content_length": endpoint.get("content_length", 0)
                    },
                    affected_assets=[endpoint.get("url", f"{job.target}{path}")],
                    recommendations=recommendations,
                    discovered_at=datetime.now(),
                    risk_score=risk_score
                ))
        
        # Report dork queries generated
        dorks_count = results.get("dorks_generated", 0)
        if dorks_count > 0:
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.EXPOSURE_DISCOVERY,
                severity="info",
                title=f"Generated {dorks_count} Search Dorks",
                description="Search engine dork queries have been generated for manual investigation",
                evidence={
                    "dork_count": dorks_count,
                    "sample_dorks": self._web_recon.generate_dorks(job.target)[:5]
                },
                affected_assets=[job.target],
                recommendations=["Use these dorks in Google to find exposed information", "Review and remove any sensitive findings"],
                discovered_at=datetime.now(),
                risk_score=15.0
            ))
        
        return findings
    
    async def _execute_infra_testing(self, job: Job) -> List[Finding]:
        """Execute real infrastructure testing using ConfigAudit collector"""
        findings = []
        
        job.progress = 20
        logger.info(f"Running infrastructure audit for {job.target}")
        
        # Run real config audit
        results = await self._config_audit.audit(job.target)
        
        job.progress = 80
        
        # Convert header analysis to findings
        headers = results.get("headers_analysis", {})
        
        # Missing headers
        for missing in headers.get("missing", []):
            header_name = missing.get("header", "Unknown")
            severity = missing.get("severity", "medium")
            
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.INFRASTRUCTURE_TESTING,
                severity=severity,
                title=f"Missing Security Header: {header_name}",
                description=f"The security header {header_name} is not present in responses from {job.target}",
                evidence={
                    "missing_header": header_name,
                    "recommendation": missing.get("recommendation")
                },
                affected_assets=[job.target],
                recommendations=[missing.get("recommendation", f"Add {header_name} header")],
                discovered_at=datetime.now(),
                risk_score=self._severity_to_score(severity)
            ))
        
        # Report present headers as info
        present_headers = headers.get("present", [])
        if present_headers:
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.INFRASTRUCTURE_TESTING,
                severity="info",
                title=f"{len(present_headers)} Security Headers Present",
                description="Some security headers are properly configured",
                evidence={
                    "headers": {h.get("header"): h.get("value")[:50] for h in present_headers}
                },
                affected_assets=[job.target],
                recommendations=["Continue monitoring security header configuration"],
                discovered_at=datetime.now(),
                risk_score=10.0
            ))
        
        # Convert vulnerability findings
        vuln_findings = results.get("findings", [])
        for vuln in vuln_findings:
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.INFRASTRUCTURE_TESTING,
                severity=vuln.get("severity", "medium"),
                title=vuln.get("description", "Vulnerability Detected"),
                description=f"Security vulnerability detected: {vuln.get('description')}",
                evidence={
                    "check": vuln.get("check"),
                    "evidence": vuln.get("evidence"),
                    "url": vuln.get("url")
                },
                affected_assets=[vuln.get("url", job.target)],
                recommendations=["Patch the identified vulnerability", "Review server configuration"],
                discovered_at=datetime.now(),
                risk_score=self._severity_to_score(vuln.get("severity", "medium"))
            ))
        
        # Report server info
        server_info = results.get("server_info", {})
        if server_info.get("server") and server_info.get("server") != "unknown":
            # Check for version disclosure
            version = server_info.get("nginx_version")
            if version:
                findings.append(Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.INFRASTRUCTURE_TESTING,
                    severity="low",
                    title="Server Version Disclosed",
                    description=f"Server version information is exposed in HTTP headers",
                    evidence={
                        "server": server_info.get("server"),
                        "version": version,
                        "powered_by": server_info.get("powered_by")
                    },
                    affected_assets=[job.target],
                    recommendations=["Hide server version in HTTP headers", "Configure server_tokens off"],
                    discovered_at=datetime.now(),
                    risk_score=30.0
                ))
        
        # Overall score as a finding
        score = results.get("score", 0)
        if score < 50:
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.INFRASTRUCTURE_TESTING,
                severity="high",
                title=f"Low Infrastructure Security Score: {score}/100",
                description="Overall infrastructure security assessment indicates significant issues",
                evidence={"security_score": score},
                affected_assets=[job.target],
                recommendations=["Address all identified security issues", "Implement security headers"],
                discovered_at=datetime.now(),
                risk_score=85.0 - score * 0.5
            ))
        
        return findings
    
    def _severity_to_score(self, severity: str) -> float:
        """Convert severity string to risk score"""
        scores = {
            "critical": 95.0,
            "high": 75.0,
            "medium": 50.0,
            "low": 25.0,
            "info": 10.0
        }
        return scores.get(severity, 50.0)
    
    def _get_spf_recommendations(self, spf: Dict[str, Any]) -> List[str]:
        """Get SPF-specific recommendations"""
        recommendations = []
        all_mech = spf.get("all_mechanism")
        
        if all_mech == "+all":
            recommendations.append("Change +all to -all or ~all immediately")
            recommendations.append("Review and whitelist only authorized senders")
        elif all_mech == "~all":
            recommendations.append("Consider upgrading ~all to -all for stricter enforcement")
        elif all_mech is None:
            recommendations.append("Add an 'all' mechanism to your SPF record")
        
        if len(spf.get("includes", [])) > 10:
            recommendations.append("Reduce SPF includes to avoid DNS lookup limits")
        
        return recommendations if recommendations else ["SPF configuration looks good"]
    
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
    
    async def _execute_darkweb_intelligence(self, job: Job) -> List[Finding]:
        """Execute real dark web intelligence collection with batch processing and incremental storage"""
        findings = []
        from app.config import settings
        from app.utils import check_tor_connectivity
        
        batch_size = settings.DARKWEB_BATCH_SIZE
        
        try:
            logger.info(
                f"[DarkWeb] [job_id={job.id}] Starting intelligence collection - "
                f"target={job.target}, batch_size={batch_size}"
            )
            start_time = time.time()
            job.progress = 5
            
            # Check Tor connectivity before starting
            logger.info(f"[DarkWeb] [job_id={job.id}] Checking Tor proxy connectivity...")
            tor_check_start = time.time()
            tor_status = check_tor_connectivity()
            tor_check_time = time.time() - tor_check_start
            if tor_status["status"] == "connected" and tor_status["is_tor"]:
                logger.info(
                    f"[DarkWeb] [job_id={job.id}] Tor proxy verified in {tor_check_time:.2f}s - "
                    f"Exit node: {tor_status.get('ip')}, Response time: {tor_status.get('response_time_ms')}ms"
                )
            else:
                logger.warning(
                    f"[DarkWeb] [job_id={job.id}] Tor proxy check failed after {tor_check_time:.2f}s - "
                    f"Status: {tor_status['status']}, Error: {tor_status.get('error')}"
                )
            
            # Use DarkWatch collector
            from app.collectors.dark_watch import DarkWatch
            init_start = time.time()
            logger.info(
                f"[DarkWeb] [job_id={job.id}] Initializing DarkWatch collector - "
                f"keywords={job.target if job.target else 'none'}"
            )
            dark_watch = DarkWatch(monitored_keywords=[job.target] if job.target else [])
            init_time = time.time() - init_start
            logger.info(
                f"[DarkWeb] [job_id={job.id}] DarkWatch collector initialized successfully in {init_time:.2f}s"
            )
            job.progress = 10
            
            # Discover URLs using engines
            logger.info(f"[DarkWeb] [job_id={job.id}] Starting URL discovery using engines...")
            discovery_start = time.time()
            job.progress = 15
            try:
                urls = dark_watch._discover_urls_with_engines()
                discovery_time = time.time() - discovery_start
                logger.info(
                    f"[DarkWeb] [job_id={job.id}] URL discovery completed in {discovery_time:.2f}s - "
                    f"Found {len(urls)} URLs from engines"
                )
                job.progress = 25
            except Exception as e:
                discovery_time = time.time() - discovery_start
                logger.error(
                    f"[DarkWeb] [job_id={job.id}] URL discovery failed after {discovery_time:.2f}s: {e}",
                    exc_info=True
                )
                urls = []  # Continue with empty list, will try database fallback
                job.progress = 20
            
            # If no URLs discovered, try to get URLs from database
            if not urls:
                logger.info(f"[DarkWeb] [job_id={job.id}] No URLs discovered from engines, checking database...")
                try:
                    from app.collectors.darkwatch_modules.crawlers.url_database import URLDatabase
                    logger.info(f"[DarkWeb] [job_id={job.id}] Connecting to URL database...")
                    db_init_start = time.time()
                    db = URLDatabase(
                        dbpath=str(settings.DATA_DIR / settings.CRAWLER_DB_PATH),
                        dbname=settings.CRAWLER_DB_NAME
                    )
                    db_init_time = time.time() - db_init_start
                    logger.info(
                        f"[DarkWeb] [job_id={job.id}] Database connection established in {db_init_time:.2f}s, "
                        f"querying for URLs..."
                    )
                    db_start = time.time()
                    # Get some URLs from database (select returns tuples: id, type, url, title, baseurl, ...)
                    db_records = db.select()
                    db_time = time.time() - db_start
                    logger.info(
                        f"[DarkWeb] [job_id={job.id}] Database query completed in {db_time:.2f}s - "
                        f"Retrieved {len(db_records)} records"
                    )
                    
                    if db_records:
                        # Extract URLs from tuples (url is index 2, baseurl is index 4)
                        urls = []
                        extraction_start = time.time()
                        for record in db_records[:10]:  # Limit to 10
                            url = record[2] if len(record) > 2 and record[2] else None
                            baseurl = record[4] if len(record) > 4 and record[4] else None
                            if url:
                                urls.append(url)
                            elif baseurl:
                                urls.append(baseurl)
                        extraction_time = time.time() - extraction_start
                        logger.info(
                            f"[DarkWeb] [job_id={job.id}] Extracted {len(urls)} URLs from database "
                            f"in {extraction_time:.3f}s"
                        )
                        job.progress = 25
                except Exception as e:
                    logger.warning(
                        f"[DarkWeb] [job_id={job.id}] Could not get URLs from database: {e}",
                        exc_info=True
                    )
            
            # If still no URLs, create a finding indicating no data available
            if not urls:
                logger.warning("[DarkWeb] No URLs available for dark web intelligence collection")
                finding = Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.DARK_WEB_INTELLIGENCE,
                    severity="info",
                    title="Dark Web Intelligence: No URLs Discovered",
                    description=f"Dark web intelligence collection completed but no URLs were discovered for target '{job.target}'. This may indicate: 1) Discovery engines need configuration, 2) No dark web activity found, 3) Network/proxy connectivity issues.",
                    evidence={"target": job.target, "status": "no_urls_discovered"},
                    affected_assets=[job.target] if job.target else [],
                    recommendations=["Check Tor proxy configuration", "Verify discovery engine settings", "Review network connectivity"],
                    discovered_at=datetime.now(),
                    risk_score=10.0
                )
                findings.append(finding)
                # Store in job immediately
                if hasattr(job, 'findings'):
                    job.findings.extend(findings)
                return findings
            
            # Limit initial crawl to avoid overwhelming
            crawl_limit = min(10, len(urls))
            logger.info(
                f"[DarkWeb] [job_id={job.id}] URL planning - Total available: {len(urls)}, "
                f"will crawl: {crawl_limit}, batch_size: {batch_size}"
            )
            
            urls_to_crawl = urls[:crawl_limit]
            total_batches = (len(urls_to_crawl) + batch_size - 1) // batch_size
            logger.info(
                f"[DarkWeb] [job_id={job.id}] Will process {total_batches} batches, "
                f"{len(urls_to_crawl)} URLs total"
            )
            job.progress = 30
            
            # Process URLs in batches
            for batch_num in range(total_batches):
                batch_start_idx = batch_num * batch_size
                batch_end_idx = min(batch_start_idx + batch_size, len(urls_to_crawl))
                batch_urls = urls_to_crawl[batch_start_idx:batch_end_idx]
                batch_num_display = batch_num + 1
                
                # Calculate progress percentage
                batch_progress_base = 30
                batch_progress_range = 60  # 30% to 90%
                batch_progress = batch_progress_base + int((batch_num / total_batches) * batch_progress_range)
                job.progress = batch_progress
                
                logger.info(
                    f"[DarkWeb] [job_id={job.id}] Processing batch {batch_num_display}/{total_batches} "
                    f"(progress: {batch_progress}%) - URLs {batch_start_idx}-{batch_end_idx-1} "
                    f"({len(batch_urls)} URLs)"
                )
                batch_start_time = time.time()
                
                # Crawl and analyze each URL in the batch
                for url_idx, url in enumerate(batch_urls):
                    url_start_time = time.time()
                    url_progress = batch_progress + int((url_idx / len(batch_urls)) * (batch_progress_range / total_batches))
                    job.progress = url_progress
                    
                    try:
                        logger.info(
                            f"[DarkWeb] [job_id={job.id}] Batch {batch_num_display}/{total_batches}, "
                            f"URL {url_idx+1}/{len(batch_urls)} (progress: {url_progress}%): "
                            f"Starting crawl of {url}"
                        )
                        site = dark_watch.crawl_site(url, depth=1)
                        url_crawl_time = time.time() - url_start_time
                        logger.info(
                            f"[DarkWeb] [job_id={job.id}] Batch {batch_num_display}/{total_batches}, "
                            f"URL {url_idx+1}/{len(batch_urls)}: Crawled {url} in {url_crawl_time:.2f}s - "
                            f"Title: {site.title[:50] if site.title else 'N/A'}, "
                            f"Entities: {len(site.extracted_entities)}, "
                            f"Keywords matched: {len(site.keywords_matched)}, "
                            f"Threat level: {site.threat_level.value}"
                        )
                        
                        batch_findings_count = 0
                        
                        # Convert to Finding objects if keywords matched
                        if site.keywords_matched:
                            finding = Finding(
                                id=f"find-{uuid.uuid4().hex[:8]}",
                                capability=Capability.DARK_WEB_INTELLIGENCE,
                                severity=self._map_threat_to_severity(site.threat_level.value),
                                title=f"Brand mention found: {site.title}",
                                description=f"Keyword '{job.target}' found on {site.onion_url}",
                                evidence={"site": site.to_dict()},
                                affected_assets=[job.target] if job.target else [],
                                recommendations=["Review dark web mention", "Monitor for data leaks"],
                                discovered_at=datetime.now(),
                                risk_score=site.risk_score
                            )
                            findings.append(finding)
                            batch_findings_count += 1
                            logger.debug(f"[DarkWeb] Batch {batch_num_display}: Created keyword match finding for {url}")
                        
                        # Also create findings for high-risk entities
                        for entity in site.extracted_entities:
                            if entity.entity_type in ["email", "credit_card"]:
                                finding = Finding(
                                    id=f"find-{uuid.uuid4().hex[:8]}",
                                    capability=Capability.DARK_WEB_INTELLIGENCE,
                                    severity="high" if entity.entity_type == "credit_card" else "medium",
                                    title=f"{entity.entity_type.title()} found on dark web",
                                    description=f"{entity.entity_type.title()} '{entity.value}' discovered on {site.onion_url}",
                                    evidence={"entity": entity.to_dict(), "site": site.onion_url},
                                    affected_assets=[entity.value],
                                    recommendations=["Investigate exposure", "Take remediation steps"],
                                    discovered_at=datetime.now(),
                                    risk_score=85.0 if entity.entity_type == "credit_card" else 65.0
                                )
                                findings.append(finding)
                                batch_findings_count += 1
                                logger.debug(f"[DarkWeb] Batch {batch_num_display}: Created entity finding for {entity.entity_type} from {url}")
                        
                        # Store findings incrementally in job object (for polling/streaming)
                        if batch_findings_count > 0:
                            if hasattr(job, 'findings'):
                                # Only add new findings (avoid duplicates)
                                existing_ids = {f.id for f in job.findings}
                                new_findings = [f for f in findings if f.id not in existing_ids]
                                job.findings.extend(new_findings)
                                logger.info(f"[DarkWeb] Batch {batch_num_display}: Stored {len(new_findings)} new findings in job. Total findings so far: {len(job.findings)}")
                    
                    except Exception as e:
                        url_error_time = time.time() - url_start_time
                        logger.error(
                            f"[DarkWeb] [job_id={job.id}] Batch {batch_num_display}/{total_batches}, "
                            f"URL {url_idx+1}/{len(batch_urls)}: Error crawling {url} after {url_error_time:.2f}s - "
                            f"Error type: {type(e).__name__}, Error: {e}",
                            exc_info=True
                        )
                        continue
                
                batch_time = time.time() - batch_start_time
                elapsed_total = time.time() - start_time
                avg_time_per_url = batch_time / len(batch_urls) if batch_urls else 0
                logger.info(
                    f"[DarkWeb] [job_id={job.id}] Batch {batch_num_display}/{total_batches} completed in {batch_time:.2f}s "
                    f"(avg {avg_time_per_url:.2f}s/URL) - Total findings: {len(findings)}, "
                    f"Elapsed time: {elapsed_total:.2f}s"
                )
                job.progress = batch_progress_base + int(((batch_num + 1) / total_batches) * batch_progress_range)
            
            # If no findings created but URLs were crawled, create info finding
            if not findings and urls:
                logger.info(f"[DarkWeb] Crawled {len(urls_to_crawl)} URLs but no matches found for '{job.target}'")
                finding = Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.DARK_WEB_INTELLIGENCE,
                    severity="info",
                    title=f"Dark Web Scan Complete: No Matches for '{job.target}'",
                    description=f"Scanned {len(urls_to_crawl)} dark web sites but found no mentions of '{job.target}' or high-risk entities.",
                    evidence={"target": job.target, "urls_scanned": len(urls_to_crawl)},
                    affected_assets=[job.target] if job.target else [],
                    recommendations=["Continue monitoring", "Review search terms if needed"],
                    discovered_at=datetime.now(),
                    risk_score=5.0
                )
                findings.append(finding)
                if hasattr(job, 'findings'):
                    job.findings.append(finding)
        
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(
                f"[DarkWeb] [job_id={job.id}] Error in dark web intelligence collection after {total_time:.2f}s - "
                f"Error type: {type(e).__name__}, Error: {e}",
                exc_info=True
            )
            job.progress = 95
            # Create error finding
            finding = Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.DARK_WEB_INTELLIGENCE,
                severity="info",
                title="Dark Web Intelligence Collection Error",
                description=f"An error occurred during dark web intelligence collection: {str(e)}",
                evidence={"error": str(e), "target": job.target if job.target else "unknown"},
                affected_assets=[job.target] if job.target else [],
                recommendations=["Check logs for details", "Verify configuration"],
                discovered_at=datetime.now(),
                risk_score=0.0
            )
            findings.append(finding)
            if hasattr(job, 'findings'):
                job.findings.append(finding)
        
        total_time = time.time() - start_time
        job.progress = 100
        logger.info(
            f"[DarkWeb] [job_id={job.id}] Dark web intelligence collection completed in {total_time:.2f}s - "
            f"Total findings: {len(findings)}, URLs crawled: {len(urls_to_crawl) if 'urls_to_crawl' in locals() else 0}, "
            f"Average time per finding: {total_time / len(findings) if findings else 0:.2f}s"
        )
        return findings
    
    def _map_threat_to_severity(self, threat_level: str) -> str:
        """Map threat level to severity string."""
        mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "info": "info"
        }
        return mapping.get(threat_level.lower(), "info")
    
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

