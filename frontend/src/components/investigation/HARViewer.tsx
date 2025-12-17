"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";

interface HARViewerProps {
  harData: any;
  className?: string;
}

export function HARViewer({ harData, className }: HARViewerProps) {
  const [selectedEntry, setSelectedEntry] = useState<any>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(["request"]));
  const [searchTerm, setSearchTerm] = useState("");

  if (!harData || !harData.entries) {
    return (
      <GlassCard className={cn("p-6", className)} hover={false}>
        <div className="text-center text-white/50 py-12">No HAR data available</div>
      </GlassCard>
    );
  }

  const filteredEntries = harData.entries.filter((entry: any) => {
    if (!searchTerm) return true;
    const url = entry.request?.url || "";
    return url.toLowerCase().includes(searchTerm.toLowerCase());
  });

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  return (
    <GlassCard className={cn("p-6", className)} hover={false}>
      <div className="space-y-4">
        {/* Search */}
        <input
          type="text"
          placeholder="Search requests..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-3 py-2 bg-white/[0.03] border border-white/[0.08] rounded-lg text-white placeholder-white/30 text-sm"
        />

        {/* Entries List */}
        <div className="space-y-2 max-h-[600px] overflow-y-auto">
          {filteredEntries.map((entry: any, idx: number) => {
            const request = entry.request || {};
            const response = entry.response || {};
            const url = request.url || "";
            const method = request.method || "GET";
            const status = response.status || 0;

            return (
              <div
                key={idx}
                className={cn(
                  "p-3 border border-white/[0.08] rounded-lg cursor-pointer transition-colors",
                  selectedEntry === entry ? "bg-orange-500/10 border-orange-500/40" : "hover:bg-white/[0.05]"
                )}
                onClick={() => setSelectedEntry(entry)}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={cn(
                      "px-2 py-0.5 rounded text-xs font-mono",
                      status >= 200 && status < 300
                        ? "bg-green-500/20 text-green-400"
                        : status >= 400
                        ? "bg-red-500/20 text-red-400"
                        : "bg-yellow-500/20 text-yellow-400"
                    )}
                  >
                    {status}
                  </span>
                  <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs font-mono">
                    {method}
                  </span>
                  <span className="flex-1 text-sm text-white/70 font-mono truncate">{url}</span>
                  <span className="text-xs text-white/50">
                    {response.bodySize > 1024
                      ? `${(response.bodySize / 1024).toFixed(1)}KB`
                      : `${response.bodySize}B`}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Entry Details */}
        {selectedEntry && (
          <div className="p-4 bg-white/[0.02] border border-white/[0.08] rounded-lg space-y-4">
            <h3 className="font-mono font-semibold text-white">Request Details</h3>

            {/* Request Section */}
            <div>
              <button
                onClick={() => toggleSection("request")}
                className="w-full flex items-center justify-between p-2 bg-white/[0.05] rounded text-left"
              >
                <span className="font-mono text-sm text-white">Request</span>
                <span className="text-white/50">{expandedSections.has("request") ? "−" : "+"}</span>
              </button>
              {expandedSections.has("request") && (
                <div className="mt-2 p-3 bg-black/30 rounded">
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-white/50">Method:</span>{" "}
                      <span className="text-white font-mono">{selectedEntry.request?.method}</span>
                    </div>
                    <div>
                      <span className="text-white/50">URL:</span>{" "}
                      <span className="text-white font-mono break-all">{selectedEntry.request?.url}</span>
                    </div>
                    <div>
                      <span className="text-white/50">HTTP Version:</span>{" "}
                      <span className="text-white">{selectedEntry.request?.httpVersion}</span>
                    </div>
                    <div>
                      <span className="text-white/50">Headers:</span>
                      <pre className="mt-1 p-2 bg-black/50 rounded text-xs overflow-x-auto">
                        {JSON.stringify(selectedEntry.request?.headers || [], null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Response Section */}
            <div>
              <button
                onClick={() => toggleSection("response")}
                className="w-full flex items-center justify-between p-2 bg-white/[0.05] rounded text-left"
              >
                <span className="font-mono text-sm text-white">Response</span>
                <span className="text-white/50">{expandedSections.has("response") ? "−" : "+"}</span>
              </button>
              {expandedSections.has("response") && (
                <div className="mt-2 p-3 bg-black/30 rounded">
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-white/50">Status:</span>{" "}
                      <span
                        className={cn(
                          "font-mono",
                          selectedEntry.response?.status >= 200 &&
                            selectedEntry.response?.status < 300
                            ? "text-green-400"
                            : selectedEntry.response?.status >= 400
                            ? "text-red-400"
                            : "text-yellow-400"
                        )}
                      >
                        {selectedEntry.response?.status} {selectedEntry.response?.statusText}
                      </span>
                    </div>
                    <div>
                      <span className="text-white/50">Size:</span>{" "}
                      <span className="text-white">
                        {selectedEntry.response?.bodySize > 1024
                          ? `${(selectedEntry.response?.bodySize / 1024).toFixed(1)}KB`
                          : `${selectedEntry.response?.bodySize}B`}
                      </span>
                    </div>
                    <div>
                      <span className="text-white/50">MIME Type:</span>{" "}
                      <span className="text-white">{selectedEntry.response?.content?.mimeType}</span>
                    </div>
                    <div>
                      <span className="text-white/50">Headers:</span>
                      <pre className="mt-1 p-2 bg-black/50 rounded text-xs overflow-x-auto">
                        {JSON.stringify(selectedEntry.response?.headers || [], null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Timings Section */}
            {selectedEntry.timings && (
              <div>
                <button
                  onClick={() => toggleSection("timings")}
                  className="w-full flex items-center justify-between p-2 bg-white/[0.05] rounded text-left"
                >
                  <span className="font-mono text-sm text-white">Timings</span>
                  <span className="text-white/50">{expandedSections.has("timings") ? "−" : "+"}</span>
                </button>
                {expandedSections.has("timings") && (
                  <div className="mt-2 p-3 bg-black/30 rounded">
                    <pre className="text-xs text-white/70">
                      {JSON.stringify(selectedEntry.timings, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </GlassCard>
  );
}

