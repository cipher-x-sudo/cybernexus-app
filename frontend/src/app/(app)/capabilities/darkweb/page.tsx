"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import Link from "next/link";
import { cn, formatRelativeTime, formatDate, formatTime } from "@/lib/utils";
import { GlassCard, GlassButton, GlassInput, Badge } from "@/components/ui";
import { api, CapabilityFinding, CapabilityJob } from "@/lib/api";
import { connectDarkwebJobWebSocket } from "@/lib/websocket";

// TypeScript interfaces for parsed data structures
interface SiteData {
  site_id: string;
  onion_url: string;
  title: string;
  category: string;
  threat_level: string;
  risk_score: number;
  is_online: boolean;
  page_count: number;
  keywords_matched: string[];
  entities_count: number;
  linked_sites_count: number;
  first_seen: string;
  last_seen: string;
  language: string;
  source_finding_id: string;
}

interface EntityData {
  type: string;
  value: string;
  context: string;
  source_url: string;
  confidence: number;
  discovered_at: string;
  source_finding_id: string;
  severity: string;
}

interface MentionData {
  keyword: string;
  site_url: string;
  site_title: string;
  context: string;
  threat_level: string;
  discovered_at: string;
  source_finding_id: string;
  severity: string;
}

interface DashboardStats {
  total_sites: number;
  total_mentions: number;
  total_entities: number;
  critical_threats: number;
  high_threats: number;
  average_risk_score: number;
  online_sites: number;
  entity_types: Record<string, number>;
}

// Data extraction helper functions
function extractSitesFromFindings(findings: CapabilityFinding[]): SiteData[] {
  const sitesMap = new Map<string, SiteData>();
  
  findings.forEach((finding) => {
    if (finding.evidence?.site) {
      const site = finding.evidence.site;
      const siteId = site.site_id || site.onion_url;
      
      if (!sitesMap.has(siteId)) {
        sitesMap.set(siteId, {
          site_id: siteId,
          onion_url: site.onion_url || "",
          title: site.title || "Unknown Site",
          category: site.category || "unknown",
          threat_level: site.threat_level || finding.severity,
          risk_score: site.risk_score || finding.risk_score || 0,
          is_online: site.is_online ?? true,
          page_count: site.page_count || 1,
          keywords_matched: site.keywords_matched || [],
          entities_count: site.entities_count || 0,
          linked_sites_count: site.linked_sites_count || 0,
          first_seen: site.first_seen || finding.discovered_at,
          last_seen: site.last_seen || finding.discovered_at,
          language: site.language || "unknown",
          source_finding_id: finding.id,
        });
      }
    }
  });
  
  return Array.from(sitesMap.values());
}

function extractEntitiesFromFindings(findings: CapabilityFinding[]): EntityData[] {
  const entities: EntityData[] = [];
  
  findings.forEach((finding) => {
    if (finding.evidence?.entity) {
      const entity = finding.evidence.entity;
      entities.push({
        type: entity.type || "unknown",
        value: entity.value || "",
        context: entity.context || "",
        source_url: entity.source_url || "",
        confidence: entity.confidence || 1.0,
        discovered_at: entity.discovered_at || finding.discovered_at,
        source_finding_id: finding.id,
        severity: finding.severity,
      });
    }
  });
  
  return entities;
}

function extractMentionsFromFindings(findings: CapabilityFinding[]): MentionData[] {
  const mentions: MentionData[] = [];
  
  findings.forEach((finding) => {
    // Brand mentions are findings with "Brand mention" in title and have site evidence
    if (finding.title.toLowerCase().includes("brand mention") && finding.evidence?.site) {
      const site = finding.evidence.site;
      mentions.push({
        keyword: finding.affected_assets?.[0] || "unknown",
        site_url: site.onion_url || "",
        site_title: site.title || "Unknown Site",
        context: finding.description || "",
        threat_level: site.threat_level || finding.severity,
        discovered_at: finding.discovered_at,
        source_finding_id: finding.id,
        severity: finding.severity,
      });
    }
  });
  
  return mentions;
}

