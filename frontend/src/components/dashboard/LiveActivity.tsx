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

const initialEvents: ActivityEvent[] = [
  {
    id: "1",
    type: "job_completed",
    message: "Email Security scan completed for example.com",
    capability: "email_security",
    timestamp: "Just now",
  },
  {
    id: "2",
    type: "finding",
    message: "New finding: Exposed API endpoint discovered",
    capability: "exposure_discovery",
    severity: "high",
    timestamp: "2m ago",
  },
  {
    id: "3",
    type: "job_started",
    message: "Dark Web scan started for 'company-name'",
    capability: "dark_web_intelligence",
    timestamp: "5m ago",
  },
  {
    id: "4",
    type: "alert",
    message: "Critical: SPF bypass vulnerability detected",
    severity: "critical",
    timestamp: "12m ago",
  },
  {
    id: "5",
    type: "job_completed",
    message: "Infrastructure scan completed",
    capability: "infrastructure_testing",
    timestamp: "18m ago",
  },
];

interface LiveActivityProps {
  className?: string;
}

export function LiveActivity({ className }: LiveActivityProps) {
  const [events, setEvents] = useState<ActivityEvent[]>(initialEvents);
  const [isLive, setIsLive] = useState(true);

  // Simulate live updates
  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(() => {
      const newEventTypes = [
        { type: "job_started" as const, message: "Scan initiated" },
        { type: "job_completed" as const, message: "Scan completed" },
        { type: "finding" as const, message: "New finding detected" },
      ];
      
      const randomEvent = newEventTypes[Math.floor(Math.random() * newEventTypes.length)];
      const capabilities = ["Email Security", "Dark Web", "Infrastructure", "Exposure"];
      
      const newEvent: ActivityEvent = {
        id: Date.now().toString(),
        type: randomEvent.type,
        message: `${randomEvent.message} - ${capabilities[Math.floor(Math.random() * capabilities.length)]}`,
        timestamp: "Just now",
      };

      setEvents(prev => [newEvent, ...prev.slice(0, 9)]);
    }, 15000); // Every 15 seconds

    return () => clearInterval(interval);
  }, [isLive]);

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
        {events.map((event, index) => (
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
              <p className="text-xs text-white/40 mt-0.5 font-mono">{event.timestamp}</p>
            </div>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

export default LiveActivity;

