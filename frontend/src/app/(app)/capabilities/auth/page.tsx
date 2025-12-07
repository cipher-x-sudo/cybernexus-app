"use client";

import { CapabilityPage } from "@/components/capabilities/CapabilityPage";

export default function AuthTestingPage() {
  return (
    <CapabilityPage
      id="authentication_testing"
      name="Authentication Testing"
      question="Are our credentials weak?"
      description="Test password strength and identify accounts vulnerable to spray attacks"
      icon={
        <svg className="w-5 h-5 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
        </svg>
      }
      color="rose"
      inputLabel="Target system (RDP/domain)"
      inputPlaceholder="domain.local or 192.168.1.100"
      configOptions={
        <div className="space-y-3">
          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
            <p className="text-xs text-amber-400">
              ⚠️ Authentication testing can lock out accounts. Ensure you have authorization and understand the lockout policy.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-rose-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Respect lockout policy</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-rose-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Smart throttling</span>
            </label>
          </div>
          <div>
            <label className="block text-xs text-white/50 mb-1">Delay between attempts (ms)</label>
            <input
              type="number"
              defaultValue={1000}
              className="w-full h-9 px-3 bg-white/[0.05] border border-white/[0.1] rounded-lg text-sm text-white/80"
            />
          </div>
          <div>
            <label className="block text-xs text-white/50 mb-1">Username list</label>
            <textarea
              placeholder="administrator&#10;admin&#10;user1"
              className="w-full h-20 p-3 bg-white/[0.05] border border-white/[0.1] rounded-lg text-sm text-white/80 resize-none font-mono"
            />
          </div>
        </div>
      }
    />
  );
}
