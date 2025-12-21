/**
 * TypeScript types for Email Security feature
 */

export interface EmailSecurityConfig {
  check_spf?: boolean;
  check_dkim?: boolean;
  check_dmarc?: boolean;
  check_mx?: boolean;
  check_bimi?: boolean;
  check_mta_sts?: boolean;
  check_dane?: boolean;
  check_arc?: boolean;
  check_subdomains?: boolean;
  check_ptr?: boolean;
  check_dnssec?: boolean;
  run_bypass_tests?: boolean;
}

export interface SPFResult {
  exists: boolean;
  record?: string;
  mechanisms: string[];
  all_mechanism?: string;
  includes: string[];
  issues: Array<{
    severity: string;
    issue: string;
  }>;
}

export interface DKIMResult {
  selectors_found: Array<{
    selector: string;
    record: string;
    key_type: string;
  }>;
  selectors_checked: number;
  issues: Array<{
    severity: string;
    issue: string;
  }>;
}

export interface DMARCResult {
  exists: boolean;
  record?: string;
  policy?: string;
  subdomain_policy?: string;
  pct: number;
  rua: string[];
  ruf: string[];
  issues: Array<{
    severity: string;
    issue: string;
  }>;
}

export interface MXRecord {
  priority: number;
  exchange: string;
}

export interface BIMIResult {
  exists: boolean;
  record?: string;
  selector: string;
  v?: string;
  l?: string;
  a?: string;
  issues: Array<{
    severity: string;
    issue: string;
  }>;
}

export interface MTASTSResult {
  exists: boolean;
  dns_record?: string;
  policy_exists: boolean;
  policy_url?: string;
  policy_content?: string;
  mode?: string;
  max_age?: string;
  issues: Array<{
    severity: string;
    issue: string;
  }>;
}

export interface DANEResult {
  exists: boolean;
  records: Array<{
    mx: string;
    usage: number;
    selector: number;
    matching_type: number;
    certificate: string;
  }>;
  issues: Array<{
    severity: string;
    issue: string;
  }>;
}

export interface ARCResult {
  configured: boolean;
  note: string;
  issues: Array<{
    severity: string;
    issue: string;
  }>;
}

export interface PTRResult {
  mx_servers: Array<{
    host: string;
    ptr_exists: boolean;
    ptr_record?: string;
    reverse_matches: boolean;
  }>;
  issues: Array<{
    severity: string;
    issue: string;
  }>;
}

export interface DNSSECResult {
  signed: boolean;
  ds_record?: string;
  issues: Array<{
    severity: string;
    issue: string;
  }>;
}

export interface SubdomainResult {
  subdomains_checked: Array<{
    subdomain: string;
    has_mx: boolean;
    has_spf: boolean;
    has_dmarc: boolean;
    has_dkim: boolean;
  }>;
  subdomains_with_email_config: Array<{
    subdomain: string;
    has_mx: boolean;
    has_spf: boolean;
    has_dmarc: boolean;
    has_dkim: boolean;
  }>;
  issues: Array<{
    severity: string;
    issue: string;
  }>;
}

export interface RiskAssessment {
  spoofing_risk: "critical" | "high" | "medium" | "low" | "unknown";
  factors: string[];
}

export interface ComplianceScore {
  rfc_7208_spf: {
    standard: string;
    compliant: boolean;
    score: number;
    issues: string[];
    recommendations: string[];
  };
  rfc_6376_dkim: {
    standard: string;
    compliant: boolean;
    score: number;
    issues: string[];
    recommendations: string[];
  };
  rfc_7489_dmarc: {
    standard: string;
    compliant: boolean;
    score: number;
    issues: string[];
    recommendations: string[];
  };
  m3aawg: {
    standard: string;
    compliant: boolean;
    score: number;
    issues: string[];
    recommendations: string[];
  };
  overall_score: number;
  overall_level: string;
}

export interface BypassVulnerability {
  severity: "critical" | "high" | "medium" | "low";
  type: string;
  test_case: string;
  title: string;
  description: string;
  attack_vector: string;
  recommendation: string;
}

export interface BypassAnalysis {
  domain: string;
  timestamp: string;
  vulnerabilities: BypassVulnerability[];
  risk_level: string;
  bypass_scenarios: Array<{
    id: string;
    severity: string;
    title: string;
    description: string;
    attack_vector: string;
    mitigation: string;
    type: string;
  }>;
}

export interface EmailAuditResult {
  domain: string;
  timestamp: string;
  spf: SPFResult;
  dkim: DKIMResult;
  dmarc: DMARCResult;
  mx_records: MXRecord[];
  risk_assessment: RiskAssessment;
  score: number;
  compliance?: ComplianceScore;
  bimi?: BIMIResult;
  mta_sts?: MTASTSResult;
  dane?: DANEResult;
  arc?: ARCResult;
  ptr_records?: PTRResult;
  dnssec?: DNSSECResult;
  subdomains?: SubdomainResult;
  bypass_analysis?: BypassAnalysis;
}

export interface EmailHistoryEntry {
  job_id: string;
  timestamp: string;
  score: number;
  findings_count: number;
  status: string;
}

export interface EmailInfrastructure {
  domain: string;
  nodes: Array<{
    id: string;
    type: string;
    label: string;
  }>;
  edges: Array<{
    from: string;
    to: string;
    relation: string;
  }>;
}

export interface EmailComparison {
  domain: string;
  job1: {
    id: string;
    timestamp: string;
    score: number;
    findings_count: number;
  };
  job2: {
    id: string;
    timestamp: string;
    score: number;
    findings_count: number;
  };
  comparison: {
    score_change: number;
    new_findings: any[];
    resolved_findings: any[];
    findings_count_change: number;
  };
}






