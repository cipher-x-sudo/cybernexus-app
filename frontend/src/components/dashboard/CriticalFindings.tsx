"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";
import { api } from "@/lib/api";

interface Finding {
  id: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low";
  capability: string;
  target: string;
  time: string;
}

interface CriticalFindingsProps {
  findings?: Finding[];
  className?: string;
}

export function CriticalFindings({ findings: propFindings, className }: CriticalFindingsProps) {
  const router = useRouter();
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  
  const handleViewInGraph = (findingId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    router.push(`/graph?findingId=${findingId}&depth=2`);
  };

  // Fetch findings if not provided
  useEffect(() => {
    if (propFindings) {
      setFindings(propFindings);
      setLoading(false);
      return;
    }

    const fetchFindings = async () => {
      try {
        setLoading(true);
        const response = await api.getDashboardCriticalFindings(10);
        if (response.findings && response.findings.length > 0) {
          const mappedFindings: Finding[] = response.findings.map((f: any) => ({
            id: f.id,
            title: f.title,
            severity: f.severity as "critical" | "high" | "medium" | "low",
            capability: f.capability || "Unknown",
            target: f.target || "",
            time: f.time_ago || "Unknown",
          }));
          setFindings(mappedFindings);
        } else {
          setFindings([]);
        }
      } catch (error) {
        console.error("Error fetching critical findings:", error);
        setFindings([]);
      } finally {
        setLoading(false);
      }
    };

    fetchFindings();

    // Poll for updates every 30 seconds
    const interval = setInterval(fetchFindings, 30000);
    return () => clearInterval(interval);
  }, [propFindings]);
  const getSeverityStyles = (severity: string) => {
    switch (severity) {
      case "critical":
        return {
          bg: "bg-red-500/10",
          border: "border-red-500/30",
          text: "text-red-400",
          dot: "bg-red-500",
          glow: "shadow-[0_0_10px_rgba(239,68,68,0.3)]",
        };
      case "high":
        return {
          bg: "bg-orange-500/10",
          border: "border-orange-500/30",
          text: "text-orange-400",
          dot: "bg-orange-500",
          glow: "",
        };
      case "medium":
        return {
          bg: "bg-amber-500/10",
          border: "border-amber-500/30",
          text: "text-amber-400",
          dot: "bg-amber-500",
          glow: "",
        };
      default:
        return {
          bg: "bg-blue-500/10",
          border: "border-blue-500/30",
          text: "text-blue-400",
          dot: "bg-blue-500",
          glow: "",
        };
    }
  };

  return (
    <GlassCard className={cn("p-6", className)} hover={false}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h2 className="font-mono text-lg font-semibold text-white">Critical Findings</h2>
          <span className="px-2 py-0.5 text-xs font-mono bg-red-500/20 text-red-400 rounded-full">
            {findings.filter(f => f.severity === "critical").length} critical
          </span>
        </div>
        <button className="text-xs font-mono text-amber-400 hover:text-amber-300 transition-colors">
          View All →
        </button>
      </div>

      <div className="space-y-3">
        {findings.map((finding, index) => {
          const styles = getSeverityStyles(finding.severity);
          return (
            <div
              key={finding.id}
              className={cn(
                "p-3 rounded-xl border transition-all duration-200",
                "hover:translate-x-1 cursor-pointer",
                styles.bg,
                styles.border,
                styles.glow,
                "animate-fade-in"
              )}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start gap-3">
                <div className={cn("w-2 h-2 rounded-full mt-1.5 flex-shrink-0", styles.dot, finding.severity === "critical" && "animate-pulse")} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={cn("text-xs font-mono uppercase tracking-wide", styles.text)}>
                      {finding.severity}
                    </span>
                    <span className="text-white/30">•</span>
                    <span className="text-xs text-white/50 font-mono">
                      {finding.capability}
                    </span>
                  </div>
                  <p className="text-sm text-white font-medium truncate">
                    {finding.title}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-white/40 font-mono truncate">
                      {finding.target}
                    </span>
                    <span className="text-white/20">•</span>
                    <span className="text-xs text-white/40 font-mono">
                      {finding.time}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={(e) => handleViewInGraph(finding.id, e)}
                    className="p-1.5 rounded-lg hover:bg-white/[0.05] transition-colors group"
                    title="View in Graph"
                  >
                    <svg className="w-4 h-4 text-white/40 group-hover:text-amber-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                    </svg>
                  </button>
                  <button className="p-1.5 rounded-lg hover:bg-white/[0.05] transition-colors">
                    <svg className="w-4 h-4 text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {loading && findings.length === 0 && (
        <div className="py-8 text-center">
          <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-white/50 font-mono">Loading findings...</p>
        </div>
      )}

      {!loading && findings.length === 0 && (
        <div className="py-8 text-center">
          <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-emerald-500/10 flex items-center justify-center">
            <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-sm text-white/50 font-mono">No critical findings</p>
          <p className="text-xs text-white/30 mt-1">Your security posture looks good!</p>
        </div>
      )}
    </GlassCard>
  );
}

export default CriticalFindings;



