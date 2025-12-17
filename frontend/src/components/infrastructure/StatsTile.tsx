"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";

interface StatsTileProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  variant?: "default" | "critical" | "warning" | "success" | "info";
  className?: string;
}

export function StatsTile({
  title,
  value,
  subtitle,
  icon,
  trend,
  variant = "default",
  className,
}: StatsTileProps) {
  const variants = {
    default: {
      bg: "bg-white/5",
      border: "border-white/10",
      accent: "text-white",
    },
    critical: {
      bg: "bg-red-500/10",
      border: "border-red-500/30",
      accent: "text-red-400",
    },
    warning: {
      bg: "bg-amber-500/10",
      border: "border-amber-500/30",
      accent: "text-amber-400",
    },
    success: {
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/30",
      accent: "text-emerald-400",
    },
    info: {
      bg: "bg-blue-500/10",
      border: "border-blue-500/30",
      accent: "text-blue-400",
    },
  };

  const style = variants[variant];

  return (
    <GlassCard
      className={cn(
        "transition-all duration-300 hover:scale-105",
        style.bg,
        style.border,
        className
      )}
      hover={false}
      padding="md"
    >
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-xs font-mono text-white/60 uppercase tracking-wider">{title}</p>
          {icon && <div className={style.accent}>{icon}</div>}
        </div>
        
        <div className="flex items-baseline gap-2">
          <p className={cn("text-2xl font-mono font-bold", style.accent)}>
            {typeof value === "number" ? value.toLocaleString() : value}
          </p>
          {trend && (
            <span
              className={cn(
                "text-xs font-mono",
                trend.isPositive ? "text-emerald-400" : "text-red-400"
              )}
            >
              {trend.isPositive ? "↑" : "↓"} {Math.abs(trend.value)}%
            </span>
          )}
        </div>

        {subtitle && (
          <p className="text-xs text-white/40 font-mono">{subtitle}</p>
        )}
      </div>
    </GlassCard>
  );
}

