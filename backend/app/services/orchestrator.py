from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import time
import base64
import json
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger
from fastapi import WebSocket

from app.core.dsa import HashMap, MinHeap, AVLTree

from app.collectors.web_recon import WebRecon
from app.collectors.email_audit import EmailAudit
from app.services.positive_scorer import get_positive_scorer
from app.collectors.config_audit import ConfigAudit
from app.collectors.domain_tree import DomainTree

from app.services.bypass_tester import BypassTester
from app.services.browser_capture import get_browser_capture_service
from app.services.visual_similarity import get_visual_similarity_service


class Capability(str, Enum):
    EXPOSURE_DISCOVERY = "exposure_discovery"
    DARK_WEB_INTELLIGENCE = "dark_web_intelligence"
    EMAIL_SECURITY = "email_security"
    INFRASTRUCTURE_TESTING = "infrastructure_testing"
    NETWORK_SECURITY = "network_security"
    INVESTIGATION = "investigation"


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(int, Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class Finding:
    id: str
    capability: Capability
    severity: str
    title: str
    description: str
    evidence: Dict[str, Any]
    affected_assets: List[str]
    recommendations: List[str]
    discovered_at: datetime
    risk_score: float
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
    id: str
    capability: Capability
    target: str
    status: JobStatus
    priority: JobPriority
    config: Dict[str, Any]
    progress: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    findings: List[Finding] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_logs: List[Dict[str, Any]] = field(default_factory=list)
    _findings_lock: Lock = field(default_factory=Lock, init=False, repr=False)
    
    def add_finding(self, finding: Finding):
        with self._findings_lock:
            self.findings.append(finding)
    
    def add_findings(self, findings: List[Finding]):
        with self._findings_lock:
            self.findings.extend(findings)
    
    def get_findings_since(self, since_timestamp: Optional[datetime] = None, since_id: Optional[str] = None) -> List[Finding]:
        with self._findings_lock:
            if since_timestamp:
                return [f for f in self.findings if f.discovered_at > since_timestamp]
            elif since_id:
                try:
                    since_index = next(i for i, f in enumerate(self.findings) if f.id == since_id)
                    return self.findings[since_index + 1:]
                except StopIteration:
                    return self.findings[:]
            else:
                return self.findings[:]
    
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
    def __init__(self):
        self._jobs = HashMap()
        self._job_queue = MinHeap()
        self._findings_index = AVLTree()
        
        self._jobs_by_capability = HashMap()
        self._jobs_by_target = HashMap()
        self._jobs_by_status = HashMap()
        
        self._all_findings: List[Finding] = []
        
        self._events: List[Dict[str, Any]] = []
        self._max_events = 1000
        
        self._stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "total_findings": 0,
            "critical_findings": 0,
            "high_findings": 0
        }
        
        self._darkwatch_instances = HashMap()
        
        self._websocket_connections: Dict[str, WebSocket] = {}
        self._websocket_lock = asyncio.Lock()
        
        self._tool_executors: Dict[str, Any] = {}
        
        self._web_recon = WebRecon()
        self._email_audit = EmailAudit()
        self._bypass_tester = BypassTester()
        self._config_audit = ConfigAudit()
        
        logger.info("Orchestrator initialized with real collectors (PostgreSQL storage)")
    
    async def _save_job_to_db(self, job: Job, user_id: Optional[str] = None):
        
        try:
            from app.core.database.database import init_db, _async_session_maker
            from app.core.database.job_storage import DBJobStorage
            
            owner_id = user_id or (job.metadata.get("user_id") if job.metadata else None)
            if not owner_id:
                return
            
            init_db()
            
            if _async_session_maker:
                async with _async_session_maker() as db:
                    try:
                        storage = DBJobStorage(db, user_id=owner_id, is_admin=False)
                        await storage.save_job(job, user_id=owner_id)
                        await db.commit()
                        logger.debug(f"Saved job {job.id} to database")
                    except Exception as e:
                        await db.rollback()
                        logger.warning(f"Failed to save job {job.id} to database: {e}")
        except Exception as e:
            logger.warning(f"Failed to initialize database storage for job {job.id}: {e}")
    
    def register_tool_executor(self, tool_name: str, executor: Any):
        self._tool_executors[tool_name] = executor
        logger.debug(f"Registered tool executor for {tool_name}")
    
    async def register_websocket(self, job_id: str, websocket: WebSocket):
        async with self._websocket_lock:
            self._websocket_connections[job_id] = websocket
            logger.info(f"Registered WebSocket connection for job {job_id}")
    
    async def unregister_websocket(self, job_id: str):
        async with self._websocket_lock:
            if job_id in self._websocket_connections:
                del self._websocket_connections[job_id]
                logger.info(f"Unregistered WebSocket connection for job {job_id}")
    
    async def get_websocket(self, job_id: str) -> Optional[WebSocket]:
        async with self._websocket_lock:
            return self._websocket_connections.get(job_id)
    
    async def send_websocket_message(self, job_id: str, message: Dict[str, Any]) -> bool:
        websocket = await self.get_websocket(job_id)
        if not websocket:
            return False
        
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message to job {job_id}: {e}")
            await self.unregister_websocket(job_id)
            return False
    
    def get_capabilities(self) -> List[Dict[str, Any]]:
        return list(CAPABILITY_METADATA.values())
    
    def get_capability(self, capability_id: str) -> Optional[Dict[str, Any]]:
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
        priority: JobPriority = JobPriority.NORMAL,
        user_id: Optional[str] = None
    ) -> Job:
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        
        default_config = CAPABILITY_METADATA[capability].get("default_config", {})
        merged_config = {**default_config, **(config or {})}
        
        metadata = {"user_id": user_id} if user_id else {}
        
        job = Job(
            id=job_id,
            capability=capability,
            target=target,
            status=JobStatus.PENDING,
            priority=priority,
            config=merged_config,
            progress=0,
            created_at=datetime.now(),
            metadata=metadata
        )
        
        self._jobs.put(job_id, job)
        
        cap_jobs = self._jobs_by_capability.get(capability.value) or []
        cap_jobs.append(job_id)
        self._jobs_by_capability.put(capability.value, cap_jobs)
        
        target_jobs = self._jobs_by_target.get(target) or []
        target_jobs.append(job_id)
        self._jobs_by_target.put(target, target_jobs)
        
        status_jobs = self._jobs_by_status.get(JobStatus.PENDING.value) or []
        status_jobs.append(job_id)
        self._jobs_by_status.put(JobStatus.PENDING.value, status_jobs)
        
        self._job_queue.push((priority.value, datetime.now().timestamp(), job_id))
        
        self._stats["total_jobs"] += 1
        
        self._add_execution_log(job, "info", f"Job created for {capability.value} on {target}", {
            "capability": capability.value,
            "target": target,
            "priority": priority.value,
            "config": merged_config
        })
        
        await self._save_job_to_db(job, user_id=user_id)
        
        self._add_event("job_created", {
            "job_id": job_id,
            "capability": capability.value,
            "target": target
        })
        
        logger.info(f"Created job {job_id} for {capability.value} on {target}")
        
        return job
    
    async def execute_job(self, job_id: str):
        job = self._jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        try:
            self._update_job_status(job, JobStatus.RUNNING)
            job.started_at = datetime.now()
            
            await self._save_job_to_db(job)
            
            self._add_event("job_started", {
                "job_id": job_id,
                "capability": job.capability.value
            })
            
            findings = await self._execute_capability(job)
            
            user_id = job.metadata.get("user_id") if job.metadata else None
            
            for finding in findings:
                finding.target = job.target
                
                if not finding.evidence:
                    finding.evidence = {}
                finding.evidence["job_id"] = job.id
                
                self._all_findings.append(finding)
                self._findings_index.insert(finding.risk_score, finding)
                
                if user_id:
                    try:
                        from app.core.database.database import init_db, _async_session_maker
                        from app.core.database.finding_storage import DBFindingStorage
                        
                        init_db()
                        
                        if _async_session_maker:
                            async with _async_session_maker() as db:
                                try:
                                    storage = DBFindingStorage(db, user_id=user_id, is_admin=False)
                                    await storage.save_finding(finding, user_id=user_id)
                                    await db.commit()
                                except Exception as e:
                                    await db.rollback()
                                    logger.warning(f"Failed to store finding in database: {e}")
                    except Exception as e:
                        logger.warning(f"Failed to initialize database storage for finding: {e}")
                
                if finding.severity == "critical":
                    self._stats["critical_findings"] += 1
                elif finding.severity == "high":
                    self._stats["high_findings"] += 1
                
                if user_id and finding.severity in ["critical", "high"]:
                    try:
                        from app.services.notification import NotificationService, NotificationPriority
                        from app.core.database.database import init_db, _async_session_maker
                        
                        init_db()
                        if _async_session_maker:
                            async with _async_session_maker() as db:
                                try:
                                    notification_service = NotificationService()
                                    priority_map = {
                                        "critical": NotificationPriority.CRITICAL,
                                        "high": NotificationPriority.HIGH,
                                    }
                                    priority = priority_map.get(finding.severity, NotificationPriority.MEDIUM)
                                    
                                    await notification_service.create_notification(
                                        db=db,
                                        user_id=user_id,
                                        channel="findings",
                                        priority=priority,
                                        title=f"New {finding.severity.upper()} Finding: {finding.title}",
                                        message=finding.description,
                                        severity=finding.severity,
                                        metadata={
                                            "finding_id": finding.id,
                                            "capability": finding.capability.value,
                                            "job_id": job.id,
                                            "target": job.target,
                                            "risk_score": finding.risk_score,
                                        }
                                    )
                                    await db.commit()
                                except Exception as e:
                                    await db.rollback()
                                    logger.warning(f"Failed to create notification for finding {finding.id}: {e}")
                    except Exception as e:
                        logger.warning(f"Failed to initialize notification service for finding: {e}")
            
            job.findings = findings
            self._stats["total_findings"] += len(findings)
            
            if findings:
                critical_count = sum(1 for f in findings if f.severity == "critical")
                high_count = sum(1 for f in findings if f.severity == "high")
                self._add_execution_log(job, "info", f"Discovered {len(findings)} findings ({critical_count} critical, {high_count} high)", {
                    "findings_count": len(findings),
                    "critical_count": critical_count,
                    "high_count": high_count
                })
            else:
                self._add_execution_log(job, "info", "No findings discovered", {})
            
            self._update_job_status(job, JobStatus.COMPLETED)
            job.completed_at = datetime.now()
            job.progress = 100
            
            self._add_execution_log(job, "info", f"Job completed successfully. Found {len(findings)} findings.", {
                "findings_count": len(findings),
                "duration_seconds": (job.completed_at - job.started_at).total_seconds() if job.started_at and job.completed_at else None
            })
            
            await self._save_job_to_db(job)
            
            if user_id:
                try:
                    from app.services.notification import NotificationService, NotificationPriority
                    from app.core.database.database import init_db, _async_session_maker
                    
                    init_db()
                    if _async_session_maker:
                        async with _async_session_maker() as db:
                            try:
                                notification_service = NotificationService()
                                
                                has_critical = any(f.severity == "critical" for f in findings)
                                has_high = any(f.severity == "high" for f in findings)
                                
                                if has_critical:
                                    priority = NotificationPriority.HIGH
                                    severity = "high"
                                elif has_high:
                                    priority = NotificationPriority.MEDIUM
                                    severity = "medium"
                                else:
                                    priority = NotificationPriority.LOW
                                    severity = "low"
                                
                                await notification_service.create_notification(
                                    db=db,
                                    user_id=user_id,
                                    channel="scans",
                                    priority=priority,
                                    title=f"Scan Completed: {job.capability.value} on {job.target}",
                                    message=f"Scan completed with {len(findings)} finding(s).",
                                    severity=severity,
                                    metadata={
                                        "job_id": job.id,
                                        "capability": job.capability.value,
                                        "target": job.target,
                                        "findings_count": len(findings),
                                        "critical_count": sum(1 for f in findings if f.severity == "critical"),
                                        "high_count": sum(1 for f in findings if f.severity == "high"),
                                    }
                                )
                                await db.commit()
                            except Exception as e:
                                await db.rollback()
                                logger.warning(f"Failed to create notification for job completion {job.id}: {e}")
                except Exception as e:
                    logger.warning(f"Failed to initialize notification service for job completion: {e}")
            
            self._stats["completed_jobs"] += 1
            
            self._add_event("job_completed", {
                "job_id": job_id,
                "capability": job.capability.value,
                "findings_count": len(findings)
            })
            
            logger.info(f"Job {job_id} completed with {len(findings)} findings")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            error_message = str(e)
            job.error = error_message
            
            self._add_execution_log(job, "error", f"Job execution failed: {error_message}", {
                "error": error_message,
                "capability": job.capability.value,
                "target": job.target
            })
            
            self._update_job_status(job, JobStatus.FAILED)
            self._stats["failed_jobs"] += 1
            
            await self._save_job_to_db(job)
            
            self._add_event("job_failed", {
                "job_id": job_id,
                "capability": job.capability.value,
                "error": str(e)
            })
    
    async def _execute_capability(self, job: Job) -> List[Finding]:
        findings = []
        
        if job.capability == Capability.DARK_WEB_INTELLIGENCE:
            websocket = await self.get_websocket(job.id)
            if websocket:
                logger.info(f"[Orchestrator] WebSocket connection found for job {job.id}, using streaming execution")
                return await self._execute_darkweb_intelligence_stream(job)
        
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
                websocket = await self.get_websocket(job.id)
                if websocket:
                    logger.info(f"[Orchestrator] WebSocket connection found for job {job.id}, using streaming execution")
                    findings = await self._execute_darkweb_intelligence_stream(job)
                else:
                    logger.info(f"[Orchestrator] No WebSocket connection for job {job.id}, using regular execution")
                    findings = await self._execute_darkweb_intelligence(job)
                logger.info(f"[Orchestrator] Dark web intelligence execution completed for job {job.id}, returned {len(findings)} findings")
            elif job.capability == Capability.NETWORK_SECURITY:
                findings = self._generate_network_findings(job)
            elif job.capability == Capability.INVESTIGATION:
                findings = await self._execute_investigation(job)
        except Exception as e:
            logger.error(f"Collector error for {job.capability.value}: {e}")
            raise
        
        job.progress = 100
        return findings
    
    async def _execute_email_audit(self, job: Job) -> List[Finding]:
        findings = []
        
        job.progress = 10
        logger.info(f"Running comprehensive email audit for {job.target}")
        
        config = job.config or {}
        audit_config = {
            "check_bimi": config.get("check_bimi", True),
            "check_mta_sts": config.get("check_mta_sts", True),
            "check_dane": config.get("check_dane", True),
            "check_arc": config.get("check_arc", True),
            "check_subdomains": config.get("check_subdomains", True),
            "check_ptr": config.get("check_ptr", True),
            "check_dnssec": config.get("check_dnssec", True)
        }
        

        job.progress = 20
        results = await self._email_audit.audit(job.target, audit_config)
        
        job.progress = 50
        
        if config.get("run_bypass_tests", True):
            bypass_results = await self._bypass_tester.analyze_bypass_vulnerabilities(
                job.target, results
            )
            results["bypass_analysis"] = bypass_results
            
            for vuln in bypass_results.get("vulnerabilities", []):
                findings.append(Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.EMAIL_SECURITY,
                    severity=vuln.get("severity", "medium"),
                    title=vuln.get("title", "Bypass Vulnerability"),
                    description=vuln.get("description", ""),
                    evidence={
                        "type": vuln.get("type"),
                        "test_case": vuln.get("test_case"),
                        "attack_vector": vuln.get("attack_vector")
                    },
                    affected_assets=[job.target],
                    recommendations=[vuln.get("recommendation", "")],
                    discovered_at=datetime.now(),
                    risk_score=self._severity_to_score(vuln.get("severity", "medium"))
                ))
        
        job.progress = 70
        
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
        
        job.progress = 75
        
        if "bimi" in results:
            bimi = results.get("bimi", {})
            if not bimi.get("exists"):
                findings.append(Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.EMAIL_SECURITY,
                    severity="low",
                    title="No BIMI Record Found",
                    description="BIMI (Brand Indicators) not configured. Optional but recommended for brand protection.",
                    evidence={"bimi_exists": False},
                    affected_assets=[job.target],
                    recommendations=["Consider implementing BIMI for brand logo display in email clients"],
                    discovered_at=datetime.now(),
                    risk_score=20.0
                ))
        
        if "mta_sts" in results:
            mta_sts = results.get("mta_sts", {})
            if not mta_sts.get("exists"):
                findings.append(Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.EMAIL_SECURITY,
                    severity="low",
                    title="No MTA-STS Configuration",
                    description="MTA-STS not configured. Optional but recommended for secure email transport.",
                    evidence={"mta_sts_exists": False},
                    affected_assets=[job.target],
                    recommendations=["Consider implementing MTA-STS for secure SMTP transport"],
                    discovered_at=datetime.now(),
                    risk_score=25.0
                ))
            elif mta_sts.get("mode") == "none":
                findings.append(Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.EMAIL_SECURITY,
                    severity="medium",
                    title="MTA-STS Mode is 'none'",
                    description="MTA-STS is in testing mode. Upgrade to enforce mode for protection.",
                    evidence={"mta_sts_mode": "none"},
                    affected_assets=[job.target],
                    recommendations=["Upgrade MTA-STS mode to 'enforce'"],
                    discovered_at=datetime.now(),
                    risk_score=40.0
                ))
        
        if "subdomains" in results:
            subdomains = results.get("subdomains", {})
            for issue in subdomains.get("issues", []):
                findings.append(Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.EMAIL_SECURITY,
                    severity=issue.get("severity", "medium"),
                    title=f"Subdomain Issue: {issue.get('issue', 'Unknown')}",
                    description=issue.get("issue", ""),
                    evidence={"subdomain_analysis": subdomains},
                    affected_assets=[job.target],
                    recommendations=["Review and secure email configuration for all subdomains"],
                    discovered_at=datetime.now(),
                    risk_score=self._severity_to_score(issue.get("severity", "medium"))
                ))
        
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
        
        positive_scorer = get_positive_scorer()
        try:
            positive_indicators = positive_scorer.analyze_scan_results(
                Capability.EMAIL_SECURITY,
                [f.to_dict() for f in findings],
                results
            )
            
            user_id = job.metadata.get("user_id") if job.metadata else None
            if positive_indicators and user_id:
                try:
                    from app.core.database.database import init_db, _async_session_maker
                    from app.core.database.models import PositiveIndicator
                    
                    init_db()
                    if _async_session_maker:
                        async with _async_session_maker() as db:
                            try:
                                for indicator in positive_indicators:
                                    db_indicator = PositiveIndicator(
                                        id=indicator["id"],
                                        user_id=user_id,
                                        indicator_type=indicator["indicator_type"],
                                        category=indicator["category"],
                                        points_awarded=indicator["points_awarded"],
                                        description=indicator["description"],
                                        evidence=indicator.get("evidence", {}),
                                        target=job.target,
                                        created_at=datetime.now()
                                    )
                                    db.add(db_indicator)
                                await db.commit()
                                logger.info(f"Stored {len(positive_indicators)} positive indicators for {job.target}")
                            except Exception as e:
                                await db.rollback()
                                logger.warning(f"Failed to store positive indicators: {e}")
                except Exception as e:
                    logger.warning(f"Failed to initialize database for positive indicators: {e}")
        except Exception as e:
            logger.warning(f"Error generating positive indicators: {e}")
        
        job.progress = 100
        return findings
    
    async def _execute_exposure_discovery(self, job: Job) -> List[Finding]:
        
        execution_start = time.time()
        findings = []
        
        job.progress = 5
        logger.info(f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Starting comprehensive exposure discovery")
        logger.debug(f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Job created at {job.created_at.isoformat()}, priority: {job.priority.value}")
        

        def progress_callback(progress: int, message: str):
            job.progress = progress
            logger.debug(
                f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Progress update: {progress}% - {message} "
                f"(findings so far: {len(findings)})"
            )
            asyncio.create_task(self.send_websocket_message(job.id, {
                "type": "progress",
                "data": {
                    "progress": progress,
                    "message": message,
                    "findings_count": len(findings)
                },
                "timestamp": datetime.now().isoformat()
            }))
        
        recon_start = time.time()
        logger.debug(f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Calling WebRecon.discover_assets()")
        try:
            results = await self._web_recon.discover_assets(
                job.target,
                progress_callback=progress_callback
            )
            recon_time = time.time() - recon_start
            logger.info(
                f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] WebRecon completed in {recon_time:.3f}s - "
                f"subdomains: {len(results.get('subdomains', []))}, "
                f"endpoints: {len(results.get('endpoints', []))}, "
                f"files: {len(results.get('files', []))}, "
                f"source_code: {len(results.get('source_code', []))}, "
                f"admin_panels: {len(results.get('admin_panels', []))}, "
                f"configs: {len(results.get('configs', []))}"
            )
        except Exception as e:
            recon_time = time.time() - recon_start
            logger.error(
                f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] WebRecon failed after {recon_time:.3f}s: {e}",
                exc_info=True
            )
            raise
        

        async def create_and_stream_finding(
            category: str,
            severity: str,
            title: str,
            description: str,
            evidence: Dict[str, Any],
            affected_assets: List[str],
            recommendations: List[str],
            risk_score: float,
            source: str = "exposure_discovery"
        ):
            finding = Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.EXPOSURE_DISCOVERY,
                severity=severity,
                title=title,
                description=description,
                evidence={
                    **evidence,
                    "category": category,
                    "source": source
                },
                affected_assets=affected_assets,
                recommendations=recommendations,
                discovered_at=datetime.now(),
                risk_score=risk_score
            )
            findings.append(finding)
            job.add_finding(finding)
            
            logger.debug(
                f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Created finding: "
                f"id={finding.id}, category={category}, severity={severity}, "
                f"risk_score={risk_score}, source={source}, title={title[:50]}..."
            )
            
            try:
                await self.send_websocket_message(job.id, {
                    "type": "finding",
                    "data": finding.to_dict(),
                    "timestamp": datetime.now().isoformat()
                })
                logger.debug(f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Streamed finding {finding.id} via WebSocket")
            except Exception as e:
                logger.warning(f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Failed to stream finding {finding.id}: {e}")
            
            return finding
        
        subdomains = results.get("subdomains", [])
        subdomain_count = len(subdomains)
        logger.debug(f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processing {subdomain_count} subdomains")
        if subdomains:
            processed_count = 0
            for idx, subdomain in enumerate(subdomains[:50]):
                severity = "info"
                risk_score = 20.0
                if not subdomain.get("https"):
                    severity = "medium"
                    risk_score = 50.0
                
                logger.debug(
                    f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processing subdomain {idx+1}/{min(50, subdomain_count)}: "
                    f"{subdomain.get('subdomain')} (severity: {severity}, https: {subdomain.get('https')})"
                )
                
                await create_and_stream_finding(
                    category="subdomain",
                    severity=severity,
                    title=f"Subdomain Discovered: {subdomain.get('subdomain')}",
                    description=f"Active subdomain found at {subdomain.get('url', subdomain.get('subdomain'))}",
                    evidence={
                        "subdomain": subdomain.get("subdomain"),
                        "url": subdomain.get("url"),
                        "status": subdomain.get("status"),
                        "https": subdomain.get("https", True),
                        "server": subdomain.get("server", ""),
                        "title": subdomain.get("title", "")
                    },
                    affected_assets=[subdomain.get("subdomain")],
                    recommendations=["Verify subdomain ownership", "Ensure proper security configuration"],
                    risk_score=risk_score,
                    source="subdomain_enum"
                )
                processed_count += 1
            
            logger.info(
                f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processed {processed_count} subdomain findings "
                f"(limited from {subdomain_count} total)"
            )
        
        endpoints = results.get("endpoints", [])
        endpoint_count = len(endpoints)
        logger.debug(f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processing {endpoint_count} endpoints")
        endpoint_processed = 0
        for idx, endpoint in enumerate(endpoints):
            path = endpoint.get("path", "")
            status = endpoint.get("status", 0)
            url = endpoint.get("url", f"https://{job.target}{path}")
            was_redirected = endpoint.get("was_redirected", False)
            final_url = endpoint.get("final_url", url)
            
            if status == 404:
                logger.debug(
                    f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Skipping endpoint {path}: "
                    f"final status is 404 (not accessible)" + (f" (redirected from {url})" if was_redirected else "")
                )
                continue
            
            severity = "info"
            risk_score = 20.0
            category = "endpoint"
            title = f"Endpoint Discovered: {path}"
            recommendations = ["Review endpoint access controls"]
            
            if "/.git" in path:
                severity = "critical"
                risk_score = 90.0
                category = "source_code"
                title = "Git Repository Exposed"
                recommendations = ["Block access to .git directory immediately", "Check for exposed secrets in git history"]
            elif path == "/.env" or ".env" in path:
                severity = "critical"
                risk_score = 95.0
                category = "file"
                title = "Environment File Exposed"
                recommendations = ["Remove .env from web root", "Rotate all exposed credentials"]
            elif "/.svn" in path or "/.hg" in path or "/.bzr" in path or "/_darcs" in path:
                severity = "critical"
                risk_score = 85.0
                category = "source_code"
                title = f"Source Code Repository Exposed: {path}"
                recommendations = ["Block access to VCS directory immediately", "Check for exposed secrets"]
            elif any(admin in path.lower() for admin in ["/admin", "/wp-admin", "/administrator", "/cpanel"]):
                severity = "high"
                risk_score = 70.0
                category = "admin_panel"
                title = f"Admin Panel Exposed: {path}"
                recommendations = ["Restrict admin access by IP", "Implement strong authentication"]
            elif any(debug in path.lower() for debug in ["/phpinfo", "/server-status", "/info"]):
                severity = "high"
                risk_score = 65.0
                title = f"Server Information Exposed: {path}"
                recommendations = ["Remove debug endpoints from production", "Disable server-status"]
            elif any(sensitive in path.lower() for sensitive in ["/backup", "/config", "/database"]):
                severity = "high"
                risk_score = 75.0
                category = "config"
                title = f"Sensitive Directory Exposed: {path}"
                recommendations = ["Remove sensitive files from web root", "Implement access controls"]
            elif path in ["/robots.txt", "/sitemap.xml"]:
                severity = "info"
                risk_score = 10.0
            
            if status == 200 or (status >= 300 and status < 400):
                logger.debug(
                    f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processing endpoint {idx+1}/{endpoint_count}: "
                    f"{path} (status: {status}, severity: {severity}, category: {category}, redirected: {was_redirected})"
                )
                evidence = {
                    "url": url,
                    "path": path,
                    "status_code": status,
                    "content_length": endpoint.get("content_length", 0),
                    "content_type": endpoint.get("content_type", ""),
                    "server": endpoint.get("server", "")
                }
                if was_redirected:
                    evidence["final_url"] = final_url
                    evidence["was_redirected"] = True
                
                await create_and_stream_finding(
                    category=category,
                    severity=severity,
                    title=title,
                    description=f"Discovered accessible endpoint at {url}" + (f" (redirected to {final_url})" if was_redirected else ""),
                    evidence=evidence,
                    affected_assets=[url],
                    recommendations=recommendations,
                    risk_score=risk_score,
                    source="endpoint_scan"
                )
                endpoint_processed += 1
        
        logger.info(
            f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processed {endpoint_processed} endpoint findings "
            f"(from {endpoint_count} discovered)"
        )
        
        files = results.get("files", [])
        file_count = len(files)
        logger.debug(f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processing {file_count} sensitive files")
        file_processed = 0
        for idx, file_info in enumerate(files):
            path = file_info.get("path", "")
            url = file_info.get("url", "")
            
            severity = "high"
            risk_score = 80.0
            if ".env" in path or "config" in path.lower():
                severity = "critical"
                risk_score = 95.0
            elif any(ext in path for ext in [".key", ".pem", ".p12", ".pfx"]):
                severity = "critical"
                risk_score = 90.0
            elif ".sql" in path or ".db" in path:
                severity = "critical"
                risk_score = 85.0
            elif ".log" in path:
                severity = "medium"
                risk_score = 60.0
            
            logger.debug(
                f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processing file {idx+1}/{file_count}: "
                f"{path} (severity: {severity}, size: {file_info.get('content_length', 0)} bytes)"
            )
            await create_and_stream_finding(
                category="file",
                severity=severity,
                title=f"Sensitive File Exposed: {path}",
                description=f"Exposed sensitive file found at {url}",
                evidence={
                    "url": url,
                    "path": path,
                    "status": file_info.get("status"),
                    "content_length": file_info.get("content_length", 0),
                    "content_type": file_info.get("content_type", ""),
                    "file_type": file_info.get("file_type", ""),
                    "content_preview": file_info.get("content_preview", "")
                },
                affected_assets=[url],
                recommendations=["Remove file from web root", "Review file contents for exposed secrets", "Rotate any exposed credentials"],
                risk_score=risk_score,
                source="file_detection"
            )
            file_processed += 1
        
        logger.info(
            f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processed {file_processed} file findings "
            f"(from {file_count} discovered)"
        )
        
        source_code = results.get("source_code", [])
        source_count = len(source_code)
        logger.debug(f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processing {source_count} source code exposures")
        for idx, exposure in enumerate(source_code):
            logger.debug(
                f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processing source code exposure {idx+1}/{source_count}: "
                f"{exposure.get('type')} at {exposure.get('path')}"
            )
            await create_and_stream_finding(
                category="source_code",
                severity="critical",
                title=f"{exposure.get('type', 'VCS').upper()} Repository Exposed",
                description=f"Version control system exposed at {exposure.get('url')}",
                evidence={
                    "type": exposure.get("type"),
                    "url": exposure.get("url"),
                    "path": exposure.get("path"),
                    "status": exposure.get("status"),
                    "content_length": exposure.get("content_length", 0)
                },
                affected_assets=[exposure.get("url")],
                recommendations=["Block access to VCS directories", "Check git history for exposed secrets", "Rotate all credentials"],
                risk_score=90.0,
                source="source_code_detection"
            )
        
        admin_panels = results.get("admin_panels", [])
        admin_count = len(admin_panels)
        logger.debug(f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processing {admin_count} admin panels")
        admin_processed = 0
        for idx, panel in enumerate(admin_panels):
            status = panel.get("status", 0)
            url = panel.get("url", "")
            path = panel.get("path", "")
            panel_name = panel.get("name", "")
            
            if status == 404:
                logger.debug(
                    f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Skipping admin panel {panel_name} at {path}: "
                    f"final status is 404 (not accessible)" + 
                    (f" (redirected from {url})" if panel.get("was_redirected") else "")
                )
                continue
            
            logger.debug(
                f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processing admin panel {idx+1}/{admin_count}: "
                f"{panel_name} at {path}"
            )
            
            evidence = {
                "name": panel_name,
                "url": url,
                "path": path,
                "status": status,
                "is_login_page": panel.get("is_login_page", False)
            }
            if panel.get("was_redirected"):
                evidence["final_url"] = panel.get("final_url")
                evidence["was_redirected"] = True
            
            description = f"Admin panel found at {url}"
            if panel.get("was_redirected"):
                description += f" (redirected to {panel.get('final_url')})"
            
            await create_and_stream_finding(
                category="admin_panel",
                severity=panel.get("severity", "high"),
                title=f"Admin Panel Discovered: {panel_name}",
                description=description,
                evidence=evidence,
                affected_assets=[url],
                recommendations=["Restrict access by IP whitelist", "Implement strong authentication", "Enable 2FA"],
                risk_score=70.0 if panel.get("severity") == "high" else 50.0,
                source="admin_panel_discovery"
            )
            admin_processed += 1
        
        logger.info(
            f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processed {admin_processed} admin panel findings "
            f"(from {admin_count} discovered)"
        )
        
        configs = results.get("configs", [])
        config_count = len(configs)
        logger.debug(f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processing {config_count} configuration files")
        for idx, config in enumerate(configs):
            logger.debug(
                f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Processing config file {idx+1}/{config_count}: "
                f"{config.get('path')} ({config.get('content_length', 0)} bytes)"
            )
            await create_and_stream_finding(
                category="config",
                severity="critical",
                title=f"Configuration File Exposed: {config.get('path')}",
                description=f"Exposed configuration file found at {config.get('url')}",
                evidence={
                    "url": config.get("url"),
                    "path": config.get("path"),
                    "status": config.get("status"),
                    "content_length": config.get("content_length", 0),
                    "content_preview": config.get("content_preview", "")
                },
                affected_assets=[config.get("url")],
                recommendations=["Remove config files from web root", "Review for exposed secrets", "Rotate all credentials"],
                risk_score=95.0,
                source="config_detection"
            )
        
        dorks_count = results.get("dorks_generated", 0)
        if dorks_count > 0:
            all_dorks = self._web_recon.generate_dorks(job.target)
            await create_and_stream_finding(
                category="endpoint",
                severity="info",
                title=f"Generated {dorks_count} Search Dorks",
                description="Search engine dork queries have been generated for manual investigation",
                evidence={
                    "dork_count": dorks_count,
                    "sample_dorks": all_dorks
                },
                affected_assets=[job.target],
                recommendations=["Use these dorks in Google to find exposed information", "Review and remove any sensitive findings"],
                risk_score=15.0,
                source="dorking"
            )
        
        job.progress = 100
        progress_callback(100, "Discovery complete")
        
        execution_time = time.time() - execution_start
        logger.info(
            f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Exposure discovery completed in {execution_time:.3f}s - "
            f"total findings: {len(findings)} (subdomains: {subdomain_count}, endpoints: {endpoint_count}, "
            f"files: {file_count}, source_code: {source_count}, admin_panels: {admin_count}, configs: {config_count})"
        )
        logger.debug(
            f"[ExposureDiscovery] [job_id={job.id}] [target={job.target}] Finding breakdown by category: "
            f"{sum(1 for f in findings if f.evidence.get('category') == 'subdomain')} subdomains, "
            f"{sum(1 for f in findings if f.evidence.get('category') == 'endpoint')} endpoints, "
            f"{sum(1 for f in findings if f.evidence.get('category') == 'file')} files, "
            f"{sum(1 for f in findings if f.evidence.get('category') == 'source_code')} source_code, "
            f"{sum(1 for f in findings if f.evidence.get('category') == 'admin_panel')} admin_panels, "
            f"{sum(1 for f in findings if f.evidence.get('category') == 'config')} configs"
        )
        return findings
    
    async def _execute_infra_testing(self, job: Job) -> List[Finding]:
        findings = []
        
        job.progress = 20
        logger.info(f"Running infrastructure audit for {job.target}")
        
        config = job.config or {}
        audit_config = {
            "crlf": config.get("crlf", True),
            "pathTraversal": config.get("pathTraversal", True),
            "versionDetection": config.get("versionDetection", True),
            "cveLookup": config.get("cveLookup", True),
            "bypassTechniques": config.get("bypassTechniques", True),
            "purgeMethod": config.get("purgeMethod", True),
            "variableLeakage": config.get("variableLeakage", True),
            "hopByHopHeaders": config.get("hopByHopHeaders", True),
            "phpDetection": config.get("phpDetection", True),
            "cve20177529": config.get("cve20177529", True),
            "paths": config.get("paths", [])
        }
        
        results = await self._config_audit.audit(job.target, config=audit_config)
        
        job.progress = 80
        
        headers = results.get("headers_analysis", {})
        
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
        

        present_headers = headers.get("present", [])
        if present_headers:
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.INFRASTRUCTURE_TESTING,
                severity="info",
                title=f"{len(present_headers)} Security Headers Present",
                description="Some security headers are properly configured",
                evidence={
                    "headers": {h.get("header"): h.get("value") for h in present_headers}
                },
                affected_assets=[job.target],
                recommendations=["Continue monitoring security header configuration"],
                discovered_at=datetime.now(),
                risk_score=10.0
            ))
        
        vuln_findings = results.get("findings", [])
        for vuln in vuln_findings:
            vuln_recommendations = vuln.get("recommendations", [])
            if not vuln_recommendations:
                vuln_recommendations = ["Patch the identified vulnerability", "Review server configuration"]
            

            evidence = {
                "check": vuln.get("check"),
                "evidence": vuln.get("evidence"),
                "url": vuln.get("url")
            }
            

            if isinstance(vuln.get("evidence"), dict):
                evidence.update(vuln.get("evidence", {}))
            
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.INFRASTRUCTURE_TESTING,
                severity=vuln.get("severity", "medium"),
                title=vuln.get("description", "Vulnerability Detected"),
                description=f"Security vulnerability detected: {vuln.get('description')}",
                evidence=evidence,
                affected_assets=[vuln.get("url", job.target)],
                recommendations=vuln_recommendations,
                discovered_at=datetime.now(),
                risk_score=self._severity_to_score(vuln.get("severity", "medium"))
            ))
        

        server_info = results.get("server_info", {})
        if server_info.get("server") and server_info.get("server") != "unknown":

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
        
        scores = {
            "critical": 95.0,
            "high": 75.0,
            "medium": 50.0,
            "low": 25.0,
            "info": 10.0
        }
        return scores.get(severity, 50.0)
    
    def _get_spf_recommendations(self, spf: Dict[str, Any]) -> List[str]:
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

            self._darkwatch_instances.put(job.id, dark_watch)
            job.progress = 10
            

            logger.info(f"[DarkWeb] [job_id={job.id}] Starting URL discovery using engines...")
            discovery_start = time.time()
            job.progress = 15
            

            keywords = None
            if job.target:

                keywords = [kw.strip() for kw in job.target.split(',') if kw.strip()]
                logger.info(f"[DarkWeb] [job_id={job.id}] Extracted keywords: {keywords}")
            else:
                logger.warning(f"[DarkWeb] [job_id={job.id}] No target/keywords provided for discovery")
            
            try:
                if not keywords:
                    raise ValueError("No keywords provided. Keywords are required for dark web discovery.")
                
                logger.info(f"[DarkWeb] [job_id={job.id}] Calling _discover_urls_with_engines with keywords: {keywords}")
                urls = dark_watch._discover_urls_with_engines(keywords=keywords)
                
                logger.info(
                    f"[DarkWeb] [job_id={job.id}] _discover_urls_with_engines returned: "
                    f"type={type(urls).__name__}, length={len(urls) if urls else 0}"
                )
                
                discovery_time = time.time() - discovery_start
                logger.info(
                    f"[DarkWeb] [job_id={job.id}] URL discovery completed in {discovery_time:.2f}s - "
                    f"Found {len(urls)} URLs from engines"
                )
                
                if urls:
                    sample_urls = urls[:3] if len(urls) >= 3 else urls
                    logger.info(f"[DarkWeb] [job_id={job.id}] Sample URLs (first 3): {sample_urls}")
                else:
                    logger.warning(f"[DarkWeb] [job_id={job.id}] Discovery returned empty URL list")
                
                job.progress = 25
            except ValueError as e:

                discovery_time = time.time() - discovery_start
                logger.error(
                    f"[DarkWeb] [job_id={job.id}] URL discovery failed: {e}",
                    exc_info=True
                )
                finding = Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.DARK_WEB_INTELLIGENCE,
                    severity="info",
                    title="Dark Web Discovery: No Keywords Provided",
                    description=f"Dark web discovery requires keywords to search. No keywords were provided in the job target.",
                    evidence={"error": str(e), "target": job.target if job.target else "none"},
                    affected_assets=[],
                    recommendations=["Provide keywords in the job target field", "Keywords are required for OnionSearch discovery"],
                    discovered_at=datetime.now(),
                    risk_score=0.0
                )
                findings.append(finding)
                job.add_finding(finding)
                urls = []
                job.progress = 20
            except Exception as e:
                discovery_time = time.time() - discovery_start
                logger.error(
                    f"[DarkWeb] [job_id={job.id}] URL discovery failed after {discovery_time:.2f}s: {e}",
                    exc_info=True
                )
                urls = []  # Continue with empty list, will try database fallback
                job.progress = 20
            

            if not urls:
                logger.info(
                    f"[DarkWeb] [job_id={job.id}] No URLs discovered from engines (0 URLs), "
                    f"triggering database fallback..."
                )
                db_fallback_start = time.time()
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

                    db_records = db.select()
                    db_time = time.time() - db_start
                    logger.info(
                        f"[DarkWeb] [job_id={job.id}] Database query completed in {db_time:.2f}s - "
                        f"Retrieved {len(db_records)} records"
                    )
                    
                    if db_records:

                        urls = []
                        extraction_start = time.time()
                        for idx, record in enumerate(db_records[:10]):  # Limit to 10
                            url = record[2] if len(record) > 2 and record[2] else None
                            baseurl = record[4] if len(record) > 4 and record[4] else None
                            if url:
                                urls.append(url)
                                if idx < 3:
                                    logger.debug(f"[DarkWeb] [job_id={job.id}] Database record {idx}: extracted URL='{url[:100]}'")
                            elif baseurl:
                                urls.append(baseurl)
                                if idx < 3:
                                    logger.debug(f"[DarkWeb] [job_id={job.id}] Database record {idx}: extracted baseURL='{baseurl[:100]}'")
                        extraction_time = time.time() - extraction_start
                        logger.info(
                            f"[DarkWeb] [job_id={job.id}] Extracted {len(urls)} URLs from database "
                            f"in {extraction_time:.3f}s"
                        )
                        if urls:
                            sample_db_urls = urls[:3]
                            logger.debug(f"[DarkWeb] [job_id={job.id}] Sample database URLs: {sample_db_urls}")
                        job.progress = 25
                    else:
                        logger.warning(f"[DarkWeb] [job_id={job.id}] Database returned 0 records")
                except Exception as e:
                    db_fallback_time = time.time() - db_fallback_start
                    logger.warning(
                        f"[DarkWeb] [job_id={job.id}] Database fallback failed after {db_fallback_time:.2f}s: {e}",
                        exc_info=True
                    )
            

            if not urls:
                no_urls_time = time.time() - discovery_start
                logger.warning(
                    f"[DarkWeb] [job_id={job.id}] No URLs available for dark web intelligence collection "
                    f"after {no_urls_time:.2f}s. Creating 'no URLs discovered' finding."
                )
                finding = Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.DARK_WEB_INTELLIGENCE,
                    severity="info",
                    title="Dark Web Intelligence: No URLs Discovered",
                    description=f"Dark web intelligence collection completed but no URLs were discovered for target '{job.target}'. This may indicate: 1) Discovery engines need configuration, 2) No dark web activity found, 3) Network/proxy connectivity issues, 4) URL extraction issue (check logs for details).",
                    evidence={
                        "target": job.target, 
                        "status": "no_urls_discovered",
                        "discovery_time_seconds": round(no_urls_time, 2),
                        "keywords_used": keywords if keywords else []
                    },
                    affected_assets=[job.target] if job.target else [],
                    recommendations=["Check Tor proxy configuration", "Verify discovery engine settings", "Review network connectivity", "Check debug logs for URL extraction details"],
                    discovered_at=datetime.now(),
                    risk_score=10.0
                )
                findings.append(finding)

                job.add_findings(findings)
                logger.info(
                    f"[DarkWeb] [job_id={job.id}] Created 'no URLs discovered' finding and returning. "
                    f"Total findings: {len(findings)}"
                )
                return findings
            

            logger.info(f"[DarkWeb] [job_id={job.id}] About to store {len(urls)} URLs in metadata")
            if not job.metadata:
                job.metadata = {}
            job.metadata['discovered_urls'] = urls
            job.metadata['crawled_urls'] = []
            job.metadata['uncrawled_urls'] = urls.copy()
            logger.info(f"[DarkWeb] [job_id={job.id}] Stored {len(urls)} URLs in job metadata")
            

            job_config = job.config if job.config else {}
            max_urls_config = job_config.get("max_urls", settings.DARKWEB_DEFAULT_CRAWL_LIMIT)
            worker_threads_config = job_config.get("worker_threads", settings.DARKWEB_MAX_WORKERS)
            depth_config = job_config.get("depth", 1)
            

            crawl_limit = min(max_urls_config, len(urls))
            logger.info(
                f"[DarkWeb] [job_id={job.id}] Applying crawl limit: {crawl_limit} from {len(urls)} URLs "
                f"(config: max_urls={max_urls_config})"
            )
            logger.info(
                f"[DarkWeb] [job_id={job.id}] URL planning - Total available: {len(urls)}, "
                f"will crawl: {crawl_limit}, batch_size: {batch_size}, "
                f"worker_threads: {worker_threads_config}, depth: {depth_config}"
            )
            
            urls_to_crawl = urls[:crawl_limit]
            logger.info(f"[DarkWeb] [job_id={job.id}] Starting crawl of {len(urls_to_crawl)} URLs")
            max_workers = worker_threads_config
            crawl_timeout = settings.DARKWEB_CRAWL_TIMEOUT
            
            logger.info(
                f"[DarkWeb] [job_id={job.id}] Will process {len(urls_to_crawl)} URLs in parallel "
                f"with {max_workers} workers"
            )
            job.progress = 30
            

            def crawl_and_analyze_url(url: str) -> List[Finding]:
                
                url_findings = []
                url_start_time = time.time()
                
                try:
                    logger.info(
                        f"[DarkWeb] [job_id={job.id}] Starting parallel crawl of {url}"
                    )
                    site = dark_watch.crawl_site(url, depth=depth_config)
                    url_crawl_time = time.time() - url_start_time
                    logger.info(
                        f"[DarkWeb] [job_id={job.id}] Crawled {url} in {url_crawl_time:.2f}s - "
                        f"Title: {site.title[:50] if site.title else 'N/A'}, "
                        f"Entities: {len(site.extracted_entities)}, "
                        f"Keywords matched: {len(site.keywords_matched)}, "
                        f"Threat level: {site.threat_level.value}"
                    )
                    

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
                        url_findings.append(finding)
                        logger.debug(f"[DarkWeb] Created keyword match finding for {url}")
                    

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
                            url_findings.append(finding)
                            logger.debug(f"[DarkWeb] Created entity finding for {entity.entity_type} from {url}")
                    
                except Exception as e:
                    url_error_time = time.time() - url_start_time
                    logger.error(
                        f"[DarkWeb] [job_id={job.id}] Error crawling {url} after {url_error_time:.2f}s - "
                        f"Error type: {type(e).__name__}, Error: {e}",
                        exc_info=True
                    )
                
                return url_findings
            

            batch_progress_base = 30
            batch_progress_range = 60  # 30% to 90%
            total_urls = len(urls_to_crawl)
            completed_count = 0
            
            crawl_start_time = time.time()
            logger.info(f"[DarkWeb] [job_id={job.id}] ThreadPoolExecutor starting with {max_workers} workers for {len(urls_to_crawl)} URLs")
            with ThreadPoolExecutor(max_workers=max_workers) as executor:

                future_to_url = {
                    executor.submit(crawl_and_analyze_url, url): url 
                    for url in urls_to_crawl
                }
                

                for future in as_completed(future_to_url, timeout=crawl_timeout):
                    url = future_to_url[future]
                    try:
                        url_findings = future.result(timeout=120)  # Individual URL timeout
                        

                        if url_findings:
                            findings.extend(url_findings)
                            job.add_findings(url_findings)
                            logger.info(
                                f"[DarkWeb] [job_id={job.id}] Stored {len(url_findings)} findings from {url}. "
                                f"Total findings so far: {len(job.findings)}"
                            )
                        

                        completed_count += 1
                        progress = batch_progress_base + int((completed_count / total_urls) * batch_progress_range)
                        job.progress = progress
                        
                        logger.debug(
                            f"[DarkWeb] [job_id={job.id}] Progress: {completed_count}/{total_urls} URLs "
                            f"({progress}%)"
                        )
                        
                    except Exception as e:
                        logger.error(
                            f"[DarkWeb] [job_id={job.id}] Error processing result for {url}: {e}",
                            exc_info=True
                        )
            
            crawl_time = time.time() - crawl_start_time
            elapsed_total = time.time() - start_time
            avg_time_per_url = crawl_time / total_urls if total_urls > 0 else 0
            logger.info(
                f"[DarkWeb] [job_id={job.id}] Parallel crawl completed in {crawl_time:.2f}s "
                f"(avg {avg_time_per_url:.2f}s/URL) - Total findings: {len(findings)}, "
                f"Elapsed time: {elapsed_total:.2f}s"
            )
            

            if job.metadata:
                job.metadata['crawled_urls'] = urls_to_crawl.copy()
                uncrawled = [url for url in job.metadata.get('discovered_urls', []) if url not in urls_to_crawl]
                job.metadata['uncrawled_urls'] = uncrawled
            
            job.progress = 90
            

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
                job.add_finding(finding)
        
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(
                f"[DarkWeb] [job_id={job.id}] Error in dark web intelligence collection after {total_time:.2f}s - "
                f"Error type: {type(e).__name__}, Error: {e}",
                exc_info=True
            )
            job.progress = 95

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
            job.add_finding(finding)
        
        total_time = time.time() - start_time
        job.progress = 100
        

        if 'dark_watch' in locals() and dark_watch:
            self._darkwatch_instances.put(job.id, dark_watch)
            logger.debug(f"[DarkWeb] [job_id={job.id}] DarkWatch instance stored for API access")
        
        crawled_count = len(urls_to_crawl) if 'urls_to_crawl' in locals() else 0
        logger.info(
            f"[DarkWeb] [job_id={job.id}] Dark web intelligence collection completed in {total_time:.2f}s - "
            f"Total findings: {len(findings)}, URLs crawled: {crawled_count}, "
            f"Average time per finding: {total_time / len(findings) if findings else 0:.2f}s"
        )
        logger.info(f"[DarkWeb] [job_id={job.id}] Returning {len(findings)} findings from _execute_darkweb_intelligence")
        return findings
    
    async def _execute_darkweb_intelligence_stream(self, job: Job) -> List[Finding]:
        
        findings = []
        from app.config import settings
        from app.utils import check_tor_connectivity
        
        batch_size = settings.DARKWEB_BATCH_SIZE
        
        async def send_finding(finding: Finding):
            await self.send_websocket_message(job.id, {
                "type": "finding",
                "data": finding.to_dict(),
                "timestamp": datetime.now().isoformat()
            })
        

        async def send_progress(progress: int, message: str = ""):
            
            await self.send_websocket_message(job.id, {
                "type": "progress",
                "data": {"progress": progress, "message": message},
                "timestamp": datetime.now().isoformat()
            })
        
        try:
            logger.info(
                f"[DarkWeb] [job_id={job.id}] Starting streaming intelligence collection - "
                f"target={job.target}, batch_size={batch_size}"
            )
            start_time = time.time()
            job.progress = 5
            await send_progress(5, "Initializing dark web intelligence collection")
            

            logger.info(f"[DarkWeb] [job_id={job.id}] Checking Tor proxy connectivity...")
            tor_check_start = time.time()
            tor_status = check_tor_connectivity()
            tor_check_time = time.time() - tor_check_start
            if tor_status["status"] == "connected" and tor_status["is_tor"]:
                logger.info(
                    f"[DarkWeb] [job_id={job.id}] Tor proxy verified in {tor_check_time:.2f}s"
                )
            else:
                logger.warning(
                    f"[DarkWeb] [job_id={job.id}] Tor proxy check failed after {tor_check_time:.2f}s"
                )
            

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
            self._darkwatch_instances.put(job.id, dark_watch)
            job.progress = 10
            await send_progress(10, "DarkWatch collector initialized")
            

            keywords = None
            if job.target:
                keywords = [kw.strip() for kw in job.target.split(',') if kw.strip()]
                logger.info(f"[DarkWeb] [job_id={job.id}] Extracted keywords: {keywords}")
            else:
                logger.warning(f"[DarkWeb] [job_id={job.id}] No target/keywords provided for discovery")
            

            logger.info(f"[DarkWeb] [job_id={job.id}] Starting URL discovery using engines...")
            discovery_start = time.time()
            job.progress = 15
            await send_progress(15, "Starting URL discovery from engines")
            
            urls = []
            discovered_urls_by_engine = {}  # Track URLs per engine
            pending_engine_findings = []  # Collect findings from callback to send after discovery
            
            def on_engine_complete(engine_name: str, engine_urls: List[str]):
                discovered_urls_by_engine[engine_name] = engine_urls
                urls.extend(engine_urls)
                

                finding = Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.DARK_WEB_INTELLIGENCE,
                    severity="info",
                    title=f"Dark Web Discovery: Found {len(engine_urls)} URLs from {engine_name}",
                    description=f"Discovery engine '{engine_name}' discovered {len(engine_urls)} URLs for target '{job.target}'",
                    evidence={
                        "engine": engine_name,
                        "url_count": len(engine_urls),
                        "sample_urls": engine_urls[:5] if engine_urls else []
                    },
                    affected_assets=[job.target] if job.target else [],
                    recommendations=["Review discovered URLs", "Monitor for brand mentions"],
                    discovered_at=datetime.now(),
                    risk_score=20.0
                )
                findings.append(finding)
                job.add_finding(finding)

                pending_engine_findings.append(finding)
            
            try:
                if not keywords:
                    raise ValueError("No keywords provided. Keywords are required for dark web discovery.")
                
                logger.info(f"[DarkWeb] [job_id={job.id}] Calling _discover_urls_with_engines with keywords: {keywords}")

                all_urls = dark_watch._discover_urls_with_engines(keywords=keywords, on_engine_complete=on_engine_complete)
                

                unique_urls = list(set(urls + (all_urls if all_urls else [])))
                urls = unique_urls
                
                logger.info(
                    f"[DarkWeb] [job_id={job.id}] URL discovery completed - "
                    f"Found {len(urls)} URLs from engines"
                )
                

                for finding in pending_engine_findings:
                    await send_finding(finding)
                pending_engine_findings.clear()
                
                job.progress = 25
                await send_progress(25, f"Discovery complete: {len(urls)} URLs found")
                
            except ValueError as e:
                discovery_time = time.time() - discovery_start
                logger.error(
                    f"[DarkWeb] [job_id={job.id}] URL discovery failed: {e}",
                    exc_info=True
                )
                finding = Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.DARK_WEB_INTELLIGENCE,
                    severity="info",
                    title="Dark Web Discovery: No Keywords Provided",
                    description=f"Dark web discovery requires keywords to search. No keywords were provided in the job target.",
                    evidence={"error": str(e), "target": job.target if job.target else "none"},
                    affected_assets=[],
                    recommendations=["Provide keywords in the job target field", "Keywords are required for OnionSearch discovery"],
                    discovered_at=datetime.now(),
                    risk_score=0.0
                )
                findings.append(finding)
                job.add_finding(finding)
                await send_finding(finding)
                urls = []
                job.progress = 20
            except Exception as e:
                discovery_time = time.time() - discovery_start
                logger.error(
                    f"[DarkWeb] [job_id={job.id}] URL discovery failed after {discovery_time:.2f}s: {e}",
                    exc_info=True
                )
                urls = []
                job.progress = 20
            

            if not urls:
                logger.info(
                    f"[DarkWeb] [job_id={job.id}] No URLs discovered from engines, "
                    f"triggering database fallback..."
                )
                db_fallback_start = time.time()
                try:
                    from app.collectors.darkwatch_modules.crawlers.url_database import URLDatabase
                    db = URLDatabase(
                        dbpath=str(settings.DATA_DIR / settings.CRAWLER_DB_PATH),
                        dbname=settings.CRAWLER_DB_NAME
                    )
                    db_records = db.select()
                    
                    if db_records:
                        urls = []
                        for idx, record in enumerate(db_records[:10]):
                            url = record[2] if len(record) > 2 and record[2] else None
                            baseurl = record[4] if len(record) > 4 and record[4] else None
                            if url:
                                urls.append(url)
                            elif baseurl:
                                urls.append(baseurl)
                        job.progress = 25
                except Exception as e:
                    db_fallback_time = time.time() - db_fallback_start
                    logger.warning(
                        f"[DarkWeb] [job_id={job.id}] Database fallback failed after {db_fallback_time:.2f}s: {e}",
                        exc_info=True
                    )
            

            if not urls:
                no_urls_time = time.time() - discovery_start
                finding = Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.DARK_WEB_INTELLIGENCE,
                    severity="info",
                    title="Dark Web Intelligence: No URLs Discovered",
                    description=f"Dark web intelligence collection completed but no URLs were discovered for target '{job.target}'.",
                    evidence={
                        "target": job.target, 
                        "status": "no_urls_discovered",
                        "discovery_time_seconds": round(no_urls_time, 2),
                        "keywords_used": keywords if keywords else []
                    },
                    affected_assets=[job.target] if job.target else [],
                    recommendations=["Check Tor proxy configuration", "Verify discovery engine settings"],
                    discovered_at=datetime.now(),
                    risk_score=10.0
                )
                findings.append(finding)
                job.add_findings(findings)
                await send_finding(finding)
                return findings
            

            if not job.metadata:
                job.metadata = {}
            job.metadata['discovered_urls'] = urls
            job.metadata['crawled_urls'] = []
            job.metadata['uncrawled_urls'] = urls.copy()
            

            job_config = job.config if job.config else {}
            max_urls_config = job_config.get("max_urls", settings.DARKWEB_DEFAULT_CRAWL_LIMIT)
            worker_threads_config = job_config.get("worker_threads", settings.DARKWEB_MAX_WORKERS)
            depth_config = job_config.get("depth", 1)
            

            crawl_limit = min(max_urls_config, len(urls))
            urls_to_crawl = urls[:crawl_limit]
            logger.info(
                f"[DarkWeb] [job_id={job.id}] Starting crawl of {len(urls_to_crawl)} URLs "
                f"(config: max_urls={max_urls_config}, worker_threads={worker_threads_config}, depth={depth_config})"
            )
            max_workers = worker_threads_config
            crawl_timeout = settings.DARKWEB_CRAWL_TIMEOUT
            
            job.progress = 30
            await send_progress(30, f"Starting crawl of {len(urls_to_crawl)} URLs")
            

            def crawl_and_analyze_url(url: str) -> List[Finding]:
                
                url_findings = []
                url_start_time = time.time()
                
                try:
                    logger.info(
                        f"[DarkWeb] [job_id={job.id}] Starting parallel crawl of {url}"
                    )
                    site = dark_watch.crawl_site(url, depth=depth_config)
                    url_crawl_time = time.time() - url_start_time
                    logger.info(
                        f"[DarkWeb] [job_id={job.id}] Crawled {url} in {url_crawl_time:.2f}s"
                    )
                    

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
                        url_findings.append(finding)
                    

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
                            url_findings.append(finding)
                    
                except Exception as e:
                    url_error_time = time.time() - url_start_time
                    logger.error(
                        f"[DarkWeb] [job_id={job.id}] Error crawling {url} after {url_error_time:.2f}s: {e}",
                        exc_info=True
                    )
                
                return url_findings
            

            batch_progress_base = 30
            batch_progress_range = 60
            total_urls = len(urls_to_crawl)
            completed_count = 0
            
            crawl_start_time = time.time()
            logger.info(f"[DarkWeb] [job_id={job.id}] ThreadPoolExecutor starting with {max_workers} workers")
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_url = {
                    executor.submit(crawl_and_analyze_url, url): url 
                    for url in urls_to_crawl
                }
                

                for future in as_completed(future_to_url, timeout=crawl_timeout):
                    url = future_to_url[future]
                    try:
                        url_findings = future.result(timeout=120)
                        
                        if url_findings:
                            findings.extend(url_findings)
                            job.add_findings(url_findings)
                            

                            for finding in url_findings:
                                await send_finding(finding)
                            
                            logger.info(
                                f"[DarkWeb] [job_id={job.id}] Stored and sent {len(url_findings)} findings from {url}"
                            )
                        

                        completed_count += 1
                        progress = batch_progress_base + int((completed_count / total_urls) * batch_progress_range)
                        job.progress = progress
                        await send_progress(progress, f"Crawled {completed_count}/{total_urls} URLs")
                        
                    except Exception as e:
                        logger.error(
                            f"[DarkWeb] [job_id={job.id}] Error processing result for {url}: {e}",
                            exc_info=True
                        )
            
            crawl_time = time.time() - crawl_start_time
            logger.info(
                f"[DarkWeb] [job_id={job.id}] Parallel crawl completed in {crawl_time:.2f}s - "
                f"Total findings: {len(findings)}"
            )
            

            if job.metadata:
                job.metadata['crawled_urls'] = urls_to_crawl.copy()
                uncrawled = [url for url in job.metadata.get('discovered_urls', []) if url not in urls_to_crawl]
                job.metadata['uncrawled_urls'] = uncrawled
            
            job.progress = 90
            await send_progress(90, "Crawl phase complete")
            

            if not findings and urls:
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
                job.add_finding(finding)
                await send_finding(finding)
        
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(
                f"[DarkWeb] [job_id={job.id}] Error in dark web intelligence collection after {total_time:.2f}s: {e}",
                exc_info=True
            )
            job.progress = 95
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
            job.add_finding(finding)
            await send_finding(finding)
            await self.send_websocket_message(job.id, {
                "type": "error",
                "data": {"error": str(e)},
                "timestamp": datetime.now().isoformat()
            })
        
        total_time = time.time() - start_time
        job.progress = 100
        

        if 'dark_watch' in locals() and dark_watch:
            self._darkwatch_instances.put(job.id, dark_watch)
        

        await self.send_websocket_message(job.id, {
            "type": "complete",
            "data": {
                "total_findings": len(findings),
                "urls_crawled": len(urls_to_crawl) if 'urls_to_crawl' in locals() else 0,
                "total_time_seconds": round(total_time, 2)
            },
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(
            f"[DarkWeb] [job_id={job.id}] Streaming dark web intelligence collection completed in {total_time:.2f}s - "
            f"Total findings: {len(findings)}"
        )
        return findings
    
    def _map_threat_to_severity(self, threat_level: str) -> str:
        mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "info": "info"
        }
        return mapping.get(threat_level.lower(), "info")
    
    def _generate_exposure_findings(self, job: Job) -> List[Finding]:
        
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
    
    def _generate_network_findings(self, job: Job) -> List[Finding]:
        
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
    
    async def _execute_investigation(self, job: Job) -> List[Finding]:
        
        findings = []
        job.progress = 10
        
        try:
            config = job.config or {}
            target = job.target
            

            if not target.startswith(('http://', 'https://')):
                target = f"https://{target}"
            
            logger.info(f"[Orchestrator] Starting investigation for {target}")
            

            browser_service = get_browser_capture_service()
            domain_tree = DomainTree()
            visual_similarity = get_visual_similarity_service()
            

            await browser_service.initialize()
            job.progress = 20
            

            capture_options = {
                'wait_until': 'networkidle',
                'timeout': 30000,
                'full_page': config.get('capture_screenshot', True),
            }
            
            logger.info(f"[Orchestrator] Capturing page: {target}")
            capture_result = await browser_service.capture_page(target, capture_options)
            job.progress = 40
            

            if not hasattr(job, 'metadata'):
                job.metadata = {}
            job.metadata['capture'] = {
                'screenshot': capture_result.get('screenshot'),
                'har': capture_result.get('har'),
                'final_url': capture_result.get('final_url'),
                'title': capture_result.get('title'),
                'redirect_chain': capture_result.get('redirect_chain', []),
                'capture_time': capture_result.get('capture_time')
            }
            

            if config.get('map_resources', True) and capture_result.get('har'):
                logger.info(f"[Orchestrator] Building domain tree from HAR")
                domain_result = await domain_tree.capture_url_async(
                    target,
                    har_data=capture_result.get('har')
                )
                job.progress = 60
                

                domain_tree_graph = domain_tree.get_capture_graph(domain_result.capture_id)
                if 'capture' in job.metadata:
                    job.metadata['capture']['domain_tree'] = domain_tree_graph
                    job.metadata['capture']['domain_tree_summary'] = {
                        'total_domains': len(domain_result.unique_domains),
                        'third_party_count': len(domain_result.third_party_domains),
                        'tracker_count': len(domain_result.trackers),
                        'risk_score': domain_result.risk_assessment.get('score', 0),
                        'risk_level': domain_result.risk_assessment.get('level', 'low')
                    }
                
                findings.extend(self._findings_from_domain_tree(domain_result, target))
            

            if config.get('visual_similarity', False) and capture_result.get('screenshot'):
                logger.info(f"[Orchestrator] Running visual similarity analysis")
                screenshot_data = base64.b64decode(capture_result['screenshot'])
                similarity_matches = visual_similarity.compare_against_references(
                    screenshot_data,
                    threshold=70.0
                )
                
                if similarity_matches:
                    findings.append(Finding(
                        id=f"find-{uuid.uuid4().hex[:8]}",
                        capability=Capability.INVESTIGATION,
                        severity="high",
                        title="Visual Similarity to Known Sites Detected",
                        description=f"Page screenshot matches {len(similarity_matches)} known reference(s) with >70% similarity",
                        evidence={
                            "matches": similarity_matches,
                            "top_match": similarity_matches[0] if similarity_matches else None
                        },
                        affected_assets=[target],
                        recommendations=[
                            "Review visual similarity matches for potential phishing/clone sites",
                            "Compare page structure and content with known legitimate sites"
                        ],
                        discovered_at=datetime.now(),
                        risk_score=75.0
                    ))
                job.progress = 75
            

            if config.get('cross_reference_darkweb', False):
                logger.info(f"[Orchestrator] Cross-referencing with dark web intelligence")
                darkweb_findings = self._cross_reference_darkweb(target)
                findings.extend(darkweb_findings)
                job.progress = 85
            

            if config.get('check_reputation', True):
                logger.info(f"[Orchestrator] Checking domain reputation")
                reputation_findings = self._check_domain_reputation(target)
                findings.extend(reputation_findings)
                job.progress = 90
            

            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.INVESTIGATION,
                severity="info",
                title="Investigation Complete",
                description=f"Comprehensive investigation of {target} completed with {len(findings)} findings",
                evidence={
                    "total_findings": len(findings),
                    "screenshot_captured": config.get('capture_screenshot', True),
                    "har_available": bool(capture_result.get('har')),
                    "domain_tree_built": config.get('map_resources', True),
                    "final_url": capture_result.get('final_url', target),
                    "redirect_count": len(capture_result.get('redirect_chain', [])) - 1
                },
                affected_assets=[target],
                recommendations=["Review all findings for security implications"],
                discovered_at=datetime.now(),
                risk_score=0.0
            ))
            
            logger.info(f"[Orchestrator] Investigation completed with {len(findings)} findings")
            return findings
            
        except Exception as e:
            logger.error(f"[Orchestrator] Investigation error: {e}", exc_info=True)

            return [
                Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.INVESTIGATION,
                    severity="high",
                    title="Investigation Failed",
                    description=f"Error during investigation: {str(e)}",
                    evidence={"error": str(e)},
                    affected_assets=[job.target],
                    recommendations=["Check target URL accessibility", "Verify network connectivity"],
                    discovered_at=datetime.now(),
                    risk_score=0.0
                )
            ]
    
    def _findings_from_domain_tree(self, domain_result, target: str) -> List[Finding]:
        findings = []
        

        if domain_result.trackers:
            tracker_count = sum(len(urls) for urls in domain_result.trackers.values())
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.INVESTIGATION,
                severity="medium",
                title=f"{len(domain_result.trackers)} Tracking Services Detected",
                description=f"Page loads {tracker_count} requests from {len(domain_result.trackers)} tracking services",
                evidence={
                    "trackers": list(domain_result.trackers.keys()),
                    "tracker_count": len(domain_result.trackers),
                    "total_tracking_requests": tracker_count
                },
                affected_assets=[target],
                recommendations=[
                    "Review privacy implications of tracking services",
                    "Consider implementing tracking protection",
                    "Audit data collection practices"
                ],
                discovered_at=datetime.now(),
                risk_score=40.0
            ))
        

        if domain_result.third_party_domains:
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.INVESTIGATION,
                severity="low" if len(domain_result.third_party_domains) < 10 else "medium",
                title=f"{len(domain_result.third_party_domains)} Third-Party Domains Detected",
                description=f"Page loads resources from {len(domain_result.third_party_domains)} third-party domains",
                evidence={
                    "third_party_domains": list(domain_result.third_party_domains),
                    "third_party_count": len(domain_result.third_party_domains),
                    "total_domains": len(domain_result.unique_domains)
                },
                affected_assets=[target],
                recommendations=[
                    "Review third-party dependencies for security risks",
                    "Implement Subresource Integrity (SRI) for third-party scripts",
                    "Monitor third-party services for security updates"
                ],
                discovered_at=datetime.now(),
                risk_score=30.0 if len(domain_result.third_party_domains) < 10 else 50.0
            ))
        

        risk_score = domain_result.risk_assessment.get('score', 0)
        if risk_score > 50:
            findings.append(Finding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                capability=Capability.INVESTIGATION,
                severity="high" if risk_score > 70 else "medium",
                title=f"High Risk Score Detected ({risk_score}/100)",
                description=f"Domain analysis indicates elevated risk level: {domain_result.risk_assessment.get('level', 'unknown')}",
                evidence={
                    "risk_score": risk_score,
                    "risk_level": domain_result.risk_assessment.get('level'),
                    "risk_factors": domain_result.risk_assessment.get('factors', []),
                    "third_party_count": domain_result.risk_assessment.get('third_party_count', 0),
                    "tracker_count": domain_result.risk_assessment.get('tracker_count', 0)
                },
                affected_assets=[target],
                recommendations=[
                    "Review risk factors in detail",
                    "Implement security controls to mitigate identified risks",
                    "Consider additional security monitoring"
                ],
                discovered_at=datetime.now(),
                risk_score=float(risk_score)
            ))
        
        return findings
    
    def _cross_reference_darkweb(self, target: str) -> List[Finding]:
        
        findings = []
        
        try:

            from urllib.parse import urlparse
            parsed = urlparse(target if target.startswith('http') else f'https://{target}')
            domain = parsed.netloc or target.split('/')[0]
            

            darkweb_findings = [
                f for f in self._all_findings
                if f.capability == Capability.DARK_WEB_INTELLIGENCE
                and domain.lower() in f.evidence.get('domain', '').lower()
            ]
            
            if darkweb_findings:
                findings.append(Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.INVESTIGATION,
                    severity="critical",
                    title="Dark Web Mention Detected",
                    description=f"Domain {domain} found in {len(darkweb_findings)} dark web intelligence finding(s)",
                    evidence={
                        "domain": domain,
                        "darkweb_findings_count": len(darkweb_findings),
                        "related_findings": [f.id for f in darkweb_findings[:5]]  # Limit to 5
                    },
                    affected_assets=[target],
                    recommendations=[
                        "Immediately investigate dark web mentions",
                        "Review related dark web intelligence findings",
                        "Consider incident response procedures"
                    ],
                    discovered_at=datetime.now(),
                    risk_score=90.0
                ))
        except Exception as e:
            logger.error(f"[Orchestrator] Error in dark web cross-reference: {e}")
        
        return findings
    
    def _check_domain_reputation(self, target: str) -> List[Finding]:
        findings = []
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(target if target.startswith('http') else f'https://{target}')
            domain = parsed.netloc or target.split('/')[0]
            

            suspicious_indicators = []
            

            suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz']
            if any(domain.endswith(tld) for tld in suspicious_tlds):
                suspicious_indicators.append("Suspicious TLD detected")
            

            common_domains = ['google', 'facebook', 'microsoft', 'apple', 'amazon']
            domain_lower = domain.lower()
            for common in common_domains:
                if common in domain_lower and domain_lower != common:
                    suspicious_indicators.append(f"Potential typosquatting: {common}")
                    break
            
            if suspicious_indicators:
                findings.append(Finding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    capability=Capability.INVESTIGATION,
                    severity="medium",
                    title="Reputation Concerns Detected",
                    description=f"Domain reputation check identified {len(suspicious_indicators)} concern(s)",
                    evidence={
                        "domain": domain,
                        "indicators": suspicious_indicators
                    },
                    affected_assets=[target],
                    recommendations=[
                        "Verify domain legitimacy through additional sources",
                        "Check domain registration information",
                        "Review domain history and ownership"
                    ],
                    discovered_at=datetime.now(),
                    risk_score=45.0
                ))
        except Exception as e:
            logger.error(f"[Orchestrator] Error in reputation check: {e}")
        
        return findings
    
    def _add_execution_log(self, job: Job, level: str, message: str, data: Optional[Dict[str, Any]] = None):
        from datetime import datetime
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        if data:
            log_entry["data"] = data
        job.execution_logs.append(log_entry)
    
    def _update_job_status(self, job: Job, new_status: JobStatus):
        old_status = job.status
        

        status_messages = {
            JobStatus.PENDING: "Job created and queued",
            JobStatus.QUEUED: "Job queued for execution",
            JobStatus.RUNNING: "Job execution started",
            JobStatus.COMPLETED: "Job completed successfully",
            JobStatus.FAILED: "Job execution failed",
            JobStatus.CANCELLED: "Job cancelled"
        }
        
        if old_status != new_status:
            message = status_messages.get(new_status, f"Job status changed to {new_status.value}")
            level = "info"
            if new_status == JobStatus.FAILED:
                level = "error"
            elif new_status == JobStatus.COMPLETED:
                level = "info"
            elif new_status == JobStatus.RUNNING:
                level = "info"
            
            self._add_execution_log(job, level, message, {
                "old_status": old_status.value,
                "new_status": new_status.value,
                "capability": job.capability.value,
                "target": job.target
            })
        

        old_status_jobs = self._jobs_by_status.get(old_status.value) or []
        if job.id in old_status_jobs:
            old_status_jobs.remove(job.id)
        self._jobs_by_status.put(old_status.value, old_status_jobs)
        

        new_status_jobs = self._jobs_by_status.get(new_status.value) or []
        new_status_jobs.append(job.id)
        self._jobs_by_status.put(new_status.value, new_status_jobs)
        
        job.status = new_status
    
    def _add_event(self, event_type: str, data: Dict[str, Any]):
        
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        

        self._events.insert(0, event)
        

        if len(self._events) > self._max_events:
            self._events = self._events[:self._max_events]
    
    def get_job(self, job_id: str) -> Optional[Job]:
        

        job = self._jobs.get(job_id)
        if job:
            return job
        
        return None
    
    def get_darkwatch_instance(self, job_id: str):
        
        from app.collectors.dark_watch import DarkWatch
        instance = self._darkwatch_instances.get(job_id)
        if instance:
            return instance
        

        job = self.get_job(job_id)
        if job and job.capability == Capability.DARK_WEB_INTELLIGENCE:


            logger.warning(f"[Orchestrator] DarkWatch instance not found for job {job_id}, cannot access advanced features")
        
        return None
    
    def get_jobs(
        self,
        capability: Optional[Capability] = None,
        status: Optional[JobStatus] = None,
        limit: int = 50
    ) -> List[Job]:
        
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

                if capability and job.capability != capability:
                    continue
                if status and job.status != status:
                    continue
                jobs.append(job)
        

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
        

        results.sort(key=lambda f: f.risk_score, reverse=True)
        
        return results
    
    def get_critical_findings(self, limit: int = 10) -> List[Finding]:
        
        critical = [f for f in self._all_findings if f.severity in ["critical", "high"]]
        critical.sort(key=lambda f: f.risk_score, reverse=True)
        return critical[:limit]
    
    def get_findings_for_target(self, target: str) -> List[Finding]:
        
        return [f for f in self._all_findings if f.target == target]
    
    async def quick_scan(self, domain: str) -> Dict[str, Any]:
        
        started_at = datetime.now()
        

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
        
        return self._stats
    
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        
        return self._events[:limit]



_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

