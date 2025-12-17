"use client";

import React, { useMemo } from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";
import { InfrastructureFinding, InfrastructureStats, calculateInfrastructureStats } from "./helpers";
import { TrendsChart } from "./InfrastructureCharts";
import { StatsTile } from "./StatsTile";

interface ComparisonViewProps {
  scanResults: Array<{
    id: string;
    name: string;
    findings: InfrastructureFinding[];
    timestamp: Date;
  }>;
  className?: string;
}

export function ComparisonView({ scanResults, className }: ComparisonViewProps) {
  const comparisonStats = useMemo(() => {
    return scanResults.map((scan) => ({
      id: scan.id,
      name: scan.name,
      stats: calculateInfrastructureStats(scan.findings),
      timestamp: scan.timestamp,
    }));
  }, [scanResults]);

  const trendsData = useMemo(() => {
    return comparisonStats.map((scan) => ({
      scan: scan.name,
      critical: scan.stats.severityBreakdown.critical,
      high: scan.stats.severityBreakdown.high,
      medium: scan.stats.severityBreakdown.medium,
      low: scan.stats.severityBreakdown.low,
    }));
  }, [comparisonStats]);

  if (scanResults.length === 0) {
    return (
      <GlassCard className={cn("p-6", className)} hover={false} padding="none">
        <div className="py-12 text-center text-white/40">
          <p className="font-mono">No scans selected for comparison</p>
          <p className="text-sm mt-2">Select multiple scans to compare results</p>
        </div>
      </GlassCard>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Comparison Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {comparisonStats.map((scan) => (
          <GlassCard key={scan.id} className="p-4" hover={false} padding="none">
            <h4 className="font-mono font-semibold text-white mb-3 text-sm">{scan.name}</h4>
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-white/60">Total Findings</span>
                <span className="text-white font-mono">{scan.stats.totalFindings}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-white/60">Critical</span>
                <span className="text-red-400 font-mono">{scan.stats.criticalFindings}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-white/60">High</span>
                <span className="text-orange-400 font-mono">{scan.stats.highFindings}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-white/60">Avg Risk</span>
                <span className="text-white font-mono">{scan.stats.averageRiskScore}</span>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>

      {/* Trends Chart */}
      {trendsData.length > 1 && (
        <TrendsChart comparisonData={trendsData} />
      )}

      {/* Detailed Comparison Table */}
      <GlassCard className="p-6" hover={false} padding="none">
        <h3 className="font-mono font-semibold text-white mb-4">Detailed Comparison</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-3 px-4 text-xs font-mono text-white/60">Metric</th>
                {comparisonStats.map((scan) => (
                  <th
                    key={scan.id}
                    className="text-right py-3 px-4 text-xs font-mono text-white/60"
                  >
                    {scan.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-white/5">
                <td className="py-3 px-4 text-sm text-white/80">Total Findings</td>
                {comparisonStats.map((scan) => (
                  <td key={scan.id} className="py-3 px-4 text-sm text-white font-mono text-right">
                    {scan.stats.totalFindings}
                  </td>
                ))}
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-3 px-4 text-sm text-white/80">Critical</td>
                {comparisonStats.map((scan) => (
                  <td key={scan.id} className="py-3 px-4 text-sm text-red-400 font-mono text-right">
                    {scan.stats.severityBreakdown.critical}
                  </td>
                ))}
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-3 px-4 text-sm text-white/80">High</td>
                {comparisonStats.map((scan) => (
                  <td key={scan.id} className="py-3 px-4 text-sm text-orange-400 font-mono text-right">
                    {scan.stats.severityBreakdown.high}
                  </td>
                ))}
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-3 px-4 text-sm text-white/80">Medium</td>
                {comparisonStats.map((scan) => (
                  <td key={scan.id} className="py-3 px-4 text-sm text-amber-400 font-mono text-right">
                    {scan.stats.severityBreakdown.medium}
                  </td>
                ))}
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-3 px-4 text-sm text-white/80">Low</td>
                {comparisonStats.map((scan) => (
                  <td key={scan.id} className="py-3 px-4 text-sm text-blue-400 font-mono text-right">
                    {scan.stats.severityBreakdown.low}
                  </td>
                ))}
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-3 px-4 text-sm text-white/80">Info</td>
                {comparisonStats.map((scan) => (
                  <td key={scan.id} className="py-3 px-4 text-sm text-purple-400 font-mono text-right">
                    {scan.stats.severityBreakdown.info}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="py-3 px-4 text-sm text-white/80">Average Risk Score</td>
                {comparisonStats.map((scan) => (
                  <td key={scan.id} className="py-3 px-4 text-sm text-white font-mono text-right">
                    {scan.stats.averageRiskScore}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  );
}

