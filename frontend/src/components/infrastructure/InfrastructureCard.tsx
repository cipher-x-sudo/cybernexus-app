"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";
import { Badge } from "@/components/ui";
import { InfrastructureFinding, categoryIcons, categoryLabels } from "./helpers";

interface InfrastructureCardProps {
  finding: InfrastructureFinding;
  isSelected?: boolean;
  onClick?: () => void;
}

export function InfrastructureCard({
  finding,
  isSelected = false,
  onClick,
}: InfrastructureCardProps) {
  const severityStyles = {
    critical: {
      bg: "bg-red-500/10",
      border: "border-red-500/30",
      text: "text-red-400",
      glow: "shadow-[0_0_20px_rgba(239,68,68,0.2)]",
    },
    high: {
      bg: "bg-orange-500/10",
      border: "border-orange-500/30",
      text: "text-orange-400",
      glow: "shadow-[0_0_20px_rgba(249,115,22,0.2)]",
    },
    medium: {
      bg: "bg-amber-500/10",
      border: "border-amber-500/30",
      text: "text-amber-400",
      glow: "shadow-[0_0_20px_rgba(245,158,11,0.2)]",
    },
    low: {
      bg: "bg-blue-500/10",
      border: "border-blue-500/30",
      text: "text-blue-400",
      glow: "shadow-[0_0_20px_rgba(59,130,246,0.2)]",
    },
    info: {
      bg: "bg-purple-500/10",
      border: "border-purple-500/30",
      text: "text-purple-400",
      glow: "shadow-[0_0_20px_rgba(139,92,246,0.2)]",
    },
  };

  const styles = severityStyles[finding.severity] || severityStyles.info;

  const getEvidencePreview = (): string => {
    if (!finding.evidence || Object.keys(finding.evidence).length === 0) {
      return "No evidence available";
    }

    if (finding.category === "headers") {
      if (finding.evidence.missing_header) {
        return `Missing: ${finding.evidence.missing_header}`;
      }
      
      if (finding.evidence.headers && typeof finding.evidence.headers === "object") {
        const headerNames = Object.keys(finding.evidence.headers);
        if (headerNames.length > 0) {
          if (headerNames.length <= 3) {
            return `${headerNames.length} headers: ${headerNames.join(", ")}`;
          }
          return `${headerNames.length} security headers configured`;
        }
      }
    }

    // Default formatting for other categories
    try {
      const evidenceStr = Object.entries(finding.evidence)
        .filter(([key]) => key !== "job_id") // Exclude job_id from preview
        .slice(0, 2)
        .map(([key, value]) => {
          if (typeof value === "object") {
            return `${key}: ${JSON.stringify(value).substring(0, 50)}...`;
          }
          const strValue = String(value);
          return `${key}: ${strValue.substring(0, 50)}${strValue.length > 50 ? "..." : ""}`;
        })
        .join(", ");

      return evidenceStr || "Evidence available";
    } catch {
      return "Evidence available";
    }
  };

  return (
    <GlassCard
      className={cn(
        "cursor-pointer transition-all duration-300",
        "hover:translate-y-[-2px] hover:scale-[1.02]",
        styles.bg,
        styles.border,
        isSelected && styles.glow,
        onClick && "hover:border-amber-500/50"
      )}
      hover={false}
      onClick={onClick}
      padding="md"
    >
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant={finding.severity} size="sm">
              {finding.severity}
            </Badge>
            <Badge variant="default" size="sm" icon={<span>{categoryIcons[finding.category]}</span>}>
              {categoryLabels[finding.category]}
            </Badge>
          </div>
          {finding.riskScore > 0 && (
            <div className={cn("text-xs font-mono px-2 py-1 rounded", styles.bg, styles.text)}>
              {finding.riskScore}
            </div>
          )}
        </div>

        <h3 className="font-mono font-semibold text-white text-sm leading-tight line-clamp-2">
          {finding.title}
        </h3>

        <p className="text-xs text-white/60 line-clamp-3 leading-relaxed">
          {finding.description}
        </p>

        <div className="p-2 rounded-lg bg-black/20 border border-white/5">
          <p className="text-[10px] font-mono text-white/50 line-clamp-2">
            {getEvidencePreview()}
          </p>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-white/40 font-mono">{finding.timestamp}</span>
          {finding.affectedAssets.length > 0 && (
            <span className="text-white/40">
              {finding.affectedAssets.length} asset{finding.affectedAssets.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>
    </GlassCard>
  );
}

