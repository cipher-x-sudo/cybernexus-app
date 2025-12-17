"use client";

import React from "react";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  Area,
  AreaChart,
} from "recharts";
import { GlassCard } from "@/components/ui";
import { cn } from "@/lib/utils";
import { InfrastructureStats, InfrastructureFinding, InfrastructureCategory, categoryLabels } from "./helpers";

interface InfrastructureChartsProps {
  stats: InfrastructureStats;
  findings: InfrastructureFinding[];
  timelineData?: Array<{ time: string; count: number }>;
  className?: string;
}

const COLORS = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#3b82f6",
  info: "#8b5cf6",
};

export function SeverityDistributionChart({
  stats,
  className,
}: {
  stats: InfrastructureStats;
  className?: string;
}) {
  const data = [
    { name: "Critical", value: stats.severityBreakdown.critical, color: COLORS.critical },
    { name: "High", value: stats.severityBreakdown.high, color: COLORS.high },
    { name: "Medium", value: stats.severityBreakdown.medium, color: COLORS.medium },
    { name: "Low", value: stats.severityBreakdown.low, color: COLORS.low },
    { name: "Info", value: stats.severityBreakdown.info, color: COLORS.info },
  ].filter((item) => item.value > 0);

  return (
    <GlassCard className={cn("p-6", className)} hover={false} padding="none">
      <h3 className="font-mono font-semibold text-white mb-4">Severity Distribution</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: "rgba(0, 0, 0, 0.8)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
              color: "#fff",
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </GlassCard>
  );
}

export function RiskHeatmap({
  findings,
  className,
}: {
  findings: InfrastructureFinding[];
  className?: string;
}) {
  // Create heatmap data: category vs severity
  const categories = Object.keys(categoryLabels) as InfrastructureCategory[];
  const severities: Array<"critical" | "high" | "medium" | "low" | "info"> = [
    "critical",
    "high",
    "medium",
    "low",
    "info",
  ];

  const heatmapData = categories.map((category) => {
    const categoryFindings = findings.filter((f) => f.category === category);
    const severityCounts = severities.reduce(
      (acc, severity) => {
        acc[severity] = categoryFindings.filter((f) => f.severity === severity).length;
        return acc;
      },
      {} as Record<string, number>
    );

    return {
      category: categoryLabels[category],
      ...severityCounts,
    };
  });

  return (
    <GlassCard className={cn("p-6", className)} hover={false} padding="none">
      <h3 className="font-mono font-semibold text-white mb-4">Risk Heatmap</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={heatmapData} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis type="number" stroke="rgba(255,255,255,0.5)" />
          <YAxis
            dataKey="category"
            type="category"
            stroke="rgba(255,255,255,0.5)"
            width={120}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "rgba(0, 0, 0, 0.8)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
              color: "#fff",
            }}
          />
          <Legend />
          <Bar dataKey="critical" stackId="a" fill={COLORS.critical} />
          <Bar dataKey="high" stackId="a" fill={COLORS.high} />
          <Bar dataKey="medium" stackId="a" fill={COLORS.medium} />
          <Bar dataKey="low" stackId="a" fill={COLORS.low} />
          <Bar dataKey="info" stackId="a" fill={COLORS.info} />
        </BarChart>
      </ResponsiveContainer>
    </GlassCard>
  );
}

export function TimelineChart({
  timelineData,
  className,
}: {
  timelineData?: Array<{ time: string; count: number }>;
  className?: string;
}) {
  if (!timelineData || timelineData.length === 0) {
    return (
      <GlassCard className={cn("p-6", className)} hover={false} padding="none">
        <h3 className="font-mono font-semibold text-white mb-4">Timeline</h3>
        <div className="h-64 flex items-center justify-center text-white/40">
          No timeline data available
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard className={cn("p-6", className)} hover={false} padding="none">
      <h3 className="font-mono font-semibold text-white mb-4">Findings Over Time</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={timelineData}>
          <defs>
            <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis
            dataKey="time"
            stroke="rgba(255,255,255,0.5)"
            tick={{ fill: "rgba(255,255,255,0.5)" }}
          />
          <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fill: "rgba(255,255,255,0.5)" }} />
          <Tooltip
            contentStyle={{
              backgroundColor: "rgba(0, 0, 0, 0.8)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
              color: "#fff",
            }}
          />
          <Area
            type="monotone"
            dataKey="count"
            stroke="#10b981"
            fillOpacity={1}
            fill="url(#colorCount)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </GlassCard>
  );
}

export function TestCoverageChart({
  stats,
  className,
}: {
  stats: InfrastructureStats;
  className?: string;
}) {
  const data = [
    {
      test: "CRLF",
      enabled: stats.testCoverage.crlf,
      findings: stats.categoryBreakdown.crlf,
    },
    {
      test: "Path Traversal",
      enabled: stats.testCoverage.pathTraversal,
      findings: stats.categoryBreakdown.path_traversal,
    },
    {
      test: "Version Detection",
      enabled: stats.testCoverage.versionDetection,
      findings: stats.categoryBreakdown.server_info,
    },
    {
      test: "CVE Lookup",
      enabled: stats.testCoverage.cveLookup,
      findings: stats.categoryBreakdown.cve,
    },
    {
      test: "Bypass Techniques",
      enabled: stats.testCoverage.bypassTechniques,
      findings: stats.categoryBreakdown.bypass,
    },
  ];

  return (
    <GlassCard className={cn("p-6", className)} hover={false} padding="none">
      <h3 className="font-mono font-semibold text-white mb-4">Test Coverage</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis type="number" stroke="rgba(255,255,255,0.5)" />
          <YAxis
            dataKey="test"
            type="category"
            stroke="rgba(255,255,255,0.5)"
            width={140}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "rgba(0, 0, 0, 0.8)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
              color: "#fff",
            }}
          />
          <Bar
            dataKey="findings"
            fill="#10b981"
            radius={[0, 4, 4, 0]}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.enabled ? "#10b981" : "rgba(255,255,255,0.1)"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </GlassCard>
  );
}

export function TrendsChart({
  comparisonData,
  className,
}: {
  comparisonData?: Array<{
    scan: string;
    critical: number;
    high: number;
    medium: number;
    low: number;
  }>;
  className?: string;
}) {
  if (!comparisonData || comparisonData.length === 0) {
    return (
      <GlassCard className={cn("p-6", className)} hover={false} padding="none">
        <h3 className="font-mono font-semibold text-white mb-4">Trends</h3>
        <div className="h-64 flex items-center justify-center text-white/40">
          No comparison data available
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard className={cn("p-6", className)} hover={false} padding="none">
      <h3 className="font-mono font-semibold text-white mb-4">Trends Comparison</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={comparisonData}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis
            dataKey="scan"
            stroke="rgba(255,255,255,0.5)"
            tick={{ fill: "rgba(255,255,255,0.5)" }}
          />
          <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fill: "rgba(255,255,255,0.5)" }} />
          <Tooltip
            contentStyle={{
              backgroundColor: "rgba(0, 0, 0, 0.8)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
              color: "#fff",
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="critical"
            stroke={COLORS.critical}
            strokeWidth={2}
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="high"
            stroke={COLORS.high}
            strokeWidth={2}
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="medium"
            stroke={COLORS.medium}
            strokeWidth={2}
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="low"
            stroke={COLORS.low}
            strokeWidth={2}
            dot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </GlassCard>
  );
}

