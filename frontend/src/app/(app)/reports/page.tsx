"use client";

import { useState, useEffect } from "react";
import { GlassCard, GlassButton, GlassInput, Badge } from "@/components/ui";
import { cn, formatDate } from "@/lib/utils";
import { api } from "@/lib/api";
import { mapToReports, ReportData } from "@/lib/data-mappers";

interface Report {
  id: string;
  name: string;
  type: string;
  status: string;
  createdAt: Date;
}

const reportTypes = [
  {
    id: "executive",
    name: "Executive Summary",
    description: "High-level overview for leadership",
    icon: "📊",
  },
  {
    id: "technical",
    name: "Technical Detail",
    description: "In-depth technical analysis",
    icon: "🔧",
  },
  {
    id: "incident",
    name: "Incident Report",
    description: "Document security incidents",
    icon: "🚨",
  },
  {
    id: "compliance",
    name: "Compliance Report",
    description: "Regulatory compliance documentation",
    icon: "📋",
  },
  {
    id: "trend",
    name: "Trend Analysis",
    description: "Threat trends over time",
    icon: "📈",
  },
  {
    id: "custom",
    name: "Custom Report",
    description: "Build your own report",
    icon: "✨",
  },
];

/**
 * Map frontend report type to backend report type
 */
function mapToBackendReportType(frontendType: string): string {
  const typeMap: Record<string, string> = {
    executive: "executive_summary",
    technical: "threat_assessment",
    incident: "threat_assessment",
    compliance: "compliance",
    trend: "dark_web_intelligence",
    custom: "custom",
  };
  return typeMap[frontendType] || "custom";
}

export default function ReportsPage() {
  const [recentReports, setRecentReports] = useState<ReportData[]>([]);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [reportName, setReportName] = useState("");
  const [dateRange, setDateRange] = useState({ start: "", end: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  // Fetch reports from API
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

    // Poll for updates every 30 seconds
    const interval = setInterval(fetchReports, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleGenerate = async () => {
    if (!selectedType || !reportName.trim()) {
      setError("Please select a report type and enter a report name");
      return;
    }

    try {
      setGenerating(true);
      setError(null);

      const backendType = mapToBackendReportType(selectedType);
      const params: any = {
        title: reportName,
        type: backendType,
        format: "pdf",
      };

      // Add date range if provided
      if (dateRange.start) {
        params.date_range_start = new Date(dateRange.start).toISOString();
      }
      if (dateRange.end) {
        params.date_range_end = new Date(dateRange.end).toISOString();
      }

      // Add sections for custom reports
      if (selectedType === "custom") {
        const selectedSections = Array.from(
          document.querySelectorAll<HTMLInputElement>('input[type="checkbox"]:checked')
        ).map((cb) => cb.nextElementSibling?.textContent || "");
        params.include_sections = selectedSections;
      }

      await api.generateReport(params);

      // Refresh reports list
      const reports = await api.getReports();
      setRecentReports(mapToReports(reports));

      // Reset form
      setSelectedType(null);
      setReportName("");
      setDateRange({ start: "", end: "" });
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
      
      // Create download link
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

  // Show loading state
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

  // Show error state
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
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-mono font-bold text-white">Reports</h1>
        <p className="text-sm text-white/50">
          Generate and export threat intelligence reports
        </p>
      </div>

      {/* Error message */}
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

      {/* Report type selection */}
      <div>
        <h2 className="font-mono text-lg text-white mb-4">Select Report Type</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {reportTypes.map((type) => (
            <GlassCard
              key={type.id}
              onClick={() => setSelectedType(type.id)}
              className={cn(
                "cursor-pointer transition-all",
                selectedType === type.id && "border-amber-500/50 shadow-[0_0_20px_rgba(245,158,11,0.15)]"
              )}
              padding="lg"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-white/[0.05] flex items-center justify-center text-2xl">
                  {type.icon}
                </div>
                <div className="flex-1">
                  <h3 className="font-mono font-semibold text-white mb-1">{type.name}</h3>
                  <p className="text-sm text-white/50">{type.description}</p>
                </div>
                {selectedType === type.id && (
                  <div className="w-5 h-5 rounded-full bg-amber-500 flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                )}
              </div>
            </GlassCard>
          ))}
        </div>
      </div>

      {/* Report configuration */}
      {selectedType && (
        <GlassCard>
          <h2 className="font-mono text-lg text-white mb-6">Configure Report</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <GlassInput
              label="Report Name"
              placeholder="Enter report name..."
              value={reportName}
              onChange={(e) => setReportName(e.target.value)}
            />
            <div className="grid grid-cols-2 gap-4">
              <GlassInput
                label="Start Date"
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
              />
              <GlassInput
                label="End Date"
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
              />
            </div>
          </div>

          {selectedType === "custom" && (
            <div className="mt-6 pt-6 border-t border-white/[0.05]">
              <h3 className="font-mono text-sm text-white mb-4">Include Sections</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  "Executive Summary",
                  "Threat Overview",
                  "Credential Leaks",
                  "Dark Web Mentions",
                  "Asset Inventory",
                  "Incident Timeline",
                  "Recommendations",
                  "Appendix",
                ].map((section) => (
                  <label
                    key={section}
                    className="flex items-center gap-2 p-3 rounded-lg bg-white/[0.03] border border-white/[0.08] cursor-pointer hover:bg-white/[0.05] transition-colors"
                  >
                    <input type="checkbox" className="rounded border-white/20 bg-white/10 text-amber-500 focus:ring-amber-500" />
                    <span className="text-sm text-white/70">{section}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="mt-6 pt-6 border-t border-white/[0.05] flex justify-end gap-3">
            <GlassButton variant="ghost" onClick={() => setSelectedType(null)}>
              Cancel
            </GlassButton>
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
        </GlassCard>
      )}

      {/* Recent reports */}
      <GlassCard>
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-mono text-lg text-white">Recent Reports</h2>
          <GlassButton variant="ghost" size="sm">View All</GlassButton>
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
                    <p className="text-white/50 font-mono text-sm">No reports yet. Generate your first report above.</p>
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

