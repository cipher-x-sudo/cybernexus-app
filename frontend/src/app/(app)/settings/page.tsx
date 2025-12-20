"use client";

import { useState, useEffect } from "react";
import { GlassCard, GlassButton, GlassInput, GlassTextarea, Badge } from "@/components/ui";
import { CompanyProfileWizard } from "@/components/company";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";

const sections = [
  { id: "profile", label: "Profile", icon: "👤" },
  { id: "company", label: "Company Profile", icon: "🏢" },
  { id: "notifications", label: "Notifications", icon: "🔔" },
  { id: "security", label: "Security", icon: "🔒" },
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
          {activeSection === "company" && <CompanyProfileSection />}
          {activeSection === "notifications" && <NotificationsSection />}
          {activeSection === "security" && <SecuritySection />}
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
            ??
          </div>
          <div>
            <GlassButton variant="secondary" size="sm">
              Upload Photo
            </GlassButton>
            <p className="text-xs text-white/40 mt-2">JPG, PNG. Max 2MB</p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <GlassInput label="First Name" />
          <GlassInput label="Last Name" />
        </div>
        <GlassInput label="Email" type="email" />
        <GlassInput label="Job Title" />
        <GlassTextarea label="Bio" placeholder="Tell us about yourself..." rows={3} />

        <div className="pt-4 border-t border-white/[0.05] flex justify-end">
          <GlassButton variant="primary">Save Changes</GlassButton>
        </div>
      </div>
    </GlassCard>
  );
}

