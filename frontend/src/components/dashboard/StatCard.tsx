"use client";

import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";
import { AnimatedStatCounter } from "@/components/effects";

interface StatCardProps {
  title: string;
  value: number;
  change?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  trend?: "up" | "down" | "neutral";
  variant?: "default" | "critical" | "warning" | "success";
  className?: string;
}

export function StatCard({
  title,
  value,
  change,
  changeLabel = "vs last week",
  icon,
  trend = "neutral",
  variant = "default",
  className,
}: StatCardProps) {
  const variants = {
    default: {
      iconBg: "bg-amber-500/20 text-amber-400",
      trendUp: "text-emerald-400",
      trendDown: "text-red-400",
    },
    critical: {
      iconBg: "bg-red-500/20 text-red-400",
      trendUp: "text-red-400",
      trendDown: "text-emerald-400",
    },
    warning: {
      iconBg: "bg-orange-500/20 text-orange-400",
      trendUp: "text-orange-400",
      trendDown: "text-emerald-400",
    },
    success: {
      iconBg: "bg-emerald-500/20 text-emerald-400",
      trendUp: "text-emerald-400",
      trendDown: "text-red-400",
    },
  };

  const v = variants[variant];

  return (
    <GlassCard className={cn("group", className)} padding="lg">
      <div className="flex items-start justify-between mb-4">
        <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center", v.iconBg)}>
          {icon}
        </div>
        {change !== undefined && (
          <div
            className={cn(
              "flex items-center gap-1 text-sm font-mono",
              trend === "up" ? v.trendUp : trend === "down" ? v.trendDown : "text-white/40"
            )}
          >
            {trend === "up" ? (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
            ) : trend === "down" ? (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
            ) : null}
            <span>{Math.abs(change)}%</span>
          </div>
        )}
      </div>

      <div className="space-y-1">
        <p className="text-sm font-mono text-white/50 uppercase tracking-wider">{title}</p>
        <p className="text-3xl font-mono font-bold text-white">
          <AnimatedStatCounter value={value} />
        </p>
        {change !== undefined && (
          <p className="text-xs text-white/30">{changeLabel}</p>
        )}
      </div>

      {/* Hover glow effect */}
      <div
        className={cn(
          "absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none",
          variant === "critical" && "bg-red-500/5",
          variant === "warning" && "bg-orange-500/5",
          variant === "success" && "bg-emerald-500/5",
          variant === "default" && "bg-amber-500/5"
        )}
      />
    </GlassCard>
  );
}

