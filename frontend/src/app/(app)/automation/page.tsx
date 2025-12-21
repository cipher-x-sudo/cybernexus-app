"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { GlassCard, GlassButton, GlassInput } from "@/components/ui";
import { api } from "@/lib/api";
import { cn, formatRelativeTime } from "@/lib/utils";
import ScheduledSearchForm from "@/components/automation/ScheduledSearchForm";
import ExecutionHistory from "@/components/automation/ExecutionHistory";

interface ScheduledSearch {
  id: string;
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
}

const capabilityNames: Record<string, string> = {
  exposure_discovery: "Exposure Discovery",
  dark_web_intelligence: "Dark Web Intelligence",
  email_security: "Email Security",
  infrastructure_testing: "Infrastructure Testing",
};

const capabilityColors: Record<string, { bg: string; accent: string; border: string }> = {
  exposure_discovery: {
    bg: "bg-cyan-500/10",
    accent: "text-cyan-400",
    border: "border-cyan-500/20",
  },
  dark_web_intelligence: {
    bg: "bg-purple-500/10",
    accent: "text-purple-400",
    border: "border-purple-500/20",
  },
  email_security: {
    bg: "bg-amber-500/10",
    accent: "text-amber-400",
    border: "border-amber-500/20",
  },
  infrastructure_testing: {
    bg: "bg-emerald-500/10",
    accent: "text-emerald-400",
    border: "border-emerald-500/20",
  },
};

