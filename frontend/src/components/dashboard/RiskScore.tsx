"use client";

import React, { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";

interface RiskScoreProps {
  score: number;
  riskLevel: string;
  trend: "improving" | "stable" | "worsening";
  criticalIssues: number;
  highIssues: number;
  className?: string;
  onClick?: () => void;
}

export function RiskScore({
  score = 78,
  riskLevel = "medium",
  trend = "stable",
  criticalIssues = 3,
  highIssues = 7,
  className,
  onClick,
}: RiskScoreProps) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Animate score on mount
    const duration = 1500;
    const steps = 60;
    const increment = score / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= score) {
        setAnimatedScore(score);
        clearInterval(timer);
      } else {
        setAnimatedScore(Math.floor(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [score]);

  const getScoreColor = (s: number) => {
    if (s >= 80) return "text-emerald-400";
    if (s >= 60) return "text-amber-400";
    if (s >= 40) return "text-orange-400";
    return "text-red-400";
  };

  const getRingColor = (s: number) => {
    if (s >= 80) return "stroke-emerald-500";
    if (s >= 60) return "stroke-amber-500";
    if (s >= 40) return "stroke-orange-500";
    return "stroke-red-500";
  };

  const getGlowColor = (s: number) => {
    if (s >= 80) return "drop-shadow-[0_0_15px_rgba(16,185,129,0.5)]";
    if (s >= 60) return "drop-shadow-[0_0_15px_rgba(245,158,11,0.5)]";
    if (s >= 40) return "drop-shadow-[0_0_15px_rgba(249,115,22,0.5)]";
    return "drop-shadow-[0_0_15px_rgba(239,68,68,0.5)]";
  };

  const getLevelLabel = (level: string) => {
    const labels: Record<string, string> = {
      minimal: "Excellent",
      low: "Good",
      medium: "Fair",
      high: "Poor",
      critical: "Critical",
    };
    return labels[level] || "Unknown";
  };

  const getTrendIcon = () => {
    if (trend === "improving") {
      return (
        <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
        </svg>
      );
    }
    if (trend === "worsening") {
      return (
        <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      );
    }
    return (
      <svg className="w-4 h-4 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
      </svg>
    );
  };

  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

  return (
    <GlassCard 
      className={cn(
        "p-6",
        onClick && "cursor-pointer transition-all hover:border-white/20 hover:shadow-lg",
        className
      )} 
      hover={false}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-mono text-lg font-semibold text-white">Security Score</h2>
        <div className="flex items-center gap-1.5 text-xs font-mono">
          {getTrendIcon()}
          <span className={cn(
            trend === "improving" && "text-emerald-400",
            trend === "worsening" && "text-red-400",
            trend === "stable" && "text-white/50"
          )}>
            {trend}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-6">
        {/* Circular Progress */}
        <div className="relative">
          <svg className={cn("w-32 h-32 transform -rotate-90", getGlowColor(animatedScore))} viewBox="0 0 100 100">
            {/* Background circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              className="text-white/[0.05]"
            />
            {/* Progress circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              strokeWidth="8"
              strokeLinecap="round"
              className={cn(getRingColor(animatedScore), "transition-all duration-500")}
              style={{
                strokeDasharray: circumference,
                strokeDashoffset: mounted ? strokeDashoffset : circumference,
                transition: "stroke-dashoffset 1.5s ease-out",
              }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={cn("text-4xl font-mono font-bold", getScoreColor(animatedScore))}>
              {animatedScore}
            </span>
            <span className="text-xs text-white/50 font-mono">/100</span>
          </div>
        </div>

        {/* Score Details */}
        <div className="flex-1 space-y-3">
          <div>
            <div className="text-sm text-white/50 font-mono mb-1">Status</div>
            <div className={cn("text-xl font-mono font-semibold", getScoreColor(animatedScore))}>
              {getLevelLabel(riskLevel)}
            </div>
          </div>

          <div className="h-px bg-white/[0.08]" />

          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              <div>
                <div className="text-lg font-mono font-semibold text-white">{criticalIssues}</div>
                <div className="text-xs text-white/50">Critical</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-orange-500" />
              <div>
                <div className="text-lg font-mono font-semibold text-white">{highIssues}</div>
                <div className="text-xs text-white/50">High</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

export default RiskScore;



