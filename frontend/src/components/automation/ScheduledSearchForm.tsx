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
    capability: string;
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
  const [capability, setCapability] = useState("exposure_discovery");
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
      setCapability(search.capability);
      setTarget(search.target);
      setCronExpression(search.cron_expression);
      setTimezone(search.timezone);
      setEnabled(search.enabled);
    }
  }, [search]);

  const getTargetPlaceholder = () => {
    const cap = capabilities.find((c) => c.value === capability);
    return cap?.targetPlaceholder || "Enter target...";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (search) {
        await api.updateScheduledSearch(search.id, {
          name,
          description: description || undefined,
          target,
          cron_expression: cronExpression,
          timezone,
          enabled,
        });
      } else {
        await api.createScheduledSearch({
          name,
          description: description || undefined,
          capability,
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
    <GlassCard className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">
          {search ? "Edit Scheduled Search" : "Create Scheduled Search"}
        </h2>
        <GlassButton onClick={onClose} variant="secondary" size="sm">
          Cancel
        </GlassButton>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded text-red-200">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
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
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Description
          </label>
          <GlassInput
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional description"
          />
        </div>

        {!search && (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Capability *
            </label>
            <GlassSelect
              value={capability}
              onChange={setCapability}
              options={capabilities.map((cap) => ({
                value: cap.value,
                label: cap.label,
              }))}
            />
          </div>
        )}

        {search && (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Capability
            </label>
            <GlassInput
              type="text"
              value={capabilities.find((c) => c.value === capability)?.label || capability}
              disabled
              className="opacity-50"
            />
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Target *
          </label>
          <GlassInput
            type="text"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder={getTargetPlaceholder()}
            required
          />
          <p className="text-xs text-gray-400 mt-1">
            {capability === "dark_web_intelligence"
              ? "Enter keywords separated by commas"
              : capability === "infrastructure_testing"
              ? "Enter full URL (e.g., https://example.com)"
              : "Enter domain name"}
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Schedule *
          </label>
          <CronExpressionBuilder
            value={cronExpression}
            onChange={setCronExpression}
            timezone={timezone}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
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

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="enabled"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="enabled" className="text-sm text-gray-300">
            Enable this scheduled search
          </label>
        </div>

        <div className="flex gap-3 pt-4">
          <GlassButton type="submit" disabled={loading} className="flex-1">
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
  );
}

