"use client";

// Type declaration for process.env in client components (Next.js replaces these at build time)
declare const process: { env: { NEXT_PUBLIC_API_URL?: string } };

// API base URL - set via NEXT_PUBLIC_API_URL environment variable at build time
// Next.js replaces process.env.NEXT_PUBLIC_* variables at build time with actual values
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// DEBUG: Log the actual values (remove after diagnosis)
if (typeof window !== 'undefined') {
  console.log('🔍 [DEBUG] API_BASE_URL:', API_BASE_URL);
  console.log('🔍 [DEBUG] process.env.NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
  console.log('🔍 [DEBUG] Window location:', window.location.href);
}

// Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: "success" | "error";
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface Threat {
  id: string;
  name: string;
  type: string;
  severity: "critical" | "high" | "medium" | "low";
  status: "active" | "investigating" | "mitigated" | "false_positive";
  source: string;
  firstSeen: string;
  lastSeen: string;
  affectedAssets: number;
  iocs: number;
  description?: string;
}

export interface Credential {
  id: string;
  username: string;
  domain: string;
  email: string;
  source: string;
  riskLevel: "critical" | "high" | "medium" | "low";
  passwordStrength: "weak" | "moderate" | "strong";
  isReused: boolean;
  discoveredAt: string;
  breachName?: string;
}

export interface Entity {
  id: string;
  name: string;
  type: "threat" | "asset" | "credential" | "domain" | "ip" | "email";
  properties: Record<string, any>;
  relationships: { target: string; type: string }[];
}

export interface DashboardStats {
  totalThreats: number;
  criticalThreats: number;
  assetsMonitored: number;
  activeScanners: number;
  credentialsExposed: number;
  darkWebMentions: number;
}

// Capability Types
export interface CapabilityInfo {
  id: string;
  name: string;
  description: string;
  question: string;
  icon: string;
  supports_scheduling: boolean;
  requires_tor: boolean;
  default_config: Record<string, any>;
}

export interface CapabilityJob {
  id: string;
  capability: string;
  target: string;
  status: "pending" | "queued" | "running" | "completed" | "failed" | "cancelled";
  progress: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  findings_count: number;
  error: string | null;
}

export interface CapabilityFinding {
  id: string;
  capability: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  title: string;
  description: string;
  evidence: Record<string, any>;
  affected_assets: string[];
  recommendations: string[];
  discovered_at: string;
  risk_score: number;
}

export interface CreateJobRequest {
  capability: string;
  target: string;
  config?: Record<string, any>;
  priority?: "critical" | "high" | "normal" | "low" | "background";
}

// API Client
class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string) {
    this.token = token;
  }

  clearToken() {
    this.token = null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    if (this.token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: "Request failed" }));
      throw new Error(error.message || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Auth
  async login(email: string, password: string) {
    return this.request<{ token: string; user: any }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async logout() {
    return this.request("/auth/logout", { method: "POST" });
  }

  // Dashboard
  async getDashboardStats() {
    return this.request<DashboardStats>("/dashboard/stats");
  }

  // Threats
  async getThreats(params?: { page?: number; pageSize?: number; severity?: string }) {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return this.request<PaginatedResponse<Threat>>(`/threats?${query}`);
  }

  async getThreat(id: string) {
    return this.request<Threat>(`/threats/${id}`);
  }

  async updateThreatStatus(id: string, status: Threat["status"]) {
    return this.request<Threat>(`/threats/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  }

  // Credentials
  async getCredentials(params?: { page?: number; pageSize?: number; riskLevel?: string }) {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return this.request<PaginatedResponse<Credential>>(`/credentials?${query}`);
  }

  async getCredential(id: string) {
    return this.request<Credential>(`/credentials/${id}`);
  }

  // Entities / Graph
  async getEntities(params?: { type?: string; limit?: number }) {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return this.request<Entity[]>(`/entities?${query}`);
  }

  async getEntityRelationships(id: string, depth?: number) {
    return this.request<{ nodes: Entity[]; edges: { source: string; target: string; type: string }[] }>(
      `/entities/${id}/relationships?depth=${depth || 2}`
    );
  }

  // Graph
  async getGraphData() {
    return this.request<{ nodes: Entity[]; edges: any[] }>("/graph");
  }

  // Timeline
  async getTimelineEvents(params?: { from?: string; to?: string; type?: string }) {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return this.request<any[]>(`/timeline?${query}`);
  }

  // Reports
  async getReports() {
    return this.request<any[]>("/reports");
  }

  async generateReport(templateId: string, params: Record<string, any>) {
    return this.request<{ reportId: string; status: string }>("/reports/generate", {
      method: "POST",
      body: JSON.stringify({ templateId, ...params }),
    });
  }

  async downloadReport(id: string) {
    const response = await fetch(`${this.baseUrl}/reports/${id}/download`, {
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
    });
    return response.blob();
  }

  // Collectors
  async getCollectorStatuses() {
    return this.request<any[]>("/collectors/status");
  }

  async startCollector(id: string) {
    return this.request(`/collectors/${id}/start`, { method: "POST" });
  }

  async stopCollector(id: string) {
    return this.request(`/collectors/${id}/stop`, { method: "POST" });
  }

  // Settings
  async getSettings() {
    return this.request<any>("/settings");
  }

  async updateSettings(settings: Record<string, any>) {
    return this.request("/settings", {
      method: "PUT",
      body: JSON.stringify(settings),
    });
  }

  // ============================================================================
  // Capabilities API
  // ============================================================================

  /**
   * List all available security capabilities
   */
  async getCapabilities() {
    return this.request<CapabilityInfo[]>("/capabilities/");
  }

  /**
   * Get a specific capability by ID
   */
  async getCapability(capabilityId: string) {
    return this.request<CapabilityInfo>(`/capabilities/${capabilityId}`);
  }

  /**
   * Create and start a capability job (scan)
   */
  async createCapabilityJob(request: CreateJobRequest) {
    return this.request<CapabilityJob>("/capabilities/jobs", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  /**
   * Get job status and progress
   */
  async getJobStatus(jobId: string) {
    return this.request<CapabilityJob>(`/capabilities/jobs/${jobId}`);
  }

  /**
   * List all jobs with optional filtering
   */
  async getJobs(params?: { capability?: string; status?: string; limit?: number }) {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return this.request<CapabilityJob[]>(`/capabilities/jobs?${query}`);
  }

  /**
   * Get findings from a completed job
   */
  async getJobFindings(jobId: string) {
    return this.request<CapabilityFinding[]>(`/capabilities/jobs/${jobId}/findings`);
  }

  /**
   * List all findings with optional filtering
   */
  async getFindings(params?: { 
    capability?: string; 
    severity?: string; 
    target?: string;
    min_risk_score?: number;
    limit?: number;
  }) {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return this.request<CapabilityFinding[]>(`/capabilities/findings?${query}`);
  }

  /**
   * Get critical findings that need immediate attention
   */
  async getCriticalFindings(limit: number = 10) {
    return this.request<CapabilityFinding[]>(`/capabilities/findings/critical?limit=${limit}`);
  }

  /**
   * Perform a quick scan of a domain
   */
  async quickScan(domain: string) {
    return this.request<{
      domain: string;
      started_at: string;
      completed_at: string;
      jobs: CapabilityJob[];
      summary: { capabilities_run: number; total_findings: number; duration_seconds: number };
      risk_score: any;
    }>("/capabilities/quick-scan", {
      method: "POST",
      body: JSON.stringify({ domain }),
    });
  }

  /**
   * Get capability statistics
   */
  async getCapabilityStats() {
    return this.request<any>("/capabilities/stats");
  }

  /**
   * Get recent capability events for live feed
   */
  async getCapabilityEvents(limit: number = 50) {
    return this.request<{ events: any[]; count: number }>(`/capabilities/events?limit=${limit}`);
  }

  // ============================================================================
  // Company Profile API
  // ============================================================================

  /**
   * Get current company profile
   */
  async getCompanyProfile() {
    return this.request<any>("/company/profile");
  }

  /**
   * Create a new company profile
   */
  async createCompanyProfile(data: Record<string, any>) {
    return this.request<any>("/company/profile", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * Update company profile (full replace)
   */
  async updateCompanyProfile(data: Record<string, any>) {
    return this.request<any>("/company/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  /**
   * Partially update company profile
   */
  async patchCompanyProfile(data: Record<string, any>) {
    return this.request<any>("/company/profile", {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // Email Security Specific Methods
  // ============================================================================

  /**
   * Get email security scan history for a domain
   */
  async getEmailHistory(domain: string, limit: number = 10) {
    return this.request<{
      domain: string;
      history: Array<{
        job_id: string;
        timestamp: string;
        score: number;
        findings_count: number;
        status: string;
      }>;
    }>(`/capabilities/email/${encodeURIComponent(domain)}/history?limit=${limit}`);
  }

  /**
   * Get email compliance report for a domain
   */
  async getEmailCompliance(domain: string) {
    return this.request<{
      domain: string;
      message: string;
      last_scan: string | null;
    }>(`/capabilities/email/${encodeURIComponent(domain)}/compliance`);
  }

  /**
   * Run bypass vulnerability tests for a domain
   */
  async runEmailBypassTest(domain: string) {
    return this.request<{
      job_id: string;
      domain: string;
      message: string;
      status: string;
    }>(`/capabilities/email/${encodeURIComponent(domain)}/bypass-test`, {
      method: "POST",
    });
  }

  /**
   * Get email infrastructure graph data
   */
  async getEmailInfrastructure(domain: string) {
    return this.request<{
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
    }>(`/capabilities/email/${encodeURIComponent(domain)}/infrastructure`);
  }

  /**
   * Export email security report
   */
  async exportEmailReport(domain: string, format: "json" | "csv" = "json") {
    const url = `/capabilities/email/${encodeURIComponent(domain)}/export?format=${format}`;
    
    if (format === "csv") {
      const response = await fetch(`${API_BASE_URL}${url}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });
      
      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = `email_report_${domain}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      return { success: true };
    } else {
      return this.request<any>(url);
    }
  }

  /**
   * Compare two email security scans
   */
  async compareEmailScans(domain: string, jobId1: string, jobId2: string) {
    return this.request<{
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
    }>(`/capabilities/email/${encodeURIComponent(domain)}/compare?job_id1=${jobId1}&job_id2=${jobId2}`);
  }
}

// Export singleton instance
export const api = new ApiClient(API_BASE_URL);

// React Query hooks (if using React Query)
export const queryKeys = {
  dashboard: ["dashboard"],
  threats: (params?: any) => ["threats", params],
  threat: (id: string) => ["threat", id],
  credentials: (params?: any) => ["credentials", params],
  credential: (id: string) => ["credential", id],
  entities: (params?: any) => ["entities", params],
  graph: ["graph"],
  timeline: (params?: any) => ["timeline", params],
  reports: ["reports"],
  collectors: ["collectors"],
  settings: ["settings"],
  // Capabilities
  capabilities: ["capabilities"],
  capability: (id: string) => ["capability", id],
  jobs: (params?: any) => ["jobs", params],
  job: (id: string) => ["job", id],
  jobFindings: (jobId: string) => ["jobFindings", jobId],
  findings: (params?: any) => ["findings", params],
  criticalFindings: ["criticalFindings"],
  capabilityStats: ["capabilityStats"],
  capabilityEvents: ["capabilityEvents"],
  // Company Profile
  companyProfile: ["companyProfile"],
};


