"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";
import { GlassButton } from "@/components/ui/glass-button";
import Link from "next/link";
import { api, CapabilityFinding, CapabilityJob } from "@/lib/api";
import { connectDarkwebJobWebSocket } from "@/lib/websocket";

interface Finding {
  id: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  description: string;
  evidence: string;
  recommendations: string[];
  timestamp: string;
}

interface CapabilityPageProps {
  id: string;
  name: string;
  question: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  inputLabel: string;
  inputPlaceholder: string;
  configOptions?: React.ReactNode;
}

// Convert API finding to display finding
function convertFinding(apiFinding: CapabilityFinding): Finding {
  // Format evidence as string for display
  let evidenceStr = "";
  if (apiFinding.evidence) {
    try {
      evidenceStr = Object.entries(apiFinding.evidence)
        .map(([key, value]) => {
          if (typeof value === "object") {
            return `${key}: ${JSON.stringify(value, null, 2)}`;
          }
          return `${key}: ${value}`;
        })
        .join("\n");
    } catch {
      evidenceStr = JSON.stringify(apiFinding.evidence, null, 2);
    }
  }

  // Format timestamp
  const timestamp = apiFinding.discovered_at
    ? formatRelativeTime(new Date(apiFinding.discovered_at))
    : "Just now";

  return {
    id: apiFinding.id,
    title: apiFinding.title,
    severity: apiFinding.severity,
    description: apiFinding.description,
    evidence: evidenceStr,
    recommendations: apiFinding.recommendations || [],
    timestamp,
  };
}

