"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { GlassCard, Badge } from "@/components/ui";
import { formatRelativeTime } from "@/lib/utils";
import { api } from "@/lib/api";

interface ActivityItem {
  id: string;
  type: "threat" | "credential" | "scan" | "alert" | "darkweb";
  title: string;
  description: string;
  severity?: "critical" | "high" | "medium" | "low" | "info";
  timestamp: Date;
}

// Fetch activities from timeline API
async function fetchActivities(): Promise<ActivityItem[]> {
  try {
    const data = await api.getRecentTimelineEvents(20);
    // Map timeline events to ActivityItem format
    return data.map((event: any) => ({
      id: event.id,
      type: event.type === 'threat_detected' ? 'threat' : 
            event.type === 'credential_leaked' ? 'credential' :
            event.type === 'scan_completed' ? 'scan' :
            event.type === 'dark_web_mention' ? 'darkweb' : 'alert',
      title: event.title,
      description: event.description,
      severity: event.severity,
      timestamp: new Date(event.timestamp),
    }));
  } catch (error) {
    console.error('Error fetching activities:', error);
    return [];
  }
}

export function ActivityFeed() {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [displayedCount, setDisplayedCount] = useState(0);

  useEffect(() => {
    // Fetch activities from API
    fetchActivities().then((fetchedActivities) => {
      setActivities(fetchedActivities);
      
      // Simulate typing effect for activity items
      const timer = setInterval(() => {
        setDisplayedCount((prev) => {
          if (prev >= fetchedActivities.length) {
            clearInterval(timer);
            return prev;
          }
          return prev + 1;
        });
      }, 500);

      return () => clearInterval(timer);
    });
  }, []);

  const typeIcons = {
    threat: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    credential: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
      </svg>
    ),
    scan: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    alert: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
    ),
    darkweb: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
      </svg>
    ),
  };

  const typeColors = {
    threat: "text-red-400 bg-red-500/20",
    credential: "text-orange-400 bg-orange-500/20",
    scan: "text-blue-400 bg-blue-500/20",
    alert: "text-yellow-400 bg-yellow-500/20",
    darkweb: "text-purple-400 bg-purple-500/20",
  };

  return (
    <GlassCard className="h-full" padding="none">
      <div className="p-5 border-b border-white/[0.05]">
        <div className="flex items-center justify-between">
          <h3 className="font-mono font-semibold text-white">Activity Feed</h3>
          <Badge variant="info" size="sm">
            Live
          </Badge>
        </div>
      </div>

      <div className="p-4 space-y-3 max-h-[400px] overflow-y-auto">
        {activities.slice(0, displayedCount).map((activity, index) => (
          <div
            key={activity.id}
            className={cn(
              "flex gap-3 p-3 rounded-xl hover:bg-white/[0.02] transition-colors cursor-pointer",
              "animate-fade-in"
            )}
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div
              className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
                typeColors[activity.type]
              )}
            >
              {typeIcons[activity.type]}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <p className="font-mono text-sm text-white truncate">
                  {activity.title}
                </p>
                {activity.severity && (
                  <Badge
                    variant={activity.severity === "info" ? "info" : activity.severity}
                    size="sm"
                  >
                    {activity.severity}
                  </Badge>
                )}
              </div>
              <p className="text-xs text-white/50 truncate">{activity.description}</p>
              <p className="text-[10px] text-white/30 mt-1">
                {formatRelativeTime(activity.timestamp)}
              </p>
            </div>
          </div>
        ))}

        {displayedCount === 0 && (
          <div className="flex items-center justify-center py-8">
            <div className="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>
    </GlassCard>
  );
}

