"use client";

import { useState, useEffect } from "react";
import { GlassCard, GlassButton, Badge } from "@/components/ui";
import { formatDate } from "@/lib/utils";
import { api } from "@/lib/api";
import { mapToReports, ReportData } from "@/lib/data-mappers";

export default function ReportsPage() {
  const [recentReports, setRecentReports] = useState<ReportData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        setLoading(true);
        setError(null);
        const reports = await api.getReports();
        setRecentReports(mapToReports(reports));
      } catch (err: any) {
        console.error("Error fetching reports:", err);
        setError(err.message || "Failed to load reports");
      } finally {
        setLoading(false);
      }
    };

    fetchReports();

    const interval = setInterval(fetchReports, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      setError(null);

      const reportName = `Report - ${new Date().toLocaleString()}`;
      const params = {
        title: reportName,
        type: "executive_summary",
        format: "pdf" as const,
      };

      await api.generateReport(params);

      const reports = await api.getReports();
      setRecentReports(mapToReports(reports));
    } catch (err: any) {
      console.error("Error generating report:", err);
      setError(err.message || "Failed to generate report");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (reportId: string) => {
    try {
      setDownloadingId(reportId);
      const blob = await api.downloadReport(reportId);
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `report-${reportId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error("Error downloading report:", err);
      setError(err.message || "Failed to download report");
    } finally {
      setDownloadingId(null);
    }
  };

  if (loading && recentReports.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-mono font-bold text-white">Reports</h1>
          <p className="text-sm text-white/50">
            Generate and export threat intelligence reports
          </p>
        </div>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-white/50 font-mono text-sm">Loading reports...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && recentReports.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-mono font-bold text-white">Reports</h1>
          <p className="text-sm text-white/50">
            Generate and export threat intelligence reports
          </p>
        </div>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <p className="text-red-400 font-mono mb-2">Error loading reports</p>
            <p className="text-white/50 font-mono text-sm">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-mono font-bold text-white">Reports</h1>
          <p className="text-sm text-white/50">
            Generate and export threat intelligence reports
          </p>
        </div>
        <GlassButton 
          variant="primary" 
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
              Generating...
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Generate Report
            </>
          )}
        </GlassButton>
      </div>

      {error && (
        <GlassCard className="border-red-500/50">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-red-400 font-mono text-sm">{error}</p>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-white/50 hover:text-white"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </GlassCard>
      )}

      <GlassCard>
        <div className="mb-6">
          <h2 className="font-mono text-lg text-white">Recent Reports</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/[0.05]">
                <th className="text-left text-xs font-mono text-white/40 pb-3">Report Name</th>
                <th className="text-left text-xs font-mono text-white/40 pb-3">Type</th>
                <th className="text-left text-xs font-mono text-white/40 pb-3">Status</th>
                <th className="text-left text-xs font-mono text-white/40 pb-3">Created</th>
                <th className="text-right text-xs font-mono text-white/40 pb-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {recentReports.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center">
                    <p className="text-white/50 font-mono text-sm">No reports yet. Click "Generate Report" to create your first report.</p>
                  </td>
                </tr>
              ) : (
                recentReports.map((report) => (
                  <tr key={report.id} className="border-b border-white/[0.03]">
                    <td className="py-4">
                      <p className="font-mono text-sm text-white">{report.name}</p>
                    </td>
                    <td className="py-4">
                      <span className="text-sm text-white/60 capitalize">{report.type}</span>
                    </td>
                    <td className="py-4">
                      <Badge
                        variant={
                          report.status === "completed" 
                            ? "success" 
                            : report.status === "failed"
                            ? "critical"
                            : "info"
                        }
                        size="sm"
                      >
                        {report.status}
                      </Badge>
                    </td>
                    <td className="py-4">
                      <span className="text-sm text-white/50">{formatDate(report.createdAt)}</span>
                    </td>
                    <td className="py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {report.status === "completed" && (
                          <>
                            <GlassButton 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleDownload(report.id)}
                              disabled={downloadingId === report.id}
                              title="Download report"
                            >
                              {downloadingId === report.id ? (
                                <div className="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
                              ) : (
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                              )}
                            </GlassButton>
                          </>
                        )}
                        {(report.status === "generating" || report.status === "pending") && (
                          <div className="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
                        )}
                        {report.status === "failed" && (
                          <span className="text-xs text-red-400">Failed</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  );
}

