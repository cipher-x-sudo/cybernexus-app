"use client";

import { useState } from "react";
import { GlassCard, GlassButton, GlassInput, Badge } from "@/components/ui";
import { cn, formatDate } from "@/lib/utils";

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

const recentReports = [
  {
    id: "1",
    name: "Q4 2024 Executive Summary",
    type: "executive",
    status: "completed",
    createdAt: new Date(Date.now() - 2 * 24 * 60 * 60000),
  },
  {
    id: "2",
    name: "Incident #1234 - Data Breach",
    type: "incident",
    status: "completed",
    createdAt: new Date(Date.now() - 5 * 24 * 60 * 60000),
  },
  {
    id: "3",
    name: "Monthly Technical Report",
    type: "technical",
    status: "generating",
    createdAt: new Date(Date.now() - 60 * 60000),
  },
  {
    id: "4",
    name: "SOC 2 Compliance Audit",
    type: "compliance",
    status: "completed",
    createdAt: new Date(Date.now() - 14 * 24 * 60 * 60000),
  },
];

export default function ReportsPage() {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [reportName, setReportName] = useState("");
  const [dateRange, setDateRange] = useState({ start: "", end: "" });

  const handleGenerate = () => {
    console.log("Generating report:", { selectedType, reportName, dateRange });
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-mono font-bold text-white">Reports</h1>
        <p className="text-sm text-white/50">
          Generate and export threat intelligence reports
        </p>
      </div>

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
            <GlassButton variant="primary" onClick={handleGenerate}>
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Generate Report
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
              {recentReports.map((report) => (
                <tr key={report.id} className="border-b border-white/[0.03]">
                  <td className="py-4">
                    <p className="font-mono text-sm text-white">{report.name}</p>
                  </td>
                  <td className="py-4">
                    <span className="text-sm text-white/60 capitalize">{report.type}</span>
                  </td>
                  <td className="py-4">
                    <Badge
                      variant={report.status === "completed" ? "success" : "info"}
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
                          <GlassButton variant="ghost" size="sm">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                          </GlassButton>
                          <GlassButton variant="ghost" size="sm">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                          </GlassButton>
                        </>
                      )}
                      {report.status === "generating" && (
                        <div className="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  );
}

