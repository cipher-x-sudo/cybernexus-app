"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

const team = [
  {
    name: "Alexandra Chen",
    role: "CEO & Co-founder",
    bio: "Former Head of Threat Intelligence at major fintech. 15+ years in cybersecurity.",
    avatar: "AC",
    linkedin: "#",
  },
  {
    name: "Marcus Rodriguez",
    role: "CTO & Co-founder",
    bio: "Ex-Google Security engineer. PhD in Machine Learning from MIT.",
    avatar: "MR",
    linkedin: "#",
  },
  {
    name: "Sarah Kim",
    role: "VP of Engineering",
    bio: "Built security products at Crowdstrike and Palo Alto Networks.",
    avatar: "SK",
    linkedin: "#",
  },
  {
    name: "James Wilson",
    role: "Head of Research",
    bio: "Published researcher specializing in dark web intelligence.",
    avatar: "JW",
    linkedin: "#",
  },
  {
    name: "Emily Zhang",
    role: "Head of Product",
    bio: "Product leader with experience at Splunk and Elastic.",
    avatar: "EZ",
    linkedin: "#",
  },
  {
    name: "David Okonkwo",
    role: "Head of Customer Success",
    bio: "Helped 100+ enterprises implement threat intelligence programs.",
    avatar: "DO",
    linkedin: "#",
  },
];

export function TeamSection() {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  return (
    <section id="team" className="py-24 lg:py-32 relative">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <p className="text-amber-400 font-mono text-sm uppercase tracking-wider mb-4">
            Our Team
          </p>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-mono font-bold text-white mb-6">
            Built by{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-orange-500">
              Security Experts
            </span>
          </h2>
          <p className="text-lg text-white/60">
            Our team combines decades of experience in cybersecurity, threat
            intelligence, and enterprise software.
          </p>
        </div>

        {/* Team grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {team.map((member, index) => (
            <div
              key={index}
              className="relative group"
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              <div className="glass rounded-2xl p-6 h-full transition-all duration-300 group-hover:border-amber-500/40">
                {/* Avatar */}
                <div className="relative mb-6">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-mono font-bold text-2xl">
                    {member.avatar}
                  </div>
                  {/* LinkedIn icon */}
                  <a
                    href={member.linkedin}
                    className={cn(
                      "absolute -bottom-2 -right-2 w-8 h-8 rounded-lg bg-[#0077b5] flex items-center justify-center text-white transition-all duration-300",
                      hoveredIndex === index
                        ? "opacity-100 scale-100"
                        : "opacity-0 scale-75"
                    )}
                  >
                    <svg
                      className="w-4 h-4"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                    </svg>
                  </a>
                </div>

                {/* Info */}
                <h3 className="font-mono font-semibold text-white text-lg mb-1">
                  {member.name}
                </h3>
                <p className="text-amber-400 text-sm font-mono mb-3">
                  {member.role}
                </p>

                {/* Bio - revealed on hover */}
                <div
                  className={cn(
                    "overflow-hidden transition-all duration-300",
                    hoveredIndex === index ? "max-h-24 opacity-100" : "max-h-0 opacity-0"
                  )}
                >
                  <p className="text-sm text-white/50 pt-3 border-t border-white/[0.05]">
                    {member.bio}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Careers CTA */}
        <div className="mt-16 text-center">
          <p className="text-white/50 mb-4">Want to join our team?</p>
          <a
            href="/dashboard"
            className="inline-flex items-center gap-2 text-amber-400 font-mono hover:text-amber-300 transition-colors"
          >
            View open positions
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 8l4 4m0 0l-4 4m4-4H3"
              />
            </svg>
          </a>
        </div>
      </div>
    </section>
  );
}

