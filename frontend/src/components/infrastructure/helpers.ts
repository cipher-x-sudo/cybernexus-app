import { CapabilityFinding } from "@/lib/api";

export type InfrastructureCategory = 
  | "crlf" 
  | "path_traversal" 
  | "cve" 
  | "headers" 
  | "server_info" 
  | "bypass" 
  | "misconfiguration" 
  | "other";

export interface InfrastructureFinding {
  id: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  description: string;
  evidence: Record<string, any>;
  recommendations: string[];
  timestamp: string;
  category: InfrastructureCategory;
  riskScore: number;
  affectedAssets: string[];
  sourceFindingId: string;
}

export interface InfrastructureStats {
  totalFindings: number;
  severityBreakdown: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
  categoryBreakdown: Record<InfrastructureCategory, number>;
  testCoverage: {
    crlf: boolean;
    pathTraversal: boolean;
    versionDetection: boolean;
    cveLookup: boolean;
    bypassTechniques: boolean;
  };
  averageRiskScore: number;
  criticalFindings: number;
  highFindings: number;
}

export interface GroupedFindings {
  category: InfrastructureCategory;
  findings: InfrastructureFinding[];
  count: number;
}

// Category icons
export const categoryIcons: Record<InfrastructureCategory, string> = {
  crlf: "↩️",
  path_traversal: "📁",
  cve: "🔒",
  headers: "📋",
  server_info: "🖥️",
  bypass: "🚫",
  misconfiguration: "⚙️",
  other: "📦",
};

// Category labels
export const categoryLabels: Record<InfrastructureCategory, string> = {
  crlf: "CRLF Injection",
  path_traversal: "Path Traversal",
  cve: "CVE",
  headers: "Headers",
  server_info: "Server Info",
  bypass: "Bypass",
  misconfiguration: "Misconfiguration",
  other: "Other",
};

/**
 * Categorize a finding based on its title and evidence
 */
export function categorizeFinding(finding: CapabilityFinding): InfrastructureCategory {
  const title = finding.title.toLowerCase();
  const description = finding.description.toLowerCase();
  const evidenceStr = JSON.stringify(finding.evidence || {}).toLowerCase();

  // CRLF injection
  if (
    title.includes("crlf") ||
    title.includes("carriage return") ||
    title.includes("line feed") ||
    description.includes("crlf") ||
    evidenceStr.includes("crlf")
  ) {
    return "crlf";
  }

  // Path traversal
  if (
    title.includes("path traversal") ||
    title.includes("directory traversal") ||
    title.includes("../") ||
    description.includes("path traversal") ||
    description.includes("directory traversal")
  ) {
    return "path_traversal";
  }

  // CVE
  if (
    title.includes("cve-") ||
    title.includes("cve ") ||
    description.includes("cve-") ||
    evidenceStr.includes("cve-")
  ) {
    return "cve";
  }

  // Headers
  if (
    title.includes("header") ||
    title.includes("missing header") ||
    title.includes("security header") ||
    description.includes("header") ||
    evidenceStr.includes("header")
  ) {
    return "headers";
  }

  // Bypass
  if (
    title.includes("bypass") ||
    title.includes("401") ||
    title.includes("403") ||
    description.includes("bypass") ||
    description.includes("authentication bypass")
  ) {
    return "bypass";
  }

  // Server info
  if (
    title.includes("server") ||
    title.includes("version") ||
    title.includes("software") ||
    description.includes("server version") ||
    description.includes("disclosure")
  ) {
    return "server_info";
  }

  // Misconfiguration
  if (
    title.includes("misconfiguration") ||
    title.includes("misconfigured") ||
    description.includes("misconfiguration")
  ) {
    return "misconfiguration";
  }

  return "other";
}

/**
 * Extract and convert infrastructure findings from API findings
 */
export function extractInfrastructureFindings(
  findings: CapabilityFinding[]
): InfrastructureFinding[] {
  return findings.map((finding) => {
    const category = categorizeFinding(finding);
    
    // Format timestamp
    const timestamp = finding.discovered_at
      ? formatRelativeTime(new Date(finding.discovered_at))
      : "Just now";

    return {
      id: finding.id,
      title: finding.title,
      severity: finding.severity,
      description: finding.description,
      evidence: finding.evidence || {},
      recommendations: finding.recommendations || [],
      timestamp,
      category,
      riskScore: finding.risk_score || 0,
      affectedAssets: finding.affected_assets || [],
      sourceFindingId: finding.id,
    };
  });
}

/**
 * Calculate infrastructure statistics
 */
export function calculateInfrastructureStats(
  findings: InfrastructureFinding[],
  testConfig?: {
    crlf?: boolean;
    pathTraversal?: boolean;
    versionDetection?: boolean;
    cveLookup?: boolean;
    bypassTechniques?: boolean;
  }
): InfrastructureStats {
  const severityBreakdown = {
    critical: findings.filter((f) => f.severity === "critical").length,
    high: findings.filter((f) => f.severity === "high").length,
    medium: findings.filter((f) => f.severity === "medium").length,
    low: findings.filter((f) => f.severity === "low").length,
    info: findings.filter((f) => f.severity === "info").length,
  };

  const categoryBreakdown: Record<InfrastructureCategory, number> = {
    crlf: 0,
    path_traversal: 0,
    cve: 0,
    headers: 0,
    server_info: 0,
    bypass: 0,
    misconfiguration: 0,
    other: 0,
  };

  findings.forEach((finding) => {
    categoryBreakdown[finding.category] = (categoryBreakdown[finding.category] || 0) + 1;
  });

  const riskScores = findings.map((f) => f.riskScore).filter((s) => s > 0);
  const averageRiskScore =
    riskScores.length > 0
      ? riskScores.reduce((a, b) => a + b, 0) / riskScores.length
      : 0;

  return {
    totalFindings: findings.length,
    severityBreakdown,
    categoryBreakdown,
    testCoverage: {
      crlf: testConfig?.crlf ?? false,
      pathTraversal: testConfig?.pathTraversal ?? false,
      versionDetection: testConfig?.versionDetection ?? false,
      cveLookup: testConfig?.cveLookup ?? false,
      bypassTechniques: testConfig?.bypassTechniques ?? false,
    },
    averageRiskScore: Math.round(averageRiskScore),
    criticalFindings: severityBreakdown.critical,
    highFindings: severityBreakdown.high,
  };
}

/**
 * Group findings by category
 */
export function groupFindingsByCategory(
  findings: InfrastructureFinding[]
): GroupedFindings[] {
  const grouped = new Map<InfrastructureCategory, InfrastructureFinding[]>();

  findings.forEach((finding) => {
    if (!grouped.has(finding.category)) {
      grouped.set(finding.category, []);
    }
    grouped.get(finding.category)!.push(finding);
  });

  return Array.from(grouped.entries())
    .map(([category, findings]) => ({
      category,
      findings,
      count: findings.length,
    }))
    .sort((a, b) => b.count - a.count);
}

/**
 * Format relative time
 */
function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

