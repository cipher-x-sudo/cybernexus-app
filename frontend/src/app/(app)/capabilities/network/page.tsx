"use client";

import { CapabilityPage } from "@/components/capabilities/CapabilityPage";

export default function NetworkSecurityPage() {
  return (
    <CapabilityPage
      id="network_security"
      name="Network Security"
      question="Can attackers tunnel into our network?"
      description="Detect HTTP tunneling attempts, covert channels, and unauthorized network access"
      icon={
        <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
        </svg>
      }
      color="blue"
      inputLabel="Network segment or IP range"
      inputPlaceholder="192.168.1.0/24 or 10.0.0.1"
      configOptions={
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-blue-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">HTTP tunnel detection</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-blue-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">DNS tunnel detection</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-blue-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">SOCKS proxy scan</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-blue-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">ICMP tunnel detection</span>
            </label>
          </div>
          <div>
            <label className="block text-xs text-white/50 mb-1">Monitor duration (seconds)</label>
            <input
              type="number"
              defaultValue={3600}
              className="w-full h-9 px-3 bg-white/[0.05] border border-white/[0.1] rounded-lg text-sm text-white/80"
            />
          </div>
        </div>
      }
    />
  );
}
