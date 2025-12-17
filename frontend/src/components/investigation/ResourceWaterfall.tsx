"use client";

import React, { useState, useMemo } from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";

interface ResourceRequest {
  url: string;
  method: string;
  type: string;
  status: number;
  size: number;
  time: number;
  startTime: number;
  endTime: number;
  domain?: string;
}

interface ResourceWaterfallProps {
  harData: any;
  className?: string;
}

export function ResourceWaterfall({ harData, className }: ResourceWaterfallProps) {
  const [selectedRequest, setSelectedRequest] = useState<ResourceRequest | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"time" | "size" | "domain">("time");

  // Parse HAR data into resource requests
  const resources = useMemo(() => {
    if (!harData || !harData.entries) return [];

    const requests: ResourceRequest[] = [];
    let currentTime = 0;

    harData.entries.forEach((entry: any) => {
      const request = entry.request || {};
      const response = entry.response || {};
      const timings = entry.timings || {};

      const startTime = currentTime;
      const totalTime = Object.values(timings).reduce(
        (sum: number, val: any) => sum + (typeof val === "number" && val > 0 ? val : 0),
        0
      );
      const endTime = startTime + totalTime;
      currentTime = endTime;

      const url = request.url || "";
      const domain = url ? new URL(url).hostname : "";

      requests.push({
        url,
        method: request.method || "GET",
        type: response.content?.mimeType?.split("/")[0] || "other",
        status: response.status || 0,
        size: response.bodySize || response.content?.size || 0,
        time: totalTime,
        startTime,
        endTime,
        domain,
      });
    });

    return requests;
  }, [harData]);

  // Filter and sort resources
  const filteredResources = useMemo(() => {
    let filtered = resources.filter((r) => {
      if (filter !== "all" && r.type !== filter) return false;
      return true;
    });

    filtered.sort((a, b) => {
      switch (sortBy) {
        case "time":
          return b.time - a.time;
        case "size":
          return b.size - a.size;
        case "domain":
          return (a.domain || "").localeCompare(b.domain || "");
        default:
          return 0;
      }
    });

    return filtered;
  }, [resources, filter, sortBy]);

  const maxTime = Math.max(...resources.map((r) => r.endTime), 0);

  const getResourceTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      document: "bg-blue-500/20 border-blue-500/40 text-blue-400",
      script: "bg-purple-500/20 border-purple-500/40 text-purple-400",
      stylesheet: "bg-green-500/20 border-green-500/40 text-green-400",
      image: "bg-pink-500/20 border-pink-500/40 text-pink-400",
      font: "bg-yellow-500/20 border-yellow-500/40 text-yellow-400",
      xhr: "bg-orange-500/20 border-orange-500/40 text-orange-400",
      fetch: "bg-cyan-500/20 border-cyan-500/40 text-cyan-400",
    };
    return colors[type] || "bg-gray-500/20 border-gray-500/40 text-gray-400";
  };

  const getStatusColor = (status: number) => {
    if (status >= 200 && status < 300) return "text-green-400";
    if (status >= 300 && status < 400) return "text-yellow-400";
    if (status >= 400) return "text-red-400";
    return "text-white/50";
  };

  return (
    <GlassCard className={cn("p-6", className)} hover={false}>
      <div className="space-y-4">
        {/* Controls */}
        <div className="flex items-center gap-4 flex-wrap">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-2 bg-white/[0.03] border border-white/[0.08] rounded-lg text-white text-sm"
          >
            <option value="all">All Types</option>
            <option value="document">Document</option>
            <option value="script">Script</option>
            <option value="stylesheet">Stylesheet</option>
            <option value="image">Image</option>
            <option value="font">Font</option>
            <option value="xhr">XHR</option>
            <option value="fetch">Fetch</option>
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 bg-white/[0.03] border border-white/[0.08] rounded-lg text-white text-sm"
          >
            <option value="time">Sort by Time</option>
            <option value="size">Sort by Size</option>
            <option value="domain">Sort by Domain</option>
          </select>
          <div className="text-sm text-white/50">
            {filteredResources.length} of {resources.length} resources
          </div>
        </div>

        {/* Waterfall Chart */}
        <div className="border border-white/[0.08] rounded-lg bg-black/20 p-4 overflow-x-auto">
          <div className="min-w-[800px] space-y-2">
            {/* Timeline Header */}
            <div className="flex items-center gap-2 mb-4 pb-2 border-b border-white/[0.08]">
              <div className="w-48 text-xs text-white/50 font-mono">Resource</div>
              <div className="flex-1 relative h-6">
                <div className="absolute inset-0 flex items-center">
                  {[0, 25, 50, 75, 100].map((percent) => (
                    <div
                      key={percent}
                      className="absolute left-[calc(var(--percent)*1%)] text-xs text-white/30"
                      style={{ left: `${percent}%` }}
                    >
                      {Math.round((maxTime * percent) / 100)}ms
                    </div>
                  ))}
                </div>
              </div>
              <div className="w-20 text-xs text-white/50 text-right">Time</div>
              <div className="w-20 text-xs text-white/50 text-right">Size</div>
            </div>

            {/* Resource Bars */}
            {filteredResources.map((resource, idx) => {
              const leftPercent = (resource.startTime / maxTime) * 100;
              const widthPercent = ((resource.endTime - resource.startTime) / maxTime) * 100;
              const displayUrl = resource.url.length > 40 ? resource.url.substring(0, 40) + "..." : resource.url;

              return (
                <div
                  key={idx}
                  className={cn(
                    "flex items-center gap-2 py-1 hover:bg-white/[0.05] rounded cursor-pointer transition-colors",
                    selectedRequest === resource && "bg-orange-500/10"
                  )}
                  onClick={() => setSelectedRequest(resource)}
                >
                  <div className="w-48 text-xs font-mono text-white/70 truncate">{displayUrl}</div>
                  <div className="flex-1 relative h-6 bg-white/[0.05] rounded">
                    <div
                      className={cn(
                        "absolute h-full rounded",
                        getResourceTypeColor(resource.type).split(" ")[0]
                      )}
                      style={{
                        left: `${leftPercent}%`,
                        width: `${Math.max(widthPercent, 0.5)}%`,
                      }}
                    />
                  </div>
                  <div className={cn("w-20 text-xs text-right", getStatusColor(resource.status))}>
                    {Math.round(resource.time)}ms
                  </div>
                  <div className="w-20 text-xs text-white/50 text-right">
                    {resource.size > 1024 ? `${(resource.size / 1024).toFixed(1)}KB` : `${resource.size}B`}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Request Details */}
        {selectedRequest && (
          <div className="p-4 bg-white/[0.02] border border-white/[0.08] rounded-lg">
            <h3 className="font-mono font-semibold text-white mb-2">Request Details</h3>
            <div className="space-y-2 text-sm text-white/70">
              <div>
                <span className="text-white/50">URL:</span>{" "}
                <span className="font-mono">{selectedRequest.url}</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-white/50">Method:</span> {selectedRequest.method}
                </div>
                <div>
                  <span className="text-white/50">Status:</span>{" "}
                  <span className={getStatusColor(selectedRequest.status)}>
                    {selectedRequest.status}
                  </span>
                </div>
                <div>
                  <span className="text-white/50">Type:</span> {selectedRequest.type}
                </div>
                <div>
                  <span className="text-white/50">Domain:</span> {selectedRequest.domain}
                </div>
                <div>
                  <span className="text-white/50">Time:</span> {Math.round(selectedRequest.time)}ms
                </div>
                <div>
                  <span className="text-white/50">Size:</span>{" "}
                  {selectedRequest.size > 1024
                    ? `${(selectedRequest.size / 1024).toFixed(1)}KB`
                    : `${selectedRequest.size}B`}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </GlassCard>
  );
}

