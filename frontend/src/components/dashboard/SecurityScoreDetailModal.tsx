"use client";

import React, { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";

interface SecurityScoreDetailModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentScore: number;
  riskLevel: string;
  trend: "improving" | "stable" | "worsening";
  criticalIssues: number;
  highIssues: number;
}

interface BreakdownData {
  overall_score: number;
  risk_level: string;
  trend: "improving" | "stable" | "worsening";
  categories: Record<string, {
    name: string;
    score: number;
    findings_count: number;
    contribution: number;
    severity_breakdown: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
  }>;
  severity_distribution: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
    calculation: {
      base_score: number;
      deductions: {
        critical: number;
        high: number;
        medium: number;
        low: number;
      };
      total_deduction: number;
      additions?: {
        resolved: number;
        indicators: number;
        total: number;
      };
      formula: string;
    };
    positive_points?: {
      resolved: number;
      indicators: number;
      total: number;
    };
  recommendations: Array<{
    priority: "critical" | "high" | "medium" | "low";
    title: string;
    description: string;
    action: string;
  }>;
}

export function SecurityScoreDetailModal({
  open,
  onOpenChange,
  currentScore,
  riskLevel,
  trend,
  criticalIssues,
  highIssues,
}: SecurityScoreDetailModalProps) {
  const [breakdownData, setBreakdownData] = useState<BreakdownData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && !breakdownData) {
      fetchBreakdown();
    }
  }, [open]);

  const fetchBreakdown = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDashboardRiskBreakdown();
      setBreakdownData(data);
    } catch (err: any) {
      console.error("Error fetching risk breakdown:", err);
      setError(err.message || "Failed to load breakdown data");
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-400";
    if (score >= 60) return "text-amber-400";
    if (score >= 40) return "text-orange-400";
    return "text-red-400";
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return "bg-emerald-500/20 border-emerald-500/40";
    if (score >= 60) return "bg-amber-500/20 border-amber-500/40";
    if (score >= 40) return "bg-orange-500/20 border-orange-500/40";
    return "bg-red-500/20 border-red-500/40";
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: "text-red-400 bg-red-500/10 border-red-500/30",
      high: "text-orange-400 bg-orange-500/10 border-orange-500/30",
      medium: "text-amber-400 bg-amber-500/10 border-amber-500/30",
      low: "text-blue-400 bg-blue-500/10 border-blue-500/30",
    };
    return colors[severity] || "text-white/50 bg-white/5 border-white/10";
  };

  const getTrendIcon = () => {
    if (trend === "improving") {
      return (
        <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
        </svg>
      );
    }
    if (trend === "worsening") {
      return (
        <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      );
    }
    return (
      <svg className="w-4 h-4 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
      </svg>
    );
  };

  const getLevelLabel = (level: string) => {
    const labels: Record<string, string> = {
      minimal: "Excellent",
      low: "Good",
      medium: "Fair",
      high: "Poor",
      critical: "Critical",
    };
    return labels[level] || "Unknown";
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-mono font-bold text-white">
            Security Score Breakdown
          </DialogTitle>
          <DialogDescription className="text-white/60 font-mono">
            Detailed analysis of your organization&apos;s security posture
          </DialogDescription>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p className="text-red-400 font-mono text-sm">{error}</p>
          </div>
        )}

        {breakdownData && !loading && (
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 bg-white/[0.03] border border-white/[0.08] rounded-lg">
              <div className="flex items-center gap-4">
                <div className={cn("text-4xl font-mono font-bold", getScoreColor(breakdownData.overall_score))}>
                  {breakdownData.overall_score}
                </div>
                <div>
                  <div className="text-sm text-white/50 font-mono">Overall Score</div>
                  <div className={cn("text-lg font-mono font-semibold", getScoreColor(breakdownData.overall_score))}>
                    {getLevelLabel(breakdownData.risk_level)}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {getTrendIcon()}
                <span className={cn(
                  "text-sm font-mono",
                  trend === "improving" && "text-emerald-400",
                  trend === "worsening" && "text-red-400",
                  trend === "stable" && "text-white/50"
                )}>
                  {trend}
                </span>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-mono font-semibold text-white mb-4">Category Breakdown</h3>
              <div className="space-y-3">
                {Object.entries(breakdownData.categories).map(([key, category]) => (
                  <div
                    key={key}
                    className="p-4 bg-white/[0.03] border border-white/[0.08] rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className="text-white font-mono font-medium">{category.name}</span>
                        <span className="text-xs text-white/50 font-mono">
                          {category.findings_count} finding{category.findings_count !== 1 ? "s" : ""}
                        </span>
                      </div>
                      <div className={cn("px-3 py-1 rounded border font-mono text-sm", getScoreBgColor(category.score))}>
                        <span className={getScoreColor(category.score)}>{category.score}</span>
                      </div>
                    </div>
                    <div className="w-full bg-white/[0.05] rounded-full h-2 mb-2">
                      <div
                        className={cn(
                          "h-2 rounded-full transition-all",
                          category.score >= 80 && "bg-emerald-500",
                          category.score >= 60 && category.score < 80 && "bg-amber-500",
                          category.score >= 40 && category.score < 60 && "bg-orange-500",
                          category.score < 40 && "bg-red-500"
                        )}
                        style={{ width: `${category.score}%` }}
                      />
                    </div>
                    <div className="flex gap-2 text-xs font-mono flex-wrap">
                      {category.severity_breakdown.critical > 0 && (
                        <span className={cn("px-2 py-1 rounded border", getSeverityColor("critical"))}>
                          {category.severity_breakdown.critical} Critical
                        </span>
                      )}
                      {category.severity_breakdown.high > 0 && (
                        <span className={cn("px-2 py-1 rounded border", getSeverityColor("high"))}>
                          {category.severity_breakdown.high} High
                        </span>
                      )}
                      {category.severity_breakdown.medium > 0 && (
                        <span className={cn("px-2 py-1 rounded border", getSeverityColor("medium"))}>
                          {category.severity_breakdown.medium} Medium
                        </span>
                      )}
                      {category.severity_breakdown.low > 0 && (
                        <span className={cn("px-2 py-1 rounded border", getSeverityColor("low"))}>
                          {category.severity_breakdown.low} Low
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-lg font-mono font-semibold text-white mb-4">Severity Distribution</h3>
              <div className="grid grid-cols-4 gap-3">
                {Object.entries(breakdownData.severity_distribution).map(([severity, count]) => (
                  <div
                    key={severity}
                    className={cn(
                      "p-4 rounded-lg border text-center",
                      getSeverityColor(severity)
                    )}
                  >
                    <div className="text-2xl font-mono font-bold mb-1">{count}</div>
                    <div className="text-xs font-mono uppercase tracking-wider">
                      {severity}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-lg font-mono font-semibold text-white mb-4">Calculation Details</h3>
              <div className="p-4 bg-white/[0.03] border border-white/[0.08] rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-white/70 font-mono">Base Score</span>
                  <span className="text-white font-mono font-semibold">{breakdownData.calculation.base_score}</span>
                </div>
                <div className="h-px bg-white/[0.08]" />
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white/60 font-mono">Critical Deductions</span>
                    <span className="text-red-400 font-mono">
                      -{breakdownData.calculation.deductions.critical * 20}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white/60 font-mono">High Deductions</span>
                    <span className="text-orange-400 font-mono">
                      -{breakdownData.calculation.deductions.high * 10}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white/60 font-mono">Medium Deductions</span>
                    <span className="text-amber-400 font-mono">
                      -{breakdownData.calculation.deductions.medium * 5}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white/60 font-mono">Low Deductions</span>
                    <span className="text-blue-400 font-mono">
                      -{breakdownData.calculation.deductions.low * 2}
                    </span>
                  </div>
                </div>
                <div className="h-px bg-white/[0.08]" />
                <div className="flex items-center justify-between">
                  <span className="text-white/70 font-mono">Total Deduction</span>
                  <span className="text-red-400 font-mono font-semibold">
                    -{breakdownData.calculation.total_deduction}
                  </span>
                </div>
                {breakdownData.positive_points && (breakdownData.positive_points.total || 0) > 0 && (
                  <>
                    <div className="h-px bg-white/[0.08]" />
                    <div className="space-y-2">
                      <div className="text-sm text-emerald-400 font-mono font-semibold mb-2">Positive Points</div>
                      {(breakdownData.positive_points.resolved || 0) > 0 && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-white/60 font-mono">Resolved Findings</span>
                          <span className="text-emerald-400 font-mono">
                            +{breakdownData.positive_points.resolved}
                          </span>
                        </div>
                      )}
                      {(breakdownData.positive_points.indicators || 0) > 0 && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-white/60 font-mono">Positive Indicators</span>
                          <span className="text-emerald-400 font-mono">
                            +{breakdownData.positive_points.indicators}
                          </span>
                        </div>
                      )}
                      <div className="flex items-center justify-between pt-2 border-t border-white/[0.08]">
                        <span className="text-white/70 font-mono font-semibold">Total Positive Points</span>
                        <span className="text-emerald-400 font-mono font-semibold">
                          +{breakdownData.positive_points.total || 0}
                        </span>
                      </div>
                    </div>
                  </>
                )}
                <div className="h-px bg-white/[0.08]" />
                <div className="flex items-center justify-between pt-2">
                  <span className="text-white/70 font-mono font-semibold">Final Score</span>
                  <span className={cn("font-mono font-bold text-xl", getScoreColor(breakdownData.overall_score))}>
                    {breakdownData.overall_score}
                  </span>
                </div>
                <div className="pt-2 text-xs text-white/50 font-mono italic">
                  {breakdownData.calculation.formula}
                </div>
              </div>
            </div>

            {breakdownData.recommendations.length > 0 && (
              <div>
                <h3 className="text-lg font-mono font-semibold text-white mb-4">Recommendations</h3>
                <div className="space-y-3">
                  {breakdownData.recommendations.map((rec, index) => (
                    <div
                      key={index}
                      className={cn(
                        "p-4 rounded-lg border",
                        rec.priority === "critical" && "bg-red-500/10 border-red-500/30",
                        rec.priority === "high" && "bg-orange-500/10 border-orange-500/30",
                        rec.priority === "medium" && "bg-amber-500/10 border-amber-500/30",
                        rec.priority === "low" && "bg-blue-500/10 border-blue-500/30"
                      )}
                    >
                      <div className="flex items-start gap-3">
                        <div className={cn(
                          "w-2 h-2 rounded-full mt-2",
                          rec.priority === "critical" && "bg-red-500",
                          rec.priority === "high" && "bg-orange-500",
                          rec.priority === "medium" && "bg-amber-500",
                          rec.priority === "low" && "bg-blue-500"
                        )} />
                        <div className="flex-1">
                          <h4 className="text-white font-mono font-semibold mb-1">{rec.title}</h4>
                          <p className="text-white/70 font-mono text-sm mb-2">{rec.description}</p>
                          <p className="text-white/50 font-mono text-xs italic">{rec.action}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

