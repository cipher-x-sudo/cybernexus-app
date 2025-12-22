"use client";

import { GlassCard } from "@/components/ui";

const certifications = [
  {
    name: "SOC 2 Type II",
    description: "Annual third-party audit of security controls",
    icon: "🛡️",
  },
  {
    name: "GDPR",
    description: "Full compliance with EU data protection regulations",
    icon: "🇪🇺",
  },
  {
    name: "ISO 27001",
    description: "International standard for information security",
    icon: "📋",
  },
  {
    name: "HIPAA",
    description: "Healthcare data protection compliant",
    icon: "🏥",
  },
];

const securityFeatures = [
  "End-to-end encryption (AES-256)",
  "Zero-trust architecture",
  "Regular penetration testing",
  "Multi-factor authentication",
  "Role-based access control",
  "Audit logging & monitoring",
];

export function SecuritySection() {
  return (
    <section id="security" className="py-24 lg:py-32 relative overflow-hidden">
      <div className="absolute inset-0">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-amber-500/5 rounded-full blur-[150px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Left: Content */}
          <div>
            <p className="text-amber-400 font-mono text-sm uppercase tracking-wider mb-4">
              Enterprise Security
            </p>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-mono font-bold text-white mb-6">
              Security You Can{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-orange-500">
                Trust
              </span>
            </h2>
            <p className="text-lg text-white/60 mb-8">
              We take security seriously. Your data is protected by
              enterprise-grade security measures and compliance with
              industry-leading standards.
            </p>

            <div className="grid grid-cols-2 gap-4">
              {securityFeatures.map((feature, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-amber-500/20 flex items-center justify-center">
                    <svg
                      className="w-3 h-3 text-amber-400"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <span className="text-sm text-white/70">{feature}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {certifications.map((cert, index) => (
              <GlassCard
                key={index}
                className="text-center"
                padding="lg"
              >
                <div className="text-4xl mb-4">{cert.icon}</div>
                <h3 className="font-mono font-semibold text-white mb-2">
                  {cert.name}
                </h3>
                <p className="text-sm text-white/50">{cert.description}</p>
              </GlassCard>
            ))}
          </div>
        </div>

        <div className="mt-16 lg:mt-24">
          <GlassCard className="text-center" padding="lg" glow>
            <div className="flex flex-col md:flex-row items-center justify-center gap-6">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
              </div>
              <div className="text-center md:text-left">
                <h3 className="font-mono font-semibold text-white text-xl mb-1">
                  Request a Security Review
                </h3>
                <p className="text-white/50">
                  Our security team is available to discuss your requirements
                </p>
              </div>
              <a
                href="/dashboard"
                className="px-6 py-3 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-400 font-mono text-sm hover:bg-amber-500/30 transition-colors"
              >
                Contact Security Team
              </a>
            </div>
          </GlassCard>
        </div>
      </div>
    </section>
  );
}

