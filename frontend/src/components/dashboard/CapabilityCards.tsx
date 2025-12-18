"use client";

import React from "react";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface Capability {
  id: string;
  name: string;
  question: string;
  description: string;
  icon: string;
  color: string;
  stats?: {
    scans: number;
    findings: number;
    lastRun?: string;
  };
  href: string;
}

const capabilities: Capability[] = [
  {
    id: "exposure_discovery",
    name: "Exposure Discovery",
    question: "What can attackers find about us online?",
    description: "Search for leaked documents, exposed configs, and sensitive data",
    icon: "search",
    color: "cyan",
    href: "/capabilities/exposure",
  },
  {
    id: "dark_web_intelligence",
    name: "Dark Web Intel",
    question: "Are we mentioned on the dark web?",
    description: "Monitor .onion sites for brand mentions and credential leaks",
    icon: "globe",
    color: "purple",
    href: "/capabilities/darkweb",
  },
  {
    id: "email_security",
    name: "Email Security",
    question: "Can our email be spoofed?",
    description: "Test SPF, DKIM, DMARC configurations for vulnerabilities",
    icon: "mail",
    color: "amber",
    href: "/capabilities/email",
  },
  {
    id: "infrastructure_testing",
    name: "Infrastructure",
    question: "Are our servers misconfigured?",
    description: "Scan for CRLF injection, path traversal, and CVEs",
    icon: "server",
    color: "emerald",
    href: "/capabilities/infrastructure",
  },
  {
    id: "network_security",
    name: "Network Security",
    question: "Can attackers tunnel into our network?",
    description: "Detect HTTP tunneling and covert channels",
    icon: "network",
    color: "blue",
    href: "/capabilities/network",
  },
  {
    id: "investigation",
    name: "Investigation",
    question: "Analyze a suspicious target",
    description: "Deep dive into URLs, domains, or indicators of compromise",
    icon: "microscope",
    color: "orange",
    href: "/capabilities/investigate",
  },
];

const IconComponent = ({ icon, className }: { icon: string; className?: string }) => {
  const icons: Record<string, React.ReactNode> = {
    search: (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    globe: (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    mail: (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
    server: (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
      </svg>
    ),
    network: (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
      </svg>
    ),
    microscope: (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
  };
  return icons[icon] || null;
};

const getColorClasses = (color: string) => {
  const colors: Record<string, { bg: string; border: string; text: string; glow: string; iconBg: string }> = {
    cyan: {
      bg: "bg-cyan-500/5 hover:bg-cyan-500/10",
      border: "border-cyan-500/20 hover:border-cyan-500/40",
      text: "text-cyan-400",
      glow: "hover:shadow-[0_0_30px_rgba(6,182,212,0.15)]",
      iconBg: "bg-cyan-500/10",
    },
    purple: {
      bg: "bg-purple-500/5 hover:bg-purple-500/10",
      border: "border-purple-500/20 hover:border-purple-500/40",
      text: "text-purple-400",
      glow: "hover:shadow-[0_0_30px_rgba(139,92,246,0.15)]",
      iconBg: "bg-purple-500/10",
    },
    amber: {
      bg: "bg-amber-500/5 hover:bg-amber-500/10",
      border: "border-amber-500/20 hover:border-amber-500/40",
      text: "text-amber-400",
      glow: "hover:shadow-[0_0_30px_rgba(245,158,11,0.15)]",
      iconBg: "bg-amber-500/10",
    },
    emerald: {
      bg: "bg-emerald-500/5 hover:bg-emerald-500/10",
      border: "border-emerald-500/20 hover:border-emerald-500/40",
      text: "text-emerald-400",
      glow: "hover:shadow-[0_0_30px_rgba(16,185,129,0.15)]",
      iconBg: "bg-emerald-500/10",
    },
    blue: {
      bg: "bg-blue-500/5 hover:bg-blue-500/10",
      border: "border-blue-500/20 hover:border-blue-500/40",
      text: "text-blue-400",
      glow: "hover:shadow-[0_0_30px_rgba(59,130,246,0.15)]",
      iconBg: "bg-blue-500/10",
    },
    orange: {
      bg: "bg-orange-500/5 hover:bg-orange-500/10",
      border: "border-orange-500/20 hover:border-orange-500/40",
      text: "text-orange-400",
      glow: "hover:shadow-[0_0_30px_rgba(249,115,22,0.15)]",
      iconBg: "bg-orange-500/10",
    },
  };
  return colors[color] || colors.cyan;
};

interface CapabilityCardsProps {
  className?: string;
  compact?: boolean;
  stats?: Record<string, {
    scans: number;
    findings: number;
    lastRun: string;
  }>;
}

export function CapabilityCards({ className, compact = false, stats: propStats }: CapabilityCardsProps) {
  // Merge prop stats with capabilities (only use real stats from API)
  const capabilitiesWithStats = capabilities.map((cap) => {
    const realStats = propStats?.[cap.id];
    return {
      ...cap,
      stats: realStats ? {
        scans: realStats.scans,
        findings: realStats.findings,
        lastRun: realStats.lastRun,
      } : undefined,
    };
  });

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-mono text-lg font-semibold text-white">What do you want to do?</h2>
        <Link 
          href="/capabilities"
          className="text-xs font-mono text-amber-400 hover:text-amber-300 transition-colors"
        >
          See All →
        </Link>
      </div>

      <div className={cn(
        "grid gap-3",
        compact ? "grid-cols-2 lg:grid-cols-4" : "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
      )}>
        {capabilitiesWithStats.map((cap, index) => {
          const colors = getColorClasses(cap.color);
          return (
            <Link
              key={cap.id}
              href={cap.href}
              className={cn(
                "group relative p-4 rounded-2xl border backdrop-blur-sm",
                "transition-all duration-300 cursor-pointer",
                colors.bg,
                colors.border,
                colors.glow,
                "animate-fade-in"
              )}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              {/* Icon */}
              <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center mb-3", colors.iconBg)}>
                <IconComponent icon={cap.icon} className={cn("w-5 h-5", colors.text)} />
              </div>

              {/* Question (primary) */}
              <p className="text-sm font-medium text-white mb-1 line-clamp-2">
                {cap.question}
              </p>

              {/* Name (secondary) */}
              <p className="text-xs text-white/40 font-mono mb-3">
                {cap.name}
              </p>

              {/* Stats */}
              {cap.stats && !compact && (
                <div className="flex items-center gap-3 text-xs">
                  {cap.stats.findings > 0 && (
                    <span className={cn("font-mono", colors.text)}>
                      {cap.stats.findings} findings
                    </span>
                  )}
                  {cap.stats.lastRun && (
                    <span className="text-white/30">
                      {cap.stats.lastRun}
                    </span>
                  )}
                </div>
              )}

              {/* Arrow indicator */}
              <div className={cn(
                "absolute right-3 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100",
                "transform translate-x-2 group-hover:translate-x-0",
                "transition-all duration-200"
              )}>
                <svg className={cn("w-5 h-5", colors.text)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

export default CapabilityCards;



