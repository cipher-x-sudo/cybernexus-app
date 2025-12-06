"use client";

import { useState } from "react";
import { GlassCard, Badge } from "@/components/ui";
import { cn } from "@/lib/utils";

const releases = [
  {
    version: "2.5.0",
    date: "December 1, 2024",
    tag: "Latest",
    changes: [
      { type: "feature", text: "Added 3D threat graph visualization" },
      { type: "feature", text: "New dark web monitoring sources" },
      { type: "improvement", text: "Improved credential leak detection accuracy" },
      { type: "fix", text: "Fixed notification delivery delays" },
    ],
  },
  {
    version: "2.4.0",
    date: "November 15, 2024",
    changes: [
      { type: "feature", text: "Custom report builder" },
      { type: "feature", text: "Slack integration" },
      { type: "improvement", text: "Enhanced threat map performance" },
      { type: "fix", text: "Fixed API rate limiting issues" },
    ],
  },
  {
    version: "2.3.0",
    date: "October 28, 2024",
    changes: [
      { type: "feature", text: "Real-time activity feed" },
      { type: "feature", text: "PDF export for reports" },
      { type: "improvement", text: "Redesigned settings page" },
      { type: "fix", text: "Fixed credential password masking" },
    ],
  },
  {
    version: "2.2.0",
    date: "October 10, 2024",
    changes: [
      { type: "feature", text: "Team collaboration features" },
      { type: "improvement", text: "Faster dashboard loading" },
      { type: "improvement", text: "Better mobile responsiveness" },
      { type: "fix", text: "Fixed timezone issues in reports" },
    ],
  },
  {
    version: "2.1.0",
    date: "September 20, 2024",
    changes: [
      { type: "feature", text: "API v2 with improved rate limits" },
      { type: "feature", text: "Webhook notifications" },
      { type: "fix", text: "Fixed search functionality" },
    ],
  },
];

const changeTypeColors = {
  feature: "bg-emerald-500/20 text-emerald-400",
  improvement: "bg-blue-500/20 text-blue-400",
  fix: "bg-orange-500/20 text-orange-400",
};

export default function ChangelogPage() {
  const [expandedVersion, setExpandedVersion] = useState<string | null>("2.5.0");

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-mono font-bold text-white">Changelog</h1>
        <p className="text-sm text-white/50">
          Stay up to date with the latest improvements and updates
        </p>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-6 top-0 bottom-0 w-px bg-gradient-to-b from-amber-500/50 via-amber-500/20 to-transparent" />

        <div className="space-y-8">
          {releases.map((release) => (
            <div key={release.version} className="relative pl-16">
              {/* Version dot */}
              <div className="absolute left-0 w-12 h-12 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
                <span className="font-mono text-sm font-bold text-amber-400">
                  {release.version.split(".")[0]}.{release.version.split(".")[1]}
                </span>
              </div>

              <GlassCard
                className={cn(
                  "cursor-pointer transition-all",
                  expandedVersion === release.version && "border-amber-500/30"
                )}
                onClick={() =>
                  setExpandedVersion(
                    expandedVersion === release.version ? null : release.version
                  )
                }
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <h2 className="font-mono text-lg font-bold text-white">
                      v{release.version}
                    </h2>
                    {release.tag && (
                      <Badge variant="success" size="sm">
                        {release.tag}
                      </Badge>
                    )}
                  </div>
                  <span className="text-sm text-white/40">{release.date}</span>
                </div>

                {/* Changes */}
                <div
                  className={cn(
                    "overflow-hidden transition-all duration-300",
                    expandedVersion === release.version
                      ? "max-h-[500px] opacity-100"
                      : "max-h-0 opacity-0"
                  )}
                >
                  <div className="pt-4 space-y-2">
                    {release.changes.map((change, index) => (
                      <div key={index} className="flex items-start gap-3">
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded text-[10px] font-mono uppercase",
                            changeTypeColors[change.type as keyof typeof changeTypeColors]
                          )}
                        >
                          {change.type}
                        </span>
                        <p className="text-sm text-white/70">{change.text}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Expand indicator */}
                <div className="flex justify-center mt-3">
                  <svg
                    className={cn(
                      "w-5 h-5 text-white/30 transition-transform",
                      expandedVersion === release.version && "rotate-180"
                    )}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </div>
              </GlassCard>
            </div>
          ))}
        </div>
      </div>

      {/* Subscribe CTA */}
      <GlassCard className="text-center">
        <h3 className="font-mono text-lg text-white mb-2">Stay Updated</h3>
        <p className="text-white/50 mb-4">
          Subscribe to our newsletter for the latest updates
        </p>
        <div className="flex gap-2 max-w-md mx-auto">
          <input
            type="email"
            placeholder="Enter your email"
            className="flex-1 h-10 px-4 bg-white/[0.03] border border-white/[0.08] rounded-xl text-white placeholder:text-white/30 font-mono text-sm focus:outline-none focus:border-amber-500/50"
          />
          <button className="px-4 py-2 bg-amber-500/20 border border-amber-500/40 rounded-xl text-amber-400 font-mono text-sm hover:bg-amber-500/30 transition-colors">
            Subscribe
          </button>
        </div>
      </GlassCard>
    </div>
  );
}

