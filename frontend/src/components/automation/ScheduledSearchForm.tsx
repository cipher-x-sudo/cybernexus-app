"use client";

import { useState, useEffect } from "react";
import { GlassCard, GlassButton, GlassInput, GlassSelect } from "@/components/ui";
import { api } from "@/lib/api";
import CronExpressionBuilder from "./CronExpressionBuilder";

interface ScheduledSearchFormProps {
  search?: {
    id: string;
    name: string;
    description: string | null;
    capabilities: string[];
    target: string;
    config: Record<string, any>;
    cron_expression: string;
    timezone: string;
    enabled: boolean;
  } | null;
  onClose: () => void;
}

const capabilities = [
  { value: "exposure_discovery", label: "Exposure Discovery", targetPlaceholder: "example.com" },
  { value: "dark_web_intelligence", label: "Dark Web Intelligence", targetPlaceholder: "keyword1, keyword2, brand name" },
  { value: "email_security", label: "Email Security", targetPlaceholder: "example.com" },
  { value: "infrastructure_testing", label: "Infrastructure Testing", targetPlaceholder: "https://example.com" },
];

const timezones = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Asia/Tokyo",
  "Asia/Shanghai",
  "Australia/Sydney",
];

export default function ScheduledSearchForm({ search, onClose }: ScheduledSearchFormProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedCapabilities, setSelectedCapabilities] = useState<string[]>(["exposure_discovery"]);
  const [target, setTarget] = useState("");
  const [cronExpression, setCronExpression] = useState("0 9 * * *");
  const [timezone, setTimezone] = useState("UTC");
  const [enabled, setEnabled] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (search) {
      setName(search.name);
      setDescription(search.description || "");
      setSelectedCapabilities(search.capabilities || []);
      setTarget(search.target);
      setCronExpression(search.cron_expression);
      setTimezone(search.timezone);
      setEnabled(search.enabled);
    }
  }, [search]);

  const handleCapabilityToggle = (capValue: string) => {
    setSelectedCapabilities((prev) => {
      if (prev.includes(capValue)) {
        // Don't allow deselecting if it's the last one
        if (prev.length === 1) {
          return prev;
        }
        return prev.filter((c) => c !== capValue);
      } else {
        return [...prev, capValue];
      }
    });
  };

  const getTargetPlaceholder = () => {
    // If multiple capabilities, show generic placeholder
    if (selectedCapabilities.length > 1) {
      return "Enter target (e.g., example.com, keywords, or URL)";
    }
    const cap = capabilities.find((c) => c.value === selectedCapabilities[0]);
    return cap?.targetPlaceholder || "Enter target...";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (selectedCapabilities.length === 0) {
        setError("Please select at least one capability");
        setLoading(false);
        return;
      }

      if (search) {
        await api.updateScheduledSearch(search.id, {
          name,
          description: description || undefined,
          capabilities: selectedCapabilities,
          target,
          cron_expression: cronExpression,
          timezone,
          enabled,
        });
      } else {
        await api.createScheduledSearch({
          name,
          description: description || undefined,
          capabilities: selectedCapabilities,
          target,
          cron_expression: cronExpression,
          timezone,
          enabled,
        });
      }
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to save scheduled search");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
              <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
            </div>
            <h1 className="text-2xl font-mono font-bold text-white">
              {search ? "Edit Scheduled Search" : "Create Scheduled Search"}
            </h1>
          </div>
          <p className="text-sm text-white/50 mt-1">
            {search ? "Update your scheduled search configuration" : "Configure a new automated search"}
          </p>
        </div>
        <GlassButton onClick={onClose} variant="secondary" size="sm">
          Cancel
        </GlassButton>
      </div>

      <GlassCard className="p-6">

      {error && (
        <GlassCard className="p-4 border-red-500/20">
          <p className="text-red-400 font-mono text-sm">{error}</p>
        </GlassCard>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-xs font-mono text-white/70 mb-2">
            Name *
          </label>
          <GlassInput
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Daily exposure scan for example.com"
            required
          />
        </div>

        <div>
          <label className="block text-xs font-mono text-white/70 mb-2">
            Description
          </label>
          <GlassInput
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional description"
          />
        </div>

        <div>
          <label className="block text-xs font-mono text-white/70 mb-2">
            Capabilities * (Select one or more)
          </label>
          <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
            {capabilities.map((cap) => (
              <label
                key={cap.value}
                className="flex items-center gap-2 cursor-pointer group"
              >
                <input
                  type="checkbox"
                  checked={selectedCapabilities.includes(cap.value)}
                  onChange={() => handleCapabilityToggle(cap.value)}
                  disabled={selectedCapabilities.length === 1 && selectedCapabilities.includes(cap.value)}
                  className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500 focus:ring-amber-500 disabled:opacity-50"
                />
                <span className="text-sm text-white/60 group-hover:text-white/80 font-mono">
                  {cap.label}
                </span>
              </label>
            ))}
          </div>
          {selectedCapabilities.length === 0 && (
            <p className="text-xs text-red-400 mt-1 font-mono">Please select at least one capability</p>
          )}
        </div>

        <div>
          <label className="block text-xs font-mono text-white/70 mb-2">
            Target *
          </label>
          <GlassInput
            type="text"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder={getTargetPlaceholder()}
            required
          />
          <p className="text-xs text-white/40 mt-1 font-mono">
            {selectedCapabilities.includes("dark_web_intelligence")
              ? "Enter keywords separated by commas"
              : selectedCapabilities.includes("infrastructure_testing")
              ? "Enter full URL (e.g., https://example.com)"
              : "Enter domain name"}
          </p>
        </div>

        <div>
          <label className="block text-xs font-mono text-white/70 mb-2">
            Schedule *
          </label>
          <CronExpressionBuilder
            value={cronExpression}
            onChange={setCronExpression}
            timezone={timezone}
          />
        </div>

        <div>
          <label className="block text-xs font-mono text-white/70 mb-2">
            Timezone *
          </label>
          <GlassSelect
            value={timezone}
            onChange={setTimezone}
            options={timezones.map((tz) => ({
              value: tz,
              label: tz,
            }))}
          />
        </div>

        <label className="flex items-center gap-2 cursor-pointer group">
          <input
            type="checkbox"
            id="enabled"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500 focus:ring-amber-500"
          />
          <span className="text-xs text-white/60 group-hover:text-white/80 font-mono">
            Enable this scheduled search
          </span>
        </label>

        <div className="flex gap-3 pt-4 border-t border-white/[0.05]">
          <GlassButton type="submit" disabled={loading} variant="primary" className="flex-1">
            {loading ? "Saving..." : search ? "Update" : "Create"}
          </GlassButton>
          <GlassButton
            type="button"
            onClick={onClose}
            variant="secondary"
            className="flex-1"
          >
            Cancel
          </GlassButton>
        </div>
      </form>
      </GlassCard>
    </div>
  );
}

