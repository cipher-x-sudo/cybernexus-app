"use client";

import React, { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";

interface ActivityEvent {
  id: string;
  type: "job_started" | "job_completed" | "finding" | "alert";
  message: string;
  capability?: string;
  severity?: string;
  timestamp: string;
}

interface LiveActivityProps {
  className?: string;
  events?: Array<{
    id?: string;
    type: string;
    message?: string;
    title?: string;
    description?: string;
    severity?: string;
    source?: string;
    timestamp: string;
  }>;
}

export function LiveActivity({ className, events: propEvents }: LiveActivityProps) {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [isLive, setIsLive] = useState(true);

  useEffect(() => {
    if (propEvents) {
      if (propEvents.length > 0) {
        setEvents(mapEventsToActivity(propEvents));
      } else {
        setEvents([]);
      }
    }
  }, [propEvents]);

  useEffect(() => {
    if (!isLive || propEvents) return;

    const fetchEvents = async () => {
      try {
        const { api } = await import("@/lib/api");
        const response = await api.getCapabilityEvents(20);
        if (response.events && response.events.length > 0) {
          const jobEvents = response.events.filter((event: any) => {
            const type = event.type || "";
            return type === "job_started" || 
                   type === "job_completed" || 
                   type === "job_created" ||
                   type === "scan_started" ||
                   type === "scan_completed" ||
                   type === "scan_queued";
          });
          setEvents(mapEventsToActivity(jobEvents));
        } else {
          setEvents([]);
        }
      } catch (error) {
        console.error("Error fetching events:", error);
      }
    };

    fetchEvents();

    const interval = setInterval(fetchEvents, 15000);

    return () => clearInterval(interval);
  }, [isLive, propEvents]);

  function mapEventsToActivity(apiEvents: Array<{ 
    id?: string; 
    type: string; 
    message?: string;
    title?: string;
    description?: string;
    severity?: string;
    source?: string;
    timestamp: string;
  }>): ActivityEvent[] {
    return apiEvents.map((event, index) => {
      let activityType: "job_started" | "job_completed" | "finding" | "alert" = "alert";
      if (event.type === "job_started") activityType = "job_started";
      else if (event.type === "job_completed" || event.type === "scan_completed") activityType = "job_completed";
      else if (event.type.includes("finding") || event.type === "threat_detected" || event.type === "credential_leaked" || event.type === "dark_web_mention") {
        activityType = "finding";
      }
      
      const message = event.title || event.description || event.message || "Unknown event";
      
      const severity = event.severity || extractSeverity(message);
      
      const capability = event.source || extractCapability(message);
      
      return {
        id: event.id || `event-${index}`,
        type: activityType,
        message: message,
        timestamp: event.timestamp,
        capability: capability,
        severity: severity,
      };
    });
  }

  function extractCapability(message: string): string | undefined {
    const capabilities = ["email_security", "dark_web", "infrastructure", "exposure_discovery"];
    for (const cap of capabilities) {
      if (message.toLowerCase().includes(cap.replace(/_/g, " "))) {
        return cap;
      }
    }
    return undefined;
  }

  function extractSeverity(message: string): string | undefined {
    if (message.toLowerCase().includes("critical")) return "critical";
    if (message.toLowerCase().includes("high")) return "high";
    return undefined;
  }

  function formatTimestamp(timestamp: string): string {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diff = now.getTime() - date.getTime();
      
      const seconds = Math.floor(diff / 1000);
      const minutes = Math.floor(seconds / 60);
      const hours = Math.floor(minutes / 60);
      const days = Math.floor(hours / 24);
      
      if (days > 0) return `${days}d ago`;
      if (hours > 0) return `${hours}h ago`;
      if (minutes > 0) return `${minutes}m ago`;
      if (seconds > 0) return `${seconds}s ago`;
      return "Just now";
    } catch {
      return new Date(timestamp).toLocaleString();
    }
  }

  const getEventIcon = (type: string, severity?: string) => {
    if (type === "alert" || severity === "critical") {
      return (
        <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center">
          <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
      );
    }
    if (type === "finding") {
      return (
        <div className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center",
          severity === "high" ? "bg-orange-500/10" : "bg-amber-500/10"
        )}>
          <svg className={cn("w-4 h-4", severity === "high" ? "text-orange-400" : "text-amber-400")} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
      );
    }
    if (type === "job_completed") {
      return (
        <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
          <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      );
    }
    return (
      <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
        <svg className="w-4 h-4 text-blue-400 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </div>
    );
  };

  return (
    <GlassCard className={cn("p-6", className)} hover={false}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h2 className="font-mono text-lg font-semibold text-white">Live Activity</h2>
          {isLive && (
            <span className="flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="text-xs text-emerald-400 font-mono">LIVE</span>
            </span>
          )}
        </div>
        <button
          onClick={() => setIsLive(!isLive)}
          className={cn(
            "text-xs font-mono px-2 py-1 rounded-lg transition-colors",
            isLive ? "text-white/50 hover:text-white/70" : "text-amber-400"
          )}
        >
          {isLive ? "Pause" : "Resume"}
        </button>
      </div>

      <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
        {events.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm text-white/50 font-mono">No recent activity</p>
            <p className="text-xs text-white/30 mt-1">Events will appear here as they occur</p>
          </div>
        ) : (
          events.map((event, index) => (
          <div
            key={event.id}
            className={cn(
              "flex items-start gap-3 p-2 rounded-lg transition-all",
              "hover:bg-white/[0.02]",
              index === 0 && "animate-fade-in"
            )}
          >
            {getEventIcon(event.type, event.severity)}
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white/80 line-clamp-2">{event.message}</p>
              <p className="text-xs text-white/40 mt-0.5 font-mono">{formatTimestamp(event.timestamp)}</p>
            </div>
          </div>
          ))
        )}
      </div>
    </GlassCard>
  );
}

export default LiveActivity;



