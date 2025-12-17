"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { GlassCard, GlassSelect, GlassInput } from "@/components/ui";
import { InfrastructureCategory, categoryLabels } from "./helpers";

export type SortOption = "severity" | "date" | "category" | "risk_score";
export type SortDirection = "asc" | "desc";

interface FilterPanelProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  severityFilter: string;
  onSeverityFilterChange: (severity: string) => void;
  categoryFilter: string;
  onCategoryFilterChange: (category: string) => void;
  sortBy: SortOption;
  onSortByChange: (sort: SortOption) => void;
  sortDirection: SortDirection;
  onSortDirectionChange: (direction: SortDirection) => void;
  className?: string;
}

export function FilterPanel({
  searchQuery,
  onSearchChange,
  severityFilter,
  onSeverityFilterChange,
  categoryFilter,
  onCategoryFilterChange,
  sortBy,
  onSortByChange,
  sortDirection,
  onSortDirectionChange,
  className,
}: FilterPanelProps) {
  const severityOptions = [
    { value: "all", label: "All Severities" },
    { value: "critical", label: "Critical" },
    { value: "high", label: "High" },
    { value: "medium", label: "Medium" },
    { value: "low", label: "Low" },
    { value: "info", label: "Info" },
  ];

  const categoryOptions = [
    { value: "all", label: "All Categories" },
    ...Object.entries(categoryLabels).map(([value, label]) => ({
      value,
      label,
    })),
  ];

  const sortOptions = [
    { value: "severity", label: "Severity" },
    { value: "date", label: "Date" },
    { value: "category", label: "Category" },
    { value: "risk_score", label: "Risk Score" },
  ];

  return (
    <GlassCard className={cn("p-4", className)} hover={false} padding="none">
      <div className="space-y-4">
        {/* Search */}
        <div>
          <label className="block text-xs font-mono text-white/60 mb-2">Search</label>
          <GlassInput
            type="text"
            placeholder="Search findings..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full"
          />
        </div>

        {/* Filters Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Severity Filter */}
          <div>
            <label className="block text-xs font-mono text-white/60 mb-2">Severity</label>
            <GlassSelect
              value={severityFilter}
              onChange={onSeverityFilterChange}
              options={severityOptions}
              className="w-full"
            />
          </div>

          {/* Category Filter */}
          <div>
            <label className="block text-xs font-mono text-white/60 mb-2">Category</label>
            <GlassSelect
              value={categoryFilter}
              onChange={onCategoryFilterChange}
              options={categoryOptions}
              className="w-full"
            />
          </div>
        </div>

        {/* Sort Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Sort By */}
          <div>
            <label className="block text-xs font-mono text-white/60 mb-2">Sort By</label>
            <GlassSelect
              value={sortBy}
              onChange={(value) => onSortByChange(value as SortOption)}
              options={sortOptions}
              className="w-full"
            />
          </div>

          {/* Sort Direction */}
          <div>
            <label className="block text-xs font-mono text-white/60 mb-2">Direction</label>
            <GlassSelect
              value={sortDirection}
              onChange={(value) => onSortDirectionChange(value as SortDirection)}
              options={[
                { value: "desc", label: "Descending" },
                { value: "asc", label: "Ascending" },
              ]}
              className="w-full"
            />
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