function calculateStats(
  sites: SiteData[],
  entities: EntityData[],
  mentions: MentionData[]
): DashboardStats {
  const criticalThreats = sites.filter((s) => s.threat_level === "critical" || s.risk_score >= 80).length +
    mentions.filter((m) => m.severity === "critical").length;
  
  const highThreats = sites.filter((s) => s.threat_level === "high" || (s.risk_score >= 60 && s.risk_score < 80)).length +
    mentions.filter((m) => m.severity === "high").length;
  
  const riskScores = sites.map((s) => s.risk_score).filter((s) => s > 0);
  const averageRiskScore = riskScores.length > 0
    ? riskScores.reduce((a, b) => a + b, 0) / riskScores.length
    : 0;
  
  const entityTypes: Record<string, number> = {};
  entities.forEach((e) => {
    entityTypes[e.type] = (entityTypes[e.type] || 0) + 1;
  });
  
  return {
    total_sites: sites.length,
    total_mentions: mentions.length,
    total_entities: entities.length,
    critical_threats: criticalThreats,
    high_threats: highThreats,
    average_risk_score: averageRiskScore,
    online_sites: sites.filter((s) => s.is_online).length,
    entity_types: entityTypes,
  };
}

// Category icons
const categoryIcons: Record<string, string> = {
  marketplace: "🏪",
  forum: "💬",
  leak_site: "📝",
  ransomware: "🔒",
  carding: "💳",
  drugs: "💊",
  hacking: "⚔️",
  fraud: "🎭",
  crypto: "₿",
  unknown: "🌐",
};

// Entity type icons
const entityTypeIcons: Record<string, string> = {
  email: "📧",
  bitcoin: "₿",
  monero: "🪙",
  ethereum: "Ξ",
  credit_card: "💳",
  ssh_fingerprint: "🔐",
  phone: "📞",
  ip_address: "🌐",
  pgp_key: "🔑",
  onion_v2: "🧅",
  onion_v3: "🧅",
  unknown: "📋",
};

