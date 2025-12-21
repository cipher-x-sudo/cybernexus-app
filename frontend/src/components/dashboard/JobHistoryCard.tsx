"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { GlassCard } from "@/components/ui";
import { api, CapabilityJob } from "@/lib/api";
import { cn } from "@/lib/utils";

interface JobHistoryCardProps {
  className?: string;
  limit?: number;
}

export function JobHistoryCard({ className, limit = 5 }: JobHistoryCardProps) {
  const router = useRouter();
  const [jobs, setJobs] = useState<CapabilityJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        setLoading(true);
        const response = await api.getRecentJobs(limit);
        // Map and cast jobs to match CapabilityJob type
        const mappedJobs: CapabilityJob[] = (response.jobs || []).map((job) => ({
          ...job,
          status: job.status as CapabilityJob["status"],
        }));
        setJobs(mappedJobs);
      } catch (error) {
        console.error("Error fetching job history:", error);
        setJobs([]);
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchJobs, 30000);
    return () => clearInterval(interval);
  }, [limit]);

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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case "running":
        return (
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        );
      case "failed":
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const handleJobClick = (jobId: string) => {
    router.push(`/jobs/${jobId}`);
  };

  return (
    <GlassCard className={cn("p-6", className)} hover={false}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-mono text-lg font-semibold text-white">Job History</h2>
        <Link
          href="/jobs"
          className="text-xs font-mono text-amber-400 hover:text-amber-300 transition-colors"
        >
          View All →
        </Link>
      </div>
      
      {loading ? (
        <div className="py-8 text-center">
          <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-xs text-white/50 font-mono">Loading...</p>
        </div>
      ) : jobs.length > 0 ? (
        <div className="space-y-3">
          {jobs.map((job) => (
            <div
              key={job.id}
              onClick={() => handleJobClick(job.id)}
              className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:border-white/[0.1] transition-colors cursor-pointer group"
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0", getStatusColor(job.status))}>
                  {getStatusIcon(job.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white font-medium truncate">{job.capability}</p>
                  <p className="text-xs text-white/40 font-mono truncate">{job.target}</p>
                </div>
              </div>
              <div className="text-right flex-shrink-0 ml-3">
                {job.status === "completed" && job.findings_count > 0 && (
                  <p className="text-sm font-mono text-amber-400">{job.findings_count} findings</p>
                )}
                <p className="text-xs text-white/40">{job.time_ago || "Just now"}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-8 text-center">
          <p className="text-sm text-white/50 font-mono">No job history</p>
          <p className="text-xs text-white/30 mt-1">Start a scan to see results here</p>
        </div>
      )}
    </GlassCard>
  );
}

