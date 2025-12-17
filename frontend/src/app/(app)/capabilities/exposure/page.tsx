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
  RedirectBanner,
} from "@/components/ui";
import { api, CapabilityFinding, CapabilityJob } from "@/lib/api";
import { connectExposureJobWebSocket } from "@/lib/websocket";

// TypeScript interfaces for exposure findings
interface ExposureFinding {
  id: string;
  category: 'file' | 'endpoint' | 'subdomain' | 'config' | 'source_code' | 'admin_panel';
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  description: string;
  url?: string;
  status_code?: number;
  file_type?: string;
  source: 'dorking' | 'subdomain_enum' | 'endpoint_scan' | 'file_detection' | 'source_code_detection' | 'admin_panel_discovery' | 'config_detection';
  evidence: Record<string, any>;
  discovered_at: string;
  risk_score: number;
  affected_assets: string[];
  recommendations: string[];
}

interface DashboardStats {
  total_findings: number;
  by_category: Record<string, number>;
  by_severity: Record<string, number>;
  by_source: Record<string, number>;
  critical_count: number;
  high_count: number;
  average_risk_score: number;
}

// Category icons
const categoryIcons: Record<string, string> = {
  file: "📄",
  endpoint: "🔗",
  subdomain: "🌐",
  config: "⚙️",
  source_code: "💻",
  admin_panel: "🔐",
};

// Source icons
const sourceIcons: Record<string, string> = {
  dorking: "🔍",
  subdomain_enum: "🌐",
  endpoint_scan: "🔗",
  file_detection: "📄",
  source_code_detection: "💻",
  admin_panel_discovery: "🔐",
  config_detection: "⚙️",
};

// Extract exposure findings from API findings
function extractExposureFindings(findings: CapabilityFinding[]): ExposureFinding[] {
  return findings.map((finding) => {
    const evidence = finding.evidence || {};
    const category = evidence.category || 'endpoint';
    const source = evidence.source || 'exposure_discovery';
    
    return {
      id: finding.id,
      category: category as ExposureFinding['category'],
      severity: finding.severity,
      title: finding.title,
      description: finding.description,
      url: evidence.url || evidence.path || finding.affected_assets?.[0],
      status_code: evidence.status_code || evidence.status,
      file_type: evidence.file_type,
      source: source as ExposureFinding['source'],
      evidence: evidence,
      discovered_at: finding.discovered_at,
      risk_score: finding.risk_score,
      affected_assets: finding.affected_assets || [],
      recommendations: finding.recommendations || [],
    };
  });
}

function calculateStats(findings: ExposureFinding[]): DashboardStats {
  const by_category: Record<string, number> = {};
  const by_severity: Record<string, number> = {};
  const by_source: Record<string, number> = {};
  
  let critical_count = 0;
  let high_count = 0;
  let total_risk = 0;
  
  findings.forEach((f) => {
    by_category[f.category] = (by_category[f.category] || 0) + 1;
    by_severity[f.severity] = (by_severity[f.severity] || 0) + 1;
    by_source[f.source] = (by_source[f.source] || 0) + 1;
    
    if (f.severity === 'critical') critical_count++;
    if (f.severity === 'high') high_count++;
    total_risk += f.risk_score;
  });
  
  return {
    total_findings: findings.length,
    by_category,
    by_severity,
    by_source,
    critical_count,
    high_count,
    average_risk_score: findings.length > 0 ? total_risk / findings.length : 0,
  };
}

