"use client";

import React, { useState } from "react";
import { GlassCard, GlassButton } from "@/components/ui";
import { cn } from "@/lib/utils";

interface FilterPanelProps {
  onFilterChange: (filters: any) => void;
  className?: string;
}

export function FilterPanel({ onFilterChange, className }: FilterPanelProps) {
  const [filters, setFilters] = useState({
    ip: "",
    endpoint: "",
    method: "",
    status: "",
    has_tunnel: "",
  });

  const handleChange = (key: string, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const clearFilters = () => {
    const emptyFilters = {
      ip: "",
      endpoint: "",
      method: "",
      status: "",
      has_tunnel: "",
    };
    setFilters(emptyFilters);
    onFilterChange(emptyFilters);
  };

  return (
    <GlassCard className={cn("", className)} hover={false}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-mono text-lg font-semibold text-white">Filters</h2>
        <GlassButton variant="ghost" size="sm" onClick={clearFilters}>
          Clear
        </GlassButton>
      </div>

      <div className="space-y-3">
        <div>
          <label className="block text-xs text-white/50 mb-1">IP Address</label>
          <input
            type="text"
            value={filters.ip}
            onChange={(e) => handleChange("ip", e.target.value)}
            placeholder="192.168.1.1"
            className="w-full h-9 px-3 bg-white/[0.05] border border-white/[0.1] rounded-lg text-sm text-white/80 font-mono"
          />
        </div>

        <div>
          <label className="block text-xs text-white/50 mb-1">Endpoint</label>
          <input
            type="text"
            value={filters.endpoint}
            onChange={(e) => handleChange("endpoint", e.target.value)}
            placeholder="/api/v1/..."
            className="w-full h-9 px-3 bg-white/[0.05] border border-white/[0.1] rounded-lg text-sm text-white/80 font-mono"
          />
        </div>

        <div>
          <label className="block text-xs text-white/50 mb-1">Method</label>
          <select
            value={filters.method}
            onChange={(e) => handleChange("method", e.target.value)}
            className="w-full h-9 px-3 bg-white/[0.05] border border-white/[0.1] rounded-lg text-sm text-white/80 font-mono"
          >
            <option value="">All</option>
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="DELETE">DELETE</option>
            <option value="PATCH">PATCH</option>
          </select>
        </div>

        <div>
          <label className="block text-xs text-white/50 mb-1">Status Code</label>
          <input
            type="number"
            value={filters.status}
            onChange={(e) => handleChange("status", e.target.value)}
            placeholder="200"
            className="w-full h-9 px-3 bg-white/[0.05] border border-white/[0.1] rounded-lg text-sm text-white/80 font-mono"
          />
        </div>

        <div>
          <label className="block text-xs text-white/50 mb-1">Tunnel Detection</label>
          <select
            value={filters.has_tunnel}
            onChange={(e) => handleChange("has_tunnel", e.target.value)}
            className="w-full h-9 px-3 bg-white/[0.05] border border-white/[0.1] rounded-lg text-sm text-white/80 font-mono"
          >
            <option value="">All</option>
            <option value="true">Tunnels Only</option>
            <option value="false">No Tunnels</option>
          </select>
        </div>
      </div>
    </GlassCard>
  );
}





