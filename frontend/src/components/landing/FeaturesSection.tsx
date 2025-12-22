"use client";

import { useEffect, useRef, useState } from "react";
import { GlassCard } from "@/components/ui";
import { cn } from "@/lib/utils";

const features = [
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    title: "Real-time Monitoring",
    description: "24/7 continuous monitoring of your digital assets with instant alerts on suspicious activities and potential threats.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    title: "3D Graph Analysis",
    description: "Visualize complex threat relationships in an interactive 3D graph. Discover hidden connections and attack patterns.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    title: "Dark Web Intel",
    description: "Monitor dark web forums, marketplaces, and paste sites for mentions of your organization, credentials, and data.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
      </svg>
    ),
    title: "Credential Tracking",
    description: "Detect leaked credentials before attackers exploit them. Get instant alerts when your organization's data appears in breaches.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    title: "Automated Reports",
    description: "Generate executive summaries, technical reports, and compliance documentation with a single click.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
    title: "API Integrations",
    description: "Connect with your existing security stack. SIEM, SOAR, ticketing systems, and more through our powerful API.",
  },
];

export function FeaturesSection() {
  const [visibleCards, setVisibleCards] = useState<number[]>([]);
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const index = parseInt(entry.target.getAttribute("data-index") || "0");
            setVisibleCards((prev) => [...prev, index]);
          }
        });
      },
      { threshold: 0.2 }
    );

    const cards = sectionRef.current?.querySelectorAll("[data-index]");
    cards?.forEach((card) => observer.observe(card));

    return () => observer.disconnect();
  }, []);

  return (
    <section id="features" ref={sectionRef} className="py-24 lg:py-32 relative">
      <div className="absolute inset-0 gradient-mesh opacity-50" />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16 lg:mb-20">
          <p className="text-amber-400 font-mono text-sm uppercase tracking-wider mb-4">
            Powerful Features
          </p>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-mono font-bold text-white mb-6">
            Everything You Need to{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-orange-500">
              Stay Protected
            </span>
          </h2>
          <p className="text-lg text-white/60">
            Comprehensive threat intelligence tools designed for modern security teams.
            From monitoring to response, we've got you covered.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              data-index={index}
              className={cn(
                "opacity-0 translate-y-8 transition-all duration-700",
                visibleCards.includes(index) && "opacity-100 translate-y-0"
              )}
              style={{ transitionDelay: `${index * 100}ms` }}
            >
              <GlassCard className="h-full group" padding="lg">
                <div className="flex flex-col h-full">
                  {/* Icon */}
                  <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-5 group-hover:scale-110 group-hover:bg-amber-500/20 transition-all duration-300">
                    {feature.icon}
                  </div>

                  {/* Content */}
                  <h3 className="text-xl font-mono font-semibold text-white mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-white/50 leading-relaxed flex-grow">
                    {feature.description}
                  </p>

                  <div className="mt-5 pt-5 border-t border-white/[0.05]">
                    <a
                      href="/dashboard"
                      className="inline-flex items-center text-sm font-mono text-amber-400 hover:text-amber-300 transition-colors group/link"
                    >
                      Learn more
                      <svg
                        className="w-4 h-4 ml-2 group-hover/link:translate-x-1 transition-transform"
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
                    </a>
                  </div>
                </div>
              </GlassCard>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

