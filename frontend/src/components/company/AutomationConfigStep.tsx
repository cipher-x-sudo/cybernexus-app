"use client";

import { useState, useEffect } from "react";
import { GlassCard, GlassButton, GlassInput } from "@/components/ui";
import SchedulePicker from "@/components/automation/SchedulePicker";
import { cn } from "@/lib/utils";

interface AutomationCapabilityConfig {
  enabled: boolean;
  targets?: string[];
  keywords?: string[];
  config?: Record<string, any>;
}

interface AutomationConfig {
  enabled: boolean;
  schedule: {
    cron: string;
    timezone: string;
  };
  capabilities: {
    [key: string]: AutomationCapabilityConfig;
  };
}

interface AutomationConfigStepProps {
  value: AutomationConfig | null;
  onChange: (config: AutomationConfig) => void;
  profileData: {
    name?: string;
    primary_domain?: string;
    additional_domains?: string[];
    key_assets?: Array<{ type: string; value: string; name: string }>;
    timezone?: string;
  };
}

const CAPABILITY_INFO = [
  {
    id: "exposure_discovery",
    name: "Exposure Discovery",
    description: "Scan domains for exposed assets, endpoints, and vulnerabilities",
    icon: "🔍",
    autoTargetFrom: ["primary_domain", "additional_domains"],
  },
  {
    id: "darkweb_intelligence",
    name: "Dark Web Intelligence",
    description: "Monitor dark web for brand mentions, credentials, and threats",
    icon: "🕵️",
    autoTargetFrom: ["company_name", "primary_domain"],
    supportsKeywords: true,
  },
  {
    id: "email_audit",
    name: "Email Security Audit",
    description: "Analyze email security configurations (SPF, DKIM, DMARC)",
    icon: "✉️",
    autoTargetFrom: ["primary_domain", "additional_domains"],
  },
  {
    id: "infrastructure_testing",
    name: "Infrastructure Testing",
    description: "Test infrastructure for misconfigurations and vulnerabilities",
    icon: "🏗️",
    autoTargetFrom: ["key_assets_urls"],
    supportsConfig: true,
  },
  {
    id: "investigation",
    name: "Investigation",
    description: "Capture and analyze web pages for threats",
    icon: "🔬",
    autoTargetFrom: ["key_assets_urls"],
  },
];

