"use client";

import { useState, useEffect } from "react";
import { GlassCard, GlassButton, GlassInput, Badge } from "@/components/ui";
import { cn, formatRelativeTime } from "@/lib/utils";

interface Mention {
  id: string;
  title: string;
  content: string;
  source: "forum" | "marketplace" | "paste_site" | "telegram" | "discord" | "tor_site" | "irc";
  severity: "critical" | "high" | "medium" | "low";
  keywords: string[];
  url: string;
  timestamp: Date;
  author?: string;
}

// Generate mentions only on client to avoid hydration mismatch
function generateMockMentions(): Mention[] {
  const now = Date.now();
  return [
    {
      id: "1",
      title: "Company.com database for sale",
      content: "Fresh dump from company.com. 500k records including emails, passwords (hashed), personal info. Contact via PM for samples.",
      source: "marketplace",
      severity: "critical",
      keywords: ["company.com", "database", "dump"],
      url: "http://dark...onion/listing/12345",
      timestamp: new Date(now - 30 * 60000),
      author: "DataBroker99",
    },
    {
      id: "2",
      title: "Looking for company.com access",
      content: "Will pay $5k for valid VPN credentials or RDP access to company.com infrastructure. Must be recent and working.",
      source: "forum",
      severity: "high",
      keywords: ["company.com", "access", "VPN"],
      url: "http://forum...onion/thread/78901",
      timestamp: new Date(now - 2 * 60 * 60000),
      author: "AccessSeeker",
    },
    {
      id: "3",
      title: "company.com employee list",
      content: "List of 200+ employees with positions and emails scraped from LinkedIn",
      source: "paste_site",
      severity: "medium",
      keywords: ["company.com", "employees", "LinkedIn"],
      url: "https://paste.../abc123",
      timestamp: new Date(now - 12 * 60 * 60000),
    },
    {
      id: "4",
      title: "Leaked API keys discussion",
      content: "Found some company.com API keys on GitHub. Testing if they work.",
      source: "telegram",
      severity: "high",
      keywords: ["company.com", "API", "GitHub"],
      url: "t.me/leak_chat/...",
      timestamp: new Date(now - 24 * 60 * 60000),
      author: "anon_researcher",
    },
    {
      id: "5",
      title: "Company infrastructure mapping",
      content: "Sharing my recon results for company.com. Found 15 subdomains, 3 with potential vulns.",
      source: "discord",
      severity: "medium",
      keywords: ["company.com", "recon", "subdomain"],
      url: "discord.gg/...",
      timestamp: new Date(now - 48 * 60 * 60000),
      author: "ReconMaster",
    },
  ];
}

const sourceIcons = {
  forum: "💬",
  marketplace: "🏪",
  paste_site: "📝",
  telegram: "✈️",
  discord: "🎮",
  tor_site: "🧅",
  irc: "📡",
};

const sourceLabels = {
  forum: "Forum",
  marketplace: "Marketplace",
  paste_site: "Paste Site",
  telegram: "Telegram",
  discord: "Discord",
  tor_site: "Tor Site",
  irc: "IRC",
};

