"""
CyberNexus Orchestration Engine

Maps user-facing capabilities to underlying tool services.
Users interact with capabilities (what they want to achieve),
not with specific tools (how it's done).

Capabilities:
1. Exposure Discovery → oxdork + lookyloo
2. Dark Web Intelligence → freshonions + VigilantOnion
3. Email Security Assessment → espoofer
4. Infrastructure Testing → nginxpwner
5. Authentication Testing → RDPassSpray
6. Network Security → Tunna
7. Investigation Mode → lookyloo + correlation

Tools are completely invisible to the user.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from loguru import logger

from app.core.dsa import HashMap, Graph, MinHeap, CircularBuffer


class Capability(str, Enum):
    """User-facing security capabilities"""
    EXPOSURE_DISCOVERY = "exposure_discovery"
    DARK_WEB_INTEL = "dark_web_intelligence"
    EMAIL_SECURITY = "email_security"
    INFRASTRUCTURE = "infrastructure_testing"
    AUTH_TESTING = "authentication_testing"
    NETWORK_SECURITY = "network_security"
    INVESTIGATION = "investigation"


class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(int, Enum):
    """Job priority levels (lower = higher priority)"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class Finding:
    """A security finding from any capability"""
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
    source_tool: str = ""  # Hidden from user, used internally
    
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
            "risk_score": self.risk_score
        }


@dataclass
class Job:
    """A capability execution job"""
    id: str
    capability: Capability
    target: str  # domain, URL, IP, etc.
    config: Dict[str, Any]
    priority: JobPriority
    status: JobStatus
    progress: int  # 0-100
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    findings: List[Finding] = field(default_factory=list)
    error: Optional[str] = None
    
    def __lt__(self, other):
        return self.priority.value < other.priority.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "capability": self.capability.value,
            "target": self.target,
            "status": self.status.value,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "findings_count": len(self.findings),
            "error": self.error
        }


@dataclass
class CapabilityConfig:
    """Configuration for a capability"""
    capability: Capability
    name: str
    description: str
    question: str  # User-facing question this answers
    icon: str
    tools: List[str]  # Internal tool mappings (hidden)
    default_config: Dict[str, Any]
    supports_scheduling: bool = True
    requires_tor: bool = False