export default function AutomationConfigStep({
  value,
  onChange,
  profileData,
}: AutomationConfigStepProps) {
  const [config, setConfig] = useState<AutomationConfig>(
    value || {
      enabled: true,
      schedule: {
        cron: "0 9 * * *",
        timezone: profileData.timezone || "UTC",
      },
      capabilities: {},
    }
  );

  const autoPopulateTargets = (capabilityId: string): string[] => {
    const capability = CAPABILITY_INFO.find((c) => c.id === capabilityId);
    if (!capability) return [];

    const targets: string[] = [];

    capability.autoTargetFrom?.forEach((source) => {
      switch (source) {
        case "primary_domain":
          if (profileData.primary_domain) {
            targets.push(profileData.primary_domain);
          }
          break;
        case "additional_domains":
          if (profileData.additional_domains) {
            targets.push(...profileData.additional_domains);
          }
          break;
        case "company_name":
          if (profileData.name) {
            targets.push(profileData.name);
          }
          break;
        case "key_assets_urls":
          if (profileData.key_assets) {
            profileData.key_assets.forEach((asset) => {
              if (["domain", "url", "server"].includes(asset.type)) {
                let value = asset.value;
                if (asset.type === "domain" && !value.startsWith("http")) {
                  value = `https://${value}`;
                }
                targets.push(value);
              }
            });
          }
          break;
      }
    });

    return Array.from(new Set(targets));
  };

  const toggleCapability = (capabilityId: string, enabled: boolean) => {
    const newCapabilities = { ...config.capabilities };

    if (enabled) {
      const autoTargets = autoPopulateTargets(capabilityId);
      const capability = CAPABILITY_INFO.find((c) => c.id === capabilityId);

      newCapabilities[capabilityId] = {
        enabled: true,
        targets: autoTargets,
        keywords: capability?.supportsKeywords
          ? [profileData.name || "", profileData.primary_domain || ""].filter(Boolean)
          : undefined,
        config: capability?.supportsConfig ? {} : undefined,
      };
    } else {
      delete newCapabilities[capabilityId];
    }

    const newConfig = { ...config, capabilities: newCapabilities };
    setConfig(newConfig);
    onChange(newConfig);
  };

  const updateCapabilityTargets = (capabilityId: string, targets: string[]) => {
    const newCapabilities = { ...config.capabilities };
    if (newCapabilities[capabilityId]) {
      newCapabilities[capabilityId] = {
        ...newCapabilities[capabilityId],
        targets,
      };
      const newConfig = { ...config, capabilities: newCapabilities };
      setConfig(newConfig);
      onChange(newConfig);
    }
  };

  const updateCapabilityKeywords = (capabilityId: string, keywords: string[]) => {
    const newCapabilities = { ...config.capabilities };
    if (newCapabilities[capabilityId]) {
      newCapabilities[capabilityId] = {
        ...newCapabilities[capabilityId],
        keywords,
      };
      const newConfig = { ...config, capabilities: newCapabilities };
      setConfig(newConfig);
      onChange(newConfig);
    }
  };

  const addTarget = (capabilityId: string) => {
    const current = config.capabilities[capabilityId]?.targets || [];
    updateCapabilityTargets(capabilityId, [...current, ""]);
  };

  const removeTarget = (capabilityId: string, index: number) => {
    const current = config.capabilities[capabilityId]?.targets || [];
    updateCapabilityTargets(
      capabilityId,
      current.filter((_, i) => i !== index)
    );
  };

  const updateTarget = (capabilityId: string, index: number, value: string) => {
    const current = config.capabilities[capabilityId]?.targets || [];
    const updated = [...current];
    updated[index] = value;
    updateCapabilityTargets(capabilityId, updated);
  };

  const addKeyword = (capabilityId: string) => {
    const current = config.capabilities[capabilityId]?.keywords || [];
    updateCapabilityKeywords(capabilityId, [...current, ""]);
  };

  const removeKeyword = (capabilityId: string, index: number) => {
    const current = config.capabilities[capabilityId]?.keywords || [];
    updateCapabilityKeywords(
      capabilityId,
      current.filter((_, i) => i !== index)
    );
  };

  const updateKeyword = (capabilityId: string, index: number, value: string) => {
    const current = config.capabilities[capabilityId]?.keywords || [];
    const updated = [...current];
    updated[index] = value;
    updateCapabilityKeywords(capabilityId, updated);
  };

  const enabledCount = Object.keys(config.capabilities).length;

  return (
    <div className="space-y-6">
      <GlassCard className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-mono text-white mb-1">Enable Automation</h3>
            <p className="text-sm text-white/50">
              Automatically run security scans on a schedule
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              const newConfig = { ...config, enabled: !config.enabled };
              setConfig(newConfig);
              onChange(newConfig);
            }}
            className={cn(
              "relative inline-flex h-8 w-14 items-center rounded-full transition-colors",
              config.enabled ? "bg-amber-500" : "bg-white/10"
            )}
          >
            <span
              className={cn(
                "inline-block h-6 w-6 transform rounded-full bg-white transition-transform",
                config.enabled ? "translate-x-7" : "translate-x-1"
              )}
            />
          </button>
        </div>
      </GlassCard>

      {config.enabled && (
        <>
          <GlassCard className="p-6">
            <h3 className="text-lg font-mono text-white mb-4">Schedule</h3>
            <SchedulePicker
              value={config.schedule}
              onChange={(schedule) => {
                const newConfig = { ...config, schedule };
                setConfig(newConfig);
                onChange(newConfig);
              }}
            />
          </GlassCard>

          <GlassCard className="p-6">
            <div className="mb-4">
              <h3 className="text-lg font-mono text-white mb-1">Select Capabilities</h3>
              <p className="text-sm text-white/50">
                Choose which security capabilities to run automatically ({enabledCount} selected)
              </p>
            </div>

            <div className="space-y-4">
              {CAPABILITY_INFO.map((capability) => {
                const isEnabled = !!config.capabilities[capability.id];
                const capConfig = config.capabilities[capability.id];

                return (
                  <div
                    key={capability.id}
                    className={cn(
                      "p-4 rounded-xl border transition-all",
                      isEnabled
                        ? "bg-amber-500/5 border-amber-500/30"
                        : "bg-white/[0.02] border-white/[0.08]"
                    )}
                  >
                    <div className="flex items-start gap-3 mb-3">
                      <input
                        type="checkbox"
                        checked={isEnabled}
                        onChange={(e) => toggleCapability(capability.id, e.target.checked)}
                        className="mt-1 h-5 w-5 rounded border-white/20 bg-white/5 text-amber-500 focus:ring-amber-500/50"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xl">{capability.icon}</span>
                          <h4 className="font-mono text-white">{capability.name}</h4>
                        </div>
                        <p className="text-sm text-white/50">{capability.description}</p>
                      </div>
                    </div>

                    {isEnabled && capConfig && (
                      <div className="ml-8 space-y-3 mt-4 pt-4 border-t border-white/[0.08]">
                        {capConfig.targets !== undefined && (
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <label className="text-sm font-mono text-white/70">
                                Targets to Scan
                              </label>
                              <button
                                type="button"
                                onClick={() => addTarget(capability.id)}
                                className="text-xs text-amber-400 hover:text-amber-300"
                              >
                                + Add
                              </button>
                            </div>
                            {capConfig.targets.length === 0 && (
                              <p className="text-xs text-white/40 mb-2">No targets configured</p>
                            )}
                            {capConfig.targets.map((target, idx) => (
                              <div key={idx} className="flex gap-2 mb-2">
                                <input
                                  type="text"
                                  value={target}
                                  onChange={(e) =>
                                    updateTarget(capability.id, idx, e.target.value)
                                  }
                                  placeholder={
                                    capability.id.includes("infrastructure") ||
                                    capability.id.includes("investigation")
                                      ? "https://example.com"
                                      : "example.com"
                                  }
                                  className={cn(
                                    "flex-1 px-3 py-2 rounded-lg text-sm",
                                    "bg-white/[0.03] border border-white/[0.08]",
                                    "text-white font-mono",
                                    "focus:outline-none focus:border-amber-500/40"
                                  )}
                                />
                                <button
                                  type="button"
                                  onClick={() => removeTarget(capability.id, idx)}
                                  className="px-3 py-2 text-white/50 hover:text-white/70"
                                >
                                  ×
                                </button>
                              </div>
                            ))}
                          </div>
                        )}

                        {capability.supportsKeywords && capConfig.keywords !== undefined && (
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <label className="text-sm font-mono text-white/70">
                                Keywords to Monitor
                              </label>
                              <button
                                type="button"
                                onClick={() => addKeyword(capability.id)}
                                className="text-xs text-amber-400 hover:text-amber-300"
                              >
                                + Add
                              </button>
                            </div>
                            {capConfig.keywords.length === 0 && (
                              <p className="text-xs text-white/40 mb-2">No keywords configured</p>
                            )}
                            {capConfig.keywords.map((keyword, idx) => (
                              <div key={idx} className="flex gap-2 mb-2">
                                <input
                                  type="text"
                                  value={keyword}
                                  onChange={(e) =>
                                    updateKeyword(capability.id, idx, e.target.value)
                                  }
                                  placeholder="brand-name, domain.com"
                                  className={cn(
                                    "flex-1 px-3 py-2 rounded-lg text-sm",
                                    "bg-white/[0.03] border border-white/[0.08]",
                                    "text-white font-mono",
                                    "focus:outline-none focus:border-amber-500/40"
                                  )}
                                />
                                <button
                                  type="button"
                                  onClick={() => removeKeyword(capability.id, idx)}
                                  className="px-3 py-2 text-white/50 hover:text-white/70"
                                >
                                  ×
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </GlassCard>

          {enabledCount > 0 && (
            <GlassCard className="p-6 bg-amber-500/5 border-amber-500/20">
              <h3 className="text-lg font-mono text-amber-400 mb-3">Automation Summary</h3>
              <div className="space-y-2 text-sm font-mono">
                <div className="text-white/70">
                  <span className="text-amber-400">{enabledCount}</span> capabilities will run{" "}
                  <span className="text-amber-400">{config.schedule.cron}</span> in{" "}
                  <span className="text-amber-400">{config.schedule.timezone}</span>
                </div>
                <ul className="list-disc list-inside text-white/50 space-y-1 ml-2">
                  {Object.entries(config.capabilities).map(([id, cfg]) => {
                    const cap = CAPABILITY_INFO.find((c) => c.id === id);
                    const targetCount = cfg.targets?.length || 0;
                    const keywordCount = cfg.keywords?.length || 0;
                    return (
                      <li key={id}>
                        {cap?.name}: {targetCount} target{targetCount !== 1 ? "s" : ""}
                        {keywordCount > 0 && `, ${keywordCount} keyword${keywordCount !== 1 ? "s" : ""}`}
                      </li>
                    );
                  })}
                </ul>
              </div>
            </GlassCard>
          )}
        </>
      )}

      {!config.enabled && (
        <GlassCard className="p-6">
          <p className="text-center text-white/50 font-mono text-sm">
            Enable automation to configure automated security scans
          </p>
        </GlassCard>
      )}
    </div>
  );
}

