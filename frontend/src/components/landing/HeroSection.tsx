"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { GlassButton } from "@/components/ui";
import { TypingText } from "@/components/effects";
import { cn } from "@/lib/utils";

export function HeroSection() {
  const globeRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const handleGetStarted = () => {
    router.push("/dashboard");
  };

  const handleWatchDemo = () => {
    // Scroll to how-it-works section or open demo
    const element = document.getElementById("how-it-works");
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    } else {
      router.push("/dashboard");
    }
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-amber-500/20 rounded-full blur-[128px] animate-float" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/15 rounded-full blur-[128px] animate-float delay-300" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-amber-500/10 rounded-full blur-[200px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Left: Content */}
          <div className="text-center lg:text-left space-y-8">
            <div className="space-y-4">
              <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500" />
                </span>
                <span className="text-xs font-mono text-amber-400 uppercase tracking-wider">
                  Real-time Protection
                </span>
              </div>

              <h1 className="text-4xl md:text-5xl lg:text-6xl font-mono font-bold leading-tight">
                <span className="text-white">Unified</span>{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-orange-500">
                  Threat Intelligence
                </span>{" "}
                <span className="text-white">Platform</span>
              </h1>

              <p className="text-lg md:text-xl text-white/60 max-w-xl mx-auto lg:mx-0">
                <TypingText
                  text="Monitor, correlate, and respond to cyber threats in real-time. Your command center for proactive security."
                  speed={30}
                />
              </p>
            </div>

            <div className="flex flex-wrap gap-4 justify-center lg:justify-start">
              <GlassButton
                variant="primary"
                size="lg"
                onClick={handleGetStarted}
                icon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                }
              >
                Get Started Free
              </GlassButton>
              <GlassButton
                variant="secondary"
                size="lg"
                onClick={handleWatchDemo}
                icon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                }
              >
                Watch Demo
              </GlassButton>
            </div>

            {/* Trust badges */}
            <div className="flex flex-wrap items-center gap-6 justify-center lg:justify-start pt-4">
              <div className="flex items-center space-x-2 text-white/40">
                <svg className="w-5 h-5 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-sm font-mono">SOC 2 Certified</span>
              </div>
              <div className="flex items-center space-x-2 text-white/40">
                <svg className="w-5 h-5 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-sm font-mono">GDPR Compliant</span>
              </div>
              <div className="flex items-center space-x-2 text-white/40">
                <svg className="w-5 h-5 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-sm font-mono">ISO 27001</span>
              </div>
            </div>
          </div>

          <div className="relative flex items-center justify-center">
            <Globe3D />
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <div className="w-6 h-10 rounded-full border-2 border-white/20 flex items-start justify-center p-2">
          <div className="w-1 h-2 bg-amber-400 rounded-full animate-pulse" />
        </div>
      </div>
    </section>
  );
}

// 3D Globe Component
function Globe3D() {
  return (
    <div className="relative w-[400px] h-[400px] lg:w-[500px] lg:h-[500px]">
      {/* Outer glow */}
      <div className="absolute inset-0 rounded-full bg-gradient-to-br from-amber-500/20 to-transparent blur-3xl" />
      
      {/* Globe container */}
      <div className="relative w-full h-full animate-rotate-globe" style={{ animationDuration: "30s" }}>
        {/* Globe sphere */}
        <div className="absolute inset-8 rounded-full border border-amber-500/30 bg-gradient-to-br from-amber-500/5 to-transparent">
          {/* Grid lines - horizontal */}
          {[...Array(6)].map((_, i) => (
            <div
              key={`h-${i}`}
              className="absolute inset-0 rounded-full border border-amber-500/10"
              style={{
                transform: `rotateX(${i * 30}deg)`,
              }}
            />
          ))}
          
          {/* Grid lines - vertical */}
          {[...Array(12)].map((_, i) => (
            <div
              key={`v-${i}`}
              className="absolute inset-0 rounded-full border border-amber-500/10"
              style={{
                transform: `rotateY(${i * 30}deg)`,
              }}
            />
          ))}
        </div>

        {/* Threat points */}
        <ThreatPoint x={30} y={25} delay={0} severity="critical" />
        <ThreatPoint x={70} y={35} delay={200} severity="high" />
        <ThreatPoint x={45} y={60} delay={400} severity="medium" />
        <ThreatPoint x={20} y={50} delay={600} severity="high" />
        <ThreatPoint x={80} y={70} delay={800} severity="critical" />
        <ThreatPoint x={55} y={20} delay={1000} severity="low" />
        <ThreatPoint x={35} y={75} delay={1200} severity="medium" />
      </div>

      {/* Floating UI cards */}
      <FloatingCard
        className="absolute -left-4 top-1/4"
        delay={0}
        title="Threats Detected"
        value="2,847"
        trend="+12%"
      />
      <FloatingCard
        className="absolute -right-4 top-1/2"
        delay={200}
        title="Assets Protected"
        value="156"
        trend="Active"
      />
      <FloatingCard
        className="absolute left-1/4 -bottom-4"
        delay={400}
        title="Response Time"
        value="<2min"
        trend="Avg"
      />
    </div>
  );
}

function ThreatPoint({
  x,
  y,
  delay,
  severity,
}: {
  x: number;
  y: number;
  delay: number;
  severity: "critical" | "high" | "medium" | "low";
}) {
  const colors = {
    critical: "bg-red-500",
    high: "bg-orange-500",
    medium: "bg-yellow-500",
    low: "bg-blue-500",
  };

  return (
    <div
      className="absolute w-3 h-3"
      style={{
        left: `${x}%`,
        top: `${y}%`,
        animationDelay: `${delay}ms`,
      }}
    >
      <span
        className={cn(
          "absolute inset-0 rounded-full animate-ping opacity-75",
          colors[severity]
        )}
      />
      <span
        className={cn(
          "relative block w-full h-full rounded-full",
          colors[severity]
        )}
      />
    </div>
  );
}

function FloatingCard({
  className,
  delay,
  title,
  value,
  trend,
}: {
  className?: string;
  delay: number;
  title: string;
  value: string;
  trend: string;
}) {
  return (
    <div
      className={cn(
        "glass rounded-xl p-3 animate-float",
        className
      )}
      style={{ animationDelay: `${delay}ms` }}
    >
      <p className="text-[10px] font-mono text-white/50 uppercase tracking-wider">
        {title}
      </p>
      <p className="text-xl font-mono font-bold text-white">{value}</p>
      <p className="text-xs font-mono text-amber-400">{trend}</p>
    </div>
  );
}