export default function ExposureDiscoveryPage() {
  const [target, setTarget] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [currentJob, setCurrentJob] = useState<CapabilityJob | null>(null);
  const [findings, setFindings] = useState<CapabilityFinding[]>([]);
  const [selectedFinding, setSelectedFinding] = useState<ExposureFinding | null>(null);
  
  // Filter states
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  
  // Refs for cleanup
  const websocketRef = useRef<WebSocket | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  // Extract and filter findings
  const allExposureFindings = useMemo(() => extractExposureFindings(findings), [findings]);
  
  const filteredFindings = useMemo(() => {
    let filtered = allExposureFindings;
    
    // Category filter
    if (categoryFilter !== "all") {
      filtered = filtered.filter((f) => f.category === categoryFilter);
    }
    
    // Severity filter
    if (severityFilter !== "all") {
      filtered = filtered.filter((f) => f.severity === severityFilter);
    }
    
    // Source filter
    if (sourceFilter !== "all") {
      filtered = filtered.filter((f) => f.source === sourceFilter);
    }
    
    // Search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (f) =>
          f.title.toLowerCase().includes(query) ||
          f.description.toLowerCase().includes(query) ||
          (f.url && f.url.toLowerCase().includes(query)) ||
          f.category.toLowerCase().includes(query)
      );
    }
    
    return filtered;
  }, [allExposureFindings, categoryFilter, severityFilter, sourceFilter, searchQuery]);
  
  const stats = useMemo(() => calculateStats(allExposureFindings), [allExposureFindings]);
  
  // Get unique values for filters
  const uniqueCategories = useMemo(() => {
    const cats = new Set(allExposureFindings.map((f) => f.category));
    return Array.from(cats).sort();
  }, [allExposureFindings]);
  
  const uniqueSources = useMemo(() => {
    const sources = new Set(allExposureFindings.map((f) => f.source));
    return Array.from(sources).sort();
  }, [allExposureFindings]);
  
  // Color scheme
  const colors = {
    accent: "text-cyan-400",
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/30",
    glow: "shadow-[0_0_30px_rgba(6,182,212,0.2)]",
  };
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, []);
  
  const handleScan = useCallback(async () => {
    if (!target.trim()) {
      setError("Please enter a domain to scan");
      return;
    }
    
    setIsScanning(true);
    setError(null);
    setProgress(0);
    setFindings([]);
    setSelectedFinding(null);
    
    try {
      const job = await api.createCapabilityJob({
        capability: "exposure_discovery",
        target: target.trim(),
        priority: "normal",
      });
      
      setCurrentJob(job);
      
      // Connect via WebSocket for real-time streaming
      const ws = connectExposureJobWebSocket(job.id, {
        onFinding: (finding: CapabilityFinding) => {
          console.log("[WebSocket] Received finding:", finding);
          setFindings((prev: CapabilityFinding[]) => {
            const exists = prev.some((f: CapabilityFinding) => f.id === finding.id);
            if (exists) return prev;
            return [...prev, finding];
          });
        },
        onProgress: (progressValue: number, message: string) => {
          setProgress(progressValue);
          setCurrentJob((prev: CapabilityJob | null) => {
            if (prev) {
              return { ...prev, progress: progressValue };
            }
            return prev;
          });
        },
        onComplete: (data: any) => {
          setIsScanning(false);
          setProgress(100);
          setCurrentJob((prev: CapabilityJob | null) => {
            if (prev) {
              return { ...prev, status: "completed", progress: 100 };
            }
            return prev;
          });
          if (websocketRef.current) {
            websocketRef.current.close();
            websocketRef.current = null;
          }
        },
        onError: (errorMsg) => {
          setError(errorMsg);
          setIsScanning(false);
        },
        onConnect: () => {
          console.log("[WebSocket] Connected to exposure discovery job");
        },
        onDisconnect: () => {
          console.log("[WebSocket] Disconnected from exposure discovery job");
        },
      });
      
      websocketRef.current = ws;
      
      // Timeout after 10 minutes
      timeoutRef.current = setTimeout(() => {
        if (websocketRef.current) {
          websocketRef.current.close();
          websocketRef.current = null;
        }
        setIsScanning(false);
        setError("Scan timed out");
      }, 600000);
      
    } catch (err) {
      console.error("Scan error:", err);
      setError(err instanceof Error ? err.message : "Failed to start scan");
      setIsScanning(false);
    }
  }, [target]);
  
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
                <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h1 className="text-2xl font-mono font-bold text-white">Exposure Discovery</h1>
            </div>
            <p className={cn("text-lg font-medium", colors.accent)}>What can attackers find about us online?</p>
            <p className="text-sm text-white/50 mt-1">
              Discover exposed files, endpoints, subdomains, and sensitive data accessible to attackers
            </p>
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
            <label className="block text-sm font-mono text-white/70 mb-2">Target domain</label>
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
                  "focus:outline-none focus:border-cyan-500/40",
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
                <GlassButton type="submit" variant="primary" size="sm" loading={isScanning} disabled={isScanning}>
                  {isScanning ? "Scanning..." : "Start Scan"}
                </GlassButton>
              </div>
            </div>
          </div>
          
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-mono animate-fade-in">
              {error}
            </div>
          )}
          
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
          
          {showConfig && (
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] animate-fade-in">
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-cyan-500"
                    />
                    <span className="text-xs text-white/60 group-hover:text-white/80">Search engine dorking</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-cyan-500"
                    />
                    <span className="text-xs text-white/60 group-hover:text-white/80">Sensitive file detection</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-cyan-500"
                    />
                    <span className="text-xs text-white/60 group-hover:text-white/80">Admin panel discovery</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-cyan-500"
                    />
                    <span className="text-xs text-white/60 group-hover:text-white/80">Source code exposure</span>
                  </label>
                </div>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-cyan-500"
                  />
                  <span className="text-xs text-white/60 group-hover:text-white/80">Include subdomains</span>
                </label>
              </div>
            </div>
          )}
        </form>
      </GlassCard>
      
      {/* Statistics Cards */}
      {findings.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <GlassCard padding="lg">
            <p className="text-xs font-mono text-white/50 mb-1">Total Findings</p>
            <p className="text-3xl font-mono font-bold text-white">{stats.total_findings}</p>
          </GlassCard>
          <GlassCard padding="lg">
            <p className="text-xs font-mono text-white/50 mb-1">Critical</p>
            <p className="text-3xl font-mono font-bold text-red-400">{stats.critical_count}</p>
            <p className="text-xs text-white/40 mt-1">{stats.high_count} high</p>
          </GlassCard>
          <GlassCard padding="lg">
            <p className="text-xs font-mono text-white/50 mb-1">Files</p>
            <p className="text-3xl font-mono font-bold text-white">{stats.by_category.file || 0}</p>
          </GlassCard>
          <GlassCard padding="lg">
            <p className="text-xs font-mono text-white/50 mb-1">Endpoints</p>
            <p className="text-3xl font-mono font-bold text-white">{stats.by_category.endpoint || 0}</p>
          </GlassCard>
          <GlassCard padding="lg">
            <p className="text-xs font-mono text-white/50 mb-1">Avg Risk Score</p>
            <p className="text-3xl font-mono font-bold text-white">{Math.round(stats.average_risk_score)}</p>
          </GlassCard>
        </div>
      )}
      
      {/* Main Content */}
      {findings.length > 0 && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Findings List */}
          <div className="lg:col-span-2 space-y-6">
            {/* Search and Filters */}
            <GlassCard padding="lg">
              <GlassInput
                placeholder="Search findings..."
                value={searchQuery}
                onChange={(e) => setSearchQuery((e.target as HTMLInputElement).value)}
                icon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                }
              />
              
              <div className="flex flex-wrap gap-2 mt-4">
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="px-3 py-1.5 text-xs font-mono bg-white/[0.05] border border-white/[0.1] rounded-lg text-white/70 focus:outline-none focus:border-cyan-500/40"
                >
                  <option value="all">All Categories</option>
                  {uniqueCategories.map((cat) => (
                    <option key={cat} value={cat}>
                      {categoryIcons[cat] || ''} {cat}
                    </option>
                  ))}
                </select>
                
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  className="px-3 py-1.5 text-xs font-mono bg-white/[0.05] border border-white/[0.1] rounded-lg text-white/70 focus:outline-none focus:border-cyan-500/40"
                >
                  <option value="all">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                  <option value="info">Info</option>
                </select>
                
                <select
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  className="px-3 py-1.5 text-xs font-mono bg-white/[0.05] border border-white/[0.1] rounded-lg text-white/70 focus:outline-none focus:border-cyan-500/40"
                >
                  <option value="all">All Sources</option>
                  {uniqueSources.map((src) => (
                    <option key={src} value={src}>
                      {sourceIcons[src] || ''} {src.replace('_', ' ')}
                    </option>
                  ))}
                </select>
                
                <div className="ml-auto text-xs text-white/50 font-mono">
                  {filteredFindings.length} of {allExposureFindings.length} findings
                </div>
              </div>
            </GlassCard>
            
            {/* Findings List */}
            <GlassCard padding="lg">
              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                {filteredFindings.length === 0 ? (
                  <div className="py-12 text-center">
                    <p className="text-white/50 font-mono">No findings match your filters</p>
                  </div>
                ) : (
                  filteredFindings.map((finding) => {
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
                          <span className="text-2xl">{categoryIcons[finding.category] || '📋'}</span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className={cn("px-2 py-0.5 text-xs font-mono uppercase rounded", styles.bg, styles.text)}>
                                {finding.severity}
                              </span>
                              <span className="text-xs text-white/40">{finding.category}</span>
                              <span className="text-xs text-white/30">{sourceIcons[finding.source] || ''} {finding.source.replace('_', ' ')}</span>
                            </div>
                            <p className="text-sm font-medium text-white truncate">{finding.title}</p>
                            <p className="text-xs text-white/40 mt-1 line-clamp-2">{finding.description}</p>
                            {finding.url && (
                              <p className="text-xs text-cyan-400/70 mt-1 truncate">{finding.url}</p>
                            )}
                          </div>
                          <span className="text-xs text-white/30 flex-shrink-0">
                            {formatRelativeTime(new Date(finding.discovered_at))}
                          </span>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            </GlassCard>
          </div>
          
          {/* Detail Panel */}
          <div>
            <GlassCard className="p-6 sticky top-6" hover={false}>
              <h2 className="font-mono text-lg font-semibold text-white mb-4">Details</h2>
              
              {selectedFinding ? (
                <div className="space-y-4 animate-fade-in">
                  {/* Header with icon and severity */}
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{categoryIcons[selectedFinding.category] || '📋'}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={cn(
                            "px-2 py-0.5 text-xs font-mono uppercase rounded",
                            getSeverityStyles(selectedFinding.severity).bg,
                            getSeverityStyles(selectedFinding.severity).text
                          )}
                        >
                          {selectedFinding.severity}
                        </span>
                        {selectedFinding.evidence?.status_code && (
                          <StatusBadge status={selectedFinding.evidence.status_code} />
                        )}
                      </div>
                      <h3 className="text-sm font-medium text-white">{selectedFinding.title}</h3>
                    </div>
                  </div>
                  
                  {/* Description */}
                  <div>
                    <p className="text-sm text-white/60">{selectedFinding.description}</p>
                  </div>
                  
                  {/* Redirect Banner */}
                  {selectedFinding.evidence?.was_redirected && selectedFinding.evidence?.final_url && (
                    <RedirectBanner
                      originalUrl={selectedFinding.url || selectedFinding.evidence.url || ""}
                      finalUrl={selectedFinding.evidence.final_url}
                    />
                  )}
                  
                  {/* URL Section */}
                  {selectedFinding.url && (
                    <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-xs font-mono text-white/50">URL</h4>
                        <CopyButton text={selectedFinding.url} />
                      </div>
                      <a
                        href={selectedFinding.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-cyan-400 hover:text-cyan-300 break-all flex items-center gap-1 group"
                      >
                        <span className="truncate">{selectedFinding.url}</span>
                        <svg
                          className="w-3 h-3 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                          />
                        </svg>
                      </a>
                    </div>
                  )}
                  
                  {/* Evidence Section - Structured Display */}
                  <ExpandableSection title="Evidence" defaultExpanded={true}>
                    <div className="space-y-3">
                      {/* Key Evidence Fields */}
                      <div className="grid grid-cols-2 gap-2">
                        {selectedFinding.evidence?.status_code && (
                          <div className="p-2 rounded bg-white/[0.02] border border-white/[0.05]">
                            <div className="text-xs text-white/40 mb-1">Status</div>
                            <StatusBadge status={selectedFinding.evidence.status_code} />
                          </div>
                        )}
                        {selectedFinding.evidence?.content_type && (
                          <div className="p-2 rounded bg-white/[0.02] border border-white/[0.05]">
                            <div className="text-xs text-white/40 mb-1">Content Type</div>
                            <div className="text-xs text-white/70 font-mono truncate">
                              {selectedFinding.evidence.content_type}
                            </div>
                          </div>
                        )}
                        {selectedFinding.evidence?.server && (
                          <div className="p-2 rounded bg-white/[0.02] border border-white/[0.05]">
                            <div className="text-xs text-white/40 mb-1">Server</div>
                            <div className="text-xs text-white/70 font-mono truncate">
                              {selectedFinding.evidence.server}
                            </div>
                          </div>
                        )}
                        {selectedFinding.evidence?.content_length !== undefined && (
                          <div className="p-2 rounded bg-white/[0.02] border border-white/[0.05]">
                            <div className="text-xs text-white/40 mb-1">Size</div>
                            <div className="text-xs text-white/70 font-mono">
                              {selectedFinding.evidence.content_length.toLocaleString()} bytes
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {/* Additional Evidence Fields */}
                      {Object.entries(selectedFinding.evidence || {})
                        .filter(([key]) => 
                          !['status_code', 'content_type', 'server', 'content_length', 'url', 'final_url', 'was_redirected', 'category', 'source'].includes(key)
                        )
                        .map(([key, value]) => (
                          <div key={key} className="p-2 rounded bg-white/[0.02] border border-white/[0.05]">
                            <div className="text-xs text-white/40 mb-1 capitalize">
                              {key.replace(/_/g, ' ')}
                            </div>
                            <div className="text-xs text-white/70 font-mono break-all">
                              {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                            </div>
                          </div>
                        ))}
                      
                      {/* Raw JSON - Collapsed by default */}
                      <ExpandableSection title="Raw JSON" defaultExpanded={false}>
                        <div className="relative">
                          <div className="absolute top-2 right-2">
                            <CopyButton text={JSON.stringify(selectedFinding.evidence, null, 2)} />
                          </div>
                          <pre className="p-3 rounded-lg bg-black/30 text-xs font-mono text-white/70 overflow-x-auto whitespace-pre-wrap max-h-48 overflow-y-auto">
                            {JSON.stringify(selectedFinding.evidence, null, 2)}
                          </pre>
                        </div>
                      </ExpandableSection>
                    </div>
                  </ExpandableSection>
                  
                  {/* Recommendations */}
                  {selectedFinding.recommendations.length > 0 && (
                    <ExpandableSection title="Recommendations" defaultExpanded={true}>
                      <ul className="space-y-2">
                        {selectedFinding.recommendations.map((rec, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-white/70">
                            <span className={cn("mt-1.5 flex-shrink-0", colors.accent)}>•</span>
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </ExpandableSection>
                  )}
                  
                  {/* Affected Assets */}
                  {selectedFinding.affected_assets && selectedFinding.affected_assets.length > 0 && (
                    <ExpandableSection title="Affected Assets" defaultExpanded={false}>
                      <ul className="space-y-1">
                        {selectedFinding.affected_assets.map((asset, i) => (
                          <li key={i} className="text-xs text-cyan-400/70 break-all">
                            {asset}
                          </li>
                        ))}
                      </ul>
                    </ExpandableSection>
                  )}
                  
                  {/* Risk Score with Visual Indicator */}
                  <div className="pt-3 border-t border-white/[0.05]">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-white/50">Risk Score</span>
                      <span className={cn("text-sm font-mono font-bold", colors.accent)}>
                        {Math.round(selectedFinding.risk_score)}
                      </span>
                    </div>
                    <div className="h-1.5 bg-white/[0.05] rounded-full overflow-hidden">
                      <div
                        className={cn(
                          "h-full rounded-full transition-all duration-300",
                          selectedFinding.risk_score >= 80
                            ? "bg-red-500/50"
                            : selectedFinding.risk_score >= 60
                            ? "bg-orange-500/50"
                            : selectedFinding.risk_score >= 40
                            ? "bg-yellow-500/50"
                            : "bg-blue-500/50"
                        )}
                        style={{ width: `${selectedFinding.risk_score}%` }}
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center">
                  <p className="text-sm text-white/40">Select a finding to view details</p>
                </div>
              )}
            </GlassCard>
          </div>
        </div>
      )}
      
      {/* Empty State */}
      {findings.length === 0 && !isScanning && (
        <GlassCard padding="lg" className="text-center py-12">
          <div className={cn("w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center", colors.bg)}>
            <svg className="w-8 h-8 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <p className="text-white/50 font-mono">No findings yet</p>
          <p className="text-sm text-white/30 mt-1">Enter a domain and start a scan</p>
        </GlassCard>
      )}
    </div>
  );
}
