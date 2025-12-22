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
  JobHistoryCard,
  SecurityScoreDetailModal,
} from "@/components/dashboard";
import { api } from "@/lib/api";
import { mapToRiskScore, mapToFindings, mapToJobs, mapToEvents, mapToCapabilityStats } from "@/lib/data-mappers";

export default function DashboardPage() {
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [criticalFindings, setCriticalFindings] = useState<any[]>([]);
  const [threatsOverTime, setThreatsOverTime] = useState<{ data: number[]; labels: string[] }>({ data: [], labels: [] });
  const [recentEvents, setRecentEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scoreModalOpen, setScoreModalOpen] = useState(false);

  const aggregateThreatsByTime = (items: any[]) => {
    if (!items || items.length === 0) {
      return { data: [], labels: [] };
    }

    const months: { [key: string]: number } = {};
    const monthLabels: string[] = [];
    const now = new Date();
    
    for (let i = 11; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      const monthLabel = date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
      months[monthKey] = 0;
      monthLabels.push(monthLabel);
    }

    items.forEach((item) => {
      let timestamp: string | null = null;
      
      if (item.discovered_at) {
        timestamp = item.discovered_at;
      } else if (item.timestamp) {
        timestamp = item.timestamp;
      } else if (item.created_at) {
        timestamp = item.created_at;
      }

      if (timestamp) {
        try {
          const date = new Date(timestamp);
          const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          if (months.hasOwnProperty(monthKey)) {
            months[monthKey]++;
          }
        } catch (e) {
        }
      }
    });

    const data = Object.values(months);
    const labels = monthLabels;

    return { data, labels };
  };

  const fetchData = async (showLoading: boolean = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);

      const overview = await api.getDashboardOverview();
      setDashboardData(overview);

      const findingsResponse = await api.getDashboardCriticalFindings(10);
      setCriticalFindings(findingsResponse.findings || []);

        try {
          const timelineEvents = await api.getRecentTimelineEvents(20);
          if (timelineEvents && timelineEvents.length > 0) {
            const jobEvents = timelineEvents.filter((event: any) => {
              const type = event.type || "";
              return type === "job_started" || 
                     type === "job_completed" || 
                     type === "job_created" ||
                     type === "scan_started" ||
                     type === "scan_completed" ||
                     type === "scan_queued";
            });
            setRecentEvents(jobEvents);
          } else {
            const allEvents = overview.recent_events || [];
            const jobEvents = allEvents.filter((event: any) => {
              const type = event.type || "";
              return type === "job_started" || 
                     type === "job_completed" || 
                     type === "job_created" ||
                     type === "scan_started" ||
                     type === "scan_completed" ||
                     type === "scan_queued";
            });
            setRecentEvents(jobEvents);
          }
        } catch (timelineErr) {
          console.error("Error fetching timeline events:", timelineErr);
          const allEvents = overview.recent_events || [];
          const jobEvents = allEvents.filter((event: any) => {
            const type = event.type || "";
            return type === "job_started" || 
                   type === "job_completed" || 
                   type === "job_created" ||
                   type === "scan_started" ||
                   type === "scan_completed" ||
                   type === "scan_queued";
          });
          setRecentEvents(jobEvents);
        }

        try {
          const timelineEvents = await api.getTimelineEvents({});
          
          let dataForChart: any[] = [];
          if (timelineEvents && timelineEvents.length > 0) {
            dataForChart = timelineEvents;
          } else if (overview.recent_events && overview.recent_events.length > 0) {
            dataForChart = overview.recent_events;
          } else {
            if (overview.threat_map_data && overview.threat_map_data.length > 0) {
              dataForChart = overview.threat_map_data;
            }
          }

          const aggregated = aggregateThreatsByTime(dataForChart);
          setThreatsOverTime(aggregated);
        } catch (chartErr) {
          console.error("Error fetching chart data:", chartErr);
          if (overview.threat_map_data) {
            const aggregated = aggregateThreatsByTime(overview.threat_map_data);
            setThreatsOverTime(aggregated);
          }
        }

    } catch (err: any) {
      console.error("Error fetching dashboard data:", err);
      setError(err.message || "Failed to load dashboard data");
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    fetchData(true);

    const interval = setInterval(() => fetchData(false), 30000);
    return () => clearInterval(interval);
  }, []);

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
  const mappedRecentEvents = recentEvents.length > 0 
    ? mapToEvents(recentEvents) 
    : (dashboardData.recent_events ? mapToEvents(dashboardData.recent_events) : []);
  const capabilityStats = dashboardData.capability_stats ? mapToCapabilityStats(dashboardData.capability_stats) : {};
  const threatMapData = dashboardData.threat_map_data || [];

  return (
    <div className="space-y-6">
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

      <div className="grid lg:grid-cols-2 gap-6">
        <RiskScore
          score={riskScoreData.score}
          riskLevel={riskScoreData.riskLevel}
          trend={riskScoreData.trend}
          criticalIssues={riskScoreData.criticalIssues}
          highIssues={riskScoreData.highIssues}
          onClick={() => setScoreModalOpen(true)}
        />
        <CriticalFindings 
          findings={findingsData} 
          onFindingResolved={() => fetchData(false)}
        />
      </div>

      <SecurityScoreDetailModal
        open={scoreModalOpen}
        onOpenChange={setScoreModalOpen}
        currentScore={riskScoreData.score}
        riskLevel={riskScoreData.riskLevel}
        trend={riskScoreData.trend}
        criticalIssues={riskScoreData.criticalIssues}
        highIssues={riskScoreData.highIssues}
      />

      <CapabilityCards stats={capabilityStats} />

      <div className="grid lg:grid-cols-3 gap-6">
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

        <LiveActivity events={mappedRecentEvents} />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <LineChart data={threatsOverTime.data} labels={threatsOverTime.labels} />
        <JobHistoryCard limit={5} />
      </div>
    </div>
  );
}
