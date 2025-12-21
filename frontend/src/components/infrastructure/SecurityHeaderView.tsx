"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { CopyButton } from "@/components/ui";

interface SecurityHeaderViewProps {
  evidence: Record<string, any>;
  severity?: "critical" | "high" | "medium" | "low" | "info";
}

export function SecurityHeaderView({ evidence, severity = "info" }: SecurityHeaderViewProps) {
  // Check if this is a missing header finding
  const missingHeader = evidence?.missing_header;
  
  // Check if this is a present headers finding
  const presentHeaders = evidence?.headers;

  // Severity-based styling
  const severityStyles = {
    critical: {
      border: "border-red-500/30",
      bg: "bg-red-500/10",
      text: "text-red-400",
      icon: "text-red-400",
    },
    high: {
      border: "border-orange-500/30",
      bg: "bg-orange-500/10",
      text: "text-orange-400",
      icon: "text-orange-400",
    },
    medium: {
      border: "border-amber-500/30",
      bg: "bg-amber-500/10",
      text: "text-amber-400",
      icon: "text-amber-400",
    },
    low: {
      border: "border-blue-500/30",
      bg: "bg-blue-500/10",
      text: "text-blue-400",
      icon: "text-blue-400",
    },
    info: {
      border: "border-purple-500/30",
      bg: "bg-purple-500/10",
      text: "text-purple-400",
      icon: "text-purple-400",
    },
  };

  const styles = severityStyles[severity] || severityStyles.info;

  // Missing header display
  if (missingHeader) {
    return (
      <div className={cn("p-4 rounded-lg border", styles.border, styles.bg)}>
        <div className="flex items-start gap-3">
          <div className={cn("flex-shrink-0 mt-0.5", styles.icon)}>
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <h4 className={cn("text-sm font-mono font-semibold mb-1", styles.text)}>
              Missing Header
            </h4>
            <p className="text-sm font-mono text-white/90 mb-2 break-all">
              {missingHeader}
            </p>
            {evidence?.recommendation && (
              <div className="mt-3 pt-3 border-t border-white/10">
                <p className="text-xs text-white/50 mb-1">Recommendation:</p>
                <p className="text-xs text-white/70">{evidence.recommendation}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Present headers display
  if (presentHeaders && typeof presentHeaders === "object") {
    const headerEntries = Object.entries(presentHeaders);

    if (headerEntries.length === 0) {
      return (
        <div className="p-4 rounded-lg bg-white/5 border border-white/10">
          <p className="text-sm text-white/50 font-mono">No headers data available</p>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2 mb-3">
          <div className={cn("flex-shrink-0", styles.icon)}>
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <h4 className="text-xs font-mono text-white/50 uppercase tracking-wide">
            {headerEntries.length} Header{headerEntries.length !== 1 ? "s" : ""} Present
          </h4>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-2 px-3 text-xs font-mono text-white/50">
                  Header Name
                </th>
                <th className="text-left py-2 px-3 text-xs font-mono text-white/50">
                  Value
                </th>
                <th className="w-10"></th>
              </tr>
            </thead>
            <tbody>
              {headerEntries.map(([headerName, headerValue], index) => {
                const valueStr = String(headerValue || "");
                return (
                  <tr
                    key={headerName}
                    className={cn(
                      "border-b border-white/5 hover:bg-white/5 transition-colors",
                      index === headerEntries.length - 1 && "border-b-0"
                    )}
                  >
                    <td className="py-3 px-3">
                      <span className="text-sm font-mono text-white/90 font-semibold">
                        {headerName}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2 max-w-md">
                        <span className="text-sm font-mono text-white/70 break-all">
                          {valueStr}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-2">
                      <CopyButton text={valueStr} size="sm" />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // Fallback for unknown evidence structure
  return (
    <div className="p-4 rounded-lg bg-white/5 border border-white/10">
      <p className="text-sm text-white/50 font-mono">Unable to parse header information</p>
      <details className="mt-2">
        <summary className="text-xs text-white/40 cursor-pointer hover:text-white/60">
          View raw evidence
        </summary>
        <pre className="mt-2 p-2 rounded bg-black/30 text-xs font-mono text-white/70 overflow-x-auto">
          {JSON.stringify(evidence, null, 2)}
        </pre>
      </details>
    </div>
  );
}

