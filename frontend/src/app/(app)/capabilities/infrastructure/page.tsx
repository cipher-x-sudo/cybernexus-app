"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { GlassCard, GlassButton, GlassInput } from "@/components/ui";
import { api, CapabilityFinding, CapabilityJob } from "@/lib/api";
import {
  extractInfrastructureFindings,
  calculateInfrastructureStats,
  InfrastructureFinding,
  InfrastructureStats,
} from "@/components/infrastructure/helpers";
import { InfrastructureCard } from "@/components/infrastructure/InfrastructureCard";
import { StatsTile } from "@/components/infrastructure/StatsTile";
import { FilterPanel, SortOption, SortDirection } from "@/components/infrastructure/FilterPanel";
import {
  SeverityDistributionChart,
  RiskHeatmap,
  TimelineChart,
  TestCoverageChart,
} from "@/components/infrastructure/InfrastructureCharts";
import { exportInfrastructure } from "@/lib/export";

export default function InfrastructurePage() {
  const [target, setTarget] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [currentJob, setCurrentJob] = useState<CapabilityJob | null>(null);
  const [findings, setFindings] = useState<CapabilityFinding[]>([]);
  const [selectedFinding, setSelectedFinding] = useState<InfrastructureFinding | null>(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<SortOption>("severity");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  // Config states
  const [testConfig, setTestConfig] = useState({
    crlf: true,
    pathTraversal: true,
    versionDetection: true,
    cveLookup: true,
    bypassTechniques: false,
  });

  // Refs for cleanup
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isPollingRef = useRef(false);
  const scanStartTimeRef = useRef<Date | null>(null);

  // Extract infrastructure findings
  const infrastructureFindings = useMemo(
    () => extractInfrastructureFindings(findings),
    [findings]
  );

  // Calculate stats
  const stats = useMemo(
    () => calculateInfrastructureStats(infrastructureFindings, testConfig),
    [infrastructureFindings, testConfig]
  );

  // Filter and sort findings
  const filteredAndSortedFindings = useMemo(() => {
    let filtered = infrastructureFindings;

    // Severity filter
    if (severityFilter !== "all") {
      filtered = filtered.filter((f) => f.severity === severityFilter);
    }

    // Category filter
    if (categoryFilter !== "all") {
      filtered = filtered.filter((f) => f.category === categoryFilter);
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (f) =>
          f.title.toLowerCase().includes(query) ||
          f.description.toLowerCase().includes(query) ||
          JSON.stringify(f.evidence).toLowerCase().includes(query)
      );
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case "severity":
          const severityOrder = { critical: 5, high: 4, medium: 3, low: 2, info: 1 };
          comparison = severityOrder[b.severity] - severityOrder[a.severity];
          break;
        case "date":
          comparison = new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
          break;
        case "category":
          comparison = a.category.localeCompare(b.category);
          break;
        case "risk_score":
          comparison = b.riskScore - a.riskScore;
          break;
      }
      return sortDirection === "asc" ? -comparison : comparison;
    });

    return filtered;
  }, [infrastructureFindings, severityFilter, categoryFilter, searchQuery, sortBy, sortDirection]);

  // Timeline data
  const timelineData = useMemo(() => {
    const timeMap = new Map<string, number>();
    infrastructureFindings.forEach((finding) => {
      const time = finding.timestamp.split(" ")[0] || "Just now";
      timeMap.set(time, (timeMap.get(time) || 0) + 1);
    });
    return Array.from(timeMap.entries()).map(([time, count]) => ({ time, count }));
  }, [infrastructureFindings]);

  // Debounced search - not used directly, search is handled in useMemo filter

  // Color scheme
  const colors = {
    accent: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    glow: "shadow-[0_0_30px_rgba(16,185,129,0.2)]",
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Poll for job status
  const pollJobStatus = useCallback(async (jobId: string) => {
    try {
      const job = await api.getJobStatus(jobId);
      setCurrentJob(job);
      setProgress(job.progress);

      if (job.status === "completed") {
        const apiFindings = await api.getJobFindings(jobId);
        setFindings(apiFindings);
        setIsScanning(false);
        setProgress(100);
        return true;
      } else if (job.status === "failed") {
        setError(job.error || "Scan failed");
        setIsScanning(false);
        return true;
      }
      return false;
    } catch (err) {
      console.error("Error polling job status:", err);
      return false;
    }
  }, []);

  const handleScan = async () => {
    if (!target.trim()) return;

    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    setIsScanning(true);
    setProgress(0);
    setError(null);
    setFindings([]);
    setSelectedFinding(null);
    scanStartTimeRef.current = new Date();
    isPollingRef.current = false;

    try {
      const job = await api.createCapabilityJob({
        capability: "infrastructure_testing",
        target: target.trim(),
        priority: "normal",
        config: testConfig,
      });

      setCurrentJob(job);

      // Poll for job completion
      pollIntervalRef.current = setInterval(async () => {
        if (isPollingRef.current) {
          return;
        }

        try {
          isPollingRef.current = true;
          const done = await pollJobStatus(job.id);
          if (done && pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
            if (timeoutRef.current) {
              clearTimeout(timeoutRef.current);
              timeoutRef.current = null;
            }
          }
        } catch (err) {
          console.error("[Polling] Error:", err);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setError("Failed to check job status");
          setIsScanning(false);
        } finally {
          isPollingRef.current = false;
        }
      }, 5000);

      // Timeout after 5 minutes
      timeoutRef.current = setTimeout(() => {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setIsScanning((current: boolean) => {
          if (current) {
            setError("Scan timed out");
            return false;
          }
          return current;
        });
      }, 300000);
    } catch (err) {
      console.error("Scan error:", err);
      setError(err instanceof Error ? err.message : "Failed to start scan");
      setIsScanning(false);
    }
  };

  const handleExport = (format: "json" | "csv" | "pdf") => {
    exportInfrastructure(format, infrastructureFindings, stats, target);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <Link
            href="/capabilities"
            className="mt-1 p-2 rounded-lg hover:bg-white/[0.05] transition-colors"
          >
            <svg className="w-5 h-5 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center", colors.bg)}>
                <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                </svg>
              </div>
              <h1 className="text-2xl font-mono font-bold text-white">Infrastructure Testing</h1>
            </div>
            <p className={cn("text-lg font-medium", colors.accent)}>Are our servers misconfigured?</p>
            <p className="text-sm text-white/50 mt-1">
              Scan for CRLF injection, path traversal, and web server misconfigurations
            </p>
          </div>
        </div>
      </div>

      {/* Scan Input */}
      <GlassCard className={cn("p-6", colors.border)} hover={false}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleScan();
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-mono text-white/70 mb-2">Target URL</label>
            <div className="relative">
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="https://example.com"
                disabled={isScanning}
                className={cn(
                  "w-full h-12 px-4 pr-40",
                  "bg-white/[0.03] border border-white/[0.08] rounded-xl",
                  "text-white placeholder-white/30",
                  "font-mono text-sm",
                  "focus:outline-none focus:border-amber-500/40",
                  "transition-all duration-200",
                  "disabled:opacity-50"
                )}
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowConfig(!showConfig)}
                  className={cn(
                    "p-2 rounded-lg transition-colors",
                    showConfig ? "bg-white/[0.1] text-white" : "text-white/40 hover:text-white/60"
                  )}
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </button>
                <GlassButton type="submit" variant="primary" size="sm" loading={isScanning}>
                  {isScanning ? "Scanning..." : "Start Scan"}
                </GlassButton>
              </div>
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-mono animate-fade-in">
              {error}
            </div>
          )}

          {isScanning && (
            <div className="space-y-2 animate-fade-in">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-white/50">
                  {currentJob?.status === "running" ? "Scanning..." : "Starting..."}
                </span>
                <span className={colors.accent}>{Math.round(progress)}%</span>
              </div>
              <div className="h-1.5 bg-white/[0.05] rounded-full overflow-hidden">
                <div
                  className={cn("h-full rounded-full transition-all duration-300", colors.bg.replace("/10", "/50"))}
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {showConfig && (
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] animate-fade-in">
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={testConfig.crlf}
                      onChange={(e) => setTestConfig({ ...testConfig, crlf: e.target.checked })}
                      className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-emerald-500"
                    />
                    <span className="text-xs text-white/60 group-hover:text-white/80">CRLF injection</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={testConfig.pathTraversal}
                      onChange={(e) => setTestConfig({ ...testConfig, pathTraversal: e.target.checked })}
                      className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-emerald-500"
                    />
                    <span className="text-xs text-white/60 group-hover:text-white/80">Path traversal</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={testConfig.versionDetection}
                      onChange={(e) => setTestConfig({ ...testConfig, versionDetection: e.target.checked })}
                      className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-emerald-500"
                    />
                    <span className="text-xs text-white/60 group-hover:text-white/80">Version detection</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={testConfig.cveLookup}
                      onChange={(e) => setTestConfig({ ...testConfig, cveLookup: e.target.checked })}
                      className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-emerald-500"
                    />
                    <span className="text-xs text-white/60 group-hover:text-white/80">CVE lookup</span>
                  </label>
                </div>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={testConfig.bypassTechniques}
                    onChange={(e) => setTestConfig({ ...testConfig, bypassTechniques: e.target.checked })}
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-emerald-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Test 401/403 bypass techniques</span>
                </label>
              </div>
            </div>
          )}
        </form>
      </GlassCard>

      {/* Statistics Dashboard */}
      {infrastructureFindings.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsTile
            title="Total Findings"
            value={stats.totalFindings}
            variant="default"
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
          />
          <StatsTile
            title="Critical"
            value={stats.criticalFindings}
            variant="critical"
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            }
          />
          <StatsTile
            title="High"
            value={stats.highFindings}
            variant="warning"
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <StatsTile
            title="Avg Risk Score"
            value={stats.averageRiskScore}
            variant="info"
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            }
          />
        </div>
      )}

      {/* Export Actions */}
      {infrastructureFindings.length > 0 && (
        <div className="flex items-center justify-end gap-2">
          <GlassButton
            variant="ghost"
            size="sm"
            onClick={() => handleExport("json")}
          >
            Export JSON
          </GlassButton>
          <GlassButton
            variant="ghost"
            size="sm"
            onClick={() => handleExport("csv")}
          >
            Export CSV
          </GlassButton>
          <GlassButton
            variant="ghost"
            size="sm"
            onClick={() => handleExport("pdf")}
          >
            Export PDF
          </GlassButton>
        </div>
      )}

      {/* Main Content Area */}
      {infrastructureFindings.length > 0 ? (
        <div className="grid lg:grid-cols-4 gap-6">
          {/* Left Sidebar - Filters and Charts */}
          <div className="lg:col-span-1 space-y-4">
            <FilterPanel
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              severityFilter={severityFilter}
              onSeverityFilterChange={setSeverityFilter}
              categoryFilter={categoryFilter}
              onCategoryFilterChange={setCategoryFilter}
              sortBy={sortBy}
              onSortByChange={setSortBy}
              sortDirection={sortDirection}
              onSortDirectionChange={setSortDirection}
            />

            <div className="space-y-4">
              <SeverityDistributionChart stats={stats} />
              <TestCoverageChart stats={stats} />
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredAndSortedFindings.map((finding) => (
                <InfrastructureCard
                  key={finding.id}
                  finding={finding}
                  isSelected={selectedFinding?.id === finding.id}
                  onClick={() => setSelectedFinding(finding)}
                />
              ))}
              {filteredAndSortedFindings.length === 0 && (
                <div className="col-span-full py-12 text-center text-white/40">
                  <p className="font-mono">No findings match your filters</p>
                </div>
              )}
            </div>

            {/* Additional Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <RiskHeatmap findings={infrastructureFindings} />
              <TimelineChart timelineData={timelineData} />
            </div>
          </div>
        </div>
      ) : (
        <GlassCard className="p-12 text-center" hover={false}>
          <div className={cn("w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center", colors.bg)}>
            <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
            </svg>
          </div>
          <p className="text-white/50 font-mono">No findings yet</p>
          <p className="text-sm text-white/30 mt-1">Enter a target and start a scan</p>
        </GlassCard>
      )}

      {/* Finding Details Sidebar */}
      {selectedFinding && (
        <GlassCard className="p-6 sticky top-6" hover={false}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-mono text-lg font-semibold text-white">Details</h2>
            <button
              onClick={() => setSelectedFinding(null)}
              className="text-white/40 hover:text-white/60"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <span className={cn(
                "px-2 py-0.5 text-xs font-mono uppercase rounded",
                selectedFinding.severity === "critical" && "bg-red-500/20 text-red-400",
                selectedFinding.severity === "high" && "bg-orange-500/20 text-orange-400",
                selectedFinding.severity === "medium" && "bg-amber-500/20 text-amber-400",
                selectedFinding.severity === "low" && "bg-blue-500/20 text-blue-400",
                selectedFinding.severity === "info" && "bg-purple-500/20 text-purple-400"
              )}>
                {selectedFinding.severity}
              </span>
              <span className="px-2 py-0.5 text-xs font-mono text-white/60 bg-white/5 rounded">
                {selectedFinding.category}
              </span>
            </div>

            <div>
              <h3 className="text-sm font-medium text-white mb-2">{selectedFinding.title}</h3>
              <p className="text-sm text-white/60">{selectedFinding.description}</p>
            </div>

            <div>
              <h4 className="text-xs font-mono text-white/50 mb-2">Evidence</h4>
              <pre className="p-3 rounded-lg bg-black/30 text-xs font-mono text-white/70 overflow-x-auto whitespace-pre-wrap max-h-48 overflow-y-auto">
                {JSON.stringify(selectedFinding.evidence, null, 2)}
              </pre>
            </div>

            {selectedFinding.recommendations.length > 0 && (
              <div>
                <h4 className="text-xs font-mono text-white/50 mb-2">Recommendations</h4>
                <ul className="space-y-1">
                  {selectedFinding.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-white/70">
                      <span className={colors.accent}>•</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </GlassCard>
      )}
    </div>
  );
}
