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
  time_ago?: string; // Optional field for formatted time display
}

export interface JobDetail extends CapabilityJob {
  priority: number;
  config: Record<string, any>;
  metadata: Record<string, any>;
  execution_logs: Array<{
    timestamp: string;
    level: string;
    message: string;
    data?: Record<string, any>;
  }>;
}

export interface JobHistoryParams {
  capability?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export interface JobHistoryResponse {
  jobs: CapabilityJob[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
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
      // Handle 401 Unauthorized - clear token and redirect to login
      if (response.status === 401) {
        this.clearToken();
        if (typeof window !== "undefined") {
          localStorage.removeItem("auth_token");
          localStorage.removeItem("auth_user");
          // Only redirect if not already on login/signup page
          if (!window.location.pathname.includes("/login") && !window.location.pathname.includes("/signup")) {
            window.location.href = "/login";
          }
        }
      }
      
      const error = await response.json().catch(() => ({ 
        message: response.status === 401 ? "Unauthorized. Please log in again." : "Request failed" 
      }));
      throw new Error(error.detail || error.message || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Auth
  async login(username: string, password: string) {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);
    
    const response = await this.request<{ access_token: string; token_type: string; expires_in: number }>("/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData.toString(),
    });
    
    return {
      token: response.access_token,
      expiresIn: response.expires_in,
    };
  }

  async register(username: string, email: string, password: string, fullName?: string) {
    return this.request<{
      id: string;
      username: string;
      email: string;
      full_name: string | null;
      disabled: boolean;
      role: string;
      onboarding_completed: boolean;
      created_at: string;
      updated_at: string;
    }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password, full_name: fullName }),
    });
  }

  async getCurrentUser() {
    return this.request<{
      id: string;
      username: string;
      email: string;
      full_name: string | null;
      disabled: boolean;
      role: string;
      onboarding_completed: boolean;
      created_at: string;
      updated_at: string;
    }>("/auth/me");
  }

  async logout() {
    this.clearToken();
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
    }
  }

  // Dashboard
  async getDashboardStats() {
    return this.request<DashboardStats>("/dashboard/stats");
  }

  /**
   * Get comprehensive dashboard overview data
   */
  async getDashboardOverview() {
    return this.request<{
      risk_score: number;
      risk_level: string;
      trend: "improving" | "stable" | "worsening";
      critical_findings_count: number;
      high_findings_count: number;
      total_jobs: number;
      active_jobs: number;
      recent_jobs: Array<{
        id: string;
        capabilities: string[];
        target: string;
        status: string;
        progress: number;
        findings_count: number;
        time_ago: string;
        created_at: string;
        completed_at: string | null;
      }>;
      recent_events: Array<{
        type: string;
        data: Record<string, any>;
        timestamp: string;
      }>;
      capability_stats: Record<string, {
        scans: number;
        findings: number;
        last_run: string;
      }>;
      threat_map_data: Array<{
        id: string;
        title: string;
        severity: string;
        risk_score: number;
        target: string;
        capabilities: string[];
        discovered_at: string;
      }>;
      timeline_stats: {
        total_events: number;
        events_24h: number;
      };
      timestamp: string;
    }>("/dashboard/overview");
  }

  /**
   * Get critical findings for dashboard
   */
  async getDashboardCriticalFindings(limit: number = 10) {
    return this.request<{
      findings: Array<{
        id: string;
        title: string;
        severity: string;
        capabilities: string[];
        target: string;
        time_ago: string;
        risk_score: number;
        discovered_at: string;
      }>;
      count: number;
    }>(`/dashboard/critical-findings?limit=${limit}`);
  }

  /**
   * Get detailed risk score breakdown with category analysis
   */
  async getDashboardRiskBreakdown() {
    return this.request<{
      overall_score: number;
      risk_level: string;
      trend: "improving" | "stable" | "worsening";
      categories: Record<string, {
        name: string;
        score: number;
        findings_count: number;
        contribution: number;
        severity_breakdown: {
          critical: number;
          high: number;
          medium: number;
          low: number;
        };
      }>;
      severity_distribution: {
        critical: number;
        high: number;
        medium: number;
        low: number;
      };
      calculation: {
        base_score: number;
        deductions: {
          critical: number;
          high: number;
          medium: number;
          low: number;
        };
        total_deduction: number;
        additions: {
          resolved: number;
          indicators: number;
          total: number;
        };
        formula: string;
      };
      positive_points: {
        resolved: number;
        indicators: number;
        total: number;
      };
      recommendations: Array<{
        priority: "critical" | "high" | "medium" | "low";
        title: string;
        description: string;
        action: string;
      }>;
    }>("/dashboard/risk-breakdown");
  }

  /**
   * Resolve a finding
   */
  async resolveFinding(findingId: string, status: "resolved" | "false_positive" | "accepted_risk" = "resolved") {
    return this.request<{
      message: string;
      finding_id: string;
      status: string;
    }>(`/capabilities/findings/${findingId}/resolve?status=${status}`, {
      method: "PATCH",
    });
  }

  /**
   * Get positive indicators
   */
  async getPositiveIndicators() {
    return this.request<{
      indicators: Array<{
        id: string;
        indicator_type: string;
        category: string;
        points_awarded: number;
        description: string;
        evidence: Record<string, any>;
        target: string | null;
        created_at: string | null;
      }>;
      count: number;
      total_points: number;
    }>("/dashboard/positive-indicators");
  }

  /**
   * Get recent jobs for dashboard
   */
  async getRecentJobs(limit: number = 10, capability?: string, status?: string) {
    const params: Record<string, string> = { limit: limit.toString() };
    if (capability) params.capability = capability;
    if (status) params.status = status;
    const query = new URLSearchParams(params).toString();
    return this.request<{
      jobs: Array<{
        id: string;
        capabilities: string[];
        target: string;
        status: string;
        progress: number;
        findings_count: number;
        time_ago: string;
        created_at: string;
        started_at: string | null;
        completed_at: string | null;
        error: string | null;
      }>;
      count: number;
    }>(`/capabilities/jobs/recent?${query}`);
  }

  async getJobHistory(params?: JobHistoryParams): Promise<JobHistoryResponse> {
    const queryParams: Record<string, string> = {};
    if (params?.capability) queryParams.capability = params.capability;
    if (params?.status) queryParams.status = params.status;
    if (params?.start_date) queryParams.start_date = params.start_date;
    if (params?.end_date) queryParams.end_date = params.end_date;
    if (params?.page) queryParams.page = params.page.toString();
    if (params?.page_size) queryParams.page_size = params.page_size.toString();
    
    const query = new URLSearchParams(queryParams).toString();
    return this.request<JobHistoryResponse>(`/capabilities/jobs/history?${query}`);
  }

  async getJobDetails(jobId: string): Promise<JobDetail> {
    return this.request<JobDetail>(`/capabilities/jobs/${jobId}`);
  }

  async restartJob(jobId: string): Promise<CapabilityJob> {
    return this.request<CapabilityJob>(`/capabilities/jobs/${jobId}/restart`, {
      method: "POST",
    });
  }

  async exportJobResults(jobId: string, format: "json" | "csv" = "json"): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/capabilities/jobs/${jobId}/export?format=${format}`, {
      headers: {
        "Authorization": this.token ? `Bearer ${this.token}` : "",
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ 
        message: response.status === 401 ? "Unauthorized. Please log in again." : "Request failed" 
      }));
      throw new Error(error.detail || error.message || `HTTP ${response.status}`);
    }

    return response.blob();
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
  async getGraphData(params?: { limit?: number; entity_types?: string[]; min_severity?: string }) {
    const queryParams: Record<string, string> = {};
    if (params?.limit) queryParams.limit = params.limit.toString();
    if (params?.entity_types) queryParams.entity_types = params.entity_types.join(",");
    if (params?.min_severity) queryParams.min_severity = params.min_severity;
    const query = new URLSearchParams(queryParams).toString();
    return this.request<{ nodes: Array<{
      id: string;
      label: string;
      type: string;
      severity: string;
      metadata: Record<string, any>;
      x?: number;
      y?: number;
      z?: number;
    }>; edges: Array<{
      id: string;
      source: string;
      target: string;
      relation: string;
      weight: number;
      metadata: Record<string, any>;
    }> }>(`/graph?${query}`);
  }

  /**
   * Get graph data focused on a specific finding
   */
  async getGraphDataForFinding(findingId: string, depth: number = 2) {
    return this.request<{ nodes: Array<{
      id: string;
      label: string;
      type: string;
      severity: string;
      metadata: Record<string, any>;
      x?: number;
      y?: number;
      z?: number;
    }>; edges: Array<{
      id: string;
      source: string;
      target: string;
      relation: string;
      weight: number;
      metadata: Record<string, any>;
    }> }>(`/graph/finding/${findingId}?depth=${depth}`);
  }

  /**
   * Get graph data focused on a specific node
   */
  async getGraphDataForNode(nodeId: string, depth: number = 2) {
    return this.request<{ nodes: Array<{
      id: string;
      label: string;
      type: string;
      severity: string;
      metadata: Record<string, any>;
      x?: number;
      y?: number;
      z?: number;
    }>; edges: Array<{
      id: string;
      source: string;
      target: string;
      relation: string;
      weight: number;
      metadata: Record<string, any>;
    }> }>(`/graph/node/${nodeId}/neighbors?depth=${depth}`);
  }

  /**
   * Get a specific finding by ID
   */
  async getFinding(findingId: string) {
    return this.request<{
      id: string;
      capabilities: string[];
      severity: string;
      title: string;
      description: string;
      evidence: Record<string, any>;
      affected_assets: string[];
      recommendations: string[];
      discovered_at: string;
      risk_score: number;
      target?: string;
    }>(`/capabilities/findings/${findingId}`);
  }

  // Timeline
  async getTimelineEvents(params?: { from?: string; to?: string; type?: string }) {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return this.request<any[]>(`/timeline?${query}`);
  }

  async getRecentTimelineEvents(n: number = 20) {
    return this.request<any[]>(`/timeline/recent?n=${n}`);
  }

  // Reports
  async getReports() {
    return this.request<any[]>("/reports");
  }

  async generateReport(params: {
    title: string;
    type: string;
    format?: "pdf" | "html" | "json" | "markdown";
    date_range_start?: string;
    date_range_end?: string;
    include_sections?: string[];
    filters?: Record<string, any>;
  }) {
    return this.request<any>("/reports/generate", {
      method: "POST",
      body: JSON.stringify({
        title: params.title,
        type: params.type,
        format: params.format || "pdf",
        date_range_start: params.date_range_start || null,
        date_range_end: params.date_range_end || null,
        include_sections: params.include_sections || [],
        filters: params.filters || {},
      }),
    });
  }

  async downloadReport(id: string) {
    const response = await fetch(`${this.baseUrl}/reports/${id}/download`, {
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
    });
    if (!response.ok) {
      throw new Error(`Failed to download report: ${response.statusText}`);
    }
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

  // ============================================================================
  // Investigation API
  // ============================================================================

  /**
   * Get screenshot from an investigation job
   */
  async getInvestigationScreenshot(jobId: string): Promise<string> {
    const response = await fetch(`${this.baseUrl}/capabilities/investigation/${jobId}/screenshot`, {
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get screenshot: ${response.statusText}`);
    }
    
    const blob = await response.blob();
    return URL.createObjectURL(blob);
  }

  /**
   * Get HAR file from an investigation job
   */
  async getInvestigationHAR(jobId: string) {
    return this.request<any>(`/capabilities/investigation/${jobId}/har`);
  }

  /**
   * Get domain tree graph from an investigation job
   */
  async getInvestigationDomainTree(jobId: string) {
    return this.request<{
      nodes: Array<{
        id: string;
        label: string;
        type: string;
        depth?: number;
        requests?: number;
        risk?: number;
        resource_type?: string;
      }>;
      edges: Array<{
        source: string;
        target: string;
        type?: string;
      }>;
      summary?: Record<string, any>;
    }>(`/capabilities/investigation/${jobId}/domain-tree`);
  }

  /**
   * Compare two investigation results
   */
  async compareInvestigations(jobId1: string, jobId2: string) {
    return this.request<{
      job1: string;
      job2: string;
      target1: string;
      target2: string;
      visual_similarity: {
        perceptual_hash_similarity: number | null;
        ssim_score: number | null;
        overall_similarity: number;
        is_similar: boolean;
      } | null;
      domain_differences: {
        added_domains: string[];
        removed_domains: string[];
        common_domains: string[];
      };
      findings_comparison: {
        count1: number;
        count2: number;
        new_findings: number;
        resolved_findings: number;
      };
    }>(`/capabilities/investigation/compare?job_id1=${jobId1}&job_id2=${jobId2}`);
  }

  /**
   * Export investigation results
   */
  async exportInvestigation(jobId: string, format: "json" | "html" = "json") {
    const url = `/capabilities/investigation/${jobId}/export?format=${format}`;
    
    if (format === "html") {
      const response = await fetch(`${this.baseUrl}${url}`, {
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
      link.download = `investigation_${jobId}.html`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      return { success: true };
    } else {
      const response = await fetch(`${this.baseUrl}${url}`, {
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
      link.download = `investigation_${jobId}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      return { success: true };
    }
  }

  // Network Monitoring
  async getNetworkLogs(params?: {
    limit?: number;
    offset?: number;
    start_time?: string;
    end_time?: string;
    ip?: string;
    endpoint?: string;
    method?: string;
    status?: number;
    has_tunnel?: boolean;
  }) {
    const query = new URLSearchParams(
      Object.entries(params || {}).reduce((acc, [key, value]) => {
        if (value !== undefined && value !== null) {
          acc[key] = String(value);
        }
        return acc;
      }, {} as Record<string, string>)
    ).toString();
    return this.request<{ logs: any[]; count: number }>(`/network/logs?${query}`);
  }

  async getNetworkLog(requestId: string) {
    return this.request<any>(`/network/logs/${requestId}`);
  }

  async searchNetworkLogs(query: string, limit: number = 100) {
    return this.request<{ logs: any[]; count: number }>(
      `/network/logs/search?q=${encodeURIComponent(query)}&limit=${limit}`
    );
  }

  async getNetworkStats(params?: { start_time?: string; end_time?: string }) {
    const query = new URLSearchParams(
      Object.entries(params || {}).reduce((acc, [key, value]) => {
        if (value !== undefined && value !== null) {
          acc[key] = String(value);
        }
        return acc;
      }, {} as Record<string, string>)
    ).toString();
    return this.request<any>(`/network/stats?${query}`);
  }

  async getTunnelDetections(params?: { limit?: number; min_confidence?: string }) {
    const query = new URLSearchParams(
      Object.entries(params || {}).reduce((acc, [key, value]) => {
        if (value !== undefined && value !== null) {
          acc[key] = String(value);
        }
        return acc;
      }, {} as Record<string, string>)
    ).toString();
    return this.request<{ detections: any[]; count: number }>(`/network/tunnels?${query}`);
  }

  // Blocking
  async blockIP(ip: string, reason: string = "", created_by: string = "") {
    return this.request<{ message: string; ip: string }>("/network/blocks/ip", {
      method: "POST",
      body: JSON.stringify({ ip, reason, created_by }),
    });
  }

  async unblockIP(ip: string) {
    return this.request<{ message: string; ip: string }>(`/network/blocks/ip/${ip}`, {
      method: "DELETE",
    });
  }

  async getBlockedIPs() {
    return this.request<{ blocked_ips: any[]; count: number }>("/network/blocks/ip");
  }

  async blockEndpoint(pattern: string, method: string = "ALL", reason: string = "", created_by: string = "") {
    return this.request<{ message: string; pattern: string; method: string }>("/network/blocks/endpoint", {
      method: "POST",
      body: JSON.stringify({ pattern, method, reason, created_by }),
    });
  }

  async unblockEndpoint(pattern: string) {
    return this.request<{ message: string; pattern: string }>(`/network/blocks/endpoint/${encodeURIComponent(pattern)}`, {
      method: "DELETE",
    });
  }

  async getBlockedEndpoints() {
    return this.request<{ blocked_endpoints: any[]; count: number }>("/network/blocks/endpoint");
  }

  async blockPattern(pattern_type: string, pattern: string, reason: string = "", created_by: string = "") {
    return this.request<{ message: string; block_id: string; pattern_type: string; pattern: string }>(
      "/network/blocks/pattern",
      {
        method: "POST",
        body: JSON.stringify({ pattern_type, pattern, reason, created_by }),
      }
    );
  }

  async unblockPattern(block_id: string) {
    return this.request<{ message: string; block_id: string }>(`/network/blocks/pattern/${block_id}`, {
      method: "DELETE",
    });
  }

  async getBlockedPatterns() {
    return this.request<{ blocked_patterns: any[]; count: number }>("/network/blocks/pattern");
  }

  async getAllBlocks() {
    return this.request<{ ips: any[]; endpoints: any[]; patterns: any[] }>("/network/blocks");
  }

  async getRateLimitStatus(ip: string, endpoint?: string) {
    const query = endpoint ? `?endpoint=${encodeURIComponent(endpoint)}` : "";
    return this.request<any>(`/network/rate-limit/${ip}${query}`);
  }

  async exportNetworkLogs(format: "json" | "csv" | "har", params?: {
    start_time?: string;
    end_time?: string;
    filters?: Record<string, any>;
  }) {
    const response = await fetch(`${this.baseUrl}/network/export`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      },
      body: JSON.stringify({ format, ...params }),
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = `network_logs.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);

    return { success: true };
  }

  // ============================================================================
  // Notifications API
  // ============================================================================

  /**
   * Get notifications for the current user
   */
  async getNotifications(params?: {
    limit?: number;
    unread_only?: boolean;
    channel?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append("limit", params.limit.toString());
    if (params?.unread_only) queryParams.append("unread_only", "true");
    if (params?.channel) queryParams.append("channel", params.channel);
    
    const query = queryParams.toString();
    const url = `/notifications${query ? `?${query}` : ""}`;
    return this.request<{
      notifications: Array<{
        id: string;
        user_id: string;
        channel: string;
        priority: string;
        title: string;
        message: string;
        severity: string;
        read: boolean;
        read_at: string | null;
        metadata: Record<string, any>;
        timestamp: string;
        created_at: string;
      }>;
      unread_count: number;
    }>(url);
  }

  /**
   * Get unread notification count
   */
  async getUnreadCount() {
    return this.request<{ unread_count: number }>("/notifications/unread-count");
  }

  /**
   * Mark a notification as read
   */
  async markNotificationRead(notificationId: string) {
    return this.request<{ message: string; id: string }>(
      `/notifications/${notificationId}/read`,
      {
        method: "PATCH",
      }
    );
  }

  /**
   * Mark all notifications as read
   */
  async markAllNotificationsRead() {
    return this.request<{ message: string; count: number }>(
      "/notifications/mark-all-read",
      {
        method: "POST",
      }
    );
  }

  // ============================================================================
  // Scheduled Searches API
  // ============================================================================

  /**
   * Create a new scheduled search
   */
  async createScheduledSearch(data: {
    name: string;
    description?: string;
    capabilities: string[];
    target: string;
    config?: Record<string, any>;
    schedule_type?: string;
    cron_expression: string;
    timezone?: string;
    enabled?: boolean;
  }) {
    return this.request<{
      id: string;
      user_id: string;
      name: string;
      description: string | null;
      capabilities: string[];
      target: string;
      config: Record<string, any>;
      schedule_type: string;
      cron_expression: string;
      timezone: string;
      enabled: boolean;
      last_run_at: string | null;
      next_run_at: string | null;
      run_count: number;
      created_at: string;
      updated_at: string;
    }>("/scheduled-searches", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * List all scheduled searches for the current user
   */
  async getScheduledSearches(enabled?: boolean) {
    const query = enabled !== undefined ? `?enabled=${enabled}` : "";
    return this.request<Array<{
      id: string;
      user_id: string;
      name: string;
      description: string | null;
      capabilities: string[];
      target: string;
      config: Record<string, any>;
      schedule_type: string;
      cron_expression: string;
      timezone: string;
      enabled: boolean;
      last_run_at: string | null;
      next_run_at: string | null;
      run_count: number;
      created_at: string;
      updated_at: string;
    }>>(`/scheduled-searches${query}`);
  }

  /**
   * Get a specific scheduled search
   */
  async getScheduledSearch(id: string) {
    return this.request<{
      id: string;
      user_id: string;
      name: string;
      description: string | null;
      capabilities: string[];
      target: string;
      config: Record<string, any>;
      schedule_type: string;
      cron_expression: string;
      timezone: string;
      enabled: boolean;
      last_run_at: string | null;
      next_run_at: string | null;
      run_count: number;
      created_at: string;
      updated_at: string;
    }>(`/scheduled-searches/${id}`);
  }

  /**
   * Update a scheduled search
   */
  async updateScheduledSearch(id: string, data: {
    name?: string;
    description?: string;
    capabilities?: string[];
    target?: string;
    config?: Record<string, any>;
    cron_expression?: string;
    timezone?: string;
    enabled?: boolean;
  }) {
    return this.request<{
      id: string;
      user_id: string;
      name: string;
      description: string | null;
      capabilities: string[];
      target: string;
      config: Record<string, any>;
      schedule_type: string;
      cron_expression: string;
      timezone: string;
      enabled: boolean;
      last_run_at: string | null;
      next_run_at: string | null;
      run_count: number;
      created_at: string;
      updated_at: string;
    }>(`/scheduled-searches/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  /**
   * Delete a scheduled search
   */
  async deleteScheduledSearch(id: string) {
    return this.request<void>(`/scheduled-searches/${id}`, {
      method: "DELETE",
    });
  }

  /**
   * Enable a scheduled search
   */
  async enableScheduledSearch(id: string) {
    return this.request<{
      id: string;
      user_id: string;
      name: string;
      description: string | null;
      capabilities: string[];
      target: string;
      config: Record<string, any>;
      schedule_type: string;
      cron_expression: string;
      timezone: string;
      enabled: boolean;
      last_run_at: string | null;
      next_run_at: string | null;
      run_count: number;
      created_at: string;
      updated_at: string;
    }>(`/scheduled-searches/${id}/enable`, {
      method: "POST",
    });
  }

  /**
   * Disable a scheduled search
   */
  async disableScheduledSearch(id: string) {
    return this.request<{
      id: string;
      user_id: string;
      name: string;
      description: string | null;
      capabilities: string[];
      target: string;
      config: Record<string, any>;
      schedule_type: string;
      cron_expression: string;
      timezone: string;
      enabled: boolean;
      last_run_at: string | null;
      next_run_at: string | null;
      run_count: number;
      created_at: string;
      updated_at: string;
    }>(`/scheduled-searches/${id}/disable`, {
      method: "POST",
    });
  }

  /**
   * Manually trigger execution of a scheduled search
   */
  async runScheduledSearchNow(id: string) {
    return this.request<{ message: string; scheduled_search_id: string }>(
      `/scheduled-searches/${id}/run-now`,
      {
        method: "POST",
      }
    );
  }

  /**
   * Get execution history for a scheduled search
   */
  async getScheduledSearchHistory(id: string, limit: number = 50) {
    return this.request<Array<{
      job_id: string;
      status: string;
      created_at: string;
      completed_at: string | null;
      findings_count: number;
      error: string | null;
    }>>(`/scheduled-searches/${id}/history?limit=${limit}`);
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
  // Scheduled Searches
  scheduledSearches: (enabled?: boolean) => ["scheduled-searches", enabled],
  scheduledSearch: (id: string) => ["scheduled-search", id],
  scheduledSearchHistory: (id: string, limit?: number) => ["scheduled-search-history", id, limit],
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


