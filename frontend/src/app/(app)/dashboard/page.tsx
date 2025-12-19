"use client";

import { useState, useEffect } from "react";
import { GlassCard } from "@/components/ui";
import {
  RiskScore,
  CriticalFindings,
  CapabilityCards,
  LiveActivity,
  MiniWorldMap,
  LineChart,
} from "@/components/dashboard";
import { api } from "@/lib/api";
import { mapToRiskScore, mapToFindings, mapToJobs, mapToEvents, mapToCapabilityStats } from "@/lib/data-mappers";

export default function DashboardPage() {
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [criticalFindings, setCriticalFindings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch dashboard overview
        const overview = await api.getDashboardOverview();
        setDashboardData(overview);

        // Fetch critical findings
        const findingsResponse = await api.getDashboardCriticalFindings(10);
        setCriticalFindings(findingsResponse.findings || []);

      } catch (err: any) {
        console.error("Error fetching dashboard data:", err);
        setError(err.message || "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Poll for updates every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Show loading state
  if (loading && !dashboardData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-white/50 font-mono text-sm">Loading dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error && !dashboardData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <p className="text-red-400 font-mono mb-2">Error loading dashboard</p>
            <p className="text-white/50 font-mono text-sm">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  // Use only real data - no fallbacks
  if (!dashboardData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-white/50 font-mono text-sm">Loading dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  const riskScoreData = mapToRiskScore(dashboardData);
  const findingsData = criticalFindings.length > 0 ? mapToFindings(criticalFindings) : [];
  const recentJobs = dashboardData.recent_jobs ? mapToJobs(dashboardData.recent_jobs) : [];
  const recentEvents = dashboardData.recent_events ? mapToEvents(dashboardData.recent_events) : [];
  const capabilityStats = dashboardData.capability_stats ? mapToCapabilityStats(dashboardData.capability_stats) : {};
  const threatMapData = dashboardData.threat_map_data || [];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-mono font-bold text-white">Security Operations Center</h1>
          <p className="text-sm text-white/50">
            Unified view of your organization&apos;s security posture
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-xs font-mono text-emerald-400">All systems operational</span>
          </span>
        </div>
      </div>

      {/* Top row: Risk Score + Critical Findings */}
      <div className="grid lg:grid-cols-2 gap-6">
        <RiskScore
          score={riskScoreData.score}
          riskLevel={riskScoreData.riskLevel}
          trend={riskScoreData.trend}
          criticalIssues={riskScoreData.criticalIssues}
          highIssues={riskScoreData.highIssues}
        />
        <CriticalFindings findings={findingsData} />
      </div>

      {/* Capability Cards */}
      <CapabilityCards stats={capabilityStats} />

      {/* Bottom row: Map + Activity + Trends */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* World map */}
        <GlassCard className="lg:col-span-2 overflow-hidden" padding="none">
          <div className="p-5 border-b border-white/[0.05]">
            <div className="flex items-center justify-between">
              <h2 className="font-mono font-semibold text-white">Global Threat Activity</h2>
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
                </span>
                <span className="text-xs font-mono text-white/50">
                  {threatMapData.length} active threats
                </span>
              </div>
            </div>
          </div>
          <div className="h-64 lg:h-72">
            <MiniWorldMap threats={threatMapData} />
          </div>
        </GlassCard>

        {/* Live Activity */}
        <LiveActivity events={recentEvents} />
      </div>

      {/* Trends row */}
      <div className="grid lg:grid-cols-2 gap-6">
        <LineChart />
        
        {/* Recent Scans Summary */}
        <GlassCard className="p-6" hover={false}>
          <h2 className="font-mono text-lg font-semibold text-white mb-4">Recent Assessments</h2>
          <div className="space-y-3">
            {recentJobs.length > 0 ? recentJobs.map((scan, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:border-white/[0.1] transition-colors"
              >
                <div className="flex items-center gap-3">
                  {scan.status === "running" ? (
                    <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                      <svg className="w-4 h-4 text-blue-400 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </div>
                  ) : (
                    <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                      <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                  <div>
                    <p className="text-sm text-white font-medium">{scan.capability}</p>
                    <p className="text-xs text-white/40 font-mono">{scan.target}</p>
                  </div>
                </div>
                <div className="text-right">
                  {scan.status === "completed" && (
                    <p className="text-sm font-mono text-amber-400">{scan.findings} findings</p>
                  )}
                  <p className="text-xs text-white/40">{scan.time}</p>
                </div>
              </div>
            )) : (
              <div className="py-8 text-center">
                <p className="text-sm text-white/50 font-mono">No recent assessments</p>
                <p className="text-xs text-white/30 mt-1">Start a scan to see results here</p>
              </div>
            )}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
