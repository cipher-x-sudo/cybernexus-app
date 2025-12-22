"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";

interface ComparisonViewProps {
  comparisonData: {
    job1: string;
    job2: string;
    target1: string;
    target2: string;
    visual_similarity: {
      overall_similarity: number;
      is_similar: boolean;
    } | null;
    domain_differences: {
      added_domains: string[];
      removed_domains: string[];
      common_domains: string[];
    };
    findings_comparison: {
      count1: number;
      count2: number;
      new_findings: number;
      resolved_findings: number;
    };
  };
  className?: string;
}

export function ComparisonView({ comparisonData, className }: ComparisonViewProps) {
  return (
    <GlassCard className={cn("p-6", className)} hover={false}>
      <div className="space-y-6">
        <h3 className="text-lg font-mono font-semibold text-white">Investigation Comparison</h3>

        {comparisonData.visual_similarity && (
          <div className="p-4 bg-white/[0.02] border border-white/[0.08] rounded-lg">
            <h4 className="text-sm font-mono font-semibold text-white mb-2">Visual Similarity</h4>
            <div className="flex items-center gap-4">
              <div className="text-3xl font-bold text-orange-400">
                {Math.round(comparisonData.visual_similarity.overall_similarity)}%
              </div>
              <div className="flex-1">
                <div className="h-2 bg-white/[0.1] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-orange-500 rounded-full"
                    style={{ width: `${comparisonData.visual_similarity.overall_similarity}%` }}
                  />
                </div>
                <div className="text-xs text-white/50 mt-1">
                  {comparisonData.visual_similarity.is_similar
                    ? "Screenshots are similar"
                    : "Screenshots differ significantly"}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="p-4 bg-white/[0.02] border border-white/[0.08] rounded-lg">
          <h4 className="text-sm font-mono font-semibold text-white mb-3">Domain Changes</h4>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-xs text-white/50 mb-1">Added Domains</div>
              <div className="text-lg font-bold text-green-400">
                {comparisonData.domain_differences.added_domains.length}
              </div>
              {comparisonData.domain_differences.added_domains.length > 0 && (
                <div className="mt-2 space-y-1">
                  {comparisonData.domain_differences.added_domains.slice(0, 3).map((domain, idx) => (
                    <div key={idx} className="text-xs text-white/70 font-mono truncate">
                      + {domain}
                    </div>
                  ))}
                  {comparisonData.domain_differences.added_domains.length > 3 && (
                    <div className="text-xs text-white/50">
                      +{comparisonData.domain_differences.added_domains.length - 3} more
                    </div>
                  )}
                </div>
              )}
            </div>
            <div>
              <div className="text-xs text-white/50 mb-1">Removed Domains</div>
              <div className="text-lg font-bold text-red-400">
                {comparisonData.domain_differences.removed_domains.length}
              </div>
              {comparisonData.domain_differences.removed_domains.length > 0 && (
                <div className="mt-2 space-y-1">
                  {comparisonData.domain_differences.removed_domains.slice(0, 3).map((domain, idx) => (
                    <div key={idx} className="text-xs text-white/70 font-mono truncate">
                      − {domain}
                    </div>
                  ))}
                  {comparisonData.domain_differences.removed_domains.length > 3 && (
                    <div className="text-xs text-white/50">
                      −{comparisonData.domain_differences.removed_domains.length - 3} more
                    </div>
                  )}
                </div>
              )}
            </div>
            <div>
              <div className="text-xs text-white/50 mb-1">Common Domains</div>
              <div className="text-lg font-bold text-blue-400">
                {comparisonData.domain_differences.common_domains.length}
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 bg-white/[0.02] border border-white/[0.08] rounded-lg">
          <h4 className="text-sm font-mono font-semibold text-white mb-3">Findings Comparison</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-white/50 mb-1">Job 1 Findings</div>
              <div className="text-2xl font-bold text-white">{comparisonData.findings_comparison.count1}</div>
            </div>
            <div>
              <div className="text-xs text-white/50 mb-1">Job 2 Findings</div>
              <div className="text-2xl font-bold text-white">{comparisonData.findings_comparison.count2}</div>
            </div>
            <div>
              <div className="text-xs text-white/50 mb-1">New Findings</div>
              <div className="text-xl font-bold text-green-400">
                +{comparisonData.findings_comparison.new_findings}
              </div>
            </div>
            <div>
              <div className="text-xs text-white/50 mb-1">Resolved Findings</div>
              <div className="text-xl font-bold text-red-400">
                −{comparisonData.findings_comparison.resolved_findings}
              </div>
            </div>
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

