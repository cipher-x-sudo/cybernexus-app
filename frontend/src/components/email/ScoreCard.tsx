"use client";

import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";

interface ScoreCardProps {
  score: number;
  title?: string;
  subtitle?: string;
  size?: "sm" | "md" | "lg";
  showBreakdown?: boolean;
  breakdown?: Array<{ label: string; score: number; color: string }>;
  className?: string;
}

export function ScoreCard({
  score,
  title = "Security Score",
  subtitle,
  size = "md",
  showBreakdown = false,
  breakdown = [],
  className,
}: ScoreCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-400";
    if (score >= 60) return "text-amber-400";
    if (score >= 40) return "text-orange-400";
    return "text-red-400";
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return "bg-emerald-500/10 border-emerald-500/30";
    if (score >= 60) return "bg-amber-500/10 border-amber-500/30";
    if (score >= 40) return "bg-orange-500/10 border-orange-500/30";
    return "bg-red-500/10 border-red-500/30";
  };

  const sizeClasses = {
    sm: "p-4",
    md: "p-6",
    lg: "p-8",
  };

  const textSizeClasses = {
    sm: "text-2xl",
    md: "text-4xl",
    lg: "text-6xl",
  };

  return (
    <GlassCard className={cn("relative overflow-hidden", sizeClasses[size], className)}>
      <div className="space-y-4">
        <div>
          {title && (
            <h3 className="text-sm font-mono text-white/60 mb-1">{title}</h3>
          )}
          {subtitle && (
            <p className="text-xs text-white/40">{subtitle}</p>
          )}
        </div>

        <div className="flex items-end gap-4">
          <div className={cn("font-mono font-bold", textSizeClasses[size], getScoreColor(score))}>
            {Math.round(score)}
          </div>
          <div className="text-2xl text-white/30 mb-1">/100</div>
        </div>

        {/* Progress bar */}
        <div className="h-2 bg-white/[0.05] rounded-full overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all duration-500", getScoreBg(score))}
            style={{ width: `${score}%` }}
          />
        </div>

        {/* Breakdown */}
        {showBreakdown && breakdown.length > 0 && (
          <div className="space-y-2 pt-2 border-t border-white/10">
            {breakdown.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs">
                <span className="text-white/60">{item.label}</span>
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1 bg-white/[0.05] rounded-full overflow-hidden">
                    <div
                      className={cn("h-full rounded-full", item.color)}
                      style={{ width: `${item.score}%` }}
                    />
                  </div>
                  <span className={cn("font-mono w-8 text-right", item.color)}>
                    {Math.round(item.score)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </GlassCard>
  );
}



