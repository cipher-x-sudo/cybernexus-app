"use client";

import { useState } from "react";
import { GlassCard, GlassButton, GlassInput } from "@/components/ui";
import { cn } from "@/lib/utils";

const steps = [
  {
    id: 1,
    title: "Welcome",
    description: "Let's set up your threat intelligence platform",
  },
  {
    id: 2,
    title: "Organization",
    description: "Tell us about your organization",
  },
  {
    id: 3,
    title: "Assets",
    description: "Add your first assets to monitor",
  },
  {
    id: 4,
    title: "Alerts",
    description: "Configure your alert preferences",
  },
  {
    id: 5,
    title: "Complete",
    description: "You're all set!",
  },
];

export default function OnboardingPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    orgName: "",
    industry: "",
    size: "",
    domain: "",
    emails: "",
    alertEmail: true,
    alertSlack: false,
  });

  const handleNext = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <div className="w-full max-w-2xl">
        {/* Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
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
                      "w-full h-0.5 mx-2",
                      currentStep > step.id ? "bg-amber-500" : "bg-white/10"
                    )}
                    style={{ width: "60px" }}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step content */}
        <GlassCard className="text-center" padding="lg">
          {currentStep === 1 && (
            <div className="space-y-6">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center mx-auto mb-6">
                <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h2 className="text-2xl font-mono font-bold text-white">
                Welcome to CyberNexus
              </h2>
              <p className="text-white/60 max-w-md mx-auto">
                Let's get you set up with your unified threat intelligence platform.
                This will only take a few minutes.
              </p>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-6 text-left">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-mono font-bold text-white">
                  Organization Details
                </h2>
                <p className="text-white/60">Tell us about your organization</p>
              </div>
              <GlassInput
                label="Organization Name"
                placeholder="Acme Corporation"
                value={formData.orgName}
                onChange={(e) => setFormData({ ...formData, orgName: e.target.value })}
              />
              <div>
                <label className="block text-sm font-mono text-white/70 mb-2">Industry</label>
                <select
                  className="w-full h-11 px-4 bg-white/[0.03] border border-white/[0.08] rounded-xl text-white/90 font-mono text-sm focus:outline-none focus:border-amber-500/50"
                  value={formData.industry}
                  onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                >
                  <option value="" className="bg-[#0a0e1a]">Select industry</option>
                  <option value="tech" className="bg-[#0a0e1a]">Technology</option>
                  <option value="finance" className="bg-[#0a0e1a]">Finance</option>
                  <option value="healthcare" className="bg-[#0a0e1a]">Healthcare</option>
                  <option value="retail" className="bg-[#0a0e1a]">Retail</option>
                  <option value="other" className="bg-[#0a0e1a]">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-mono text-white/70 mb-2">Company Size</label>
                <div className="grid grid-cols-4 gap-2">
                  {["1-50", "51-200", "201-1000", "1000+"].map((size) => (
                    <button
                      key={size}
                      onClick={() => setFormData({ ...formData, size })}
                      className={cn(
                        "p-3 rounded-lg font-mono text-sm transition-all",
                        formData.size === size
                          ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                          : "bg-white/[0.03] text-white/60 border border-white/[0.08]"
                      )}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-6 text-left">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-mono font-bold text-white">
                  Add Assets
                </h2>
                <p className="text-white/60">What should we monitor?</p>
              </div>
              <GlassInput
                label="Primary Domain"
                placeholder="example.com"
                value={formData.domain}
                onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                hint="Your main company domain"
              />
              <GlassInput
                label="Key Email Addresses"
                placeholder="ceo@example.com, admin@example.com"
                value={formData.emails}
                onChange={(e) => setFormData({ ...formData, emails: e.target.value })}
                hint="Separate multiple emails with commas"
              />
              <p className="text-xs text-white/40">
                You can add more assets later from the dashboard.
              </p>
            </div>
          )}

          {currentStep === 4 && (
            <div className="space-y-6 text-left">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-mono font-bold text-white">
                  Alert Preferences
                </h2>
                <p className="text-white/60">How should we notify you?</p>
              </div>
              <div className="space-y-3">
                {[
                  { key: "alertEmail", label: "Email notifications", desc: "Get alerts via email" },
                  { key: "alertSlack", label: "Slack notifications", desc: "Connect to Slack" },
                ].map((item) => (
                  <div
                    key={item.key}
                    className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]"
                  >
                    <div>
                      <p className="font-mono text-white">{item.label}</p>
                      <p className="text-sm text-white/50">{item.desc}</p>
                    </div>
                    <button
                      onClick={() =>
                        setFormData({
                          ...formData,
                          [item.key]: !formData[item.key as keyof typeof formData],
                        })
                      }
                      className={cn(
                        "w-12 h-6 rounded-full transition-colors relative",
                        formData[item.key as keyof typeof formData]
                          ? "bg-amber-500"
                          : "bg-white/10"
                      )}
                    >
                      <span
                        className={cn(
                          "absolute top-1 w-4 h-4 rounded-full bg-white transition-transform",
                          formData[item.key as keyof typeof formData]
                            ? "translate-x-7"
                            : "translate-x-1"
                        )}
                      />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {currentStep === 5 && (
            <div className="space-y-6">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center mx-auto mb-6">
                <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-mono font-bold text-white">
                You're All Set! 🎉
              </h2>
              <p className="text-white/60 max-w-md mx-auto">
                Your threat intelligence platform is ready. We've started monitoring
                your assets and will alert you of any threats.
              </p>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between mt-8 pt-6 border-t border-white/[0.05]">
            <GlassButton
              variant="ghost"
              onClick={handleBack}
              disabled={currentStep === 1}
            >
              Back
            </GlassButton>
            {currentStep < steps.length ? (
              <GlassButton variant="primary" onClick={handleNext}>
                Continue
              </GlassButton>
            ) : (
              <GlassButton variant="primary" onClick={() => window.location.href = "/dashboard"}>
                Go to Dashboard
              </GlassButton>
            )}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}

