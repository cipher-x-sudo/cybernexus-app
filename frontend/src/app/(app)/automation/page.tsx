"use client";

import { useState, useEffect } from "react";
import { GlassCard, GlassButton, Badge } from "@/components/ui";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import ScheduledSearchForm from "@/components/automation/ScheduledSearchForm";
import ExecutionHistory from "@/components/automation/ExecutionHistory";

interface ScheduledSearch {
  id: string;
  name: string;
  description: string | null;
  capability: string;
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

export default function AutomationPage() {
  const [scheduledSearches, setScheduledSearches] = useState<ScheduledSearch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingSearch, setEditingSearch] = useState<ScheduledSearch | null>(null);
  const [selectedSearch, setSelectedSearch] = useState<string | null>(null);

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

  if (showForm) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-6">
        <div className="max-w-4xl mx-auto">
          <ScheduledSearchForm
            search={editingSearch}
            onClose={handleFormClose}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Automated Searches</h1>
            <p className="text-gray-300">
              Configure recurring searches to automatically monitor your assets
            </p>
          </div>
          <GlassButton onClick={handleCreate} className="px-6">
            + Create Scheduled Search
          </GlassButton>
        </div>

        {error && (
          <GlassCard className="mb-6 p-4 bg-red-500/20 border-red-500/50">
            <p className="text-red-200">{error}</p>
          </GlassCard>
        )}

        {loading ? (
          <GlassCard className="p-8 text-center">
            <p className="text-gray-300">Loading scheduled searches...</p>
          </GlassCard>
        ) : scheduledSearches.length === 0 ? (
          <GlassCard className="p-8 text-center">
            <p className="text-gray-300 mb-4">No scheduled searches configured</p>
            <GlassButton onClick={handleCreate}>Create Your First Scheduled Search</GlassButton>
          </GlassCard>
        ) : (
          <div className="space-y-4">
            {scheduledSearches.map((search) => (
              <GlassCard key={search.id} className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-semibold text-white">{search.name}</h3>
                      <Badge variant={search.enabled ? "success" : "default"}>
                        {search.enabled ? "Enabled" : "Disabled"}
                      </Badge>
                      <Badge variant="info">
                        {capabilityNames[search.capability] || search.capability}
                      </Badge>
                    </div>
                    {search.description && (
                      <p className="text-gray-300 mb-3">{search.description}</p>
                    )}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">Target:</span>
                        <p className="text-white font-mono">{search.target}</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Schedule:</span>
                        <p className="text-white font-mono text-xs">{search.cron_expression}</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Last Run:</span>
                        <p className="text-white">
                          {search.last_run_at
                            ? formatRelativeTime(new Date(search.last_run_at))
                            : "Never"}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-400">Next Run:</span>
                        <p className="text-white">
                          {search.next_run_at
                            ? formatRelativeTime(new Date(search.next_run_at))
                            : "Not scheduled"}
                        </p>
                      </div>
                    </div>
                    <div className="mt-3 text-sm text-gray-400">
                      Run count: {search.run_count} | Created:{" "}
                      {formatRelativeTime(new Date(search.created_at))}
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 ml-4">
                    <GlassButton
                      size="sm"
                      onClick={() => handleEdit(search)}
                      className="w-full"
                    >
                      Edit
                    </GlassButton>
                    <GlassButton
                      size="sm"
                      onClick={() => handleRunNow(search.id)}
                      className="w-full"
                      variant="secondary"
                    >
                      Run Now
                    </GlassButton>
                    {search.enabled ? (
                      <GlassButton
                        size="sm"
                        onClick={() => handleDisable(search.id)}
                        className="w-full"
                        variant="secondary"
                      >
                        Disable
                      </GlassButton>
                    ) : (
                      <GlassButton
                        size="sm"
                        onClick={() => handleEnable(search.id)}
                        className="w-full"
                        variant="secondary"
                      >
                        Enable
                      </GlassButton>
                    )}
                    <GlassButton
                      size="sm"
                      onClick={() => setSelectedSearch(selectedSearch === search.id ? null : search.id)}
                      className="w-full"
                      variant="secondary"
                    >
                      {selectedSearch === search.id ? "Hide History" : "View History"}
                    </GlassButton>
                    <GlassButton
                      size="sm"
                      onClick={() => handleDelete(search.id)}
                      className="w-full text-red-400 hover:text-red-300"
                      variant="secondary"
                    >
                      Delete
                    </GlassButton>
                  </div>
                </div>
                {selectedSearch === search.id && (
                  <div className="mt-4 pt-4 border-t border-white/10">
                    <ExecutionHistory scheduledSearchId={search.id} />
                  </div>
                )}
              </GlassCard>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

