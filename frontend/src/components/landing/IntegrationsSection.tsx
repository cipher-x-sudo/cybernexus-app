"use client";

import { useState } from "react";
import { GlassCard } from "@/components/ui";
import { cn } from "@/lib/utils";

const categories = [
  { id: "siem", label: "SIEM" },
  { id: "cloud", label: "Cloud" },
  { id: "identity", label: "Identity" },
  { id: "ticketing", label: "Ticketing" },
];

const integrations = [
  {
    name: "Splunk",
    category: "siem",
    description: "Forward threat intelligence directly to your Splunk instance",
    color: "from-green-500 to-emerald-600",
  },
  {
    name: "Elastic",
    category: "siem",
    description: "Seamless integration with Elastic Security",
    color: "from-pink-500 to-rose-600",
  },
  {
    name: "Sentinel",
    category: "siem",
    description: "Microsoft Sentinel native integration",
    color: "from-blue-500 to-cyan-600",
  },
  {
    name: "AWS",
    category: "cloud",
    description: "Monitor AWS infrastructure and GuardDuty findings",
    color: "from-orange-500 to-amber-600",
  },
  {
    name: "Azure",
    category: "cloud",
    description: "Connect Azure Security Center alerts",
    color: "from-blue-600 to-indigo-600",
  },
  {
    name: "GCP",
    category: "cloud",
    description: "Google Cloud Security Command Center integration",
    color: "from-red-500 to-orange-600",
  },
  {
    name: "Okta",
    category: "identity",
    description: "Monitor identity threats and compromised accounts",
    color: "from-blue-500 to-blue-600",
  },
  {
    name: "Azure AD",
    category: "identity",
    description: "Entra ID risk detection and monitoring",
    color: "from-sky-500 to-blue-600",
  },
  {
    name: "Jira",
    category: "ticketing",
    description: "Auto-create tickets for detected threats",
    color: "from-blue-500 to-blue-700",
  },
  {
    name: "ServiceNow",
    category: "ticketing",
    description: "Enterprise ticketing and workflow automation",
    color: "from-green-500 to-teal-600",
  },
  {
    name: "PagerDuty",
    category: "ticketing",
    description: "Critical alert escalation and on-call routing",
    color: "from-green-400 to-emerald-600",
  },
  {
    name: "Slack",
    category: "ticketing",
    description: "Real-time notifications and ChatOps",
    color: "from-purple-500 to-violet-600",
  },
];

export function IntegrationsSection() {
  const [activeCategory, setActiveCategory] = useState("siem");

  const filteredIntegrations = integrations.filter(
    (i) => i.category === activeCategory
  );

  return (
    <section id="integrations" className="py-24 lg:py-32 relative">
      <div className="absolute inset-0 gradient-mesh opacity-30" />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <p className="text-amber-400 font-mono text-sm uppercase tracking-wider mb-4">
            Integrations
          </p>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-mono font-bold text-white mb-6">
            Connects With Your{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-orange-500">
              Security Stack
            </span>
          </h2>
          <p className="text-lg text-white/60">
            Seamlessly integrate with the tools you already use. No complex
            configurations required.
          </p>
        </div>

        {/* Category tabs */}
        <div className="flex flex-wrap justify-center gap-2 mb-12">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={cn(
                "px-5 py-2.5 rounded-xl font-mono text-sm transition-all duration-300",
                activeCategory === category.id
                  ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                  : "bg-white/[0.03] text-white/60 border border-white/[0.08] hover:bg-white/[0.05] hover:text-white/80"
              )}
            >
              {category.label}
            </button>
          ))}
        </div>

        {/* Integration cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredIntegrations.map((integration, index) => (
            <GlassCard
              key={integration.name}
              className="group cursor-pointer"
              padding="lg"
            >
              <div className="flex items-start gap-4">
                <div
                  className={cn(
                    "w-12 h-12 rounded-xl bg-gradient-to-br flex items-center justify-center text-white font-mono font-bold text-lg shrink-0",
                    integration.color
                  )}
                >
                  {integration.name.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-mono font-semibold text-white mb-1 group-hover:text-amber-400 transition-colors">
                    {integration.name}
                  </h3>
                  <p className="text-sm text-white/50">
                    {integration.description}
                  </p>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-white/[0.05] flex items-center justify-between">
                <span className="text-xs font-mono text-white/30 uppercase">
                  {integration.category}
                </span>
                <svg
                  className="w-5 h-5 text-white/30 group-hover:text-amber-400 group-hover:translate-x-1 transition-all"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </div>
            </GlassCard>
          ))}
        </div>

        {/* API callout */}
        <div className="mt-16 text-center">
          <GlassCard className="inline-block" padding="lg">
            <div className="flex flex-col md:flex-row items-center gap-6">
              <div className="w-16 h-16 rounded-2xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <svg
                  className="w-8 h-8"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
                  />
                </svg>
              </div>
              <div className="text-center md:text-left">
                <h3 className="font-mono font-semibold text-white text-lg mb-1">
                  Build Custom Integrations
                </h3>
                <p className="text-white/50 text-sm">
                  Use our REST API to build custom integrations with any tool
                </p>
              </div>
              <a
                href="#"
                className="font-mono text-sm text-amber-400 hover:text-amber-300 transition-colors whitespace-nowrap"
              >
                View API Docs →
              </a>
            </div>
          </GlassCard>
        </div>
      </div>
    </section>
  );
}

