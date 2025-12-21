"use client";

import React, { useState, useEffect } from "react";
import { GlassCard } from "@/components/ui";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { TunnelAlert, connectNetworkWebSocket, disconnectNetworkWebSocket } from "@/lib/network-websocket";

interface TunnelAlertsPanelProps {
  className?: string;
}

export function TunnelAlertsPanel({ className }: TunnelAlertsPanelProps) {
  const [alerts, setAlerts] = useState<TunnelAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const wsRef = React.useRef<WebSocket | null>(null);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const data = await api.getTunnelDetections({ limit: 50 });
        setAlerts(data.detections.map((d: any) => d.detection));
      } catch (error) {
        console.error("Error fetching tunnel alerts:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();

    // Connect WebSocket for real-time alerts
    wsRef.current = connectNetworkWebSocket({
      onTunnelAlert: (alert) => {
        setAlerts((prev) => [alert, ...prev].slice(0, 50));
      },
    });

    return () => {
      if (wsRef.current) {
        disconnectNetworkWebSocket(wsRef.current);
      }
    };
  }, []);

  const getConfidenceColor = (confidence: string) => {
    switch (confidence.toLowerCase()) {
      case "confirmed":
        return "text-red-400";
      case "high":
        return "text-orange-400";
      case "medium":
        return "text-yellow-400";
      default:
        return "text-white/60";
    }
  };

  if (loading) {
    return (
      <GlassCard className={cn("", className)} hover={false}>
        <div className="text-white/40 font-mono text-sm">Loading tunnel alerts...</div>
      </GlassCard>
    );
  }

  return (
    <GlassCard className={cn("", className)} hover={false}>
      <h2 className="font-mono text-lg font-semibold text-white mb-4">
        Tunnel Alerts ({alerts.length})
      </h2>

      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="py-8 text-center text-white/40 font-mono text-sm">
            No tunnel detections
          </div>
        ) : (
          alerts.map((alert, index) => (
            <div
              key={alert.detection_id || index}
              className="p-3 rounded-lg bg-red-500/10 border border-red-500/30"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-mono font-semibold text-red-400">
                  {alert.tunnel_type}
                </span>
                <span className={cn("text-xs font-mono", getConfidenceColor(alert.confidence))}>
                  {alert.confidence}
                </span>
              </div>
              <div className="text-xs text-white/70 mb-1">Risk Score: {alert.risk_score}</div>
              {alert.indicators && alert.indicators.length > 0 && (
                <div className="text-xs text-white/50">
                  {alert.indicators.slice(0, 2).join(", ")}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </GlassCard>
  );
}



