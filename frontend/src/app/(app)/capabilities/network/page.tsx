"use client";

import React from "react";
import Link from "next/link";
import { LiveStream, FilterPanel, StatisticsPanel, TunnelAlertsPanel, BlockManager } from "@/components/network";
import { GlassCard } from "@/components/ui";
import { cn } from "@/lib/utils";

export default function NetworkMonitoringPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <Link
            href="/capabilities"
            className="mt-1 p-2 rounded-lg hover:bg-white/[0.05] transition-colors"
          >
            <svg className="w-5 h-5 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-blue-500/10">
                <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                </svg>
              </div>
              <h1 className="text-2xl font-mono font-bold text-white">Network Monitoring</h1>
            </div>
            <p className="text-lg font-medium text-blue-400">Real-time traffic monitoring and blocking</p>
            <p className="text-sm text-white/50 mt-1">
              Monitor all API requests, detect tunnel patterns, and manage network blocks
            </p>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left Column - Live Stream and Tunnel Alerts */}
        <div className="lg:col-span-2 space-y-6">
          <LiveStream />
          <TunnelAlertsPanel />
        </div>

        {/* Right Column - Filters, Stats, and Blocks */}
        <div className="space-y-6">
          <FilterPanel onFilterChange={(filters) => console.log("Filters:", filters)} />
          <StatisticsPanel />
          <BlockManager />
        </div>
      </div>
    </div>
  );
}
