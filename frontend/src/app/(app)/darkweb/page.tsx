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

declare const process: { env: { NEXT_PUBLIC_API_URL?: string } };

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function fetchMentions(): Promise<Mention[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/darkweb/mentions`);
    if (!response.ok) {
      if (response.status === 404) {
        console.warn('Darkweb mentions endpoint not available yet');
        return [];
      }
      throw new Error(`Failed to fetch mentions: ${response.status}`);
    }
    const data = await response.json();
    
    return data.map((item: any) => ({
      id: item.id,
      title: item.title,
      content: item.content,
      source: item.source as Mention["source"],
      severity: item.severity as Mention["severity"],
      keywords: item.keywords || [],
      url: item.url,
      timestamp: new Date(item.timestamp),
      author: item.author
    }));
  } catch (error) {
    console.error('Error fetching mentions:', error);
    return [];
  }
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
    fetchMentions().then(setMentions);
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

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total Mentions", value: mentions.length },
          { label: "Critical", value: mentions.filter((m) => m.severity === "critical").length },
          { label: "This Week", value: mentions.filter((m) => {
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            return m.timestamp >= weekAgo;
          }).length },
          { label: "Sources", value: new Set(mentions.map((m) => m.source)).size },
        ].map((stat) => (
          <GlassCard key={stat.label} padding="lg">
            <p className="text-sm font-mono text-white/50 mb-1">{stat.label}</p>
            <p className="text-3xl font-mono font-bold text-white">{stat.value}</p>
          </GlassCard>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <GlassCard padding="none">
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

            <div className="divide-y divide-white/[0.03]">
              {filteredMentions.length === 0 ? (
                <div className="p-8 text-center text-white/50">
                  <p className="font-mono text-sm">No mentions found</p>
                  <p className="font-mono text-xs mt-2">Submit a dark web intelligence job to start monitoring</p>
                </div>
              ) : (
                filteredMentions.map((mention) => (
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
                ))
              )}
            </div>
          </GlassCard>
        </div>

        <div className="space-y-4">
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

