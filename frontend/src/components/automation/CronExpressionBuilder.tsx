"use client";

import { useState, useEffect } from "react";
import { GlassCard, GlassButton, GlassInput, GlassSelect } from "@/components/ui";

interface CronExpressionBuilderProps {
  value: string;
  onChange: (cronExpression: string) => void;
  timezone?: string;
}

const presets = [
  { label: "Every minute", value: "* * * * *" },
  { label: "Every hour", value: "0 * * * *" },
  { label: "Every day at midnight", value: "0 0 * * *" },
  { label: "Every day at 9 AM", value: "0 9 * * *" },
  { label: "Every day at noon", value: "0 12 * * *" },
  { label: "Every day at 6 PM", value: "0 18 * * *" },
  { label: "Every Monday at 9 AM", value: "0 9 * * 1" },
  { label: "Every weekday at 9 AM", value: "0 9 * * 1-5" },
  { label: "Every Sunday at midnight", value: "0 0 * * 0" },
  { label: "First day of month at midnight", value: "0 0 1 * *" },
];

export default function CronExpressionBuilder({
  value,
  onChange,
  timezone = "UTC",
}: CronExpressionBuilderProps) {
  const [usePreset, setUsePreset] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState("");
  const [customExpression, setCustomExpression] = useState(value || "0 9 * * *");
  const [parts, setParts] = useState({
    minute: "0",
    hour: "9",
    day: "*",
    month: "*",
    weekday: "*",
  });

  useEffect(() => {
    if (value) {
      const cronParts = value.split(" ");
      if (cronParts.length === 5) {
        setParts({
          minute: cronParts[0],
          hour: cronParts[1],
          day: cronParts[2],
          month: cronParts[3],
          weekday: cronParts[4],
        });
        setCustomExpression(value);
      }
    }
  }, [value]);

  const handlePresetChange = (presetValue: string) => {
    setSelectedPreset(presetValue);
    setCustomExpression(presetValue);
    onChange(presetValue);
  };

  const handlePartChange = (part: keyof typeof parts, newValue: string) => {
    const newParts = { ...parts, [part]: newValue };
    setParts(newParts);
    const expression = `${newParts.minute} ${newParts.hour} ${newParts.day} ${newParts.month} ${newParts.weekday}`;
    setCustomExpression(expression);
    onChange(expression);
  };

  const handleCustomChange = (newValue: string) => {
    setCustomExpression(newValue);
    onChange(newValue);
  };

  return (
    <GlassCard className="p-4 overflow-visible">
      <div className="space-y-4">
        <div>
          <label className="block text-xs font-mono text-white/70 mb-2">
            Schedule Type
          </label>
          <div className="flex gap-2">
            <GlassButton
              size="sm"
              variant={usePreset ? "secondary" : "primary"}
              onClick={() => setUsePreset(false)}
            >
              Custom Cron
            </GlassButton>
            <GlassButton
              size="sm"
              variant={usePreset ? "primary" : "secondary"}
              onClick={() => setUsePreset(true)}
            >
              Preset
            </GlassButton>
          </div>
        </div>

        {usePreset ? (
          <div className="relative">
            <label className="block text-xs font-mono text-white/70 mb-2">
              Select Preset Schedule
            </label>
            <GlassSelect
              value={selectedPreset || customExpression}
              onChange={handlePresetChange}
              options={[
                { value: "", label: "Select a preset..." },
                ...presets.map((preset) => ({
                  value: preset.value,
                  label: preset.label,
                })),
              ]}
            />
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-white/70 mb-2">
                Custom Cron Expression
              </label>
              <GlassInput
                type="text"
                value={customExpression}
                onChange={(e) => handleCustomChange(e.target.value)}
                placeholder="0 9 * * *"
                className="font-mono"
              />
              <p className="text-xs text-white/40 mt-1 font-mono">
                Format: minute hour day month weekday (e.g., "0 9 * * *" = daily at 9 AM)
              </p>
            </div>

            <div className="grid grid-cols-5 gap-2">
              <div>
                <label className="block text-xs font-mono text-white/50 mb-1">Minute</label>
                <GlassInput
                  type="text"
                  value={parts.minute}
                  onChange={(e) => handlePartChange("minute", e.target.value)}
                  placeholder="0-59"
                  className="text-sm font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-white/50 mb-1">Hour</label>
                <GlassInput
                  type="text"
                  value={parts.hour}
                  onChange={(e) => handlePartChange("hour", e.target.value)}
                  placeholder="0-23"
                  className="text-sm font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-white/50 mb-1">Day</label>
                <GlassInput
                  type="text"
                  value={parts.day}
                  onChange={(e) => handlePartChange("day", e.target.value)}
                  placeholder="1-31"
                  className="text-sm font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-white/50 mb-1">Month</label>
                <GlassInput
                  type="text"
                  value={parts.month}
                  onChange={(e) => handlePartChange("month", e.target.value)}
                  placeholder="1-12"
                  className="text-sm font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-white/50 mb-1">Weekday</label>
                <GlassInput
                  type="text"
                  value={parts.weekday}
                  onChange={(e) => handlePartChange("weekday", e.target.value)}
                  placeholder="0-6"
                  className="text-sm font-mono"
                />
              </div>
            </div>
          </div>
        )}

        <div className="pt-2 border-t border-white/10">
          <p className="text-xs font-mono text-white/50">
            Current expression: <code className="text-white">{customExpression}</code>
          </p>
          <p className="text-xs font-mono text-white/50 mt-1">Timezone: {timezone}</p>
        </div>
      </div>
    </GlassCard>
  );
}

