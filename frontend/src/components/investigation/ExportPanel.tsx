"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";
import { api } from "@/lib/api";

interface ExportPanelProps {
  jobId: string;
  className?: string;
}

export function ExportPanel({ jobId, className }: ExportPanelProps) {
  const [exporting, setExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState<"json" | "html">("json");

  const handleExport = async () => {
    setExporting(true);
    try {
      await api.exportInvestigation(jobId, exportFormat);
    } catch (error) {
      console.error("Export failed:", error);
      alert("Export failed. Please try again.");
    } finally {
      setExporting(false);
    }
  };

  return (
    <GlassCard className={cn("p-6", className)} hover={false}>
      <div className="space-y-4">
        <h3 className="text-lg font-mono font-semibold text-white">Export Investigation</h3>
        
        <div>
          <label className="block text-sm text-white/70 mb-2">Export Format</label>
          <select
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value as "json" | "html")}
            className="w-full px-3 py-2 bg-white/[0.03] border border-white/[0.08] rounded-lg text-white text-sm"
          >
            <option value="json">JSON</option>
            <option value="html">HTML Report</option>
          </select>
        </div>

        <div className="text-sm text-white/50">
          <p>Export includes:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>All findings</li>
            <li>Capture metadata</li>
            <li>Domain tree structure</li>
            <li>Risk assessment</li>
          </ul>
        </div>

        <button
          onClick={handleExport}
          disabled={exporting}
          className="w-full px-4 py-2 bg-orange-500/20 border border-orange-500/40 text-orange-400 rounded-lg hover:bg-orange-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {exporting ? "Exporting..." : `Export as ${exportFormat.toUpperCase()}`}
        </button>
      </div>
    </GlassCard>
  );
}

