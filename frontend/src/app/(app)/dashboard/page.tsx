"use client";

import { GlassCard } from "@/components/ui";
import {
  RiskScore,
  CriticalFindings,
  CapabilityCards,
  LiveActivity,
  QuickStart,
  MiniWorldMap,
  LineChart,
} from "@/components/dashboard";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-mono font-bold text-white">Security Operations Center</h1>
          <p className="text-sm text-white/50">
            Unified view of your organization&apos;s security posture
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-xs font-mono text-emerald-400">All systems operational</span>
          </span>
        </div>
      </div>

      {/* Top row: Risk Score + Critical Findings */}
      <div className="grid lg:grid-cols-2 gap-6">
        <RiskScore
          score={78}
          riskLevel="medium"
          trend="improving"
          criticalIssues={3}
          highIssues={7}
        />
        <CriticalFindings />
      </div>

      {/* Quick Start */}
      <QuickStart 
        onScan={(domain) => console.log("Scanning:", domain)}
      />

      {/* Capability Cards */}
      <CapabilityCards />

      {/* Bottom row: Map + Activity + Trends */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* World map */}
        <GlassCard className="lg:col-span-2 overflow-hidden" padding="none">
          <div className="p-5 border-b border-white/[0.05]">
            <div className="flex items-center justify-between">
              <h2 className="font-mono font-semibold text-white">Global Threat Activity</h2>
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
                </span>
                <span className="text-xs font-mono text-white/50">12 active threats</span>
              </div>
            </div>
          </div>
          <div className="h-64 lg:h-72">
            <MiniWorldMap />
          </div>
        </GlassCard>

        {/* Live Activity */}
        <LiveActivity />
      </div>

      {/* Trends row */}
      <div className="grid lg:grid-cols-2 gap-6">
        <LineChart />
        
        {/* Recent Scans Summary */}
        <GlassCard className="p-6" hover={false}>
          <h2 className="font-mono text-lg font-semibold text-white mb-4">Recent Assessments</h2>
          <div className="space-y-3">
            {[
              { capability: "Email Security", target: "example.com", status: "completed", findings: 3, time: "2h ago" },
              { capability: "Exposure Discovery", target: "example.com", status: "completed", findings: 5, time: "4h ago" },
              { capability: "Infrastructure", target: "api.example.com", status: "completed", findings: 8, time: "6h ago" },
              { capability: "Dark Web Intel", target: "company-name", status: "running", findings: 0, time: "Started 15m ago" },
            ].map((scan, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:border-white/[0.1] transition-colors"
              >
                <div className="flex items-center gap-3">
                  {scan.status === "running" ? (
                    <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                      <svg className="w-4 h-4 text-blue-400 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </div>
                  ) : (
                    <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                      <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                  <div>
                    <p className="text-sm text-white font-medium">{scan.capability}</p>
                    <p className="text-xs text-white/40 font-mono">{scan.target}</p>
                  </div>
                </div>
                <div className="text-right">
                  {scan.status === "completed" && (
                    <p className="text-sm font-mono text-amber-400">{scan.findings} findings</p>
                  )}
                  <p className="text-xs text-white/40">{scan.time}</p>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
