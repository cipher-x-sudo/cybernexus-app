"use client";

import { CapabilityPage } from "@/components/capabilities/CapabilityPage";

const sampleFindings = [
  {
    id: "1",
    title: "Credentials found on dark web marketplace",
    severity: "critical" as const,
    description: "Employee email and password combo found listed for sale on a prominent dark web marketplace. The credentials appear to be from a recent breach.",
    evidence: "user@company.com:******* (partially redacted)\nFound on: DarkMarket\nListing date: 2024-01-15",
    recommendations: [
      "Immediately reset the affected password",
      "Enable multi-factor authentication",
      "Monitor for unauthorized access",
      "Notify the affected employee",
    ],
    timestamp: "2h ago",
  },
  {
    id: "2",
    title: "Brand impersonation site detected",
    severity: "high" as const,
    description: "A phishing site mimicking your company's login page has been discovered on the dark web. The site is actively collecting credentials.",
    evidence: "URL: c0mpany-login.onion\nSimilarity score: 94%\nStatus: Active",
    recommendations: [
      "Report to hosting provider",
      "Alert employees about the threat",
      "Monitor for credential stuffing attacks",
    ],
    timestamp: "4h ago",
  },
  {
    id: "3",
    title: "Company mentioned in threat actor forum",
    severity: "medium" as const,
    description: "Your organization was mentioned in a hacking forum discussion about potential targets. No specific attack plans were observed.",
    evidence: "Forum: HackingForum\nThread: \"Corporate targets Q1 2024\"\nMention context: Listed among potential targets",
    recommendations: [
      "Increase monitoring",
      "Review perimeter security",
      "Conduct security awareness training",
    ],
    timestamp: "1d ago",
  },
];

export default function DarkWebPage() {
  return (
    <CapabilityPage
      id="dark_web_intelligence"
      name="Dark Web Intelligence"
      question="Are we mentioned on the dark web?"
      description="Monitor .onion sites for brand mentions, credential leaks, and threat actor discussions"
      icon={
        <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      }
      color="purple"
      inputLabel="Keywords to monitor"
      inputPlaceholder="company-name, @domain.com, brand-name"
      findings={sampleFindings}
      configOptions={
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-purple-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Credential leaks</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-purple-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Brand mentions</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-purple-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Impersonation sites</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-purple-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Ransomware mentions</span>
            </label>
          </div>
          <div>
            <label className="block text-xs text-white/50 mb-1">Crawl depth</label>
            <select className="w-full h-9 px-3 bg-white/[0.05] border border-white/[0.1] rounded-lg text-sm text-white/80">
              <option value="1">Shallow (faster)</option>
              <option value="2">Normal</option>
              <option value="3">Deep (slower)</option>
            </select>
          </div>
        </div>
      }
    />
  );
}

