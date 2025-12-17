"use client";

import React, { useMemo } from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";
import { InfrastructureFinding } from "./helpers";
import { formatRelativeTime, formatDate, formatTime } from "@/lib/utils";

interface TimelineViewProps {
  findings: InfrastructureFinding[];
  scanStartTime?: Date;
  scanEndTime?: Date;
  onFindingClick?: (finding: InfrastructureFinding) => void;
  selectedFindingId?: string;
  className?: string;
}

interface TimelineEvent {
  id: string;
  type: "finding" | "milestone";
  timestamp: Date;
  finding?: InfrastructureFinding;
  label: string;
  description?: string;
}

export function TimelineView({
  findings,
  scanStartTime,
  scanEndTime,
  onFindingClick,
  selectedFindingId,
  className,
}: TimelineViewProps) {
  const events = useMemo(() => {
    const timelineEvents: TimelineEvent[] = [];

    // Add scan start
    if (scanStartTime) {
      timelineEvents.push({
        id: "scan-start",
        type: "milestone",
        timestamp: scanStartTime,
        label: "Scan Started",
        description: "Infrastructure scan initiated",
      });
    }

    // Add findings
    findings.forEach((finding) => {
      // Try to parse timestamp, fallback to current time
      let discoveredAt: Date;
      try {
        // If timestamp is a relative time string like "2h ago", use current time
        if (finding.timestamp.includes("ago") || finding.timestamp === "Just now") {
          discoveredAt = new Date();
        } else {
          discoveredAt = new Date(finding.timestamp);
          // If invalid date, use current time
          if (isNaN(discoveredAt.getTime())) {
            discoveredAt = new Date();
          }
        }
      } catch {
        discoveredAt = new Date();
      }
      
      timelineEvents.push({
        id: finding.id,
        type: "finding",
        timestamp: discoveredAt,
        finding,
        label: finding.title,
        description: finding.severity,
      });
    });

    // Add scan end
    if (scanEndTime) {
      timelineEvents.push({
        id: "scan-end",
        type: "milestone",
        timestamp: scanEndTime,
        label: "Scan Completed",
        description: `Found ${findings.length} findings`,
      });
    }

    // Sort by timestamp
    return timelineEvents.sort(
      (a, b) => a.timestamp.getTime() - b.timestamp.getTime()
    );
  }, [findings, scanStartTime, scanEndTime]);

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: "bg-red-500",
      high: "bg-orange-500",
      medium: "bg-amber-500",
      low: "bg-blue-500",
      info: "bg-purple-500",
    };
    return colors[severity] || colors.info;
  };

  return (
    <GlassCard className={cn("p-6", className)} hover={false} padding="none">
      <h3 className="font-mono font-semibold text-white mb-6">Scan Timeline</h3>
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-white/10" />

        {/* Events */}
        <div className="space-y-6">
          {events.map((event, index) => {
            const isSelected = event.finding?.id === selectedFindingId;
            const isFinding = event.type === "finding";

            return (
              <div
                key={event.id}
                className={cn(
                  "relative flex items-start gap-4",
                  isFinding && "cursor-pointer hover:opacity-80 transition-opacity",
                  isSelected && "opacity-100"
                )}
                onClick={() => isFinding && event.finding && onFindingClick?.(event.finding)}
              >
                {/* Timeline dot */}
                <div className="relative z-10 flex-shrink-0">
                  <div
                    className={cn(
                      "w-12 h-12 rounded-full border-2 flex items-center justify-center",
                      isFinding && getSeverityColor(event.finding!.severity),
                      isFinding && "border-white/20",
                      !isFinding && "bg-emerald-500/20 border-emerald-500/50",
                      isSelected && "ring-2 ring-amber-500 ring-offset-2 ring-offset-slate-900"
                    )}
                  >
                    {isFinding ? (
                      <span className="text-white text-xs font-bold">
                        {event.finding!.severity.charAt(0).toUpperCase()}
                      </span>
                    ) : (
                      <span className="text-emerald-400 text-lg">●</span>
                    )}
                  </div>
                </div>

                {/* Event content */}
                <div className="flex-1 min-w-0 pt-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-mono font-semibold text-white text-sm">
                      {event.label}
                    </h4>
                    {isFinding && (
                      <span
                        className={cn(
                          "px-2 py-0.5 text-xs font-mono uppercase rounded",
                          event.finding!.severity === "critical" && "bg-red-500/20 text-red-400",
                          event.finding!.severity === "high" && "bg-orange-500/20 text-orange-400",
                          event.finding!.severity === "medium" && "bg-amber-500/20 text-amber-400",
                          event.finding!.severity === "low" && "bg-blue-500/20 text-blue-400",
                          event.finding!.severity === "info" && "bg-purple-500/20 text-purple-400"
                        )}
                      >
                        {event.finding!.severity}
                      </span>
                    )}
                  </div>
                  {event.description && (
                    <p className="text-xs text-white/50 mb-2">{event.description}</p>
                  )}
                  <div className="flex items-center gap-4 text-xs text-white/40 font-mono">
                    <span>{formatTime(event.timestamp)}</span>
                    <span>{formatDate(event.timestamp)}</span>
                    <span>{formatRelativeTime(event.timestamp)}</span>
                  </div>
                  {isFinding && event.finding && (
                    <p className="text-xs text-white/60 mt-2 line-clamp-2">
                      {event.finding.description}
                    </p>
                  )}
                </div>
              </div>
            );
          })}

          {events.length === 0 && (
            <div className="py-12 text-center text-white/40">
              <p className="font-mono">No timeline events available</p>
            </div>
          )}
        </div>
      </div>
    </GlassCard>
  );
}

