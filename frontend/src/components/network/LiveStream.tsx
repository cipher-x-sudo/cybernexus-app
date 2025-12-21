"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { GlassCard } from "@/components/ui";
import { cn } from "@/lib/utils";
import { connectNetworkWebSocket, disconnectNetworkWebSocket, NetworkLogEntry } from "@/lib/network-websocket";

interface LiveStreamProps {
  className?: string;
  maxLogs?: number;
}

export function LiveStream({ className, maxLogs = 500 }: LiveStreamProps) {
  const [logs, setLogs] = useState<NetworkLogEntry[]>([]);
  const [selectedLog, setSelectedLog] = useState<NetworkLogEntry | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    wsRef.current = connectNetworkWebSocket({
      onLog: (log) => {
        setLogs((prev) => {
          const newLogs = [log, ...prev].slice(0, maxLogs);
          return newLogs;
        });
      },
      onConnect: () => setConnected(true),
      onDisconnect: () => setConnected(false),
      onError: (error) => console.error("WebSocket error:", error),
    });

    return () => {
      if (wsRef.current) {
        disconnectNetworkWebSocket(wsRef.current);
      }
    };
  }, [maxLogs]);

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = 0;
    }
  }, [logs, autoScroll]);

  const getStatusColor = (status: number) => {
    if (status >= 200 && status < 300) return "text-green-400";
    if (status >= 300 && status < 400) return "text-blue-400";
    if (status >= 400 && status < 500) return "text-orange-400";
    if (status >= 500) return "text-red-400";
    return "text-white/50";
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  return (
    <GlassCard className={cn("", className)} hover={false}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="font-mono text-lg font-semibold text-white">Live Stream</h2>
          <div className={cn("w-2 h-2 rounded-full", connected ? "bg-green-400" : "bg-red-400")} />
        </div>
        <label className="flex items-center gap-2 text-xs text-white/60 cursor-pointer">
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => setAutoScroll(e.target.checked)}
            className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1]"
          />
          Auto-scroll
        </label>
      </div>

      <div
        ref={containerRef}
        className="space-y-2 max-h-[600px] overflow-y-auto pr-2"
        style={{ scrollBehavior: autoScroll ? "smooth" : "auto" }}
      >
        {logs.length === 0 ? (
          <div className="py-12 text-center text-white/40 font-mono text-sm">
            {connected ? "Waiting for requests..." : "Connecting..."}
          </div>
        ) : (
          logs.map((log) => (
            <button
              key={log.id}
              onClick={() => setSelectedLog(log)}
              className={cn(
                "w-full p-3 rounded-lg border text-left transition-all",
                "hover:translate-x-1 bg-white/[0.02] border-white/[0.05]",
                selectedLog?.id === log.id && "bg-blue-500/10 border-blue-500/30"
              )}
            >
              <div className="flex items-center gap-3">
                <span className={cn("text-xs font-mono", getStatusColor(log.status))}>
                  {log.status}
                </span>
                <span className="text-xs font-mono text-white/60">{log.method}</span>
                <span className="text-sm text-white/80 truncate flex-1">{log.path}</span>
                {log.tunnel_detection && (
                  <span className="px-2 py-0.5 text-xs font-mono bg-red-500/20 text-red-400 rounded">
                    TUNNEL
                  </span>
                )}
                <span className="text-xs text-white/40">{formatTime(log.timestamp)}</span>
              </div>
            </button>
          ))
        )}
      </div>

      {selectedLog && (
        <div className="mt-4 p-4 rounded-lg bg-white/[0.02] border border-white/[0.05]">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-mono text-sm font-semibold text-white">Request Details</h3>
            <button
              onClick={() => setSelectedLog(null)}
              className="text-white/40 hover:text-white/80"
            >
              ×
            </button>
          </div>
          <div className="space-y-2 text-xs font-mono">
            <div>
              <span className="text-white/50">IP:</span>{" "}
              <span className="text-white/80">{selectedLog.ip}</span>
            </div>
            <div>
              <span className="text-white/50">Method:</span>{" "}
              <span className="text-white/80">{selectedLog.method}</span>
            </div>
            <div>
              <span className="text-white/50">Path:</span>{" "}
              <span className="text-white/80">{selectedLog.path}</span>
            </div>
            <div>
              <span className="text-white/50">Status:</span>{" "}
              <span className={getStatusColor(selectedLog.status)}>{selectedLog.status}</span>
            </div>
            <div>
              <span className="text-white/50">Response Time:</span>{" "}
              <span className="text-white/80">{selectedLog.response_time_ms}ms</span>
            </div>
            {selectedLog.tunnel_detection && (
              <div className="mt-3 p-2 rounded bg-red-500/10 border border-red-500/30">
                <div className="text-red-400 font-semibold mb-1">Tunnel Detected</div>
                <div className="text-white/70">
                  Type: {selectedLog.tunnel_detection.tunnel_type} | Confidence:{" "}
                  {selectedLog.tunnel_detection.confidence} | Risk:{" "}
                  {selectedLog.tunnel_detection.risk_score}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </GlassCard>
  );
}