export default function DarkWebPage() {
  const [target, setTarget] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [currentJob, setCurrentJob] = useState<CapabilityJob | null>(null);
  const [findings, setFindings] = useState<CapabilityFinding[]>([]);
  const [selectedItem, setSelectedItem] = useState<{
    type: "site" | "entity" | "mention";
    data: SiteData | EntityData | MentionData;
  } | null>(null);
  
  // Filter states
  const [searchQuery, setSearchQuery] = useState("");
  const [siteCategoryFilter, setSiteCategoryFilter] = useState<string>("all");
  const [siteThreatFilter, setSiteThreatFilter] = useState<string>("all");
  const [entityTypeFilter, setEntityTypeFilter] = useState<string>("all");
  const [mentionKeywordFilter, setMentionKeywordFilter] = useState<string>("all");
  
  // Refs for cleanup
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  
  // Extract data from findings
  const allSites = useMemo(() => extractSitesFromFindings(findings), [findings]);
  const allEntities = useMemo(() => extractEntitiesFromFindings(findings), [findings]);
  const allMentions = useMemo(() => extractMentionsFromFindings(findings), [findings]);
  
  // Filtered data
  const sites = useMemo(() => {
    let filtered = allSites;
    
    // Category filter
    if (siteCategoryFilter !== "all") {
      filtered = filtered.filter((s: SiteData) => s.category === siteCategoryFilter);
    }
    
    // Threat level filter
    if (siteThreatFilter !== "all") {
      filtered = filtered.filter((s: SiteData) => s.threat_level === siteThreatFilter);
    }
    
    // Search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (s: SiteData) =>
          s.title.toLowerCase().includes(query) ||
          s.onion_url.toLowerCase().includes(query) ||
          s.keywords_matched.some((kw: string) => kw.toLowerCase().includes(query))
      );
    }
    
    return filtered;
  }, [allSites, siteCategoryFilter, siteThreatFilter, searchQuery]);
  
  const entities = useMemo(() => {
    let filtered = allEntities;
    
    // Type filter
    if (entityTypeFilter !== "all") {
      filtered = filtered.filter((e: EntityData) => e.type === entityTypeFilter);
    }
    
    // Search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (e: EntityData) =>
          e.value.toLowerCase().includes(query) ||
          e.type.toLowerCase().includes(query) ||
          (e.context && e.context.toLowerCase().includes(query))
      );
    }
    
    return filtered;
  }, [allEntities, entityTypeFilter, searchQuery]);
  
  const mentions = useMemo(() => {
    let filtered = allMentions;
    
    // Keyword filter
    if (mentionKeywordFilter !== "all") {
      filtered = filtered.filter((m: MentionData) => m.keyword === mentionKeywordFilter);
    }
    
    // Search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (m: MentionData) =>
          m.keyword.toLowerCase().includes(query) ||
          m.site_title.toLowerCase().includes(query) ||
          (m.context && m.context.toLowerCase().includes(query))
      );
    }
    
    return filtered;
  }, [allMentions, mentionKeywordFilter, searchQuery]);
  
  const stats = useMemo(() => calculateStats(allSites, allEntities, allMentions), [allSites, allEntities, allMentions]);
  
  // Get unique values for filters
  const uniqueCategories = useMemo(() => {
    const cats = new Set(allSites.map((s: SiteData) => s.category));
    return Array.from(cats).sort();
  }, [allSites]);
  
  const uniqueEntityTypes = useMemo(() => {
    const types = new Set(allEntities.map((e: EntityData) => e.type));
    return Array.from(types).sort();
  }, [allEntities]);
  
  const uniqueKeywords = useMemo(() => {
    const keywords = new Set(allMentions.map((m: MentionData) => m.keyword));
    return Array.from(keywords).sort();
  }, [allMentions]);
  
  // Color scheme
  const colors = {
    accent: "text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/30",
    glow: "shadow-[0_0_30px_rgba(168,85,247,0.2)]",
  };
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
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
      setError("Please enter keywords to monitor");
      return;
    }
    
    setIsScanning(true);
    setError(null);
    setProgress(0);
    setFindings([]);
    setSelectedItem(null);
    
    try {
      const job = await api.createCapabilityJob({
        capability: "dark_web_intelligence",
        target: target.trim(),
        priority: "normal",
      });
      
      setCurrentJob(job);
      
      // Connect via WebSocket for real-time streaming
      const ws = connectDarkwebJobWebSocket(job.id, {
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
          console.log("[WebSocket] Connected to darkweb job");
        },
        onDisconnect: () => {
          console.log("[WebSocket] Disconnected from darkweb job");
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
                <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h1 className="text-2xl font-mono font-bold text-white">Dark Web Intelligence</h1>
            </div>
            <p className={cn("text-lg font-medium", colors.accent)}>Are we mentioned on the dark web?</p>
            <p className="text-sm text-white/50 mt-1">
              Monitor .onion sites for brand mentions, credential leaks, and threat actor discussions
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
            <label className="block text-sm font-mono text-white/70 mb-2">Keywords to monitor</label>
            <div className="relative">
              <input
                type="text"
                value={target}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTarget(e.target.value)}
                placeholder="company-name, @domain.com, brand-name"
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
                      className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-purple-500"
                    />
                    <span className="text-xs text-white/60 group-hover:text-white/80">Credential leaks</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-purple-500"
                    />
                    <span className="text-xs text-white/60 group-hover:text-white/80">Brand mentions</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-purple-500"
                    />
                    <span className="text-xs text-white/60 group-hover:text-white/80">Impersonation sites</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-purple-500"
                    />
                    <span className="text-xs text-white/60 group-hover:text-white/80">Ransomware mentions</span>
                  </label>
                </div>
                <div>
                  <label className="block text-xs text-white/50 mb-1">Crawl depth</label>
                  <select className="w-full h-9 px-3 bg-white/[0.05] border border-white/[0.1] rounded-lg text-sm text-white/80">
                    <option value="1">Shallow (faster)</option>
                    <option value="2">Normal</option>
                    <option value="3">Deep (slower)</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </form>
      </GlassCard>
      
      {/* Statistics Cards */}
      {findings.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <GlassCard padding="lg">
            <p className="text-xs font-mono text-white/50 mb-1">Sites Discovered</p>
            <p className="text-3xl font-mono font-bold text-white">{stats.total_sites}</p>
            <p className="text-xs text-white/40 mt-1">{stats.online_sites} online</p>
          </GlassCard>
          <GlassCard padding="lg">
            <p className="text-xs font-mono text-white/50 mb-1">Brand Mentions</p>
            <p className="text-3xl font-mono font-bold text-white">{stats.total_mentions}</p>
          </GlassCard>
          <GlassCard padding="lg">
            <p className="text-xs font-mono text-white/50 mb-1">Entities Extracted</p>
            <p className="text-3xl font-mono font-bold text-white">{stats.total_entities}</p>
          </GlassCard>
          <GlassCard padding="lg">
            <p className="text-xs font-mono text-white/50 mb-1">Critical Threats</p>
            <p className="text-3xl font-mono font-bold text-red-400">{stats.critical_threats}</p>
            <p className="text-xs text-white/40 mt-1">{stats.high_threats} high</p>
          </GlassCard>
          <GlassCard padding="lg">
            <p className="text-xs font-mono text-white/50 mb-1">Avg Risk Score</p>
            <p className="text-3xl font-mono font-bold text-white">{Math.round(stats.average_risk_score)}</p>
          </GlassCard>
        </div>
      )}
      
      {/* Dashboard Sections */}
      {findings.length > 0 && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content - Sites and Mentions */}
          <div className="lg:col-span-2 space-y-6">
            {/* Search and Filters */}
            <GlassCard padding="lg">
              <GlassInput
                placeholder="Search across all results..."
                value={searchQuery}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
                icon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                }
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="mt-2 text-xs text-purple-400 hover:text-purple-300 font-mono"
                >
                  Clear search
                </button>
              )}
            </GlassCard>
            
            {/* Sites Discovered */}
            <GlassCard padding="lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-mono text-lg font-semibold text-white">
                  Sites Discovered ({sites.length})
                </h2>
              </div>
              
              {/* Site Filters */}
              <div className="flex flex-wrap gap-2 mb-4">
                <select
                  value={siteCategoryFilter}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSiteCategoryFilter(e.target.value)}
                  className="px-3 py-1.5 text-xs rounded-lg bg-white/[0.05] border border-white/[0.1] text-white/80 font-mono"
                >
                  <option value="all">All Categories</option>
                  {uniqueCategories.map((cat: string) => (
                    <option key={cat} value={cat}>
                      {cat.charAt(0).toUpperCase() + cat.slice(1).replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
                <select
                  value={siteThreatFilter}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSiteThreatFilter(e.target.value)}
                  className="px-3 py-1.5 text-xs rounded-lg bg-white/[0.05] border border-white/[0.1] text-white/80 font-mono"
                >
                  <option value="all">All Threat Levels</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                  <option value="info">Info</option>
                </select>
              </div>
              
              {sites.length === 0 ? (
                <div className="py-8 text-center text-white/50">
                  <p className="font-mono text-sm">No sites discovered yet</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                  {sites.map((site: SiteData) => {
                    const severityStyles = getSeverityStyles(site.threat_level);
                    return (
                      <button
                        key={site.site_id}
                        onClick={() => setSelectedItem({ type: "site", data: site })}
                        className={cn(
                          "w-full p-4 rounded-xl border text-left transition-all hover:translate-x-1",
                          selectedItem?.type === "site" && selectedItem.data === site
                            ? colors.glow
                            : "",
                          severityStyles.bg,
                          severityStyles.border
                        )}
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-lg bg-white/[0.05] flex items-center justify-center text-xl flex-shrink-0">
                            {categoryIcons[site.category] || categoryIcons.unknown}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant={site.threat_level as any} size="sm">
                                {site.threat_level}
                              </Badge>
                              {site.is_online && (
                                <span className="w-2 h-2 rounded-full bg-green-400" title="Online" />
                              )}
                              <span className="text-xs text-white/30 ml-auto">
                                {formatRelativeTime(site.last_seen)}
                              </span>
                            </div>
                            <p className="font-mono text-sm text-white mb-1 truncate">{site.title}</p>
                            <code className="text-xs text-purple-400 font-mono block truncate mb-2">
                              {site.onion_url}
                            </code>
                            <div className="flex flex-wrap gap-2 text-xs">
                              <span className="text-white/40">Risk: {Math.round(site.risk_score)}</span>
                              {site.page_count > 0 && (
                                <span className="text-white/40">• {site.page_count} pages</span>
                              )}
                              {site.entities_count > 0 && (
                                <span className="text-white/40">• {site.entities_count} entities</span>
                              )}
                              {site.keywords_matched.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                              {site.keywords_matched.slice(0, 3).map((kw: string) => (
                                <span
                                  key={kw}
                                  className="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 text-[10px] font-mono"
                                >
                                  {kw}
                                </span>
                              ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </GlassCard>
            
            {/* Brand Mentions */}
            <GlassCard padding="lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-mono text-lg font-semibold text-white">
                  Brand Mentions ({mentions.length})
                </h2>
              </div>
              
              {/* Mention Filters */}
              {uniqueKeywords.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  <select
                    value={mentionKeywordFilter}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setMentionKeywordFilter(e.target.value)}
                    className="px-3 py-1.5 text-xs rounded-lg bg-white/[0.05] border border-white/[0.1] text-white/80 font-mono"
                  >
                    <option value="all">All Keywords</option>
                    {uniqueKeywords.map((kw: string) => (
                      <option key={kw} value={kw}>
                        {kw}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              
              {mentions.length === 0 ? (
                <div className="py-8 text-center text-white/50">
                  <p className="font-mono text-sm">No brand mentions found yet</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                  {mentions.map((mention: MentionData, idx: number) => {
                    const severityStyles = getSeverityStyles(mention.severity);
                    return (
                      <button
                        key={`${mention.source_finding_id}-${idx}`}
                        onClick={() => setSelectedItem({ type: "mention", data: mention })}
                        className={cn(
                          "w-full p-4 rounded-xl border text-left transition-all hover:translate-x-1",
                          selectedItem?.type === "mention" && selectedItem.data === mention
                            ? colors.glow
                            : "",
                          severityStyles.bg,
                          severityStyles.border
                        )}
                      >
                        <div className="flex items-start gap-3">
                          <Badge variant={mention.severity as any} size="sm">
                            {mention.severity}
                          </Badge>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-mono text-sm text-purple-300">{mention.keyword}</span>
                              <span className="text-xs text-white/30 ml-auto">
                                {formatRelativeTime(mention.discovered_at)}
                              </span>
                            </div>
                            <p className="text-sm text-white/70 mb-1 truncate">{mention.site_title}</p>
                            <code className="text-xs text-purple-400 font-mono block truncate">
                              {mention.site_url}
                            </code>
                            {mention.context && (
                              <p className="text-xs text-white/50 mt-2 line-clamp-2">{mention.context}</p>
                            )}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </GlassCard>
            
            {/* Extracted Entities */}
            <GlassCard padding="lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-mono text-lg font-semibold text-white">
                  Extracted Entities ({entities.length})
                </h2>
              </div>
              
              {/* Entity Filters */}
              {uniqueEntityTypes.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  <select
                    value={entityTypeFilter}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setEntityTypeFilter(e.target.value)}
                    className="px-3 py-1.5 text-xs rounded-lg bg-white/[0.05] border border-white/[0.1] text-white/80 font-mono"
                  >
                    <option value="all">All Entity Types</option>
                    {uniqueEntityTypes.map((type: string) => (
                      <option key={type} value={type}>
                        {type.charAt(0).toUpperCase() + type.slice(1).replace(/_/g, " ")}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              
              {entities.length === 0 ? (
                <div className="py-8 text-center text-white/50">
                  <p className="font-mono text-sm">No entities extracted yet</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                  {entities.map((entity: EntityData, idx: number) => {
                    const severityStyles = getSeverityStyles(entity.severity);
                    // Mask sensitive values
                    const displayValue =
                      entity.type === "credit_card"
                        ? `****${entity.value.slice(-4)}`
                        : entity.type === "email"
                        ? entity.value
                        : entity.value.length > 30
                        ? `${entity.value.slice(0, 30)}...`
                        : entity.value;
                    
                    return (
                      <button
                        key={`${entity.source_finding_id}-${idx}`}
                        onClick={() => setSelectedItem({ type: "entity", data: entity })}
                        className={cn(
                          "w-full p-4 rounded-xl border text-left transition-all hover:translate-x-1",
                          selectedItem?.type === "entity" && selectedItem.data === entity
                            ? colors.glow
                            : "",
                          severityStyles.bg,
                          severityStyles.border
                        )}
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-lg bg-white/[0.05] flex items-center justify-center text-xl flex-shrink-0">
                            {entityTypeIcons[entity.type] || entityTypeIcons.unknown}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant={entity.severity as any} size="sm">
                                {entity.type}
                              </Badge>
                              {entity.confidence < 1.0 && (
                                <span className="text-xs text-white/40">
                                  {Math.round(entity.confidence * 100)}% confidence
                                </span>
                              )}
                              <span className="text-xs text-white/30 ml-auto">
                                {formatRelativeTime(entity.discovered_at)}
                              </span>
                            </div>
                            <code className="text-sm text-white font-mono block truncate mb-2">
                              {displayValue}
                            </code>
                            {entity.context && (
                              <p className="text-xs text-white/50 line-clamp-2">{entity.context}</p>
                            )}
                            {entity.source_url && (
                              <code className="text-xs text-purple-400 font-mono block truncate mt-1">
                                {entity.source_url}
                              </code>
                            )}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </GlassCard>
          </div>
          
          {/* Sidebar - Details */}
          <div>
            <GlassCard className="p-6 sticky top-6" hover={false}>
              <h2 className="font-mono text-lg font-semibold text-white mb-4">Details</h2>
              
              {selectedItem ? (
                <div className="space-y-4 animate-fade-in">
                  {selectedItem.type === "site" && (
                    <>
                      <div>
                        <Badge variant={(selectedItem.data as SiteData).threat_level as any} size="md">
                          {(selectedItem.data as SiteData).threat_level}
                        </Badge>
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-white mb-1">{(selectedItem.data as SiteData).title}</h3>
                        <code className="text-xs text-purple-400 font-mono break-all block">
                          {(selectedItem.data as SiteData).onion_url}
                        </code>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-xs text-white/50 mb-1">Category</p>
                          <p className="text-white capitalize">{(selectedItem.data as SiteData).category}</p>
                        </div>
                        <div>
                          <p className="text-xs text-white/50 mb-1">Risk Score</p>
                          <p className="text-white">{Math.round((selectedItem.data as SiteData).risk_score)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-white/50 mb-1">Status</p>
                          <p className="text-white">
                            {(selectedItem.data as SiteData).is_online ? "Online" : "Offline"}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-white/50 mb-1">Pages</p>
                          <p className="text-white">{(selectedItem.data as SiteData).page_count}</p>
                        </div>
                        <div>
                          <p className="text-xs text-white/50 mb-1">First Seen</p>
                          <p className="text-white text-xs">
                            {formatDate((selectedItem.data as SiteData).first_seen)}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-white/50 mb-1">Last Seen</p>
                          <p className="text-white text-xs">
                            {formatDate((selectedItem.data as SiteData).last_seen)}
                          </p>
                        </div>
                      </div>
                      {(selectedItem.data as SiteData).keywords_matched.length > 0 && (
                        <div>
                          <p className="text-xs text-white/50 mb-2">Keywords Matched</p>
                          <div className="flex flex-wrap gap-1.5">
                          {(selectedItem.data as SiteData).keywords_matched.map((kw: string) => (
                            <span
                              key={kw}
                              className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 text-xs font-mono"
                            >
                              {kw}
                            </span>
                          ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                  
                  {selectedItem.type === "entity" && (
                    <>
                      <div>
                        <Badge variant={(selectedItem.data as EntityData).severity as any} size="md">
                          {(selectedItem.data as EntityData).type}
                        </Badge>
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-white mb-1">Entity Value</h3>
                        <code className="text-xs text-white font-mono break-all block p-2 rounded bg-white/[0.05]">
                          {(selectedItem.data as EntityData).value}
                        </code>
                      </div>
                      {(selectedItem.data as EntityData).context && (
                        <div>
                          <p className="text-xs text-white/50 mb-1">Context</p>
                          <p className="text-sm text-white/70 whitespace-pre-wrap">
                            {(selectedItem.data as EntityData).context}
                          </p>
                        </div>
                      )}
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-xs text-white/50 mb-1">Confidence</p>
                          <p className="text-white">{Math.round((selectedItem.data as EntityData).confidence * 100)}%</p>
                        </div>
                        <div>
                          <p className="text-xs text-white/50 mb-1">Discovered</p>
                          <p className="text-white text-xs">
                            {formatDate((selectedItem.data as EntityData).discovered_at)}
                          </p>
                        </div>
                      </div>
                      {(selectedItem.data as EntityData).source_url && (
                        <div>
                          <p className="text-xs text-white/50 mb-1">Source URL</p>
                          <code className="text-xs text-purple-400 font-mono break-all block">
                            {(selectedItem.data as EntityData).source_url}
                          </code>
                        </div>
                      )}
                    </>
                  )}
                  
                  {selectedItem.type === "mention" && (
                    <>
                      <div>
                        <Badge variant={(selectedItem.data as MentionData).severity as any} size="md">
                          {(selectedItem.data as MentionData).severity}
                        </Badge>
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-white mb-1">Keyword</h3>
                        <p className="text-purple-300 font-mono">{(selectedItem.data as MentionData).keyword}</p>
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-white mb-1">Source Site</h3>
                        <p className="text-sm text-white/70 mb-1">{(selectedItem.data as MentionData).site_title}</p>
                        <code className="text-xs text-purple-400 font-mono break-all block">
                          {(selectedItem.data as MentionData).site_url}
                        </code>
                      </div>
                      {(selectedItem.data as MentionData).context && (
                        <div>
                          <p className="text-xs text-white/50 mb-1">Context</p>
                          <p className="text-sm text-white/70 whitespace-pre-wrap">
                            {(selectedItem.data as MentionData).context}
                          </p>
                        </div>
                      )}
                      <div>
                        <p className="text-xs text-white/50 mb-1">Discovered</p>
                        <p className="text-white text-xs">
                          {formatDate((selectedItem.data as MentionData).discovered_at)}
                        </p>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <div className="py-8 text-center">
                  <p className="text-sm text-white/40">Select an item to view details</p>
                </div>
              )}
            </GlassCard>
          </div>
        </div>
      )}
      
      {/* Empty State */}
      {findings.length === 0 && !isScanning && (
        <GlassCard className="p-12" hover={false}>
          <div className="text-center">
            <div className={cn("w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center", colors.bg)}>
              <svg className="w-8 h-8 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-white/50 font-mono mb-1">No findings yet</p>
            <p className="text-sm text-white/30">Enter keywords and start a scan to monitor the dark web</p>
          </div>
        </GlassCard>
      )}
    </div>
  );
}
