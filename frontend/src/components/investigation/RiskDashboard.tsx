"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";

interface RiskDashboardProps {
  riskScore: number;
  riskLevel: string;
  riskFactors: string[];
  thirdPartyCount: number;
  trackerCount: number;
  totalDomains: number;
  className?: string;
}

export function RiskDashboard({
  riskScore,
  riskLevel,
  riskFactors,
  thirdPartyCount,
  trackerCount,
  totalDomains,
  className,
}: RiskDashboardProps) {
  const getRiskColor = (score: number) => {
    if (score >= 70) return "text-red-400";
    if (score >= 50) return "text-orange-400";
    if (score >= 30) return "text-yellow-400";
    return "text-green-400";
  };

  const getRiskBgColor = (score: number) => {
    if (score >= 70) return "bg-red-500/10 border-red-500/40";
    if (score >= 50) return "bg-orange-500/10 border-orange-500/40";
    if (score >= 30) return "bg-yellow-500/10 border-yellow-500/40";
    return "bg-green-500/10 border-green-500/40";
  };

  // Calculate gauge angle (0-180 degrees for semicircle)
  const gaugeAngle = (riskScore / 100) * 180;

  return (
    <GlassCard className={cn("p-6", className)} hover={false}>
      <div className="space-y-6">
        <div className="text-center">
          <h3 className="text-lg font-mono font-semibold text-white mb-4">Risk Score</h3>
          <div className="relative w-48 h-24 mx-auto">
            <svg viewBox="0 0 200 100" className="w-full h-full">
              <path
                d="M 20 80 A 80 80 0 0 1 180 80"
                fill="none"
                stroke="rgba(255,255,255,0.1)"
                strokeWidth="20"
                strokeLinecap="round"
              />
              <path
                d="M 20 80 A 80 80 0 0 1 180 80"
                fill="none"
                stroke={riskScore >= 70 ? "#ef4444" : riskScore >= 50 ? "#f97316" : "#eab308"}
                strokeWidth="20"
                strokeLinecap="round"
                strokeDasharray={`${(gaugeAngle / 180) * 251.2} 251.2`}
                transform="rotate(-90 100 100)"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className={cn("text-4xl font-bold", getRiskColor(riskScore))}>
                  {Math.round(riskScore)}
                </div>
                <div className="text-sm text-white/50">/ 100</div>
              </div>
            </div>
          </div>
          <div className={cn("mt-2 px-3 py-1 rounded text-sm font-mono", getRiskBgColor(riskScore))}>
            {riskLevel.toUpperCase()}
          </div>
        </div>

        {/* Statistics Grid */}
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 bg-white/[0.02] border border-white/[0.08] rounded-lg text-center">
            <div className="text-2xl font-bold text-white">{totalDomains}</div>
            <div className="text-xs text-white/50 mt-1">Total Domains</div>
          </div>
          <div className="p-4 bg-white/[0.02] border border-white/[0.08] rounded-lg text-center">
            <div className="text-2xl font-bold text-amber-400">{thirdPartyCount}</div>
            <div className="text-xs text-white/50 mt-1">Third Party</div>
          </div>
          <div className="p-4 bg-white/[0.02] border border-white/[0.08] rounded-lg text-center">
            <div className="text-2xl font-bold text-red-400">{trackerCount}</div>
            <div className="text-xs text-white/50 mt-1">Trackers</div>
          </div>
        </div>

        {riskFactors.length > 0 && (
          <div>
            <h4 className="text-sm font-mono font-semibold text-white mb-2">Risk Factors</h4>
            <div className="space-y-2">
              {riskFactors.map((factor, idx) => (
                <div
                  key={idx}
                  className="p-2 bg-white/[0.02] border border-white/[0.08] rounded text-sm text-white/70"
                >
                  • {factor}
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <h4 className="text-sm font-mono font-semibold text-white mb-2">Recommendations</h4>
          <div className="space-y-2 text-sm text-white/70">
            {riskScore >= 70 && (
              <div className="p-2 bg-red-500/10 border border-red-500/30 rounded">
                ⚠️ High risk detected. Immediate review recommended.
              </div>
            )}
            {trackerCount > 5 && (
              <div className="p-2 bg-amber-500/10 border border-amber-500/30 rounded">
                Consider implementing tracking protection.
              </div>
            )}
            {thirdPartyCount > 10 && (
              <div className="p-2 bg-blue-500/10 border border-blue-500/30 rounded">
                Review third-party dependencies for security risks.
              </div>
            )}
            {riskScore < 30 && (
              <div className="p-2 bg-green-500/10 border border-green-500/30 rounded">
                ✓ Low risk profile. Continue monitoring.
              </div>
            )}
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

