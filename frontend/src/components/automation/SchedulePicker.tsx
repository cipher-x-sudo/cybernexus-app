"use client";

import { useState, useEffect } from "react";
import { GlassCard } from "@/components/ui/GlassCard";
import { cn } from "@/lib/utils";

interface SchedulePickerProps {
  value: {
    cron: string;
    timezone: string;
  };
  onChange: (schedule: { cron: string; timezone: string }) => void;
  className?: string;
}

type FrequencyType = "daily" | "weekly" | "monthly" | "custom";

const FREQUENCY_OPTIONS: { value: FrequencyType; label: string }[] = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "custom", label: "Custom" },
];

const WEEKDAY_OPTIONS = [
  { value: "0", label: "Sunday" },
  { value: "1", label: "Monday" },
  { value: "2", label: "Tuesday" },
  { value: "3", label: "Wednesday" },
  { value: "4", label: "Thursday" },
  { value: "5", label: "Friday" },
  { value: "6", label: "Saturday" },
];

const TIMEZONE_OPTIONS = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Asia/Tokyo",
  "Asia/Shanghai",
  "Asia/Kolkata",
  "Australia/Sydney",
];

export default function SchedulePicker({ value, onChange, className }: SchedulePickerProps) {
  const [frequency, setFrequency] = useState<FrequencyType>("daily");
  const [hour, setHour] = useState<string>("9");
  const [minute, setMinute] = useState<string>("0");
  const [dayOfWeek, setDayOfWeek] = useState<string>("1");
  const [dayOfMonth, setDayOfMonth] = useState<string>("1");
  const [customCron, setCustomCron] = useState<string>("");
  const [timezone, setTimezone] = useState<string>(value.timezone || "UTC");
  const [nextRuns, setNextRuns] = useState<string[]>([]);

  // Parse initial cron value
  useEffect(() => {
    if (value.cron) {
      const parts = value.cron.split(" ");
      if (parts.length === 5) {
        const [min, hr, dom, mon, dow] = parts;
        setMinute(min);
        setHour(hr);

        // Detect frequency from pattern
        if (dom === "*" && mon === "*" && dow === "*") {
          setFrequency("daily");
        } else if (dom === "*" && mon === "*" && dow !== "*") {
          setFrequency("weekly");
          setDayOfWeek(dow);
        } else if (dom !== "*" && mon === "*") {
          setFrequency("monthly");
          setDayOfMonth(dom);
        } else {
          setFrequency("custom");
          setCustomCron(value.cron);
        }
      }
    }
    setTimezone(value.timezone || "UTC");
  }, [value]);

  // Generate cron expression and notify parent
  useEffect(() => {
    let cronExpression = "";

    switch (frequency) {
      case "daily":
        cronExpression = `${minute} ${hour} * * *`;
        break;
      case "weekly":
        cronExpression = `${minute} ${hour} * * ${dayOfWeek}`;
        break;
      case "monthly":
        cronExpression = `${minute} ${hour} ${dayOfMonth} * *`;
        break;
      case "custom":
        cronExpression = customCron;
        break;
    }

    if (cronExpression && cronExpression !== value.cron) {
      onChange({ cron: cronExpression, timezone });
    }

    // Calculate next runs (simplified - in production use a library like croniter)
    calculateNextRuns(cronExpression);
  }, [frequency, hour, minute, dayOfWeek, dayOfMonth, customCron, timezone]);

  const calculateNextRuns = (cron: string) => {
    // Simplified next run calculation for display
    const parts = cron.split(" ");
    if (parts.length !== 5) {
      setNextRuns([]);
      return;
    }

    const [min, hr] = parts;
    const time = `${hr.padStart(2, "0")}:${min.padStart(2, "0")}`;

    let description = "";
    switch (frequency) {
      case "daily":
        description = `Every day at ${time}`;
        break;
      case "weekly":
        const day = WEEKDAY_OPTIONS.find((d) => d.value === dayOfWeek)?.label || "";
        description = `Every ${day} at ${time}`;
        break;
      case "monthly":
        description = `Day ${dayOfMonth} of every month at ${time}`;
        break;
      case "custom":
        description = `Custom: ${cron}`;
        break;
    }

    setNextRuns([description]);
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Frequency Selector */}
      <div>
        <label className="block text-sm font-mono text-white/70 mb-2">Frequency</label>
        <div className="grid grid-cols-4 gap-2">
          {FREQUENCY_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setFrequency(option.value)}
              className={cn(
                "px-3 py-2 rounded-lg font-mono text-sm transition-all",
                "border",
                frequency === option.value
                  ? "bg-amber-500/20 border-amber-500/40 text-amber-400"
                  : "bg-white/[0.03] border-white/[0.08] text-white/70 hover:bg-white/[0.05]"
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Time Picker */}
      {frequency !== "custom" && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-mono text-white/70 mb-2">Hour (24h)</label>
            <input
              type="number"
              min="0"
              max="23"
              value={hour}
              onChange={(e) => setHour(e.target.value)}
              className={cn(
                "w-full px-3 py-2 rounded-lg",
                "bg-white/[0.03] border border-white/[0.08]",
                "text-white font-mono text-sm",
                "focus:outline-none focus:border-amber-500/40"
              )}
            />
          </div>
          <div>
            <label className="block text-sm font-mono text-white/70 mb-2">Minute</label>
            <input
              type="number"
              min="0"
              max="59"
              value={minute}
              onChange={(e) => setMinute(e.target.value)}
              className={cn(
                "w-full px-3 py-2 rounded-lg",
                "bg-white/[0.03] border border-white/[0.08]",
                "text-white font-mono text-sm",
                "focus:outline-none focus:border-amber-500/40"
              )}
            />
          </div>
        </div>
      )}

      {/* Weekly - Day of Week */}
      {frequency === "weekly" && (
        <div>
          <label className="block text-sm font-mono text-white/70 mb-2">Day of Week</label>
          <select
            value={dayOfWeek}
            onChange={(e) => setDayOfWeek(e.target.value)}
            className={cn(
              "w-full px-3 py-2 rounded-lg",
              "bg-white/[0.03] border border-white/[0.08]",
              "text-white font-mono text-sm",
              "focus:outline-none focus:border-amber-500/40"
            )}
          >
            {WEEKDAY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Monthly - Day of Month */}
      {frequency === "monthly" && (
        <div>
          <label className="block text-sm font-mono text-white/70 mb-2">Day of Month</label>
          <input
            type="number"
            min="1"
            max="31"
            value={dayOfMonth}
            onChange={(e) => setDayOfMonth(e.target.value)}
            className={cn(
              "w-full px-3 py-2 rounded-lg",
              "bg-white/[0.03] border border-white/[0.08]",
              "text-white font-mono text-sm",
              "focus:outline-none focus:border-amber-500/40"
            )}
          />
        </div>
      )}

      {/* Custom Cron */}
      {frequency === "custom" && (
        <div>
          <label className="block text-sm font-mono text-white/70 mb-2">
            Cron Expression
            <span className="ml-2 text-xs text-white/40">(minute hour day month weekday)</span>
          </label>
          <input
            type="text"
            value={customCron}
            onChange={(e) => setCustomCron(e.target.value)}
            placeholder="0 9 * * *"
            className={cn(
              "w-full px-3 py-2 rounded-lg",
              "bg-white/[0.03] border border-white/[0.08]",
              "text-white font-mono text-sm",
              "focus:outline-none focus:border-amber-500/40"
            )}
          />
        </div>
      )}

      {/* Timezone */}
      <div>
        <label className="block text-sm font-mono text-white/70 mb-2">Timezone</label>
        <select
          value={timezone}
          onChange={(e) => {
            setTimezone(e.target.value);
            onChange({ cron: value.cron, timezone: e.target.value });
          }}
          className={cn(
            "w-full px-3 py-2 rounded-lg",
            "bg-white/[0.03] border border-white/[0.08]",
            "text-white font-mono text-sm",
            "focus:outline-none focus:border-amber-500/40"
          )}
        >
          {TIMEZONE_OPTIONS.map((tz) => (
            <option key={tz} value={tz}>
              {tz}
            </option>
          ))}
        </select>
      </div>

      {/* Next Runs Preview */}
      {nextRuns.length > 0 && (
        <div className="p-3 rounded-lg bg-white/[0.03] border border-white/[0.08]">
          <div className="text-xs font-mono text-white/50 mb-1">Schedule Preview</div>
          {nextRuns.map((run, idx) => (
            <div key={idx} className="text-sm font-mono text-amber-400/90">
              {run}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

