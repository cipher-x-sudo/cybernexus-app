"use client";

import { useState } from "react";
import { GlassCard, GlassButton, GlassInput, GlassTextarea, Badge } from "@/components/ui";
import { cn } from "@/lib/utils";

const sections = [
  { id: "profile", label: "Profile", icon: "👤" },
  { id: "notifications", label: "Notifications", icon: "🔔" },
  { id: "api_keys", label: "API Keys", icon: "🔑" },
  { id: "integrations", label: "Integrations", icon: "🔗" },
  { id: "appearance", label: "Appearance", icon: "🎨" },
  { id: "security", label: "Security", icon: "🔒" },
  { id: "team", label: "Team", icon: "👥" },
];

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState("profile");

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-mono font-bold text-white">Settings</h1>
        <p className="text-sm text-white/50">
          Manage your account and preferences
        </p>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <GlassCard padding="sm" className="lg:col-span-1 h-fit">
          <nav className="space-y-1">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors",
                  activeSection === section.id
                    ? "bg-amber-500/20 text-amber-400"
                    : "text-white/60 hover:bg-white/[0.05] hover:text-white"
                )}
              >
                <span className="text-lg">{section.icon}</span>
                <span className="font-mono text-sm">{section.label}</span>
              </button>
            ))}
          </nav>
        </GlassCard>

        {/* Content */}
        <div className="lg:col-span-3">
          {activeSection === "profile" && <ProfileSection />}
          {activeSection === "notifications" && <NotificationsSection />}
          {activeSection === "api_keys" && <APIKeysSection />}
          {activeSection === "integrations" && <IntegrationsSection />}
          {activeSection === "appearance" && <AppearanceSection />}
          {activeSection === "security" && <SecuritySection />}
          {activeSection === "team" && <TeamSection />}
        </div>
      </div>
    </div>
  );
}

function ProfileSection() {
  return (
    <GlassCard>
      <h2 className="font-mono text-lg text-white mb-6">Profile Settings</h2>
      <div className="space-y-6">
        {/* Avatar */}
        <div className="flex items-center gap-4">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-mono text-2xl font-bold">
            JD
          </div>
          <div>
            <GlassButton variant="secondary" size="sm">
              Upload Photo
            </GlassButton>
            <p className="text-xs text-white/40 mt-2">JPG, PNG. Max 2MB</p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <GlassInput label="First Name" defaultValue="John" />
          <GlassInput label="Last Name" defaultValue="Doe" />
        </div>
        <GlassInput label="Email" type="email" defaultValue="john.doe@company.com" />
        <GlassInput label="Job Title" defaultValue="Security Analyst" />
        <GlassTextarea label="Bio" placeholder="Tell us about yourself..." rows={3} />

        <div className="pt-4 border-t border-white/[0.05] flex justify-end">
          <GlassButton variant="primary">Save Changes</GlassButton>
        </div>
      </div>
    </GlassCard>
  );
}

