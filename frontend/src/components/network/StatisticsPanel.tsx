"use client";

import React, { useState, useEffect } from "react";
import { GlassCard } from "@/components/ui";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";

interface StatisticsPanelProps {
  className?: string;
}

export function StatisticsPanel({ className }: StatisticsPanelProps) {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await api.getNetworkStats();
        setStats(data);
      } catch (error) {
        console.error("Error fetching stats:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <GlassCard className={cn("", className)} hover={false}>
        <div className="text-white/40 font-mono text-sm">Loading statistics...</div>
      </GlassCard>
    );
  }

  return (
    <GlassCard className={cn("", className)} hover={false}>
      <h2 className="font-mono text-lg font-semibold text-white mb-4">Statistics</h2>

      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
            <div className="text-xs text-white/50 mb-1">Total Requests</div>
            <div className="text-xl font-mono font-bold text-white">
              {stats?.total_requests || 0}
            </div>
          </div>

          <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
            <div className="text-xs text-white/50 mb-1">Tunnel Detections</div>
            <div className="text-xl font-mono font-bold text-red-400">
              {stats?.tunnel_detections || 0}
            </div>
          </div>

          <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
            <div className="text-xs text-white/50 mb-1">Avg Response Time</div>
            <div className="text-xl font-mono font-bold text-white">
              {stats?.average_response_time_ms?.toFixed(0) || 0}ms
            </div>
          </div>

          <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
            <div className="text-xs text-white/50 mb-1">Status Codes</div>
            <div className="text-sm font-mono text-white/80">
              {Object.entries(stats?.status_counts || {})
                .slice(0, 3)
                .map(([code, count]: [string, any]) => (
                  <div key={code}>
                    {code}: {count}
                  </div>
                ))}
            </div>
          </div>
        </div>

        {stats?.top_ips && stats.top_ips.length > 0 && (
          <div>
            <div className="text-xs text-white/50 mb-2">Top IPs</div>
            <div className="space-y-1">
              {stats.top_ips.slice(0, 5).map((item: any) => (
                <div
                  key={item.ip}
                  className="flex justify-between text-xs font-mono text-white/80"
                >
                  <span className="truncate">{item.ip}</span>
                  <span className="text-white/50">{item.count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </GlassCard>
  );
}


