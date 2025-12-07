"use client";

import { useState, useEffect, useMemo } from "react";
import { GlassCard, GlassButton, GlassInput, Badge } from "@/components/ui";
import { cn, formatRelativeTime } from "@/lib/utils";

interface Credential {
  id: string;
  email: string;
  domain: string;
  password: string;
  source: string;
  severity: "critical" | "high" | "medium" | "low";
  foundAt: Date;
  status: "active" | "resolved" | "investigating";
}

// Generate credentials only on client to avoid hydration mismatch
function generateMockCredentials(): Credential[] {
  const now = Date.now();
  return [
    {
      id: "1",
      email: "admin@company.com",
      domain: "company.com",
      password: "p@$$w0rd123",
      source: "Data Breach - MegaCorp",
      severity: "critical",
      foundAt: new Date(now - 2 * 60 * 60000),
      status: "active",
    },
    {
      id: "2",
      email: "john.doe@company.com",
      domain: "company.com",
      password: "JohnDoe2024!",
      source: "Paste Site",
      severity: "high",
      foundAt: new Date(now - 24 * 60 * 60000),
      status: "investigating",
    },
    {
      id: "3",
      email: "sarah.smith@company.com",
      domain: "company.com",
      password: "S@rah123",
      source: "Dark Web Forum",
      severity: "high",
      foundAt: new Date(now - 3 * 24 * 60 * 60000),
      status: "resolved",
    },
    {
      id: "4",
      email: "dev@company.com",
      domain: "company.com",
      password: "dev_pass_temp",
      source: "GitHub Commit",
      severity: "medium",
      foundAt: new Date(now - 7 * 24 * 60 * 60000),
      status: "active",
    },
    {
      id: "5",
      email: "support@company.com",
      domain: "company.com",
      password: "Support2023",
      source: "Stealer Logs",
      severity: "critical",
      foundAt: new Date(now - 12 * 60 * 60000),
      status: "active",
    },
  ];
}

export default function CredentialsPage() {
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [selectedCredential, setSelectedCredential] = useState<Credential | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => {
    setCredentials(generateMockCredentials());
  }, []);

  const filteredCredentials = credentials.filter((cred) => {
    if (statusFilter !== "all" && cred.status !== statusFilter) return false;
    if (searchQuery && !cred.email.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const statusColors = {
    active: "bg-red-500/20 text-red-400 border-red-500/30",
    investigating: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    resolved: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-mono font-bold text-white">Credentials</h1>
          <p className="text-sm text-white/50">
            Monitor and manage leaked credential alerts
          </p>
        </div>

        <div className="flex gap-3">
          <GlassButton variant="secondary" size="sm">
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export PDF
          </GlassButton>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total Leaked", value: credentials.length, color: "text-white" },
          { label: "Active", value: credentials.filter((c) => c.status === "active").length, color: "text-red-400" },
          { label: "Investigating", value: credentials.filter((c) => c.status === "investigating").length, color: "text-yellow-400" },
          { label: "Resolved", value: credentials.filter((c) => c.status === "resolved").length, color: "text-emerald-400" },
        ].map((stat) => (
          <GlassCard key={stat.label} padding="lg">
            <p className="text-sm font-mono text-white/50 mb-1">{stat.label}</p>
            <p className={cn("text-3xl font-mono font-bold", stat.color)}>{stat.value}</p>
          </GlassCard>
        ))}
      </div>

      {/* Split view */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* List */}
        <GlassCard padding="none" className="h-[600px] flex flex-col">
          {/* Filters */}
          <div className="p-4 border-b border-white/[0.05] space-y-3">
            <GlassInput
              placeholder="Search by email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              }
            />
            <div className="flex gap-2">
              {["all", "active", "investigating", "resolved"].map((status) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={cn(
                    "px-3 py-1.5 rounded-lg font-mono text-xs transition-all",
                    statusFilter === status
                      ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                      : "bg-white/[0.03] text-white/60 border border-white/[0.08]"
                  )}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* List items */}
          <div className="flex-1 overflow-y-auto">
            {filteredCredentials.map((cred) => (
              <div
                key={cred.id}
                onClick={() => setSelectedCredential(cred)}
                className={cn(
                  "p-4 border-b border-white/[0.03] cursor-pointer transition-colors",
                  selectedCredential?.id === cred.id
                    ? "bg-amber-500/10"
                    : "hover:bg-white/[0.02]"
                )}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Badge variant={cred.severity} size="sm">
                      {cred.severity}
                    </Badge>
                    <span className={cn("text-xs px-2 py-0.5 rounded-full border", statusColors[cred.status])}>
                      {cred.status}
                    </span>
                  </div>
                  <span className="text-xs text-white/30">{formatRelativeTime(cred.foundAt)}</span>
                </div>
                <p className="font-mono text-sm text-white mb-1">{cred.email}</p>
                <p className="text-xs text-white/50">{cred.source}</p>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Detail panel */}
        <GlassCard className="h-[600px]">
          {selectedCredential ? (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="font-mono font-semibold text-white">Credential Details</h3>
                <button
                  onClick={() => setSelectedCredential(null)}
                  className="text-white/40 hover:text-white"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-xs text-white/40 mb-1">Email</p>
                  <p className="font-mono text-white">{selectedCredential.email}</p>
                </div>

                <div>
                  <p className="text-xs text-white/40 mb-1">Password (Exposed)</p>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 p-3 rounded-lg bg-white/[0.03] border border-white/[0.08] font-mono text-red-400 text-sm">
                      {selectedCredential.password}
                    </code>
                    <GlassButton variant="ghost" size="sm">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </GlassButton>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-white/40 mb-1">Domain</p>
                    <p className="font-mono text-white">{selectedCredential.domain}</p>
                  </div>
                  <div>
                    <p className="text-xs text-white/40 mb-1">Source</p>
                    <p className="font-mono text-white">{selectedCredential.source}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-white/40 mb-1">Severity</p>
                    <Badge variant={selectedCredential.severity}>
                      {selectedCredential.severity}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-xs text-white/40 mb-1">Status</p>
                    <span className={cn("text-xs px-2 py-0.5 rounded-full border", statusColors[selectedCredential.status])}>
                      {selectedCredential.status}
                    </span>
                  </div>
                </div>

                <div>
                  <p className="text-xs text-white/40 mb-1">Found At</p>
                  <p className="font-mono text-white">
                    {selectedCredential.foundAt.toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="pt-4 border-t border-white/[0.05] space-y-2">
                <GlassButton variant="primary" className="w-full">
                  Force Password Reset
                </GlassButton>
                <GlassButton variant="secondary" className="w-full">
                  Mark as Resolved
                </GlassButton>
                <GlassButton variant="ghost" className="w-full">
                  View Timeline
                </GlassButton>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-white/30">
              <div className="text-center">
                <svg className="w-16 h-16 mx-auto mb-4 text-white/10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                </svg>
                <p className="font-mono">Select a credential to view details</p>
              </div>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
}