function NotificationsSection() {
  const [settings, setSettings] = useState({
    email_critical: true,
    email_high: true,
    email_medium: false,
    push_enabled: true,
    sound_enabled: true,
    digest_weekly: true,
  });

  return (
    <GlassCard>
      <h2 className="font-mono text-lg text-white mb-6">Notification Preferences</h2>
      <div className="space-y-6">
        <div>
          <h3 className="font-mono text-sm text-white/70 mb-3">Email Notifications</h3>
          <div className="space-y-3">
            {[
              { key: "email_critical", label: "Critical threats", desc: "Immediate notification" },
              { key: "email_high", label: "High severity", desc: "Within 1 hour" },
              { key: "email_medium", label: "Medium severity", desc: "Daily digest" },
            ].map((item) => (
              <div key={item.key} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02]">
                <div>
                  <p className="text-sm text-white">{item.label}</p>
                  <p className="text-xs text-white/40">{item.desc}</p>
                </div>
                <button
                  onClick={() => setSettings({ ...settings, [item.key]: !settings[item.key as keyof typeof settings] })}
                  className={cn(
                    "w-12 h-6 rounded-full transition-colors relative",
                    settings[item.key as keyof typeof settings] ? "bg-amber-500" : "bg-white/10"
                  )}
                >
                  <span
                    className={cn(
                      "absolute top-1 w-4 h-4 rounded-full bg-white transition-transform",
                      settings[item.key as keyof typeof settings] ? "translate-x-7" : "translate-x-1"
                    )}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="font-mono text-sm text-white/70 mb-3">Other Settings</h3>
          <div className="space-y-3">
            {[
              { key: "push_enabled", label: "Push notifications", desc: "Browser notifications" },
              { key: "sound_enabled", label: "Sound alerts", desc: "Play sound for critical alerts" },
              { key: "digest_weekly", label: "Weekly digest", desc: "Summary email every Monday" },
            ].map((item) => (
              <div key={item.key} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02]">
                <div>
                  <p className="text-sm text-white">{item.label}</p>
                  <p className="text-xs text-white/40">{item.desc}</p>
                </div>
                <button
                  onClick={() => setSettings({ ...settings, [item.key]: !settings[item.key as keyof typeof settings] })}
                  className={cn(
                    "w-12 h-6 rounded-full transition-colors relative",
                    settings[item.key as keyof typeof settings] ? "bg-amber-500" : "bg-white/10"
                  )}
                >
                  <span
                    className={cn(
                      "absolute top-1 w-4 h-4 rounded-full bg-white transition-transform",
                      settings[item.key as keyof typeof settings] ? "translate-x-7" : "translate-x-1"
                    )}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="pt-4 border-t border-white/[0.05] flex justify-end">
          <GlassButton variant="primary">Save Preferences</GlassButton>
        </div>
      </div>
    </GlassCard>
  );
}

function APIKeysSection() {
  const apiKeys = [
    { id: "1", name: "Production API", key: "cn_prod_...a1b2", created: "2024-01-15", lastUsed: "2 hours ago" },
    { id: "2", name: "Development", key: "cn_dev_...c3d4", created: "2024-02-20", lastUsed: "5 days ago" },
  ];

  return (
    <GlassCard>
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-mono text-lg text-white">API Keys</h2>
        <GlassButton variant="primary" size="sm">
          <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Create Key
        </GlassButton>
      </div>

      <div className="space-y-4">
        {apiKeys.map((key) => (
          <div key={key.id} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-mono text-white">{key.name}</h3>
              <GlassButton variant="ghost" size="sm">Revoke</GlassButton>
            </div>
            <div className="flex items-center gap-2 mb-2">
              <code className="flex-1 p-2 rounded bg-white/[0.03] font-mono text-sm text-white/70">
                {key.key}
              </code>
              <GlassButton variant="ghost" size="sm">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </GlassButton>
            </div>
            <div className="flex items-center gap-4 text-xs text-white/40">
              <span>Created: {key.created}</span>
              <span>Last used: {key.lastUsed}</span>
            </div>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

function IntegrationsSection() {
  const integrations = [
    { name: "Slack", status: "connected", icon: "💬" },
    { name: "Jira", status: "connected", icon: "📋" },
    { name: "Splunk", status: "disconnected", icon: "📊" },
    { name: "PagerDuty", status: "disconnected", icon: "🚨" },
  ];

  return (
    <GlassCard>
      <h2 className="font-mono text-lg text-white mb-6">Integrations</h2>
      <div className="grid md:grid-cols-2 gap-4">
        {integrations.map((integration) => (
          <div
            key={integration.name}
            className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">{integration.icon}</span>
              <div>
                <p className="font-mono text-white">{integration.name}</p>
                <p className={cn(
                  "text-xs",
                  integration.status === "connected" ? "text-emerald-400" : "text-white/40"
                )}>
                  {integration.status === "connected" ? "Connected" : "Not connected"}
                </p>
              </div>
            </div>
            <GlassButton
              variant={integration.status === "connected" ? "ghost" : "secondary"}
              size="sm"
            >
              {integration.status === "connected" ? "Configure" : "Connect"}
            </GlassButton>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

function AppearanceSection() {
  return (
    <GlassCard>
      <h2 className="font-mono text-lg text-white mb-6">Appearance</h2>
      <div className="space-y-6">
        <div>
          <h3 className="font-mono text-sm text-white/70 mb-3">Theme</h3>
          <div className="flex gap-3">
            {[
              { id: "dark", label: "Dark", active: true },
              { id: "light", label: "Light", active: false },
              { id: "system", label: "System", active: false },
            ].map((theme) => (
              <button
                key={theme.id}
                className={cn(
                  "px-4 py-2 rounded-lg font-mono text-sm transition-all",
                  theme.active
                    ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                    : "bg-white/[0.03] text-white/60 border border-white/[0.08]"
                )}
              >
                {theme.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <h3 className="font-mono text-sm text-white/70 mb-3">Accent Color</h3>
          <div className="flex gap-2">
            {["#f59e0b", "#ef4444", "#3b82f6", "#10b981", "#8b5cf6", "#ec4899"].map((color) => (
              <button
                key={color}
                className={cn(
                  "w-8 h-8 rounded-full border-2 transition-transform hover:scale-110",
                  color === "#f59e0b" ? "border-white" : "border-transparent"
                )}
                style={{ backgroundColor: color }}
              />
            ))}
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

function SecuritySection() {
  return (
    <GlassCard>
      <h2 className="font-mono text-lg text-white mb-6">Security</h2>
      <div className="space-y-6">
        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-mono text-white">Two-Factor Authentication</p>
              <p className="text-sm text-white/50">Add an extra layer of security</p>
            </div>
            <Badge variant="success">Enabled</Badge>
          </div>
          <GlassButton variant="ghost" size="sm" className="mt-3">
            Manage 2FA
          </GlassButton>
        </div>

        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
          <p className="font-mono text-white mb-2">Change Password</p>
          <p className="text-sm text-white/50 mb-4">Last changed 30 days ago</p>
          <GlassButton variant="secondary" size="sm">
            Update Password
          </GlassButton>
        </div>

        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
          <p className="font-mono text-white mb-2">Active Sessions</p>
          <p className="text-sm text-white/50 mb-4">3 active sessions</p>
          <GlassButton variant="ghost" size="sm">
            View Sessions
          </GlassButton>
        </div>
      </div>
    </GlassCard>
  );
}

function TeamSection() {
  const members = [
    { name: "John Doe", email: "john@company.com", role: "Admin", avatar: "JD" },
    { name: "Sarah Smith", email: "sarah@company.com", role: "Analyst", avatar: "SS" },
    { name: "Mike Johnson", email: "mike@company.com", role: "Viewer", avatar: "MJ" },
  ];

  return (
    <GlassCard>
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-mono text-lg text-white">Team Members</h2>
        <GlassButton variant="primary" size="sm">
          <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Invite Member
        </GlassButton>
      </div>

      <div className="space-y-3">
        {members.map((member) => (
          <div
            key={member.email}
            className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-mono text-sm font-bold">
                {member.avatar}
              </div>
              <div>
                <p className="font-mono text-white">{member.name}</p>
                <p className="text-sm text-white/50">{member.email}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant={member.role === "Admin" ? "info" : "default"} size="sm">
                {member.role}
              </Badge>
              <GlassButton variant="ghost" size="sm">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                </svg>
              </GlassButton>
            </div>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

