"use client";

import { useState, useEffect } from "react";
import { GlassCard, GlassButton, GlassInput, GlassTextarea } from "@/components/ui";
import AutomationConfigStep from "@/components/company/AutomationConfigStep";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";

const DRAFT_STORAGE_KEY = "cybernexus_company_profile_draft";
const AUTO_SAVE_INTERVAL = 30000; // 30 seconds

interface WizardStep {
  id: number;
  title: string;
  description: string;
}

const steps: WizardStep[] = [
  {
    id: 1,
    title: "Basic Information",
    description: "Tell us about your company",
  },
  {
    id: 2,
    title: "Contact Details",
    description: "How can we reach you?",
  },
  {
    id: 3,
    title: "Domains & Assets",
    description: "What should we monitor?",
  },
  {
    id: 4,
    title: "Automation",
    description: "Configure automated scans",
  },
  {
    id: 5,
    title: "Review & Complete",
    description: "Review your information",
  },
];

interface CompanyProfileData {
  // Basic Info
  name: string;
  industry: string;
  company_size: string;
  description: string;
  
  // Contact
  phone: string;
  email: string;
  website: string;
  address: {
    street: string;
    city: string;
    state: string;
    country: string;
    zip: string;
  };
  
  // Domains & Assets
  primary_domain: string;
  additional_domains: string[];
  ip_ranges: string[];
  key_assets: Array<{
    name: string;
    type: string;
    value: string;
    description: string;
  }>;
  
  // Automation
  automation_config: {
    enabled: boolean;
    schedule: {
      cron: string;
      timezone: string;
    };
    capabilities: {
      [key: string]: {
        enabled: boolean;
        targets?: string[];
        keywords?: string[];
        config?: any;
      };
    };
  } | null;
  
  // Metadata
  timezone: string;
  locale: string;
}

interface CompanyProfileWizardProps {
  onComplete?: () => void;
  onCancel?: () => void;
  initialData?: Partial<CompanyProfileData>;
  mode?: "create" | "edit";
}