function CompanyProfileSection() {
  const [companyProfile, setCompanyProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const profile = await api.getCompanyProfile();
      setCompanyProfile(profile);
      setError(null);
    } catch (err: any) {
      if (err.message?.includes("404") || err.message?.includes("not found")) {
        setError("No company profile found. Please create one.");
      } else {
        setError("Failed to load company profile");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    setEditing(true);
  };

  const handleCancel = () => {
    setEditing(false);
  };

  const handleComplete = async () => {
    setEditing(false);
    await loadProfile();
  };

  if (editing) {
    return (
      <div>
        <div className="mb-6">
          <GlassButton variant="ghost" onClick={handleCancel} size="sm">
            ← Back to View
          </GlassButton>
        </div>
        <CompanyProfileWizard
          onComplete={handleComplete}
          onCancel={handleCancel}
          initialData={companyProfile}
          mode="edit"
        />
      </div>
    );
  }

  if (loading) {
    return (
      <GlassCard>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
          <span className="ml-3 text-white/60">Loading company profile...</span>
        </div>
      </GlassCard>
    );
  }

  if (error && !companyProfile) {
    return (
      <GlassCard>
        <div className="text-center py-12">
          <div className="w-16 h-16 rounded-full bg-white/[0.05] flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">🏢</span>
          </div>
          <h3 className="font-mono text-lg text-white mb-2">No Company Profile</h3>
          <p className="text-sm text-white/60 mb-6">{error}</p>
          <CompanyProfileWizard onComplete={handleComplete} mode="create" />
        </div>
      </GlassCard>
    );
  }

  const profile = companyProfile || {};
  const completionFields = [
    profile.name,
    profile.industry,
    profile.primary_domain,
    profile.email,
  ];
  const completionPercentage = Math.round(
    (completionFields.filter(Boolean).length / completionFields.length) * 100
  );

  return (
    <GlassCard>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="font-mono text-lg text-white">Company Profile</h2>
          <p className="text-sm text-white/50 mt-1">Manage your company information</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge
            variant={completionPercentage === 100 ? "success" : completionPercentage >= 50 ? "info" : "default"}
            size="sm"
          >
            {completionPercentage}% Complete
          </Badge>
          <GlassButton variant="primary" size="sm" onClick={handleEdit}>
            Edit Profile
          </GlassButton>
        </div>
      </div>

      <div className="space-y-6">
        {/* Basic Information */}
        <div>
          <h3 className="font-mono text-sm text-white/70 mb-4">Basic Information</h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-white/50 mb-1">Company Name</label>
              <p className="text-sm text-white">{profile.name || "—"}</p>
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1">Industry</label>
              <p className="text-sm text-white">{profile.industry || "—"}</p>
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1">Company Size</label>
              <p className="text-sm text-white">{profile.company_size || "—"}</p>
            </div>
            {profile.description && (
              <div className="md:col-span-2">
                <label className="block text-xs text-white/50 mb-1">Description</label>
                <p className="text-sm text-white">{profile.description}</p>
              </div>
            )}
          </div>
        </div>

        {/* Contact Information */}
        {(profile.email || profile.phone || profile.website || profile.address) && (
          <div>
            <h3 className="font-mono text-sm text-white/70 mb-4">Contact Information</h3>
            <div className="grid md:grid-cols-2 gap-4">
              {profile.email && (
                <div>
                  <label className="block text-xs text-white/50 mb-1">Email</label>
                  <p className="text-sm text-white">{profile.email}</p>
                </div>
              )}
              {profile.phone && (
                <div>
                  <label className="block text-xs text-white/50 mb-1">Phone</label>
                  <p className="text-sm text-white">{profile.phone}</p>
                </div>
              )}
              {profile.website && (
                <div>
                  <label className="block text-xs text-white/50 mb-1">Website</label>
                  <p className="text-sm text-white">
                    <a href={profile.website} target="_blank" rel="noopener noreferrer" className="text-amber-400 hover:text-amber-300">
                      {profile.website}
                    </a>
                  </p>
                </div>
              )}
              {profile.address && Object.values(profile.address).some((v: any) => v) && (
                <div className="md:col-span-2">
                  <label className="block text-xs text-white/50 mb-1">Address</label>
                  <p className="text-sm text-white">
                    {[
                      profile.address.street,
                      profile.address.city,
                      profile.address.state,
                      profile.address.country,
                      profile.address.zip,
                    ]
                      .filter(Boolean)
                      .join(", ") || "—"}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Domains & Assets */}
        {(profile.primary_domain || 
          (profile.additional_domains && profile.additional_domains.length > 0) ||
          (profile.ip_ranges && profile.ip_ranges.length > 0) ||
          (profile.key_assets && profile.key_assets.length > 0)) && (
          <div>
            <h3 className="font-mono text-sm text-white/70 mb-4">Domains & Assets</h3>
            <div className="space-y-4">
              {profile.primary_domain && (
                <div>
                  <label className="block text-xs text-white/50 mb-1">Primary Domain</label>
                  <p className="text-sm text-white">{profile.primary_domain}</p>
                </div>
              )}
              {profile.additional_domains && profile.additional_domains.length > 0 && (
                <div>
                  <label className="block text-xs text-white/50 mb-1">Additional Domains</label>
                  <div className="flex flex-wrap gap-2">
                    {profile.additional_domains.map((domain: string, idx: number) => (
                      <Badge key={idx} variant="default" size="sm">
                        {domain}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {profile.ip_ranges && profile.ip_ranges.length > 0 && (
                <div>
                  <label className="block text-xs text-white/50 mb-1">IP Ranges</label>
                  <div className="flex flex-wrap gap-2">
                    {profile.ip_ranges.map((ip: string, idx: number) => (
                      <Badge key={idx} variant="default" size="sm">
                        {ip}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {profile.key_assets && profile.key_assets.length > 0 && (
                <div>
                  <label className="block text-xs text-white/50 mb-1">Key Assets</label>
                  <div className="space-y-2">
                    {profile.key_assets.map((asset: any, idx: number) => (
                      <div key={idx} className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-white font-mono">{asset.name}</p>
                            <p className="text-xs text-white/60">
                              {asset.type} • {asset.value}
                            </p>
                            {asset.description && (
                              <p className="text-xs text-white/40 mt-1">{asset.description}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {!profile.name && !profile.primary_domain && !profile.email && (
          <div className="text-center py-8">
            <p className="text-sm text-white/60 mb-4">No company profile information available.</p>
            <GlassButton variant="primary" onClick={handleEdit}>
              Create Company Profile
            </GlassButton>
          </div>
        )}
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
          </div>
          <GlassButton variant="ghost" size="sm" className="mt-3">
            Manage 2FA
          </GlassButton>
        </div>

        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
          <p className="font-mono text-white mb-2">Change Password</p>
          <GlassButton variant="secondary" size="sm" className="mt-4">
            Update Password
          </GlassButton>
        </div>

        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
          <p className="font-mono text-white mb-2">Active Sessions</p>
          <GlassButton variant="ghost" size="sm" className="mt-4">
            View Sessions
          </GlassButton>
        </div>
      </div>
    </GlassCard>
  );
}