export default function DarkWebPage() {
  const [mentions, setMentions] = useState<Mention[]>([]);
  const [selectedMention, setSelectedMention] = useState<Mention | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sourceFilter, setSourceFilter] = useState<string>("all");

  useEffect(() => {
    setMentions(generateMockMentions());
  }, []);

  const filteredMentions = mentions.filter((mention) => {
    if (sourceFilter !== "all" && mention.source !== sourceFilter) return false;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        mention.title.toLowerCase().includes(query) ||
        mention.content.toLowerCase().includes(query) ||
        mention.keywords.some((k) => k.toLowerCase().includes(query))
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-mono font-bold text-white">Dark Web Monitoring</h1>
          <p className="text-sm text-white/50">
            Track mentions of your organization across dark web sources
          </p>
        </div>

        <GlassButton variant="primary" size="sm">
          <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Add Keyword Alert
        </GlassButton>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total Mentions", value: mentions.length },
          { label: "Critical", value: mentions.filter((m) => m.severity === "critical").length },
          { label: "This Week", value: mentions.length }, // All mock data is within a week
          { label: "Sources", value: new Set(mentions.map((m) => m.source)).size },
        ].map((stat) => (
          <GlassCard key={stat.label} padding="lg">
            <p className="text-sm font-mono text-white/50 mb-1">{stat.label}</p>
            <p className="text-3xl font-mono font-bold text-white">{stat.value}</p>
          </GlassCard>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main feed */}
        <div className="lg:col-span-2">
          <GlassCard padding="none">
            {/* Filters */}
            <div className="p-4 border-b border-white/[0.05]">
              <GlassInput
                placeholder="Search mentions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                icon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                }
              />
              <div className="flex flex-wrap gap-2 mt-3">
                <button
                  onClick={() => setSourceFilter("all")}
                  className={cn(
                    "px-3 py-1.5 rounded-lg font-mono text-xs transition-all",
                    sourceFilter === "all"
                      ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                      : "bg-white/[0.03] text-white/60 border border-white/[0.08]"
                  )}
                >
                  All Sources
                </button>
                {Object.entries(sourceLabels).map(([key, label]) => (
                  <button
                    key={key}
                    onClick={() => setSourceFilter(key)}
                    className={cn(
                      "px-3 py-1.5 rounded-lg font-mono text-xs transition-all flex items-center gap-1",
                      sourceFilter === key
                        ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                        : "bg-white/[0.03] text-white/60 border border-white/[0.08]"
                    )}
                  >
                    <span>{sourceIcons[key as keyof typeof sourceIcons]}</span>
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Feed items */}
            <div className="divide-y divide-white/[0.03]">
              {filteredMentions.map((mention) => (
                <div
                  key={mention.id}
                  onClick={() => setSelectedMention(mention)}
                  className={cn(
                    "p-4 cursor-pointer transition-colors",
                    selectedMention?.id === mention.id
                      ? "bg-amber-500/10"
                      : "hover:bg-white/[0.02]"
                  )}
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-white/[0.05] flex items-center justify-center text-xl">
                      {sourceIcons[mention.source]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant={mention.severity} size="sm">
                          {mention.severity}
                        </Badge>
                        <span className="text-xs text-white/30">
                          {sourceLabels[mention.source]}
                        </span>
                        <span className="text-xs text-white/30 ml-auto">
                          {formatRelativeTime(mention.timestamp)}
                        </span>
                      </div>
                      <p className="font-mono text-sm text-white mb-2">{mention.title}</p>
                      <p className="text-sm text-white/50 line-clamp-2">{mention.content}</p>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {mention.keywords.map((keyword) => (
                          <span
                            key={keyword}
                            className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 text-[10px] font-mono"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Keyword alerts */}
          <GlassCard>
            <h3 className="font-mono font-semibold text-white mb-4">Keyword Alerts</h3>
            <div className="space-y-2">
              {["company.com", "company-internal", "CEO name", "product name", "api.company.com"].map(
                (keyword) => (
                  <div
                    key={keyword}
                    className="flex items-center justify-between p-2 rounded-lg bg-white/[0.02]"
                  >
                    <span className="font-mono text-sm text-white">{keyword}</span>
                    <button className="text-white/30 hover:text-red-400 transition-colors">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                )
              )}
            </div>
            <GlassButton variant="ghost" size="sm" className="w-full mt-3">
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Keyword
            </GlassButton>
          </GlassCard>

          {/* Selected mention details */}
          {selectedMention && (
            <GlassCard>
              <h3 className="font-mono font-semibold text-white mb-4">Mention Details</h3>
              <div className="space-y-4">
                <div>
                  <p className="text-xs text-white/40 mb-1">Title</p>
                  <p className="font-mono text-sm text-white">{selectedMention.title}</p>
                </div>
                <div>
                  <p className="text-xs text-white/40 mb-1">Content</p>
                  <p className="text-sm text-white/70">{selectedMention.content}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-white/40 mb-1">Source</p>
                    <p className="flex items-center gap-1 font-mono text-sm text-white">
                      {sourceIcons[selectedMention.source]} {sourceLabels[selectedMention.source]}
                    </p>
                  </div>
                  {selectedMention.author && (
                    <div>
                      <p className="text-xs text-white/40 mb-1">Author</p>
                      <p className="font-mono text-sm text-white">{selectedMention.author}</p>
                    </div>
                  )}
                </div>
                <div>
                  <p className="text-xs text-white/40 mb-1">URL</p>
                  <code className="block p-2 rounded bg-white/[0.03] text-xs text-amber-400 font-mono break-all">
                    {selectedMention.url}
                  </code>
                </div>
                <div className="pt-4 border-t border-white/[0.05] space-y-2">
                  <GlassButton variant="primary" size="sm" className="w-full">
                    Create Incident
                  </GlassButton>
                  <GlassButton variant="ghost" size="sm" className="w-full">
                    Mark as Reviewed
                  </GlassButton>
                </div>
              </div>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
}