export default function CompanyProfileWizard({
  onComplete,
  onCancel,
  initialData,
  mode = "create",
}: CompanyProfileWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const [formData, setFormData] = useState<CompanyProfileData>({
    name: "",
    industry: "",
    company_size: "",
    description: "",
    phone: "",
    email: "",
    website: "",
    address: {
      street: "",
      city: "",
      state: "",
      country: "",
      zip: "",
    },
    primary_domain: "",
    additional_domains: [],
    ip_ranges: [],
    key_assets: [],
    automation_config: null,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
    locale: navigator.language || "en-US",
    ...initialData,
  });

  // Load draft from localStorage on mount
  useEffect(() => {
    const savedDraft = localStorage.getItem(DRAFT_STORAGE_KEY);
    if (savedDraft && !initialData) {
      try {
        const draft = JSON.parse(savedDraft);
        setFormData((prev) => ({ ...prev, ...draft }));
      } catch (e) {
        // Invalid draft, ignore
      }
    }
  }, [initialData]);

  // Auto-save draft
  useEffect(() => {
    const interval = setInterval(() => {
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(formData));
    }, AUTO_SAVE_INTERVAL);
    
    return () => clearInterval(interval);
  }, [formData]);

  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (step === 1) {
      if (!formData.name.trim()) {
        newErrors.name = "Company name is required";
      }
    }
    
    if (step === 2) {
      if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        newErrors.email = "Invalid email format";
      }
      if (formData.website && !/^https?:\/\/.+/.test(formData.website) && !/^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$/.test(formData.website)) {
        newErrors.website = "Invalid website format";
      }
    }
    
    if (step === 3) {
      if (formData.primary_domain && !/^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$/.test(formData.primary_domain)) {
        newErrors.primary_domain = "Invalid domain format";
      }
      // Validate additional domains
      formData.additional_domains.forEach((domain, idx) => {
        if (domain && !/^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$/.test(domain)) {
          newErrors[`additional_domain_${idx}`] = "Invalid domain format";
        }
      });
      // Validate IP ranges
      formData.ip_ranges.forEach((ip, idx) => {
        if (ip && !/^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$/.test(ip)) {
          newErrors[`ip_range_${idx}`] = "Invalid IP range format (use CIDR notation)";
        }
      });
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      if (currentStep < steps.length) {
        setCurrentStep(currentStep + 1);
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      setErrors({});
    }
  };

  const handleSubmit = async () => {
    if (!validateStep(5)) {
      setCurrentStep(1); // Go to first step with errors
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // Prepare data for API
      const submitData: any = {
        name: formData.name,
        industry: formData.industry || undefined,
        company_size: formData.company_size || undefined,
        description: formData.description || undefined,
        phone: formData.phone || undefined,
        email: formData.email || undefined,
        website: formData.website || undefined,
        primary_domain: formData.primary_domain || undefined,
        additional_domains: formData.additional_domains.filter((d) => d.trim()),
        ip_ranges: formData.ip_ranges.filter((ip) => ip.trim()),
        key_assets: formData.key_assets.filter((a) => a.name.trim() && a.value.trim()),
        automation_config: formData.automation_config,
        timezone: formData.timezone,
        locale: formData.locale,
      };
      
      // Add address if any field is filled
      if (Object.values(formData.address).some((v) => v.trim())) {
        submitData.address = formData.address;
      }
      
      if (mode === "edit") {
        await api.patchCompanyProfile(submitData);
      } else {
        await api.createCompanyProfile(submitData);
      }
      
      // Sync automation if enabled
      if (formData.automation_config?.enabled) {
        try {
          await api.syncCompanyAutomation();
        } catch (syncError) {
          console.error("Failed to sync automation:", syncError);
          // Don't fail the whole submission if sync fails
        }
      }
      
      // Clear draft on success
      localStorage.removeItem(DRAFT_STORAGE_KEY);
      
      if (onComplete) {
        onComplete();
      }
    } catch (error: any) {
      setErrors({ submit: error.message || "Failed to save profile. Please try again." });
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateField = (field: string, value: any) => {
    if (field.startsWith("address.")) {
      const addrField = field.split(".")[1];
      setFormData((prev) => ({
        ...prev,
        address: { ...prev.address, [addrField]: value },
      }));
    } else {
      setFormData((prev) => ({ ...prev, [field]: value }));
    }
  };

  const addListItem = (field: "additional_domains" | "ip_ranges" | "key_assets", value?: any) => {
    if (field === "key_assets") {
      setFormData((prev) => ({
        ...prev,
        key_assets: [...prev.key_assets, { name: "", type: "domain", value: "", description: "" }],
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [field]: [...prev[field], ""],
      }));
    }
  };

  const removeListItem = (field: "additional_domains" | "ip_ranges" | "key_assets", index: number) => {
    setFormData((prev) => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index),
    }));
  };

  const updateListItem = (field: "additional_domains" | "ip_ranges" | "key_assets", index: number, value: any) => {
    if (field === "key_assets") {
      setFormData((prev) => {
        const newAssets = [...prev.key_assets];
        newAssets[index] = { ...newAssets[index], ...value };
        return { ...prev, key_assets: newAssets };
      });
    } else {
      setFormData((prev) => {
        const newList = [...prev[field]];
        newList[index] = value;
        return { ...prev, [field]: newList };
      });
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex items-center">
                <div
                  className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center font-mono text-sm transition-all",
                    currentStep >= step.id
                      ? "bg-amber-500 text-white"
                      : "bg-white/[0.05] text-white/40"
                  )}
                >
                  {currentStep > step.id ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    step.id
                  )}
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={cn(
                      "h-0.5 mx-2 flex-1",
                      currentStep > step.id ? "bg-amber-500" : "bg-white/10"
                    )}
                  />
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="text-center">
          <h3 className="font-mono text-lg text-white">{steps[currentStep - 1].title}</h3>
          <p className="text-sm text-white/60">{steps[currentStep - 1].description}</p>
        </div>
      </div>

      {/* Step Content */}
      <GlassCard padding="lg">
        {errors.submit && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            {errors.submit}
          </div>
        )}

        {/* Step 1: Basic Information */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <GlassInput
              label="Company Name *"
              value={formData.name}
              onChange={(e) => updateField("name", e.target.value)}
              error={errors.name}
              placeholder="Acme Corporation"
            />
            
            <div>
              <label className="block text-sm font-mono text-white/70 mb-2">Industry</label>
              <select
                className="w-full h-11 px-4 bg-white/[0.03] border border-white/[0.08] rounded-xl text-white/90 font-mono text-sm focus:outline-none focus:border-amber-500/50"
                value={formData.industry}
                onChange={(e) => updateField("industry", e.target.value)}
              >
                <option value="" className="bg-[#0a0e1a]">Select industry</option>
                <option value="technology" className="bg-[#0a0e1a]">Technology</option>
                <option value="finance" className="bg-[#0a0e1a]">Finance</option>
                <option value="healthcare" className="bg-[#0a0e1a]">Healthcare</option>
                <option value="retail" className="bg-[#0a0e1a]">Retail</option>
                <option value="manufacturing" className="bg-[#0a0e1a]">Manufacturing</option>
                <option value="education" className="bg-[#0a0e1a]">Education</option>
                <option value="government" className="bg-[#0a0e1a]">Government</option>
                <option value="other" className="bg-[#0a0e1a]">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-mono text-white/70 mb-2">Company Size</label>
              <div className="grid grid-cols-4 gap-2">
                {["1-50", "51-200", "201-1000", "1000+"].map((size) => (
                  <button
                    key={size}
                    onClick={() => updateField("company_size", size)}
                    className={cn(
                      "p-3 rounded-lg font-mono text-sm transition-all",
                      formData.company_size === size
                        ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                        : "bg-white/[0.03] text-white/60 border border-white/[0.08]"
                    )}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>

            <GlassTextarea
              label="Description"
              value={formData.description}
              onChange={(e) => updateField("description", e.target.value)}
              placeholder="Tell us about your company..."
              rows={4}
            />
          </div>
        )}

        {/* Step 2: Contact Details */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <GlassInput
              label="Contact Email"
              type="email"
              value={formData.email}
              onChange={(e) => updateField("email", e.target.value)}
              error={errors.email}
              placeholder="contact@company.com"
            />

            <GlassInput
              label="Phone"
              type="tel"
              value={formData.phone}
              onChange={(e) => updateField("phone", e.target.value)}
              placeholder="+1 (555) 123-4567"
            />

            <GlassInput
              label="Website"
              value={formData.website}
              onChange={(e) => updateField("website", e.target.value)}
              error={errors.website}
              placeholder="https://www.company.com"
              hint="Include https:// or just the domain"
            />

            <div className="space-y-4">
              <h4 className="font-mono text-sm text-white/70">Address</h4>
              <GlassInput
                label="Street"
                value={formData.address.street}
                onChange={(e) => updateField("address.street", e.target.value)}
                placeholder="123 Main St"
              />
              <div className="grid grid-cols-2 gap-4">
                <GlassInput
                  label="City"
                  value={formData.address.city}
                  onChange={(e) => updateField("address.city", e.target.value)}
                  placeholder="New York"
                />
                <GlassInput
                  label="State/Province"
                  value={formData.address.state}
                  onChange={(e) => updateField("address.state", e.target.value)}
                  placeholder="NY"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <GlassInput
                  label="Country"
                  value={formData.address.country}
                  onChange={(e) => updateField("address.country", e.target.value)}
                  placeholder="United States"
                />
                <GlassInput
                  label="ZIP/Postal Code"
                  value={formData.address.zip}
                  onChange={(e) => updateField("address.zip", e.target.value)}
                  placeholder="10001"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Domains & Assets */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <GlassInput
              label="Primary Domain"
              value={formData.primary_domain}
              onChange={(e) => updateField("primary_domain", e.target.value)}
              error={errors.primary_domain}
              placeholder="example.com"
              hint="Your main company domain"
            />

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-mono text-white/70">Additional Domains</label>
                <GlassButton
                  variant="secondary"
                  size="sm"
                  onClick={() => addListItem("additional_domains")}
                >
                  + Add Domain
                </GlassButton>
              </div>
              {formData.additional_domains.length === 0 && (
                <p className="text-xs text-white/40 mb-2">No additional domains added</p>
              )}
              {formData.additional_domains.map((domain, idx) => (
                <div key={idx} className="flex gap-2 mb-2">
                  <GlassInput
                    value={domain}
                    onChange={(e) => updateListItem("additional_domains", idx, e.target.value)}
                    error={errors[`additional_domain_${idx}`]}
                    placeholder="subdomain.example.com"
                    className="flex-1"
                  />
                  <GlassButton
                    variant="ghost"
                    size="sm"
                    onClick={() => removeListItem("additional_domains", idx)}
                  >
                    ×
                  </GlassButton>
                </div>
              ))}
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-mono text-white/70">IP Ranges (CIDR)</label>
                <GlassButton
                  variant="secondary"
                  size="sm"
                  onClick={() => addListItem("ip_ranges")}
                >
                  + Add IP Range
                </GlassButton>
              </div>
              {formData.ip_ranges.length === 0 && (
                <p className="text-xs text-white/40 mb-2">No IP ranges added</p>
              )}
              {formData.ip_ranges.map((ip, idx) => (
                <div key={idx} className="flex gap-2 mb-2">
                  <GlassInput
                    value={ip}
                    onChange={(e) => updateListItem("ip_ranges", idx, e.target.value)}
                    error={errors[`ip_range_${idx}`]}
                    placeholder="192.168.1.0/24"
                    hint={idx === 0 ? "Use CIDR notation (e.g., 192.168.1.0/24)" : undefined}
                    className="flex-1"
                  />
                  <GlassButton
                    variant="ghost"
                    size="sm"
                    onClick={() => removeListItem("ip_ranges", idx)}
                  >
                    ×
                  </GlassButton>
                </div>
              ))}
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-mono text-white/70">Key Assets</label>
                <GlassButton
                  variant="secondary"
                  size="sm"
                  onClick={() => addListItem("key_assets")}
                >
                  + Add Asset
                </GlassButton>
              </div>
              {formData.key_assets.length === 0 && (
                <p className="text-xs text-white/40 mb-2">No key assets added</p>
              )}
              {formData.key_assets.map((asset, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] mb-3 space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <GlassInput
                      label="Asset Name"
                      value={asset.name}
                      onChange={(e) => updateListItem("key_assets", idx, { name: e.target.value })}
                      placeholder="Main Web Server"
                    />
                    <div>
                      <label className="block text-sm font-mono text-white/70 mb-2">Type</label>
                      <select
                        className="w-full h-11 px-4 bg-white/[0.03] border border-white/[0.08] rounded-xl text-white/90 font-mono text-sm focus:outline-none focus:border-amber-500/50"
                        value={asset.type}
                        onChange={(e) => updateListItem("key_assets", idx, { type: e.target.value })}
                      >
                        <option value="domain" className="bg-[#0a0e1a]">Domain</option>
                        <option value="ip" className="bg-[#0a0e1a]">IP Address</option>
                        <option value="server" className="bg-[#0a0e1a]">Server</option>
                        <option value="application" className="bg-[#0a0e1a]">Application</option>
                        <option value="other" className="bg-[#0a0e1a]">Other</option>
                      </select>
                    </div>
                  </div>
                  <GlassInput
                    label="Value"
                    value={asset.value}
                    onChange={(e) => updateListItem("key_assets", idx, { value: e.target.value })}
                    placeholder="server.example.com"
                  />
                  <div className="flex gap-2">
                    <GlassTextarea
                      label="Description"
                      value={asset.description}
                      onChange={(e) => updateListItem("key_assets", idx, { description: e.target.value })}
                      placeholder="Optional description..."
                      rows={2}
                      className="flex-1"
                    />
                    <GlassButton
                      variant="ghost"
                      size="sm"
                      onClick={() => removeListItem("key_assets", idx)}
                      className="self-end"
                    >
                      ×
                    </GlassButton>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Automation */}
        {currentStep === 4 && (
          <AutomationConfigStep
            value={formData.automation_config}
            onChange={(config) => setFormData((prev) => ({ ...prev, automation_config: config }))}
            profileData={{
              name: formData.name,
              primary_domain: formData.primary_domain,
              additional_domains: formData.additional_domains,
              key_assets: formData.key_assets,
              timezone: formData.timezone,
            }}
          />
        )}

        {/* Step 5: Review & Complete */}
        {currentStep === 5 && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <div className="w-16 h-16 rounded-full bg-amber-500/20 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="font-mono text-xl text-white mb-2">Review Your Information</h3>
              <p className="text-sm text-white/60">Please review all details before submitting</p>
            </div>

            <div className="space-y-4">
              {/* Basic Info */}
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                <h4 className="font-mono text-sm text-white/70 mb-3">Basic Information</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="text-white/60">Company:</span> <span className="text-white">{formData.name || "—"}</span></div>
                  <div><span className="text-white/60">Industry:</span> <span className="text-white">{formData.industry || "—"}</span></div>
                  <div><span className="text-white/60">Size:</span> <span className="text-white">{formData.company_size || "—"}</span></div>
                  {formData.description && (
                    <div><span className="text-white/60">Description:</span> <span className="text-white">{formData.description}</span></div>
                  )}
                </div>
              </div>

              {/* Contact */}
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                <h4 className="font-mono text-sm text-white/70 mb-3">Contact Details</h4>
                <div className="space-y-2 text-sm">
                  {formData.email && <div><span className="text-white/60">Email:</span> <span className="text-white">{formData.email}</span></div>}
                  {formData.phone && <div><span className="text-white/60">Phone:</span> <span className="text-white">{formData.phone}</span></div>}
                  {formData.website && <div><span className="text-white/60">Website:</span> <span className="text-white">{formData.website}</span></div>}
                  {Object.values(formData.address).some(v => v) && (
                    <div>
                      <span className="text-white/60">Address:</span>
                      <span className="text-white ml-2">
                        {[
                          formData.address.street,
                          formData.address.city,
                          formData.address.state,
                          formData.address.country,
                          formData.address.zip,
                        ].filter(Boolean).join(", ") || "—"}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Domains & Assets */}
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                <h4 className="font-mono text-sm text-white/70 mb-3">Domains & Assets</h4>
                <div className="space-y-2 text-sm">
                  {formData.primary_domain && (
                    <div><span className="text-white/60">Primary Domain:</span> <span className="text-white">{formData.primary_domain}</span></div>
                  )}
                  {formData.additional_domains.filter(d => d.trim()).length > 0 && (
                    <div>
                      <span className="text-white/60">Additional Domains:</span>
                      <span className="text-white ml-2">{formData.additional_domains.filter(d => d.trim()).join(", ")}</span>
                    </div>
                  )}
                  {formData.ip_ranges.filter(ip => ip.trim()).length > 0 && (
                    <div>
                      <span className="text-white/60">IP Ranges:</span>
                      <span className="text-white ml-2">{formData.ip_ranges.filter(ip => ip.trim()).join(", ")}</span>
                    </div>
                  )}
                  {formData.key_assets.filter(a => a.name.trim()).length > 0 && (
                    <div>
                      <span className="text-white/60">Key Assets:</span>
                      <div className="mt-1 space-y-1">
                        {formData.key_assets.filter(a => a.name.trim()).map((asset, idx) => (
                          <div key={idx} className="text-white ml-4">
                            {asset.name} ({asset.type}): {asset.value}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Automation */}
              {formData.automation_config?.enabled && (
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                  <h4 className="font-mono text-sm text-white/70 mb-3">Automation</h4>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-white/60">Status:</span>{" "}
                      <span className="text-amber-400">Enabled</span>
                    </div>
                    <div>
                      <span className="text-white/60">Schedule:</span>{" "}
                      <span className="text-white">{formData.automation_config.schedule.cron}</span>{" "}
                      <span className="text-white/40">({formData.automation_config.schedule.timezone})</span>
                    </div>
                    <div>
                      <span className="text-white/60">Capabilities:</span>{" "}
                      <span className="text-white">
                        {Object.keys(formData.automation_config.capabilities).length} enabled
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8 pt-6 border-t border-white/[0.05]">
          <div>
            {onCancel && (
              <GlassButton variant="ghost" onClick={onCancel}>
                Cancel
              </GlassButton>
            )}
          </div>
          <div className="flex gap-3">
            {currentStep > 1 && (
              <GlassButton variant="ghost" onClick={handleBack} disabled={isSubmitting}>
                Back
              </GlassButton>
            )}
            {currentStep < steps.length ? (
              <GlassButton variant="primary" onClick={handleNext} disabled={isSubmitting}>
                Continue
              </GlassButton>
            ) : (
              <GlassButton
                variant="primary"
                onClick={handleSubmit}
                disabled={isSubmitting}
              >
                {isSubmitting ? "Saving..." : mode === "edit" ? "Update Profile" : "Complete Setup"}
              </GlassButton>
            )}
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