export default function AutomationPage() {
  const [scheduledSearches, setScheduledSearches] = useState<ScheduledSearch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingSearch, setEditingSearch] = useState<ScheduledSearch | null>(null);
  const [selectedSearch, setSelectedSearch] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const loadScheduledSearches = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getScheduledSearches();
      setScheduledSearches(data);
    } catch (err: any) {
      setError(err.message || "Failed to load scheduled searches");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadScheduledSearches();
  }, []);

  const handleCreate = () => {
    setEditingSearch(null);
    setShowForm(true);
  };

  const handleEdit = (search: ScheduledSearch) => {
    setEditingSearch(search);
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this scheduled search?")) {
      return;
    }

    try {
      await api.deleteScheduledSearch(id);
      await loadScheduledSearches();
    } catch (err: any) {
      alert(err.message || "Failed to delete scheduled search");
    }
  };

  const handleEnable = async (id: string) => {
    try {
      await api.enableScheduledSearch(id);
      await loadScheduledSearches();
    } catch (err: any) {
      alert(err.message || "Failed to enable scheduled search");
    }
  };

  const handleDisable = async (id: string) => {
    try {
      await api.disableScheduledSearch(id);
      await loadScheduledSearches();
    } catch (err: any) {
      alert(err.message || "Failed to disable scheduled search");
    }
  };

  const handleRunNow = async (id: string) => {
    try {
      await api.runScheduledSearchNow(id);
      alert("Scheduled search execution triggered");
    } catch (err: any) {
      alert(err.message || "Failed to trigger scheduled search");
    }
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingSearch(null);
    loadScheduledSearches();
  };

  const filteredSearches = scheduledSearches.filter((search) =>
    search.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    search.target.toLowerCase().includes(searchQuery.toLowerCase()) ||
    search.capabilities.some(cap => capabilityNames[cap]?.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  if (showForm) {
    return (
      <div className="space-y-6">
        <ScheduledSearchForm
          search={editingSearch}
          onClose={handleFormClose}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <Link
            href="/dashboard"
            className="mt-1 p-2 rounded-lg hover:bg-white/[0.05] transition-colors"
          >
            <svg className="w-5 h-5 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
                <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
              </div>
              <h1 className="text-2xl font-mono font-bold text-white">Automated Searches</h1>
            </div>
            <p className="text-lg font-medium text-amber-400">Schedule recurring security scans</p>
            <p className="text-sm text-white/50 mt-1">
              Configure automated searches to continuously monitor your assets
            </p>
          </div>
        </div>
        <GlassButton onClick={handleCreate} variant="primary" size="sm">
          + Create Scheduled Search
        </GlassButton>
      </div>

      {error && (
        <GlassCard className="p-4 border-red-500/20">
          <p className="text-red-400 font-mono text-sm">{error}</p>
        </GlassCard>
      )}

      {/* Search and Stats */}
      {scheduledSearches.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <GlassCard padding="lg">
            <p className="text-xs font-mono text-white/50 mb-1">Total Scheduled</p>
            <p className="text-3xl font-mono font-bold text-white">{scheduledSearches.length}</p>
          </GlassCard>
          <GlassCard padding="lg">
            <p className="text-xs font-mono text-white/50 mb-1">Enabled</p>
            <p className="text-3xl font-mono font-bold text-emerald-400">
              {scheduledSearches.filter((s) => s.enabled).length}
            </p>
          </GlassCard>
          <GlassCard padding="lg">
            <p className="text-xs font-mono text-white/50 mb-1">Total Runs</p>
            <p className="text-3xl font-mono font-bold text-white">
              {scheduledSearches.reduce((sum, s) => sum + (s.run_count || 0), 0)}
            </p>
          </GlassCard>
          <GlassCard padding="lg">
            <p className="text-xs font-mono text-white/50 mb-1">Next Run</p>
            <p className="text-sm font-mono text-white/80">
              {scheduledSearches
                .filter((s) => s.enabled && s.next_run_at)
                .sort((a, b) => {
                  if (!a.next_run_at) return 1;
                  if (!b.next_run_at) return -1;
                  return new Date(a.next_run_at).getTime() - new Date(b.next_run_at).getTime();
                })[0]?.next_run_at
                ? formatRelativeTime(
                    new Date(
                      scheduledSearches
                        .filter((s) => s.enabled && s.next_run_at)
                        .sort((a, b) => {
                          if (!a.next_run_at) return 1;
                          if (!b.next_run_at) return -1;
                          return new Date(a.next_run_at).getTime() - new Date(b.next_run_at).getTime();
                        })[0].next_run_at!
                    )
                  )
                : "None scheduled"}
            </p>
          </GlassCard>
        </div>
      )}

      {/* Search Bar */}
      {scheduledSearches.length > 0 && (
        <GlassCard className="p-6">
          <GlassInput
            placeholder="Search scheduled searches..."
            value={searchQuery}
            onChange={(e) => setSearchQuery((e.target as HTMLInputElement).value)}
          />
        </GlassCard>
      )}

      {/* Scheduled Searches List */}
      <GlassCard className="p-6" padding="none">
        <div className="p-6 border-b border-white/[0.05]">
          <h2 className="font-mono text-lg font-semibold text-white">
            Scheduled Searches ({filteredSearches.length})
          </h2>
        </div>

        {loading ? (
          <div className="py-12 text-center">
            <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm text-white/50 font-mono">Loading scheduled searches...</p>
          </div>
        ) : filteredSearches.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-sm text-white/50 font-mono mb-2">
              {searchQuery ? "No scheduled searches match your search" : "No scheduled searches configured"}
            </p>
            {!searchQuery && (
              <GlassButton onClick={handleCreate} variant="primary" size="sm" className="mt-4">
                Create Your First Scheduled Search
              </GlassButton>
            )}
          </div>
        ) : (
          <div className="divide-y divide-white/[0.05]">
            {filteredSearches.map((search) => {
              // Use first capability for icon color, or default to exposure_discovery
              const firstCapability = (search.capabilities && search.capabilities[0]) || "exposure_discovery";
              const colors = capabilityColors[firstCapability] || capabilityColors.exposure_discovery;
              return (
                <div key={search.id} className="p-6 hover:bg-white/[0.02] transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-start gap-3 mb-3">
                        <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center", colors.bg)}>
                          <svg className={cn("w-4 h-4", colors.accent)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                          </svg>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <h3 className="text-lg font-mono font-semibold text-white">{search.name}</h3>
                            <span
                              className={cn(
                                "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-mono border",
                                search.enabled
                                  ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                                  : "text-white/40 bg-white/5 border-white/10"
                              )}
                            >
                              {search.enabled ? "Enabled" : "Disabled"}
                            </span>
                            {search.capabilities.map((cap) => {
                              const capColors = capabilityColors[cap] || capabilityColors.exposure_discovery;
                              return (
                                <span
                                  key={cap}
                                  className={cn(
                                    "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-mono border",
                                    capColors.bg,
                                    capColors.accent,
                                    capColors.border
                                  )}
                                >
                                  {capabilityNames[cap] || cap}
                                </span>
                              );
                            })}
                          </div>
                          {search.description && (
                            <p className="text-sm text-white/60 mb-3">{search.description}</p>
                          )}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-xs font-mono text-white/50 mb-1">Target</p>
                          <p className="text-sm font-mono text-white/80 truncate">{search.target}</p>
                        </div>
                        <div>
                          <p className="text-xs font-mono text-white/50 mb-1">Schedule</p>
                          <p className="text-sm font-mono text-white/80">{search.cron_expression}</p>
                        </div>
                        <div>
                          <p className="text-xs font-mono text-white/50 mb-1">Last Run</p>
                          <p className="text-sm font-mono text-white/80">
                            {search.last_run_at
                              ? formatRelativeTime(new Date(search.last_run_at))
                              : "Never"}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs font-mono text-white/50 mb-1">Next Run</p>
                          <p className="text-sm font-mono text-white/80">
                            {search.next_run_at
                              ? formatRelativeTime(new Date(search.next_run_at))
                              : "Not scheduled"}
                          </p>
                        </div>
                      </div>

                      <div className="mt-3 flex items-center gap-4 text-xs font-mono text-white/40">
                        <span>Run count: {search.run_count}</span>
                        <span>•</span>
                        <span>Created: {formatRelativeTime(new Date(search.created_at))}</span>
                      </div>

                      {selectedSearch === search.id && (
                        <div className="mt-4 pt-4 border-t border-white/10">
                          <ExecutionHistory scheduledSearchId={search.id} />
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col gap-2 ml-6">
                      <GlassButton
                        size="sm"
                        onClick={() => handleEdit(search)}
                        variant="secondary"
                      >
                        Edit
                      </GlassButton>
                      <GlassButton
                        size="sm"
                        onClick={() => handleRunNow(search.id)}
                        variant="secondary"
                      >
                        Run Now
                      </GlassButton>
                      {search.enabled ? (
                        <GlassButton
                          size="sm"
                          onClick={() => handleDisable(search.id)}
                          variant="secondary"
                        >
                          Disable
                        </GlassButton>
                      ) : (
                        <GlassButton
                          size="sm"
                          onClick={() => handleEnable(search.id)}
                          variant="secondary"
                        >
                          Enable
                        </GlassButton>
                      )}
                      <GlassButton
                        size="sm"
                        onClick={() => setSelectedSearch(selectedSearch === search.id ? null : search.id)}
                        variant="secondary"
                      >
                        {selectedSearch === search.id ? "Hide History" : "View History"}
                      </GlassButton>
                      <GlassButton
                        size="sm"
                        onClick={() => handleDelete(search.id)}
                        variant="danger"
                      >
                        Delete
                      </GlassButton>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </GlassCard>
    </div>
  );
}
