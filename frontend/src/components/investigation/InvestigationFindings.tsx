"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";
import { CapabilityFinding, api } from "@/lib/api";

interface InvestigationFindingsProps {
  findings: CapabilityFinding[];
  className?: string;
  onFindingSelect?: (finding: CapabilityFinding) => void;
}

export function InvestigationFindings({
  findings,
  className,
  onFindingSelect,
}: InvestigationFindingsProps) {
  const [selectedFinding, setSelectedFinding] = useState<CapabilityFinding | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [groupBy, setGroupBy] = useState<"severity" | "category">("severity");

  const getSeverityStyles = (severity: string) => {
    const styles: Record<string, { bg: string; text: string; border: string }> = {
      critical: { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/30" },
      high: { bg: "bg-orange-500/10", text: "text-orange-400", border: "border-orange-500/30" },
      medium: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30" },
      low: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/30" },
      info: { bg: "bg-slate-500/10", text: "text-slate-400", border: "border-slate-500/30" },
    };
    return styles[severity] || styles.info;
  };

  const filteredFindings = findings.filter((f) => {
    if (filter !== "all" && f.severity !== filter) return false;
    return true;
  });

  const groupedFindings = filteredFindings.reduce((acc, finding) => {
    const key = groupBy === "severity" ? finding.severity : "general";
    if (!acc[key]) acc[key] = [];
    acc[key].push(finding);
    return acc;
  }, {} as Record<string, CapabilityFinding[]>);

  const handleFindingClick = (finding: CapabilityFinding) => {
    setSelectedFinding(finding);
    onFindingSelect?.(finding);
  };

  return (
    <GlassCard className={cn("p-6", className)} hover={false}>
      <div className="space-y-4">
        <div className="flex items-center gap-4 flex-wrap">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-2 bg-white/[0.03] border border-white/[0.08] rounded-lg text-white text-sm"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="info">Info</option>
          </select>
          <select
            value={groupBy}
            onChange={(e) => setGroupBy(e.target.value as any)}
            className="px-3 py-2 bg-white/[0.03] border border-white/[0.08] rounded-lg text-white text-sm"
          >
            <option value="severity">Group by Severity</option>
            <option value="category">Group by Category</option>
          </select>
          <div className="text-sm text-white/50">
            {filteredFindings.length} finding{filteredFindings.length !== 1 ? "s" : ""}
          </div>
        </div>

        <div className="space-y-6 max-h-[600px] overflow-y-auto">
          {Object.entries(groupedFindings).map(([group, groupFindings]) => (
            <div key={group}>
              <h4 className="text-sm font-mono font-semibold text-white/70 mb-3 uppercase">{group}</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {groupFindings.map((finding) => {
                  const styles = getSeverityStyles(finding.severity);
                  return (
                    <button
                      key={finding.id}
                      onClick={() => handleFindingClick(finding)}
                      className={cn(
                        "p-4 rounded-xl border text-left transition-all",
                        "hover:scale-[1.02] hover:shadow-lg",
                        "flex flex-col h-full min-h-[140px]",
                        styles.bg,
                        styles.border,
                        selectedFinding?.id === finding.id && "ring-2 ring-orange-500 scale-[1.02]"
                      )}
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <span
                          className={cn(
                            "px-2 py-0.5 text-xs font-mono uppercase rounded flex-shrink-0",
                            styles.bg,
                            styles.text
                          )}
                        >
                          {finding.severity}
                        </span>
                        <div className="text-right flex-shrink-0">
                          <div className={cn("text-sm font-mono font-semibold", styles.text)}>
                            {Math.round(finding.risk_score)}
                          </div>
                          <div className="text-xs text-white/30">risk</div>
                        </div>
                      </div>
                      <div className="flex-1 flex flex-col">
                        <p className="text-sm font-medium text-white mb-1 line-clamp-2">{finding.title}</p>
                        <p className="text-xs text-white/40 line-clamp-3 mt-auto">{finding.description}</p>
                      </div>
                      <div className="mt-2 flex justify-end">
                        <button
                          onClick={async (e) => {
                            e.stopPropagation();
                            try {
                              // Get finding to extract job_id from evidence
                              const findingData = await api.getFinding(finding.id);
                              const jobId = findingData.evidence?.job_id;
                              if (jobId) {
                                window.location.href = `/graph?jobId=${jobId}&depth=2`;
                              } else {
                                // Fallback: still use findingId
                                window.location.href = `/graph?findingId=${finding.id}&depth=2`;
                              }
                            } catch (error) {
                              console.error("Error getting finding for graph:", error);
                              // Fallback: still use findingId
                              window.location.href = `/graph?findingId=${finding.id}&depth=2`;
                            }
                          }}
                          className="p-1.5 rounded-lg hover:bg-white/[0.05] transition-colors group"
                          title="View in Graph"
                        >
                          <svg className="w-4 h-4 text-white/40 group-hover:text-amber-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                          </svg>
                        </button>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {selectedFinding && (
          <div className="p-4 bg-white/[0.02] border border-white/[0.08] rounded-lg space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-mono font-semibold text-white">{selectedFinding.title}</h3>
              <span
                className={cn(
                  "px-2 py-0.5 text-xs font-mono uppercase rounded",
                  getSeverityStyles(selectedFinding.severity).bg,
                  getSeverityStyles(selectedFinding.severity).text
                )}
              >
                {selectedFinding.severity}
              </span>
            </div>
            <p className="text-sm text-white/70">{selectedFinding.description}</p>
            {selectedFinding.evidence && (
              <div>
                <h4 className="text-xs font-mono text-white/50 mb-2">Evidence</h4>
                <pre className="p-3 rounded-lg bg-black/30 text-xs font-mono text-white/70 overflow-x-auto whitespace-pre-wrap max-h-48 overflow-y-auto">
                  {JSON.stringify(selectedFinding.evidence, null, 2)}
                </pre>
              </div>
            )}
            {selectedFinding.recommendations && selectedFinding.recommendations.length > 0 && (
              <div>
                <h4 className="text-xs font-mono text-white/50 mb-2">Recommendations</h4>
                <ul className="space-y-1">
                  {selectedFinding.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-white/70">
                      <span className="text-orange-400">•</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </GlassCard>
  );
}

