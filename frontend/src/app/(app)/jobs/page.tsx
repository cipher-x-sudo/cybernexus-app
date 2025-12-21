"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { GlassCard, GlassButton, GlassInput } from "@/components/ui";
import { api, CapabilityJob, JobHistoryParams } from "@/lib/api";
import { cn } from "@/lib/utils";

const capabilities = [
  { value: "", label: "All Capabilities" },
  { value: "exposure_discovery", label: "Exposure Discovery" },
  { value: "dark_web_intelligence", label: "Dark Web Intelligence" },
  { value: "email_security", label: "Email Security" },
  { value: "infrastructure_testing", label: "Infrastructure Testing" },
  { value: "network_security", label: "Network Security" },
  { value: "investigation", label: "Investigation" },
];

const statuses = [
  { value: "", label: "All Statuses" },
  { value: "pending", label: "Pending" },
  { value: "queued", label: "Queued" },
  { value: "running", label: "Running" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "cancelled", label: "Cancelled" },
];

export default function JobHistoryPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<CapabilityJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(0);
  
  // Filters
  const [capabilityFilter, setCapabilityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const params: JobHistoryParams = {
        page,
        page_size: pageSize,
      };
      
      if (capabilityFilter) params.capability = capabilityFilter;
      if (statusFilter) params.status = statusFilter;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      
      const response = await api.getJobHistory(params);
      // Map and cast jobs to match CapabilityJob type
      const mappedJobs: CapabilityJob[] = (response.jobs || []).map((job) => ({
        ...job,
        status: job.status as CapabilityJob["status"],
      }));
      setJobs(mappedJobs);
      setTotal(response.total || 0);
      setTotalPages(response.total_pages || 0);
    } catch (error) {
      console.error("Error fetching job history:", error);
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [page, capabilityFilter, statusFilter, startDate, endDate]);

  const handleJobClick = (jobId: string) => {
    router.push(`/jobs/${jobId}`);
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

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-mono font-bold text-white">Job History</h1>
          <p className="text-sm text-white/50">
            View and manage all your security assessment jobs
          </p>
        </div>
      </div>

      {/* Filters */}
      <GlassCard className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-mono text-white/50 mb-2">Capability</label>
            <select
              value={capabilityFilter}
              onChange={(e) => {
                setCapabilityFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white font-mono text-sm focus:outline-none focus:border-amber-500/50"
            >
              {capabilities.map((cap) => (
                <option key={cap.value} value={cap.value}>
                  {cap.label}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-xs font-mono text-white/50 mb-2">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white font-mono text-sm focus:outline-none focus:border-amber-500/50"
            >
              {statuses.map((status) => (
                <option key={status.value} value={status.value}>
                  {status.label}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-xs font-mono text-white/50 mb-2">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value);
                setPage(1);
              }}
              className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white font-mono text-sm focus:outline-none focus:border-amber-500/50"
            />
          </div>
          
          <div>
            <label className="block text-xs font-mono text-white/50 mb-2">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value);
                setPage(1);
              }}
              className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white font-mono text-sm focus:outline-none focus:border-amber-500/50"
            />
          </div>
        </div>
      </GlassCard>

      {/* Jobs table */}
      <GlassCard className="p-6" padding="none">
        <div className="p-6 border-b border-white/[0.05]">
          <h2 className="font-mono text-lg font-semibold text-white">
            Jobs ({total})
          </h2>
        </div>
        
        {loading ? (
          <div className="py-12 text-center">
            <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm text-white/50 font-mono">Loading jobs...</p>
          </div>
        ) : jobs.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/[0.05]">
                    <th className="px-6 py-3 text-left text-xs font-mono text-white/50 uppercase tracking-wider">ID</th>
                    <th className="px-6 py-3 text-left text-xs font-mono text-white/50 uppercase tracking-wider">Capability</th>
                    <th className="px-6 py-3 text-left text-xs font-mono text-white/50 uppercase tracking-wider">Target</th>
                    <th className="px-6 py-3 text-left text-xs font-mono text-white/50 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-mono text-white/50 uppercase tracking-wider">Progress</th>
                    <th className="px-6 py-3 text-left text-xs font-mono text-white/50 uppercase tracking-wider">Findings</th>
                    <th className="px-6 py-3 text-left text-xs font-mono text-white/50 uppercase tracking-wider">Created</th>
                    <th className="px-6 py-3 text-left text-xs font-mono text-white/50 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.05]">
                  {jobs.map((job) => (
                    <tr
                      key={job.id}
                      onClick={() => handleJobClick(job.id)}
                      className="hover:bg-white/[0.02] transition-colors cursor-pointer"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <p className="text-sm font-mono text-white/60">{job.id}</p>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <p className="text-sm text-white font-medium">{job.capability}</p>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm font-mono text-white/80 truncate max-w-xs">{job.target}</p>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={cn("inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono border", getStatusColor(job.status))}>
                          {job.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-white/5 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-amber-500 transition-all"
                              style={{ width: `${job.progress}%` }}
                            />
                          </div>
                          <span className="text-xs font-mono text-white/60">{job.progress}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {job.findings_count > 0 ? (
                          <span className="text-sm font-mono text-amber-400">{job.findings_count}</span>
                        ) : (
                          <span className="text-sm font-mono text-white/40">0</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <p className="text-xs font-mono text-white/60">{formatDate(job.created_at)}</p>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleJobClick(job.id);
                          }}
                          className="text-xs font-mono text-amber-400 hover:text-amber-300 transition-colors"
                        >
                          View →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="p-6 border-t border-white/[0.05] flex items-center justify-between">
                <p className="text-sm font-mono text-white/50">
                  Page {page} of {totalPages} ({total} total)
                </p>
                <div className="flex items-center gap-2">
                  <GlassButton
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="text-xs"
                  >
                    Previous
                  </GlassButton>
                  <GlassButton
                    onClick={() => setPage(Math.min(totalPages, page + 1))}
                    disabled={page === totalPages}
                    className="text-xs"
                  >
                    Next
                  </GlassButton>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="py-12 text-center">
            <p className="text-sm text-white/50 font-mono">No jobs found</p>
            <p className="text-xs text-white/30 mt-1">Try adjusting your filters</p>
          </div>
        )}
      </GlassCard>
    </div>
  );
}

