"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";
import { GlassButton } from "@/components/ui/glass-button";

interface QuickStartProps {
  onScan?: (domain: string) => void;
  className?: string;
}

export function QuickStart({ onScan, className }: QuickStartProps) {
  const [domain, setDomain] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!domain.trim()) return;

    setIsScanning(true);
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    if (onScan) {
      onScan(domain);
    }
    
    setIsScanning(false);
  };

  return (
    <GlassCard 
      className={cn("p-6 border-amber-500/20", className)}
      variant="strong"
      hover={false}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="font-mono text-lg font-semibold text-white mb-1">
            Quick Security Assessment
          </h2>
          <p className="text-sm text-white/50">
            Enter your domain to start a comprehensive security scan
          </p>
        </div>
        <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
          <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <input
            type="text"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="example.com"
            disabled={isScanning}
            className={cn(
              "w-full h-12 px-4 pr-32",
              "bg-white/[0.03] border border-white/[0.08] rounded-xl",
              "text-white placeholder-white/30",
              "font-mono text-sm",
              "focus:outline-none focus:border-amber-500/40 focus:ring-1 focus:ring-amber-500/20",
              "transition-all duration-200",
              "disabled:opacity-50"
            )}
          />
          <GlassButton
            type="submit"
            variant="primary"
            size="sm"
            loading={isScanning}
            className="absolute right-2 top-1/2 -translate-y-1/2"
          >
            {isScanning ? "Scanning..." : "Start Scan"}
          </GlassButton>
        </div>

        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-1.5 text-xs text-white/40 hover:text-white/60 transition-colors"
        >
          <svg 
            className={cn("w-4 h-4 transition-transform", showAdvanced && "rotate-90")} 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className="font-mono">Advanced options</span>
        </button>

        {showAdvanced && (
          <div className="space-y-3 p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] animate-fade-in">
            <div className="grid grid-cols-2 gap-3">
              <label className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500 focus:ring-amber-500/20"
                />
                <span className="text-xs text-white/60 group-hover:text-white/80">Email Security</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500 focus:ring-amber-500/20"
                />
                <span className="text-xs text-white/60 group-hover:text-white/80">Exposure Discovery</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500 focus:ring-amber-500/20"
                />
                <span className="text-xs text-white/60 group-hover:text-white/80">Infrastructure</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500 focus:ring-amber-500/20"
                />
                <span className="text-xs text-white/60 group-hover:text-white/80">Dark Web (slower)</span>
              </label>
            </div>
          </div>
        )}
      </form>

      <div className="mt-4 pt-4 border-t border-white/[0.05]">
        <p className="text-xs text-white/40 mb-2 font-mono">This scan will check:</p>
        <div className="flex flex-wrap gap-2">
          {["SPF/DKIM/DMARC", "Exposed data", "Misconfigurations", "Public assets"].map((item) => (
            <span
              key={item}
              className="px-2 py-1 text-xs font-mono bg-white/[0.03] border border-white/[0.05] rounded-lg text-white/50"
            >
              {item}
            </span>
          ))}
        </div>
      </div>
    </GlassCard>
  );
}

export default QuickStart;



