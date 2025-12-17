"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import Link from "next/link";
import { cn, formatRelativeTime } from "@/lib/utils";
import {
  GlassCard,
  GlassButton,
  GlassInput,
  Badge,
  ExpandableSection,
  CopyButton,
  StatusBadge,
} from "@/components/ui";
import { api, CapabilityFinding, CapabilityJob } from "@/lib/api";
import { ScoreCard } from "@/components/email/ScoreCard";
import type { EmailAuditResult, ComplianceScore } from "@/lib/emailTypes";

interface EmailFinding extends CapabilityFinding {
  category?: "spf" | "dkim" | "dmarc" | "bimi" | "mta_sts" | "bypass" | "compliance" | "other";
}

export default function EmailSecurityPage() {
  const [target, setTarget] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [currentJob, setCurrentJob] = useState<CapabilityJob | null>(null);
  const [findings, setFindings] = useState<EmailFinding[]>([]);
  const [selectedFinding, setSelectedFinding] = useState<EmailFinding | null>(null);
  const [emailData, setEmailData] = useState<EmailAuditResult | null>(null);
  
  // Config state
  const [config, setConfig] = useState({
    check_spf: true,
    check_dkim: true,
    check_dmarc: true,
    check_mx: true,
    check_bimi: true,
    check_mta_sts: true,
    check_subdomains: false,
    run_bypass_tests: false,
  });
  
  // Refs
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isPollingRef = useRef(false);
  
  // Color scheme
  const colors = {
    accent: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    glow: "shadow-[0_0_30px_rgba(245,158,11,0.2)]",
  };
  
  // Calculate stats
  const stats = useMemo(() => {
    const bySeverity = {
      critical: findings.filter((f) => f.severity === "critical").length,
      high: findings.filter((f) => f.severity === "high").length,
      medium: findings.filter((f) => f.severity === "medium").length,
      low: findings.filter((f) => f.severity === "low").length,
      info: findings.filter((f) => f.severity === "info").length,
    };
    
    // Calculate security score (inverse of average risk)
    const avgRisk = findings.length > 0
      ? findings.reduce((sum, f) => sum + f.risk_score, 0) / findings.length
      : 0;
    const securityScore = Math.max(0, 100 - avgRisk);
    
    return {
      total: findings.length,
      bySeverity,
      securityScore,
      criticalCount: bySeverity.critical,
      highCount: bySeverity.high,
    };
  }, [findings]);
  
  // Categorize findings
  const categorizedFindings = useMemo(() => {
    const categories: Record<string, EmailFinding[]> = {
      spf: [],
      dkim: [],
      dmarc: [],
      bimi: [],
      mta_sts: [],
      bypass: [],
      compliance: [],
      other: [],
    };
    
    findings.forEach((finding) => {
      const title = finding.title.toLowerCase();
      if (title.includes("spf")) {
        categories.spf.push(finding);
      } else if (title.includes("dkim")) {
        categories.dkim.push(finding);
      } else if (title.includes("dmarc")) {
        categories.dmarc.push(finding);
      } else if (title.includes("bimi")) {
        categories.bimi.push(finding);
      } else if (title.includes("mta-sts") || title.includes("mta_sts")) {
        categories.mta_sts.push(finding);
      } else if (title.includes("bypass")) {
        categories.bypass.push(finding);
      } else if (title.includes("compliance")) {
        categories.compliance.push(finding);
      } else {
        categories.other.push(finding);
      }
    });
    
    return categories;
  }, [findings]);
  
  // Poll for job status
  const pollJobStatus = useCallback(async (jobId: string) => {
    if (isPollingRef.current) return false;
    
    try {
      isPollingRef.current = true;
      const job = await api.getJobStatus(jobId);
      setCurrentJob(job);
      setProgress(job.progress);
      
      if (job.status === "completed") {
        const apiFindings = await api.getJobFindings(jobId);
        setFindings(apiFindings as EmailFinding[]);
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
    } finally {
      isPollingRef.current = false;
    }
  }, []);
  
  const handleScan = async () => {
    if (!target.trim()) return;
    
    // Cleanup
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    
    setIsScanning(true);
    setProgress(0);
    setError(null);
    setFindings([]);
    setSelectedFinding(null);
    setEmailData(null);
    
    try {
      const job = await api.createCapabilityJob({
        capability: "email_security",
        target: target.trim(),
        config: config,
        priority: "normal",
      });
      
      setCurrentJob(job);
      
      // Poll for completion
      pollIntervalRef.current = setInterval(async () => {
        const done = await pollJobStatus(job.id);
        if (done && pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      }, 3000);
      
      // Timeout after 5 minutes
      timeoutRef.current = setTimeout(() => {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setIsScanning(false);
        setError("Scan timed out");
      }, 300000);
      
    } catch (err) {
      console.error("Scan error:", err);
      setError(err instanceof Error ? err.message : "Failed to start scan");
      setIsScanning(false);
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
  
  const handleExport = async (format: "json" | "csv") => {
    if (!target.trim()) return;
    try {
      await api.exportEmailReport(target.trim(), format);
    } catch (err) {
      console.error("Export error:", err);
      setError("Failed to export report");
    }
  };
  
  // Cleanup
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);
  
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
                <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h1 className="text-2xl font-mono font-bold text-white">Email Security</h1>
            </div>
            <p className={cn("text-lg font-medium", colors.accent)}>Can our email be spoofed?</p>
            <p className="text-sm text-white/50 mt-1">
              Comprehensive email security assessment with SPF, DKIM, DMARC, and advanced checks
            </p>
          </div>
        </div>
        
        {findings.length > 0 && (
          <div className="flex gap-2">
            <GlassButton
              onClick={() => handleExport("csv")}
              variant="secondary"
              size="sm"
            >
              Export CSV
            </GlassButton>
            <GlassButton
              onClick={() => handleExport("json")}
              variant="secondary"
              size="sm"
            >
              Export JSON
            </GlassButton>
          </div>
        )}
      </div>
      
      {/* Scan Input */}
      <GlassCard className={cn("p-6", colors.border)}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleScan();
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-mono text-white/70 mb-2">Domain to check</label>
            <div className="relative">
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="example.com"
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
          
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-mono">
              {error}
            </div>
          )}
          
          {isScanning && (
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-white/50">Scanning...</span>
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
          
          {showConfig && (
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.check_spf}
                    onChange={(e) => setConfig({ ...config, check_spf: e.target.checked })}
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Check SPF</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.check_dkim}
                    onChange={(e) => setConfig({ ...config, check_dkim: e.target.checked })}
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Check DKIM</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.check_dmarc}
                    onChange={(e) => setConfig({ ...config, check_dmarc: e.target.checked })}
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Check DMARC</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.check_mx}
                    onChange={(e) => setConfig({ ...config, check_mx: e.target.checked })}
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Check MX records</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.check_bimi}
                    onChange={(e) => setConfig({ ...config, check_bimi: e.target.checked })}
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Check BIMI</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.check_mta_sts}
                    onChange={(e) => setConfig({ ...config, check_mta_sts: e.target.checked })}
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Check MTA-STS</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.check_subdomains}
                    onChange={(e) => setConfig({ ...config, check_subdomains: e.target.checked })}
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Check subdomains</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.run_bypass_tests}
                    onChange={(e) => setConfig({ ...config, run_bypass_tests: e.target.checked })}
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Bypass tests</span>
                </label>
              </div>
            </div>
          )}
        </form>
      </GlassCard>
      
      {/* Results */}
      {findings.length > 0 && (
        <>
          {/* Dashboard Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <ScoreCard
              score={stats.securityScore}
              title="Security Score"
              subtitle="Overall email security rating"
              size="lg"
              showBreakdown={false}
            />
            <GlassCard className="p-6">
              <h3 className="text-sm font-mono text-white/60 mb-4">Findings Summary</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-white/60">Total</span>
                  <span className="text-white font-mono">{stats.total}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-red-400">Critical</span>
                  <span className="text-white font-mono">{stats.criticalCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-orange-400">High</span>
                  <span className="text-white font-mono">{stats.highCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-amber-400">Medium</span>
                  <span className="text-white font-mono">{stats.bySeverity.medium}</span>
                </div>
              </div>
            </GlassCard>
            <GlassCard className="p-6">
              <h3 className="text-sm font-mono text-white/60 mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <GlassButton
                  onClick={() => {
                    const complianceSection = document.getElementById("compliance-section");
                    complianceSection?.scrollIntoView({ behavior: "smooth" });
                  }}
                  variant="secondary"
                  size="sm"
                  className="w-full"
                >
                  View Compliance
                </GlassButton>
                <GlassButton
                  onClick={() => api.getEmailInfrastructure(target.trim())}
                  variant="secondary"
                  size="sm"
                  className="w-full"
                >
                  Infrastructure Map
                </GlassButton>
              </div>
            </GlassCard>
          </div>
          
          {/* Grid Layout - All Sections */}
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Left Column - Main Content Grid */}
            <div className="lg:col-span-2 space-y-6">
              {/* Overview - All Findings */}
              <GlassCard className="p-6">
                <h2 className="font-mono text-lg font-semibold text-white mb-4">
                  All Findings ({findings.length})
                </h2>
                <div className="space-y-3 max-h-[400px] overflow-y-auto">
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
                          <span className={cn("px-2 py-0.5 text-xs font-mono uppercase rounded", styles.bg, styles.text)}>
                            {finding.severity}
                          </span>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-white truncate">{finding.title}</p>
                            <p className="text-xs text-white/40 mt-1 line-clamp-2">{finding.description}</p>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </GlassCard>

              {/* SPF Analysis */}
              {categorizedFindings.spf.length > 0 && (
                <GlassCard className="p-6">
                  <h2 className="font-mono text-lg font-semibold text-white mb-4">
                    SPF Analysis ({categorizedFindings.spf.length} findings)
                  </h2>
                  <div className="space-y-3 max-h-[300px] overflow-y-auto">
                    {categorizedFindings.spf.map((finding) => (
                      <div key={finding.id} className="p-4 rounded-xl border border-white/10">
                        <div className="flex items-start gap-3">
                          <span className={cn("px-2 py-0.5 text-xs font-mono uppercase rounded", getSeverityStyles(finding.severity).bg, getSeverityStyles(finding.severity).text)}>
                            {finding.severity}
                          </span>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-white">{finding.title}</p>
                            <p className="text-xs text-white/60 mt-1">{finding.description}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              )}

              {/* DKIM Analysis */}
              {categorizedFindings.dkim.length > 0 && (
                <GlassCard className="p-6">
                  <h2 className="font-mono text-lg font-semibold text-white mb-4">
                    DKIM Analysis ({categorizedFindings.dkim.length} findings)
                  </h2>
                  <div className="space-y-3 max-h-[300px] overflow-y-auto">
                    {categorizedFindings.dkim.map((finding) => (
                      <div key={finding.id} className="p-4 rounded-xl border border-white/10">
                        <div className="flex items-start gap-3">
                          <span className={cn("px-2 py-0.5 text-xs font-mono uppercase rounded", getSeverityStyles(finding.severity).bg, getSeverityStyles(finding.severity).text)}>
                            {finding.severity}
                          </span>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-white">{finding.title}</p>
                            <p className="text-xs text-white/60 mt-1">{finding.description}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              )}

              {/* DMARC Analysis */}
              {categorizedFindings.dmarc.length > 0 && (
                <GlassCard className="p-6">
                  <h2 className="font-mono text-lg font-semibold text-white mb-4">
                    DMARC Analysis ({categorizedFindings.dmarc.length} findings)
                  </h2>
                  <div className="space-y-3 max-h-[300px] overflow-y-auto">
                    {categorizedFindings.dmarc.map((finding) => (
                      <div key={finding.id} className="p-4 rounded-xl border border-white/10">
                        <div className="flex items-start gap-3">
                          <span className={cn("px-2 py-0.5 text-xs font-mono uppercase rounded", getSeverityStyles(finding.severity).bg, getSeverityStyles(finding.severity).text)}>
                            {finding.severity}
                          </span>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-white">{finding.title}</p>
                            <p className="text-xs text-white/60 mt-1">{finding.description}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              )}

              {/* Advanced Checks */}
              {([...categorizedFindings.bimi, ...categorizedFindings.mta_sts, ...categorizedFindings.other].length > 0) && (
                <GlassCard className="p-6">
                  <h2 className="font-mono text-lg font-semibold text-white mb-4">Advanced Checks</h2>
                  <div className="space-y-3 max-h-[300px] overflow-y-auto">
                    {[...categorizedFindings.bimi, ...categorizedFindings.mta_sts, ...categorizedFindings.other].map((finding) => (
                      <div key={finding.id} className="p-4 rounded-xl border border-white/10">
                        <div className="flex items-start gap-3">
                          <span className={cn("px-2 py-0.5 text-xs font-mono uppercase rounded", getSeverityStyles(finding.severity).bg, getSeverityStyles(finding.severity).text)}>
                            {finding.severity}
                          </span>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-white">{finding.title}</p>
                            <p className="text-xs text-white/60 mt-1">{finding.description}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              )}

              {/* Bypass Vulnerabilities */}
              {categorizedFindings.bypass.length > 0 && (
                <GlassCard className="p-6 border-red-500/30">
                  <h2 className="font-mono text-lg font-semibold text-white mb-4">
                    Bypass Vulnerabilities ({categorizedFindings.bypass.length} findings)
                  </h2>
                  <div className="space-y-3 max-h-[300px] overflow-y-auto">
                    {categorizedFindings.bypass.map((finding) => (
                      <div key={finding.id} className="p-4 rounded-xl border border-red-500/30 bg-red-500/10">
                        <div className="flex items-start gap-3">
                          <span className={cn("px-2 py-0.5 text-xs font-mono uppercase rounded", getSeverityStyles(finding.severity).bg, getSeverityStyles(finding.severity).text)}>
                            {finding.severity}
                          </span>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-white">{finding.title}</p>
                            <p className="text-xs text-white/60 mt-1">{finding.description}</p>
                            {finding.evidence && finding.evidence.attack_vector && (
                              <div className="mt-2 p-2 rounded bg-black/30">
                                <p className="text-xs text-red-400 font-mono">Attack Vector:</p>
                                <p className="text-xs text-white/70 mt-1">{finding.evidence.attack_vector}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              )}

              {/* Compliance Report */}
              {categorizedFindings.compliance.length > 0 && (
                <GlassCard id="compliance-section" className="p-6">
                  <h2 className="font-mono text-lg font-semibold text-white mb-4">Compliance Report</h2>
                  <div className="space-y-4">
                    {categorizedFindings.compliance.map((finding) => (
                      <div key={finding.id} className="p-4 rounded-xl border border-white/10">
                        <p className="text-sm font-medium text-white">{finding.title}</p>
                        <p className="text-xs text-white/60 mt-1">{finding.description}</p>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              )}
              
              {/* Compliance Info (if no compliance findings yet) */}
              {categorizedFindings.compliance.length === 0 && (
                <GlassCard id="compliance-section" className="p-6">
                  <h2 className="font-mono text-lg font-semibold text-white mb-4">Compliance Report</h2>
                  <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10">
                    <p className="text-sm text-amber-400 font-mono">Compliance scores are calculated during scan</p>
                    <p className="text-xs text-white/60 mt-1">Run a scan to see detailed compliance breakdown</p>
                  </div>
                </GlassCard>
              )}
            </div>
            
            {/* Finding Details Sidebar */}
            <div>
              <GlassCard className="p-6 sticky top-6">
                <h2 className="font-mono text-lg font-semibold text-white mb-4">Details</h2>
                
                {selectedFinding ? (
                  <div className="space-y-4">
                    <div>
                      <span className={cn("px-2 py-0.5 text-xs font-mono uppercase rounded", getSeverityStyles(selectedFinding.severity).bg, getSeverityStyles(selectedFinding.severity).text)}>
                        {selectedFinding.severity}
                      </span>
                    </div>
                    
                    <div>
                      <h3 className="text-sm font-medium text-white">{selectedFinding.title}</h3>
                      <p className="text-sm text-white/60 mt-2">{selectedFinding.description}</p>
                    </div>
                    
                    {selectedFinding.evidence && (
                      <div>
                        <h4 className="text-xs font-mono text-white/50 mb-2">Evidence</h4>
                        <pre className="p-3 rounded-lg bg-black/30 text-xs font-mono text-white/70 overflow-x-auto whitespace-pre-wrap max-h-48 overflow-y-auto">
                          {JSON.stringify(selectedFinding.evidence, null, 2)}
                        </pre>
                      </div>
                    )}
                    
                    {selectedFinding.recommendations && selectedFinding.recommendations.length > 0 && (
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
        </>
      )}
      
      {findings.length === 0 && !isScanning && (
        <GlassCard className="p-12 text-center">
          <div className={cn("w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center", colors.bg)}>
            <svg className="w-8 h-8 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <p className="text-white/50 font-mono">No findings yet</p>
          <p className="text-sm text-white/30 mt-1">Enter a domain and start a scan</p>
        </GlassCard>
      )}
    </div>
  );
}
