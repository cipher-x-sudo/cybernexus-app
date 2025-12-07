"use client";

import { CapabilityPage } from "@/components/capabilities/CapabilityPage";

export default function InfrastructurePage() {
  return (
    <CapabilityPage
      id="infrastructure_testing"
      name="Infrastructure Testing"
      question="Are our servers misconfigured?"
      description="Scan for CRLF injection, path traversal, and web server misconfigurations"
      icon={
        <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
        </svg>
      }
      color="emerald"
      inputLabel="Target URL"
      inputPlaceholder="https://example.com"
      configOptions={
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-emerald-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">CRLF injection</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-emerald-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Path traversal</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-emerald-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Version detection</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-emerald-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">CVE lookup</span>
            </label>
          </div>
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              type="checkbox"
              className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-emerald-500"
            />
            <span className="text-xs text-white/60 group-hover:text-white/80">Test 401/403 bypass techniques</span>
          </label>
        </div>
      }
    />
  );
}
