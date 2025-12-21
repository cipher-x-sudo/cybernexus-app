"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { GlassCard, GlassButton } from "@/components/ui";
import { api, JobDetail } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function JobDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;
  
  const [job, setJob] = useState<JobDetail | null>(null);
  const [findings, setFindings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "findings" | "logs" | "config">("overview");

  useEffect(() => {
    const fetchJobDetails = async () => {
      try {
        setLoading(true);
        const jobData = await api.getJobDetails(jobId);
        // Normalize capability field: convert capability (singular) to capabilities (array)
        // Backend may return 'capability' (singular) but frontend expects 'capabilities' (array)
        const jobDataAny = jobData as any;
        const normalizedJob = {
          ...jobData,
          capabilities: jobData.capabilities || (jobDataAny.capability ? [jobDataAny.capability] : []),
        };
        setJob(normalizedJob as JobDetail);
        
        // Fetch findings
        try {
          const findingsData = await api.getJobFindings(jobId);
          setFindings(findingsData || []);
        } catch (err) {
          console.error("Error fetching findings:", err);
        }
      } catch (error) {
        console.error("Error fetching job details:", error);
      } finally {
        setLoading(false);
      }
    };

    if (jobId) {
      fetchJobDetails();
      
      // Poll for updates if job is running
      const interval = setInterval(() => {
        if (job && (job.status === "running" || job.status === "pending" || job.status === "queued")) {
          fetchJobDetails();
        }
      }, 5000);
      
      return () => clearInterval(interval);
    }
  }, [jobId]);

  const handleExport = async (format: "json" | "csv") => {
    try {
      setExporting(true);
      const blob = await api.exportJobResults(jobId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `job_${jobId}_export.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Error exporting job results:", error);
      alert("Failed to export job results");
    } finally {
      setExporting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
      case "running":
        return "text-blue-400 bg-blue-500/10 border-blue-500/20";
      case "failed":
        return "text-red-400 bg-red-500/10 border-red-500/20";
      case "pending":
      case "queued":
        return "text-amber-400 bg-amber-500/10 border-amber-500/20";
      default:
        return "text-white/40 bg-white/5 border-white/10";
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "N/A";
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  if (loading && !job) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-white/50 font-mono text-sm">Loading job details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <p className="text-red-400 font-mono mb-2">Job not found</p>
            <GlassButton onClick={() => router.push("/jobs")} className="mt-4">
              Back to Job History
            </GlassButton>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={() => router.push("/jobs")}
              className="text-white/50 hover:text-white transition-colors"
            >
              ← Back
            </button>
            <h1 className="text-2xl font-mono font-bold text-white">Job Details</h1>
          </div>
          <p className="text-sm text-white/50 font-mono">{job.id}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={cn("inline-flex items-center px-3 py-1.5 rounded-full text-sm font-mono border", getStatusColor(job.status))}>
            {job.status}
          </span>
          <GlassButton
            onClick={() => router.push(`/graph?jobId=${jobId}&depth=2`)}
            className="text-xs"
          >
            View in Graph
          </GlassButton>
          <GlassButton
            onClick={() => handleExport("json")}
            disabled={exporting}
            className="text-xs"
          >
            {exporting ? "Exporting..." : "Export JSON"}
          </GlassButton>
          <GlassButton
            onClick={() => handleExport("csv")}
            disabled={exporting}
            className="text-xs"
          >
            {exporting ? "Exporting..." : "Export CSV"}
          </GlassButton>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-white/[0.05]">
        {[
          { id: "overview", label: "Overview" },
          { id: "findings", label: `Findings (${findings.length})` },
          { id: "logs", label: "Execution Logs" },
          { id: "config", label: "Configuration" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={cn(
              "px-4 py-2 text-sm font-mono transition-colors border-b-2",
              activeTab === tab.id
                ? "text-amber-400 border-amber-500"
                : "text-white/50 border-transparent hover:text-white/80"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === "overview" && (
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Basic Info */}
          <GlassCard className="p-6">
            <h2 className="font-mono text-lg font-semibold text-white mb-4">Basic Information</h2>
            <div className="space-y-4">
              <div>
                <p className="text-xs font-mono text-white/50 mb-1">Capabilities</p>
                <p className="text-sm text-white font-medium">
                  {job.capabilities && job.capabilities.length > 0 
                    ? job.capabilities.join(", ")
                    : "Unknown"}
                </p>
              </div>
              <div>
                <p className="text-xs font-mono text-white/50 mb-1">Target</p>
                <p className="text-sm font-mono text-white/80">{job.target}</p>
              </div>
              <div>
                <p className="text-xs font-mono text-white/50 mb-1">Priority</p>
                <p className="text-sm text-white font-medium">{job.priority}</p>
              </div>
              <div>
                <p className="text-xs font-mono text-white/50 mb-1">Progress</p>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-amber-500 transition-all"
                      style={{ width: `${job.progress}%` }}
                    />
                  </div>
                  <span className="text-sm font-mono text-white/60">{job.progress}%</span>
                </div>
              </div>
              <div>
                <p className="text-xs font-mono text-white/50 mb-1">Findings Count</p>
                <p className="text-sm text-white font-medium">{job.findings_count}</p>
              </div>
            </div>
          </GlassCard>

          {/* Timestamps */}
          <GlassCard className="p-6">
            <h2 className="font-mono text-lg font-semibold text-white mb-4">Timeline</h2>
            <div className="space-y-4">
              <div>
                <p className="text-xs font-mono text-white/50 mb-1">Created At</p>
                <p className="text-sm font-mono text-white/80">{formatDate(job.created_at)}</p>
              </div>
              <div>
                <p className="text-xs font-mono text-white/50 mb-1">Started At</p>
                <p className="text-sm font-mono text-white/80">{formatDate(job.started_at)}</p>
              </div>
              <div>
                <p className="text-xs font-mono text-white/50 mb-1">Completed At</p>
                <p className="text-sm font-mono text-white/80">{formatDate(job.completed_at)}</p>
              </div>
              {job.started_at && job.completed_at && (
                <div>
                  <p className="text-xs font-mono text-white/50 mb-1">Duration</p>
                  <p className="text-sm font-mono text-white/80">
                    {Math.round((new Date(job.completed_at).getTime() - new Date(job.started_at).getTime()) / 1000)}s
                  </p>
                </div>
              )}
            </div>
          </GlassCard>

          {/* Error Logs */}
          {job.error && (
            <GlassCard className="p-6 lg:col-span-2">
              <h2 className="font-mono text-lg font-semibold text-red-400 mb-4">Error</h2>
              <pre className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-sm font-mono text-red-300 whitespace-pre-wrap overflow-x-auto">
                {job.error}
              </pre>
            </GlassCard>
          )}
        </div>
      )}

      {/* Findings Tab */}
      {activeTab === "findings" && (
        <GlassCard className="p-6">
          <h2 className="font-mono text-lg font-semibold text-white mb-4">
            Findings ({findings.length})
          </h2>
          {findings.length > 0 ? (
            <div className="space-y-4">
              {findings.map((finding) => (
                <div
                  key={finding.id}
                  className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-sm font-medium text-white">{finding.title}</h3>
                    <span className={cn(
                      "px-2 py-1 rounded text-xs font-mono",
                      finding.severity === "critical" && "text-red-400 bg-red-500/10",
                      finding.severity === "high" && "text-orange-400 bg-orange-500/10",
                      finding.severity === "medium" && "text-amber-400 bg-amber-500/10",
                      finding.severity === "low" && "text-blue-400 bg-blue-500/10",
                      finding.severity === "info" && "text-white/60 bg-white/5"
                    )}>
                      {finding.severity}
                    </span>
                  </div>
                  <p className="text-sm text-white/60 mb-2">{finding.description}</p>
                  <div className="flex items-center gap-4 text-xs font-mono text-white/40">
                    <span>Risk Score: {finding.risk_score}</span>
                    <span>Discovered: {formatDate(finding.discovered_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-12 text-center">
              <p className="text-sm text-white/50 font-mono">No findings</p>
            </div>
          )}
        </GlassCard>
      )}

      {/* Execution Logs Tab */}
      {activeTab === "logs" && (
        <GlassCard className="p-6">
          <h2 className="font-mono text-lg font-semibold text-white mb-4">Execution Timeline</h2>
          {job.execution_logs && job.execution_logs.length > 0 ? (
            <div className="space-y-3">
              {job.execution_logs.map((log, index) => (
                <div
                  key={index}
                  className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.05]"
                >
                  <div className="flex items-start justify-between mb-1">
                    <span className={cn(
                      "text-xs font-mono px-2 py-0.5 rounded",
                      log.level === "error" && "text-red-400 bg-red-500/10",
                      log.level === "warning" && "text-amber-400 bg-amber-500/10",
                      log.level === "info" && "text-blue-400 bg-blue-500/10",
                      "text-white/60 bg-white/5"
                    )}>
                      {log.level}
                    </span>
                    <span className="text-xs font-mono text-white/40">{log.timestamp}</span>
                  </div>
                  <p className="text-sm text-white/80 font-mono">{log.message}</p>
                  {log.data && (
                    <pre className="mt-2 p-2 bg-white/5 rounded text-xs font-mono text-white/60 overflow-x-auto">
                      {JSON.stringify(log.data, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="py-12 text-center">
              <p className="text-sm text-white/50 font-mono">No execution logs available</p>
            </div>
          )}
        </GlassCard>
      )}

      {/* Configuration Tab */}
      {activeTab === "config" && (
        <div className="grid lg:grid-cols-2 gap-6">
          <GlassCard className="p-6">
            <h2 className="font-mono text-lg font-semibold text-white mb-4">Job Configuration</h2>
            <pre className="p-4 bg-white/5 border border-white/10 rounded-xl text-sm font-mono text-white/80 overflow-x-auto">
              {JSON.stringify(job.config, null, 2)}
            </pre>
          </GlassCard>
          <GlassCard className="p-6">
            <h2 className="font-mono text-lg font-semibold text-white mb-4">Metadata</h2>
            <pre className="p-4 bg-white/5 border border-white/10 rounded-xl text-sm font-mono text-white/80 overflow-x-auto">
              {JSON.stringify(job.metadata, null, 2)}
            </pre>
          </GlassCard>
        </div>
      )}
    </div>
  );
}