function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export function CapabilityPage({
  id,
  name,
  question,
  description,
  icon,
  color,
  inputLabel,
  inputPlaceholder,
  configOptions,
}: CapabilityPageProps) {
  const [target, setTarget] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [progress, setProgress] = useState(0);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [currentJob, setCurrentJob] = useState<CapabilityJob | null>(null);
  
  // Refs to track polling state and cleanup on unmount
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isPollingRef = useRef(false);
  const websocketRef = useRef<WebSocket | null>(null);
  
  // Check if this is a darkweb job (use WebSocket instead of polling)
  const isDarkwebJob = id === "dark_web_intelligence";

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      if (websocketRef.current) {
        websocketRef.current.close();
        websocketRef.current = null;
      }
    };
  }, []);

  const getColorClasses = () => {
    const colors: Record<string, { accent: string; bg: string; border: string; glow: string }> = {
      cyan: {
        accent: "text-cyan-400",
        bg: "bg-cyan-500/10",
        border: "border-cyan-500/30",
        glow: "shadow-[0_0_30px_rgba(6,182,212,0.2)]",
      },
      purple: {
        accent: "text-purple-400",
        bg: "bg-purple-500/10",
        border: "border-purple-500/30",
        glow: "shadow-[0_0_30px_rgba(139,92,246,0.2)]",
      },
      amber: {
        accent: "text-amber-400",
        bg: "bg-amber-500/10",
        border: "border-amber-500/30",
        glow: "shadow-[0_0_30px_rgba(245,158,11,0.2)]",
      },
      emerald: {
        accent: "text-emerald-400",
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/30",
        glow: "shadow-[0_0_30px_rgba(16,185,129,0.2)]",
      },
      rose: {
        accent: "text-rose-400",
        bg: "bg-rose-500/10",
        border: "border-rose-500/30",
        glow: "shadow-[0_0_30px_rgba(244,63,94,0.2)]",
      },
      blue: {
        accent: "text-blue-400",
        bg: "bg-blue-500/10",
        border: "border-blue-500/30",
        glow: "shadow-[0_0_30px_rgba(59,130,246,0.2)]",
      },
      orange: {
        accent: "text-orange-400",
        bg: "bg-orange-500/10",
        border: "border-orange-500/30",
        glow: "shadow-[0_0_30px_rgba(249,115,22,0.2)]",
      },
    };
    return colors[color] || colors.cyan;
  };

  const colors = getColorClasses();

  // Poll for job status
  const pollJobStatus = useCallback(async (jobId: string) => {
    try {
      const job = await api.getJobStatus(jobId);
      setCurrentJob(job);
      setProgress(job.progress);

      if (job.status === "completed") {
        // Fetch findings
        const apiFindings = await api.getJobFindings(jobId);
        const convertedFindings = apiFindings.map(convertFinding);
        setFindings(convertedFindings);
        setIsScanning(false);
        setProgress(100);
        return true; // Done
      } else if (job.status === "failed") {
        setError(job.error || "Scan failed");
        setIsScanning(false);
        return true; // Done
      }
      return false; // Keep polling
    } catch (err) {
      console.error("Error polling job status:", err);
      return false;
    }
  }, []);

  const handleScan = async () => {
    if (!target.trim()) return;
    
    // Clean up any existing polling or WebSocket
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    
    setIsScanning(true);
    setProgress(0);
    setError(null);
    setFindings([]);
    setSelectedFinding(null);
    isPollingRef.current = false;

    try {
      // Create job via API
      const job = await api.createCapabilityJob({
        capability: id,
        target: target.trim(),
        priority: "normal",
      });

      setCurrentJob(job);

      // Use WebSocket for darkweb jobs, polling for others
      if (isDarkwebJob) {
        // Connect via WebSocket for real-time streaming
        const ws = connectDarkwebJobWebSocket(job.id, {
          onFinding: (finding) => {
            console.log("[WebSocket] Received finding:", finding);
            // Convert and add finding immediately
            try {
              const convertedFinding = convertFinding(finding);
              setFindings((prev: Finding[]) => {
                // Check if finding already exists to avoid duplicates
                const exists = prev.some(f => f.id === convertedFinding.id);
                if (exists) {
                  console.log("[WebSocket] Finding already exists, skipping:", convertedFinding.id);
                  return prev;
                }
                return [...prev, convertedFinding];
              });
            } catch (err) {
              console.error("[WebSocket] Error converting finding:", err, finding);
            }
          },
          onProgress: (progressValue, message) => {
            console.log("[WebSocket] Progress update:", progressValue, message);
            setProgress(progressValue);
            // Update job status if needed
            setCurrentJob((prev) => {
              if (prev) {
                return { ...prev, progress: progressValue };
              }
              return prev;
            });
          },
          onComplete: (data) => {
            console.log("[WebSocket] Job complete:", data);
            setIsScanning(false);
            setProgress(100);
            // Update job status to completed
            setCurrentJob((prev) => {
              if (prev) {
                return { ...prev, status: "completed", progress: 100 };
              }
              return prev;
            });
            // Close WebSocket connection
            if (websocketRef.current) {
              websocketRef.current.close();
              websocketRef.current = null;
            }
          },
          onError: (errorMsg) => {
            console.error("[WebSocket] Error:", errorMsg);
            setError(errorMsg);
            setIsScanning(false);
          },
          onConnect: () => {
            console.log("[WebSocket] Connected to darkweb job");
          },
          onDisconnect: () => {
            console.log("[WebSocket] Disconnected from darkweb job");
          },
        });
        
        websocketRef.current = ws;
        
        // Timeout after 10 minutes for darkweb jobs (they can take longer)
        timeoutRef.current = setTimeout(() => {
          if (websocketRef.current) {
            websocketRef.current.close();
            websocketRef.current = null;
          }
          setIsScanning((current: boolean) => {
            if (current) {
              setError("Scan timed out");
              return false;
            }
            return current;
          });
        }, 600000); // 10 minutes
      } else {
        // Poll for job completion - slower interval to prevent request backlog
        pollIntervalRef.current = setInterval(async () => {
          // Skip if previous request is still in flight
          if (isPollingRef.current) {
            console.warn("[Polling] Skipping poll - previous request still pending");
            return;
          }

          try {
            isPollingRef.current = true;
            const done = await pollJobStatus(job.id);
            if (done && pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
              if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
                timeoutRef.current = null;
              }
            }
          } catch (err) {
            console.error("[Polling] Error polling job status:", err);
            // On network error, stop polling to prevent backlog
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
            if (timeoutRef.current) {
              clearTimeout(timeoutRef.current);
              timeoutRef.current = null;
            }
            setError("Failed to check job status. Please refresh the page.");
            setIsScanning(false);
          } finally {
            isPollingRef.current = false;
          }
        }, 5000); // Poll every 5 seconds to reduce load and prevent CORS preflight backlog

        // Timeout after 5 minutes
        timeoutRef.current = setTimeout(() => {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setIsScanning((current: boolean) => {
            if (current) {
              setError("Scan timed out");
              return false;
            }
            return current;
          });
        }, 300000);
      }

    } catch (err) {
      console.error("Scan error:", err);
      setError(err instanceof Error ? err.message : "Failed to start scan");
      setIsScanning(false);
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      if (websocketRef.current) {
        websocketRef.current.close();
        websocketRef.current = null;
      }
    }
  };

  const getSeverityStyles = (severity: string) => {
    const styles: Record<string, { bg: string; text: string; border: string }> = {
      critical: { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/30" },
      high: { bg: "bg-orange-500/10", text: "text-orange-400", border: "border-orange-500/30" },
      medium: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30" },
      low: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/30" },
      info: { bg: "bg-slate-500/10", text: "text-slate-400", border: "border-slate-500/30" },
    };
    return styles[severity] || styles.info;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <Link
            href="/capabilities"
            className="mt-1 p-2 rounded-lg hover:bg-white/[0.05] transition-colors"
          >
            <svg className="w-5 h-5 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center", colors.bg)}>
                {icon}
              </div>
              <h1 className="text-2xl font-mono font-bold text-white">{name}</h1>
            </div>
            <p className={cn("text-lg font-medium", colors.accent)}>{question}</p>
            <p className="text-sm text-white/50 mt-1">{description}</p>
          </div>
        </div>
      </div>

      {/* Scan Input */}
      <GlassCard className={cn("p-6", colors.border)} hover={false}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleScan();
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-mono text-white/70 mb-2">{inputLabel}</label>
            <div className="relative">
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder={inputPlaceholder}
                disabled={isScanning}
                className={cn(
                  "w-full h-12 px-4 pr-40",
                  "bg-white/[0.03] border border-white/[0.08] rounded-xl",
                  "text-white placeholder-white/30",
                  "font-mono text-sm",
                  "focus:outline-none focus:border-amber-500/40",
                  "transition-all duration-200",
                  "disabled:opacity-50"
                )}
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowConfig(!showConfig)}
                  className={cn(
                    "p-2 rounded-lg transition-colors",
                    showConfig ? "bg-white/[0.1] text-white" : "text-white/40 hover:text-white/60"
                  )}
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </button>
                <GlassButton type="submit" variant="primary" size="sm" loading={isScanning}>
                  {isScanning ? "Scanning..." : "Start Scan"}
                </GlassButton>
              </div>
            </div>
          </div>

          {/* Error message */}
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-mono animate-fade-in">
              {error}
            </div>
          )}

          {/* Progress bar */}
          {isScanning && (
            <div className="space-y-2 animate-fade-in">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-white/50">
                  {currentJob?.status === "running" ? "Scanning..." : "Starting..."}
                </span>
                <span className={colors.accent}>{Math.round(progress)}%</span>
              </div>
              <div className="h-1.5 bg-white/[0.05] rounded-full overflow-hidden">
                <div
                  className={cn("h-full rounded-full transition-all duration-300", colors.bg.replace("/10", "/50"))}
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Config options */}
          {showConfig && configOptions && (
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] animate-fade-in">
              {configOptions}
            </div>
          )}
        </form>
      </GlassCard>

      {/* Results */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Findings List */}
        <div className="lg:col-span-2">
          <GlassCard className="p-6" hover={false}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-mono text-lg font-semibold text-white">
                Findings ({findings.length})
              </h2>
              {findings.length > 0 && (
                <div className="flex items-center gap-2 text-xs font-mono">
                  <span className="text-red-400">{findings.filter((f) => f.severity === "critical").length} critical</span>
                  <span className="text-white/30">•</span>
                  <span className="text-orange-400">{findings.filter((f) => f.severity === "high").length} high</span>
                </div>
              )}
            </div>

            {findings.length === 0 ? (
              <div className="py-12 text-center">
                <div className={cn("w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center", colors.bg)}>
                  {icon}
                </div>
                <p className="text-white/50 font-mono">No findings yet</p>
                <p className="text-sm text-white/30 mt-1">Enter a target and start a scan</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                {findings.map((finding) => {
                  const styles = getSeverityStyles(finding.severity);
                  return (
                    <button
                      key={finding.id}
                      onClick={() => setSelectedFinding(finding)}
                      className={cn(
                        "w-full p-4 rounded-xl border text-left transition-all",
                        "hover:translate-x-1",
                        styles.bg,
                        styles.border,
                        selectedFinding?.id === finding.id && colors.glow
                      )}
                    >
                      <div className="flex items-start gap-3">
                        <span
                          className={cn(
                            "px-2 py-0.5 text-xs font-mono uppercase rounded flex-shrink-0",
                            styles.bg,
                            styles.text
                          )}
                        >
                          {finding.severity}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-white truncate">{finding.title}</p>
                          <p className="text-xs text-white/40 mt-1 line-clamp-2">{finding.description}</p>
                        </div>
                        <span className="text-xs text-white/30 flex-shrink-0">{finding.timestamp}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </GlassCard>
        </div>

        {/* Finding Details */}
        <div>
          <GlassCard className="p-6 sticky top-6" hover={false}>
            <h2 className="font-mono text-lg font-semibold text-white mb-4">Details</h2>
            
            {selectedFinding ? (
              <div className="space-y-4 animate-fade-in">
                <div>
                  <span
                    className={cn(
                      "px-2 py-0.5 text-xs font-mono uppercase rounded",
                      getSeverityStyles(selectedFinding.severity).bg,
                      getSeverityStyles(selectedFinding.severity).text
                    )}
                  >
                    {selectedFinding.severity}
                  </span>
                </div>
                
                <div>
                  <h3 className="text-sm font-medium text-white">{selectedFinding.title}</h3>
                  <p className="text-sm text-white/60 mt-2">{selectedFinding.description}</p>
                </div>

                <div>
                  <h4 className="text-xs font-mono text-white/50 mb-2">Evidence</h4>
                  <pre className="p-3 rounded-lg bg-black/30 text-xs font-mono text-white/70 overflow-x-auto whitespace-pre-wrap max-h-48 overflow-y-auto">
                    {selectedFinding.evidence || "No evidence available"}
                  </pre>
                </div>

                {selectedFinding.recommendations.length > 0 && (
                  <div>
                    <h4 className="text-xs font-mono text-white/50 mb-2">Recommendations</h4>
                    <ul className="space-y-1">
                      {selectedFinding.recommendations.map((rec, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-white/70">
                          <span className={colors.accent}>•</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-8 text-center">
                <p className="text-sm text-white/40">Select a finding to view details</p>
              </div>
            )}
          </GlassCard>
        </div>
      </div>
    </div>
  );
}

export default CapabilityPage;
