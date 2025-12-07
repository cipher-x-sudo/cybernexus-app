"use client";

import { CapabilityPage } from "@/components/capabilities/CapabilityPage";

export default function EmailSecurityPage() {
  return (
    <CapabilityPage
      id="email_security"
      name="Email Security"
      question="Can our email be spoofed?"
      description="Test SPF, DKIM, and DMARC configurations to identify email authentication vulnerabilities"
      icon={
        <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      }
      color="amber"
      inputLabel="Domain to check"
      inputPlaceholder="example.com"
      configOptions={
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Check SPF</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Check DKIM</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Check DMARC</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Check MX records</span>
            </label>
          </div>
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              type="checkbox"
              className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-amber-500"
            />
            <span className="text-xs text-white/60 group-hover:text-white/80">Run authentication bypass tests (advanced)</span>
          </label>
        </div>
      }
    />
  );
}
