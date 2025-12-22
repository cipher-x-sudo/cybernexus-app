"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";
import { GlassButton } from "@/components/ui/glass-button";
import { api, CapabilityFinding, CapabilityJob } from "@/lib/api";
import { DomainTreeView } from "@/components/investigation/DomainTreeView";
import { ScreenshotViewer } from "@/components/investigation/ScreenshotViewer";
import { ResourceWaterfall } from "@/components/investigation/ResourceWaterfall";
import { HARViewer } from "@/components/investigation/HARViewer";
import { RiskDashboard } from "@/components/investigation/RiskDashboard";
import { InvestigationFindings } from "@/components/investigation/InvestigationFindings";
import { ExportPanel } from "@/components/investigation/ExportPanel";

export default function InvestigationPage() {
  const [target, setTarget] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentJob, setCurrentJob] = useState<CapabilityJob | null>(null);
  const [findings, setFindings] = useState<CapabilityFinding[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  // Investigation data
  const [screenshotUrl, setScreenshotUrl] = useState<string | null>(null);
  const [harData, setHarData] = useState<any>(null);
  const [domainTree, setDomainTree] = useState<{ nodes: any[]; edges: any[] } | null>(null);
  const [riskData, setRiskData] = useState<any>(null);

  const [config, setConfig] = useState({
    capture_screenshot: true,
    map_resources: true,
    check_reputation: true,
    visual_similarity: false,
    cross_reference_darkweb: false,
  });

  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isPollingRef = useRef(false);

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const pollJobStatus = useCallback(async (jobId: string) => {
    try {
      const job = await api.getJobStatus(jobId);
      setCurrentJob(job);
      setProgress(job.progress);

      if (job.status === "completed") {
        const apiFindings = await api.getJobFindings(jobId);
        setFindings(apiFindings);
        
        try {
          const screenshot = await api.getInvestigationScreenshot(jobId);
          setScreenshotUrl(screenshot);
        } catch (e) {
          console.warn("Screenshot not available:", e);
        }

        try {
          const har = await api.getInvestigationHAR(jobId);
          setHarData(har);
        } catch (e) {
          console.warn("HAR not available:", e);
        }

        try {
          const tree = await api.getInvestigationDomainTree(jobId);
          setDomainTree(tree);
        } catch (e) {
          console.warn("Domain tree not available:", e);
        }

        const riskFinding = apiFindings.find((f) => f.title.includes("Risk Score"));
        if (riskFinding && riskFinding.evidence) {
          setRiskData({
            riskScore: riskFinding.evidence.risk_score || 0,
            riskLevel: riskFinding.evidence.risk_level || "low",
            riskFactors: riskFinding.evidence.risk_factors || [],
            thirdPartyCount: riskFinding.evidence.third_party_count || 0,
            trackerCount: riskFinding.evidence.tracker_count || 0,
            totalDomains: riskFinding.evidence.total_domains || 0,
          });
        }

        setIsScanning(false);
        setProgress(100);
        return true;
      } else if (job.status === "failed") {
        setError(job.error || "Scan failed");
        setIsScanning(false);
        return true;
      }
      return false;
    } catch (err) {
      console.error("Error polling job status:", err);
      return false;
    }
  }, []);

  const handleScan = async () => {
    if (!target.trim()) return;

    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    setIsScanning(true);
    setProgress(0);
    setError(null);
    setFindings([]);
    setScreenshotUrl(null);
    setHarData(null);
    setDomainTree(null);
    setRiskData(null);
    isPollingRef.current = false;

    try {
      const job = await api.createCapabilityJob({
        capability: "investigation",
        target: target.trim(),
        priority: "normal",
        config: config,
      });

      setCurrentJob(job);

      // Immediate poll to get initial progress
      pollJobStatus(job.id).catch(err => {
        console.error("[Initial Poll] Error:", err);
      });

      // Poll for job completion
      pollIntervalRef.current = setInterval(async () => {
        if (isPollingRef.current) return;

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
          console.error("[Polling] Error:", err);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setError("Failed to check job status");
          setIsScanning(false);
        } finally {
          isPollingRef.current = false;
        }
      }, 5000);

      timeoutRef.current = setTimeout(() => {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setIsScanning((current) => {
          if (current) {
            setError("Scan timed out");
            return false;
          }
          return current;
        });
      }, 300000);
    } catch (err) {
      console.error("Scan error:", err);
      setError(err instanceof Error ? err.message : "Failed to start scan");
      setIsScanning(false);
    }
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
              <div className="w-10 h-10 rounded-xl bg-orange-500/10 flex items-center justify-center">
                <svg className="w-5 h-5 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h1 className="text-2xl font-mono font-bold text-white">Investigation Mode</h1>
            </div>
            <p className="text-lg font-medium text-orange-400">Analyze a suspicious target</p>
            <p className="text-sm text-white/50 mt-1">
              Deep dive into suspicious URLs, domains, or indicators with full page capture and analysis
            </p>
          </div>
        </div>
      </div>

      <GlassCard className="p-6 border-orange-500/30" hover={false}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleScan();
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-mono text-white/70 mb-2">
              URL or domain to investigate
            </label>
            <div className="relative">
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="https://suspicious-site.com or suspicious.com"
                disabled={isScanning}
                className={cn(
                  "w-full h-12 px-4 pr-40",
                  "bg-white/[0.03] border border-white/[0.08] rounded-xl",
                  "text-white placeholder-white/30",
                  "font-mono text-sm",
                  "focus:outline-none focus:border-orange-500/40",
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
                  {isScanning ? "Scanning..." : "Start Investigation"}
                </GlassButton>
              </div>
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-mono">
              {error}
            </div>
          )}

          {isScanning && (
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-white/50">
                  {currentJob?.status === "running" ? "Investigating..." : "Starting..."}
                </span>
                <span className="text-orange-400">{Math.round(progress)}%</span>
              </div>
              <div className="h-1.5 bg-white/[0.05] rounded-full overflow-hidden">
                <div
                  className="h-full bg-orange-500/50 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {showConfig && (
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.capture_screenshot}
                    onChange={(e) => setConfig({ ...config, capture_screenshot: e.target.checked })}
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-orange-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Full page capture</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.map_resources}
                    onChange={(e) => setConfig({ ...config, map_resources: e.target.checked })}
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-orange-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Domain tree mapping</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.check_reputation}
                    onChange={(e) => setConfig({ ...config, check_reputation: e.target.checked })}
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-orange-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Reputation check</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.visual_similarity}
                    onChange={(e) => setConfig({ ...config, visual_similarity: e.target.checked })}
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-orange-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Visual similarity</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.cross_reference_darkweb}
                    onChange={(e) => setConfig({ ...config, cross_reference_darkweb: e.target.checked })}
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-orange-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Dark web cross-ref</span>
                </label>
              </div>
            </div>
          )}
        </form>
      </GlassCard>

      {currentJob && currentJob.status === "completed" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {screenshotUrl && (
            <div className="lg:col-span-8">
              <ScreenshotViewer
                screenshotUrl={screenshotUrl}
                onExport={() => {
                  if (screenshotUrl) {
                    const link = document.createElement("a");
                    link.href = screenshotUrl;
                    link.download = `investigation_${currentJob?.id}_screenshot.png`;
                    link.click();
                  }
                }}
              />
            </div>
          )}

          {riskData && (
            <div className="lg:col-span-4">
              <RiskDashboard
                riskScore={riskData.riskScore}
                riskLevel={riskData.riskLevel}
                riskFactors={riskData.riskFactors}
                thirdPartyCount={riskData.thirdPartyCount}
                trackerCount={riskData.trackerCount}
                totalDomains={riskData.totalDomains}
              />
            </div>
          )}

          {domainTree && (
            <div className="lg:col-span-12">
              <DomainTreeView nodes={domainTree.nodes} edges={domainTree.edges} />
            </div>
          )}

          {findings.length > 0 && (
            <div className="lg:col-span-12">
              <InvestigationFindings findings={findings} />
            </div>
          )}

          {harData && (
            <>
              <div className="lg:col-span-6">
                <ResourceWaterfall harData={harData} />
              </div>
              <div className="lg:col-span-6">
                <HARViewer harData={harData} />
              </div>
            </>
          )}

          {currentJob && (
            <div className="lg:col-span-12">
              <ExportPanel jobId={currentJob.id} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
