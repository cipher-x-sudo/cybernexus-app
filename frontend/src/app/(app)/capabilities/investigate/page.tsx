"use client";

import { CapabilityPage } from "@/components/capabilities/CapabilityPage";

export default function InvestigationPage() {
  return (
    <CapabilityPage
      id="investigation"
      name="Investigation Mode"
      question="Analyze a suspicious target"
      description="Deep dive into suspicious URLs, domains, or indicators with full page capture and analysis"
      icon={
        <svg className="w-5 h-5 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      }
      color="orange"
      inputLabel="URL or domain to investigate"
      inputPlaceholder="https://suspicious-site.com or suspicious.com"
      configOptions={
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-orange-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Full page capture</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-orange-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Domain tree mapping</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-orange-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Screenshot</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-orange-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">HAR export</span>
            </label>
          </div>
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              type="checkbox"
              className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-orange-500"
            />
            <span className="text-xs text-white/60 group-hover:text-white/80">Cross-reference with dark web data</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              type="checkbox"
              className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-orange-500"
            />
            <span className="text-xs text-white/60 group-hover:text-white/80">Visual similarity analysis</span>
          </label>
        </div>
      }
    />
  );
}
