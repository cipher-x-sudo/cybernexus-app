"use client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

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
};


