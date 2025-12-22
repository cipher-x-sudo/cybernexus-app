export interface RiskScoreData {
  score: number;
  riskLevel: string;
  trend: "improving" | "stable" | "worsening";
  criticalIssues: number;
  highIssues: number;
}

export interface FindingData {
  id: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low";
  capability: string;
  target: string;
  time: string;
}

export interface JobData {
  capability: string;
  target: string;
  status: "completed" | "running" | "failed" | "pending";
  findings: number;
  time: string;
}

export interface EventData {
  id: string;
  type: string;
  message: string;
  timestamp: string;
}

export interface CapabilityStat {
  scans: number;
  findings: number;
  lastRun: string;
}

export interface ReportData {
  id: string;
  name: string;
  type: string;
  status: "completed" | "generating" | "pending" | "failed";
  createdAt: Date;
}

export function mapToRiskScore(overview: any): RiskScoreData {
  return {
    score: overview.risk_score !== undefined && overview.risk_score !== null ? overview.risk_score : 100,
    riskLevel: overview.risk_level || "minimal",
    trend: overview.trend || "stable",
    criticalIssues: overview.critical_findings_count ?? 0,
    highIssues: overview.high_findings_count ?? 0,
  };
}

export function mapToFindings(findings: any[]): FindingData[] {
  return findings.map((f) => ({
    id: f.id,
    title: f.title,
    severity: f.severity as "critical" | "high" | "medium" | "low",
    capability: f.capability || "Unknown",
    target: f.target || "",
    time: f.time_ago || formatTimeAgo(f.discovered_at),
  }));
}

export function mapToJobs(jobs: any[]): JobData[] {
  return jobs.map((job) => {
    const capabilityValue = job.capabilities?.[0] || job.capability || "Unknown";
    return {
      capability: formatCapabilityName(capabilityValue),
      target: job.target,
      status: mapJobStatus(job.status),
      findings: job.findings_count || 0,
      time: job.time_ago || formatTimeAgo(job.created_at),
    };
  });
}

export function mapToEvents(events: any[]): EventData[] {
  return events.map((event, index) => ({
    id: event.id || event.timestamp || `event-${index}`,
    type: event.type || "info",
    message: formatEventMessage(event),
    timestamp: event.timestamp || new Date().toISOString(),
  }));
}

export function mapToCapabilityStats(
  capabilityStats: Record<string, any>
): Record<string, CapabilityStat> {
  const mapped: Record<string, CapabilityStat> = {};
  
  for (const [key, stats] of Object.entries(capabilityStats)) {
    mapped[key] = {
      scans: stats.scans || 0,
      findings: stats.findings || 0,
      lastRun: stats.last_run || "Never",
    };
  }
  
  return mapped;
}

export function mapToReports(reports: any[]): ReportData[] {
  return reports.map((report) => ({
    id: report.id,
    name: report.title || report.name || "Untitled Report",
    type: mapReportType(report.type),
    status: mapReportStatus(report.status),
    createdAt: report.created_at ? new Date(report.created_at) : new Date(),
  }));
}

function mapReportType(backendType: string): string {
  const typeMap: Record<string, string> = {
    executive_summary: "executive",
    threat_assessment: "technical",
    vulnerability_report: "technical",
    credential_exposure: "incident",
    dark_web_intelligence: "trend",
    attack_surface: "technical",
    compliance: "compliance",
    custom: "custom",
  };
  return typeMap[backendType] || backendType;
}

function mapReportStatus(backendStatus: string): "completed" | "generating" | "pending" | "failed" {
  const statusMap: Record<string, "completed" | "generating" | "pending" | "failed"> = {
    completed: "completed",
    generating: "generating",
    pending: "generating",
    failed: "failed",
  };
  return statusMap[backendStatus] || "pending";
}

function formatCapabilityName(capability: string): string {
  const names: Record<string, string> = {
    exposure_discovery: "Exposure Discovery",
    dark_web_intelligence: "Dark Web Intel",
    email_security: "Email Security",
    infrastructure_testing: "Infrastructure",
    network_security: "Network Security",
    investigation: "Investigation",
  };
  return names[capability] || capability.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

function mapJobStatus(status: string): "completed" | "running" | "failed" | "pending" {
  const statusMap: Record<string, "completed" | "running" | "failed" | "pending"> = {
    completed: "completed",
    running: "running",
    failed: "failed",
    cancelled: "failed",
    pending: "pending",
    queued: "pending",
  };
  return statusMap[status] || "pending";
}

function formatEventMessage(event: any): string {
  if (event.title) {
    return event.title;
  }
  if (event.description) {
    return event.description;
  }
  
  const type = event.type || "";
  const data = event.data || {};
  
  const messages: Record<string, string> = {
    job_created: `Scan initiated - ${data.capabilities?.[0] || data.capability || "Unknown"}`,
    job_started: `Scan started - ${data.capabilities?.[0] || data.capability || "Unknown"}`,
    job_completed: `Scan completed - ${data.capabilities?.[0] || data.capability || "Unknown"}${data.findings_count ? ` (${data.findings_count} findings)` : ""}`,
    job_failed: `Scan failed - ${data.capabilities?.[0] || data.capability || "Unknown"}`,
    finding: `New finding detected - ${data.title || "Unknown"}`,
  };
  
  return messages[type] || `${type} - ${data.capabilities?.[0] || data.capability || "Unknown"}`;
}

function formatTimeAgo(timestamp: string | null | undefined): string {
  if (!timestamp) return "Unknown";
  
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return "Just now";
  } catch {
    return "Unknown";
  }
}