class Orchestrator:
    """
    Central orchestration engine for CyberNexus.
    
    Manages capability execution, job scheduling, and result aggregation.
    Completely abstracts underlying tools from users.
    """
    
    # Capability configurations
    CAPABILITIES: Dict[Capability, CapabilityConfig] = {
        Capability.EXPOSURE_DISCOVERY: CapabilityConfig(
            capability=Capability.EXPOSURE_DISCOVERY,
            name="Exposure Discovery",
            description="Discover what attackers can find about your organization online",
            question="What can attackers find about us online?",
            icon="search",
            tools=["web_recon", "domain_tree"],  # oxdork + lookyloo internally
            default_config={"depth": 2, "include_subdomains": True},
            supports_scheduling=True,
            requires_tor=False
        ),
        Capability.DARK_WEB_INTEL: CapabilityConfig(
            capability=Capability.DARK_WEB_INTEL,
            name="Dark Web Intelligence",
            description="Monitor dark web for mentions, leaks, and threats targeting you",
            question="Are we mentioned on the dark web?",
            icon="globe",
            tools=["dark_watch", "keyword_monitor"],  # freshonions + VigilantOnion
            default_config={"crawl_depth": 2, "monitor_keywords": True},
            supports_scheduling=True,
            requires_tor=True
        ),
        Capability.EMAIL_SECURITY: CapabilityConfig(
            capability=Capability.EMAIL_SECURITY,
            name="Email Security Assessment",
            description="Test if your email can be spoofed and identify authentication gaps",
            question="Can our email be spoofed?",
            icon="mail",
            tools=["email_audit"],  # espoofer internally
            default_config={"check_spf": True, "check_dkim": True, "check_dmarc": True},
            supports_scheduling=True,
            requires_tor=False
        ),
        Capability.INFRASTRUCTURE: CapabilityConfig(
            capability=Capability.INFRASTRUCTURE,
            name="Infrastructure Testing",
            description="Scan for server misconfigurations and vulnerabilities",
            question="Are our servers misconfigured?",
            icon="server",
            tools=["config_audit"],  # nginxpwner internally
            default_config={"check_crlf": True, "check_traversal": True, "check_cve": True},
            supports_scheduling=True,
            requires_tor=False
        ),
        Capability.AUTH_TESTING: CapabilityConfig(
            capability=Capability.AUTH_TESTING,
            name="Authentication Testing",
            description="Test credential strength and identify weak authentication",
            question="Are our credentials weak?",
            icon="key",
            tools=["credential_analyzer"],  # RDPassSpray internally
            default_config={"respect_lockout": True, "throttle_ms": 1000},
            supports_scheduling=False,  # Requires explicit execution
            requires_tor=False
        ),
        Capability.NETWORK_SECURITY: CapabilityConfig(
            capability=Capability.NETWORK_SECURITY,
            name="Network Security",
            description="Detect tunneling attempts and covert channels",
            question="Can attackers tunnel into our network?",
            icon="network",
            tools=["tunnel_detector"],  # Tunna internally
            default_config={"detection_mode": True, "monitor_duration": 3600},
            supports_scheduling=True,
            requires_tor=False
        ),
        Capability.INVESTIGATION: CapabilityConfig(
            capability=Capability.INVESTIGATION,
            name="Investigation Mode",
            description="Deep analysis of suspicious URLs, domains, or indicators",
            question="Analyze this suspicious target",
            icon="microscope",
            tools=["domain_tree", "web_recon", "dark_watch"],  # Multiple tools
            default_config={"full_capture": True, "cross_reference": True},
            supports_scheduling=False,
            requires_tor=False
        ),
    }
    
    def __init__(self):
        """Initialize the orchestrator"""
        # Job management
        self._jobs = HashMap()  # job_id -> Job
        self._job_queue = MinHeap()  # Priority queue for pending jobs
        self._active_jobs: Dict[str, Job] = {}
        
        # Results storage
        self._findings = HashMap()  # finding_id -> Finding
        self._findings_by_capability = HashMap()  # capability -> [finding_ids]
        self._findings_by_target = HashMap()  # target -> [finding_ids]
        
        # Entity correlation graph
        self._correlation_graph = Graph(directed=False)
        
        # Event stream for real-time updates
        self._event_buffer = CircularBuffer(capacity=1000)
        
        # Tool executors (will be injected)
        self._tool_executors: Dict[str, Callable] = {}
        
        # Statistics
        self._stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "total_findings": 0,
            "findings_by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            }
        }
        
        logger.info("Orchestrator initialized")
    
    def register_tool_executor(self, tool_name: str, executor: Callable):
        """Register a tool executor function"""
        self._tool_executors[tool_name] = executor
        logger.debug(f"Registered tool executor: {tool_name}")
    
    def get_capabilities(self) -> List[Dict[str, Any]]:
        """Get all available capabilities (user-facing)"""
        return [
            {
                "id": cap.capability.value,
                "name": cap.name,
                "description": cap.description,
                "question": cap.question,
                "icon": cap.icon,
                "supports_scheduling": cap.supports_scheduling,
                "requires_tor": cap.requires_tor,
                "default_config": cap.default_config
            }
            for cap in self.CAPABILITIES.values()
        ]
    
    def get_capability(self, capability_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific capability by ID"""
        try:
            cap = Capability(capability_id)
            config = self.CAPABILITIES.get(cap)
            if config:
                return {
                    "id": config.capability.value,
                    "name": config.name,
                    "description": config.description,
                    "question": config.question,
                    "icon": config.icon,
                    "supports_scheduling": config.supports_scheduling,
                    "requires_tor": config.requires_tor,
                    "default_config": config.default_config
                }
        except ValueError:
            pass
        return None
    
    async def create_job(
        self,
        capability: Capability,
        target: str,
        config: Optional[Dict[str, Any]] = None,
        priority: JobPriority = JobPriority.NORMAL
    ) -> Job:
        """Create a new capability execution job"""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        cap_config = self.CAPABILITIES.get(capability)
        
        if not cap_config:
            raise ValueError(f"Unknown capability: {capability}")
        
        # Merge with default config
        final_config = {**cap_config.default_config, **(config or {})}
        
        job = Job(
            id=job_id,
            capability=capability,
            target=target,
            config=final_config,
            priority=priority,
            status=JobStatus.PENDING,
            progress=0,
            created_at=datetime.now()
        )
        
        self._jobs.put(job_id, job)
        self._job_queue.push(job)
        self._stats["total_jobs"] += 1
        
        # Emit event
        self._emit_event("job_created", {
            "job_id": job_id,
            "capability": capability.value,
            "target": target
        })
        
        logger.info(f"Created job {job_id} for {capability.value} on {target}")
        return job
    
    async def execute_job(self, job_id: str) -> Job:
        """Execute a job immediately"""
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        if job.status != JobStatus.PENDING:
            raise ValueError(f"Job {job_id} is not in pending state")
        
        # Start execution
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        self._active_jobs[job_id] = job
        
        self._emit_event("job_started", {"job_id": job_id})
        
        try:
            # Get capability configuration
            cap_config = self.CAPABILITIES.get(job.capability)
            if not cap_config:
                raise ValueError(f"Unknown capability: {job.capability}")
            
            # Execute each tool for this capability
            all_findings = []
            tool_count = len(cap_config.tools)
            
            for i, tool_name in enumerate(cap_config.tools):
                executor = self._tool_executors.get(tool_name)
                
                if executor:
                    try:
                        # Execute tool
                        tool_findings = await executor(job.target, job.config)
                        
                        # Convert to Finding objects
                        for tf in tool_findings:
                            finding = self._create_finding(
                                capability=job.capability,
                                tool_data=tf,
                                source_tool=tool_name
                            )
                            all_findings.append(finding)
                            self._store_finding(finding, job.target)
                        
                    except Exception as e:
                        logger.error(f"Tool {tool_name} failed: {e}")
                
                # Update progress
                job.progress = int(((i + 1) / tool_count) * 100)
                self._emit_event("job_progress", {
                    "job_id": job_id,
                    "progress": job.progress
                })
            
            # Job completed
            job.findings = all_findings
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.progress = 100
            
            self._stats["completed_jobs"] += 1
            
            self._emit_event("job_completed", {
                "job_id": job_id,
                "findings_count": len(all_findings)
            })
            
            logger.info(f"Job {job_id} completed with {len(all_findings)} findings")
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()
            
            self._emit_event("job_failed", {
                "job_id": job_id,
                "error": str(e)
            })
            
            logger.error(f"Job {job_id} failed: {e}")
        
        finally:
            if job_id in self._active_jobs:
                del self._active_jobs[job_id]
        
        return job
    
    def _create_finding(
        self,
        capability: Capability,
        tool_data: Dict[str, Any],
        source_tool: str
    ) -> Finding:
        """Create a Finding from tool output"""
        finding_id = f"find_{uuid.uuid4().hex[:12]}"
        
        # Map severity
        severity = tool_data.get("severity", "info").lower()
        if severity not in ["critical", "high", "medium", "low", "info"]:
            severity = "info"
        
        finding = Finding(
            id=finding_id,
            capability=capability,
            severity=severity,
            title=tool_data.get("title", "Finding"),
            description=tool_data.get("description", ""),
            evidence=tool_data.get("evidence", {}),
            affected_assets=tool_data.get("affected_assets", []),
            recommendations=tool_data.get("recommendations", []),
            discovered_at=datetime.now(),
            risk_score=tool_data.get("risk_score", 50.0),
            source_tool=source_tool  # Hidden from user
        )
        
        return finding
    
    def _store_finding(self, finding: Finding, target: str):
        """Store a finding and update indices"""
        # Main storage
        self._findings.put(finding.id, finding)
        
        # Index by capability
        cap_key = finding.capability.value
        cap_findings = self._findings_by_capability.get(cap_key) or []
        cap_findings.append(finding.id)
        self._findings_by_capability.put(cap_key, cap_findings)
        
        # Index by target
        target_findings = self._findings_by_target.get(target) or []
        target_findings.append(finding.id)
        self._findings_by_target.put(target, target_findings)
        
        # Add to correlation graph
        self._correlation_graph.add_vertex(finding.id, {
            "type": "finding",
            "capability": finding.capability.value,
            "severity": finding.severity
        })
        
        for asset in finding.affected_assets:
            if not self._correlation_graph.has_vertex(asset):
                self._correlation_graph.add_vertex(asset, {"type": "asset"})
            self._correlation_graph.add_edge(finding.id, asset, weight=finding.risk_score)
        
        # Update stats
        self._stats["total_findings"] += 1
        self._stats["findings_by_severity"][finding.severity] += 1
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to the event buffer"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self._event_buffer.push(event)
    
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
        jobs = []
        for key in self._jobs.keys():
            job = self._jobs.get(key)
            if job:
                if capability and job.capability != capability:
                    continue
                if status and job.status != status:
                    continue
                jobs.append(job)
        
        # Sort by created_at desc
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
        findings = []
        
        # Get finding IDs to search
        if target:
            finding_ids = self._findings_by_target.get(target) or []
        elif capability:
            finding_ids = self._findings_by_capability.get(capability.value) or []
        else:
            finding_ids = self._findings.keys()
        
        for fid in finding_ids:
            finding = self._findings.get(fid)
            if finding:
                if severity and finding.severity != severity:
                    continue
                if finding.risk_score < min_risk_score:
                    continue
                findings.append(finding)
        
        # Sort by risk score desc
        findings.sort(key=lambda f: f.risk_score, reverse=True)
        return findings[:limit]
    
    def get_critical_findings(self, limit: int = 10) -> List[Finding]:
        """Get critical and high severity findings"""
        return self.get_findings(severity="critical", limit=limit) + \
               self.get_findings(severity="high", limit=limit)
    
    def get_findings_for_target(self, target: str) -> List[Finding]:
        """Get all findings for a specific target"""
        return self.get_findings(target=target)
    
    def get_correlation_graph(self, finding_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get correlation graph around a finding"""
        if not self._correlation_graph.has_vertex(finding_id):
            return {"nodes": [], "edges": []}
        
        visited = set()
        nodes = []
        edges = []
        queue = [(finding_id, 0)]
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            vertex_data = self._correlation_graph.get_vertex_data(current_id)
            
            nodes.append({
                "id": current_id,
                **vertex_data
            })
            
            neighbors = self._correlation_graph.get_neighbors(current_id)
            for neighbor_id, weight in neighbors:
                edges.append({
                    "source": current_id,
                    "target": neighbor_id,
                    "weight": weight
                })
                if neighbor_id not in visited:
                    queue.append((neighbor_id, current_depth + 1))
        
        return {"nodes": nodes, "edges": edges}
    
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent events from the event buffer"""
        events = []
        # Read recent events from circular buffer
        for i in range(min(limit, len(self._event_buffer))):
            event = self._event_buffer.get(i)
            if event:
                events.append(event)
        return events
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            **self._stats,
            "active_jobs": len(self._active_jobs),
            "queued_jobs": len(self._job_queue),
            "correlation_nodes": self._correlation_graph.vertex_count(),
            "correlation_edges": self._correlation_graph.edge_count()
        }
    
    async def quick_scan(self, domain: str) -> Dict[str, Any]:
        """
        Perform a quick scan across all relevant capabilities.
        Used for onboarding/first-time scans.
        """
        logger.info(f"Starting quick scan for {domain}")
        
        results = {
            "domain": domain,
            "started_at": datetime.now().isoformat(),
            "jobs": [],
            "summary": {}
        }
        
        # Create jobs for quick-scan relevant capabilities
        quick_scan_caps = [
            Capability.EXPOSURE_DISCOVERY,
            Capability.EMAIL_SECURITY,
            Capability.INFRASTRUCTURE,
        ]
        
        for cap in quick_scan_caps:
            try:
                job = await self.create_job(
                    capability=cap,
                    target=domain,
                    priority=JobPriority.HIGH
                )
                
                # Execute immediately
                completed_job = await self.execute_job(job.id)
                results["jobs"].append(completed_job.to_dict())
                
            except Exception as e:
                logger.error(f"Quick scan {cap.value} failed: {e}")
        
        results["completed_at"] = datetime.now().isoformat()
        results["summary"] = self._generate_quick_scan_summary(domain)
        
        return results
    
    def _generate_quick_scan_summary(self, domain: str) -> Dict[str, Any]:
        """Generate summary for quick scan results"""
        findings = self.get_findings_for_target(domain)
        
        return {
            "total_findings": len(findings),
            "critical": len([f for f in findings if f.severity == "critical"]),
            "high": len([f for f in findings if f.severity == "high"]),
            "medium": len([f for f in findings if f.severity == "medium"]),
            "low": len([f for f in findings if f.severity == "low"]),
            "top_issues": [
                {
                    "title": f.title,
                    "severity": f.severity,
                    "capability": f.capability.value
                }
                for f in findings[:5]
            ]
        }


# Global orchestrator instance
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """Get the global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

