"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";

const capabilities = [
  {
    id: "exposure_discovery",
    name: "Exposure Discovery",
    question: "What can attackers find about us online?",
    description: "Search for leaked documents, exposed configs, credentials via intelligent queries. Capture and map web presence.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    color: "cyan",
    href: "/capabilities/exposure",
  },
  {
    id: "dark_web_intelligence",
    name: "Dark Web Intelligence",
    question: "Are we mentioned on the dark web?",
    description: "Monitor .onion sites for brand mentions, track leaked credentials, identify clone sites and threat actors.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    color: "purple",
    href: "/capabilities/darkweb",
  },
  {
    id: "email_security",
    name: "Email Security Assessment",
    question: "Can our email be spoofed?",
    description: "Test SPF, DKIM, DMARC configurations. Run authentication bypass scenarios and generate compliance reports.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
    color: "amber",
    href: "/capabilities/email",
  },
  {
    id: "infrastructure_testing",
    name: "Infrastructure Testing",
    question: "Are our servers misconfigured?",
    description: "Scan for CRLF injection, path traversal, outdated software CVEs, and information disclosure issues.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
      </svg>
    ),
    color: "emerald",
    href: "/capabilities/infrastructure",
  },
  {
    id: "network_security",
    name: "Network Security",
    question: "Can attackers tunnel into our network?",
    description: "Detect HTTP tunneling, identify covert channels, test firewall bypass vulnerabilities.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
      </svg>
    ),
    color: "blue",
    href: "/capabilities/network",
  },
  {
    id: "investigation",
    name: "Investigation Mode",
    question: "Analyze a suspicious target",
    description: "Full page capture with resource trees, domain relationship mapping, screenshot and artifact collection.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    color: "orange",
    href: "/capabilities/investigate",
  },
];

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

export default function CapabilitiesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-mono font-bold text-white">Security Capabilities</h1>
        <p className="text-sm text-white/50 mt-1">
          Select a capability to assess your organization&apos;s security posture
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {capabilities.map((cap, index) => {
          const colors = getColorClasses(cap.color);
          return (
            <Link
              key={cap.id}
              href={cap.href}
              className={cn(
                "group relative p-6 rounded-2xl border backdrop-blur-sm",
                "transition-all duration-300",
                colors.bg,
                colors.border,
                colors.glow,
                "animate-fade-in"
              )}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              {/* Icon */}
              <div className={cn("w-14 h-14 rounded-2xl flex items-center justify-center mb-4", colors.iconBg)}>
                <div className={colors.text}>{cap.icon}</div>
              </div>

              <h3 className="font-mono font-semibold text-white mb-2">{cap.name}</h3>

              <p className={cn("text-lg font-medium mb-3", colors.text)}>{cap.question}</p>

              <p className="text-sm text-white/50 line-clamp-3">{cap.description}</p>

              <div className={cn(
                "absolute bottom-6 right-6 opacity-0 group-hover:opacity-100",
                "transform translate-x-2 group-hover:translate-x-0",
                "transition-all duration-200"
              )}>
                <svg className={cn("w-6 h-6", colors.text)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </div>
            </Link>
          );
        })}
      </div>

      <GlassCard className="p-6" hover={false}>
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="font-mono font-semibold text-white mb-1">About Capabilities</h3>
            <p className="text-sm text-white/60">
              Each capability focuses on a specific security question. Behind the scenes, CyberNexus orchestrates
              the appropriate security tools and techniques to answer that question - you just focus on what
              you want to learn about your security posture.
            </p>
          </div>
        </div>
      </GlassCard>
    </div>
  );
}



