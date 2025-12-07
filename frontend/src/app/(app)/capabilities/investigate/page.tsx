"use client";

import { CapabilityPage } from "@/components/capabilities/CapabilityPage";

const sampleFindings = [
  {
    id: "1",
    title: "Suspicious domain registration",
    severity: "high" as const,
    description: "The investigated domain was registered recently and uses privacy protection, common characteristics of malicious domains.",
    evidence: "Domain: suspicious-login.com\nRegistration: 7 days ago\nRegistrar: NameCheap\nWHOIS: Privacy protected",
    recommendations: [
      "Block the domain in security controls",
      "Alert users about potential phishing",
      "Monitor for similar domain registrations",
    ],
    timestamp: "Just now",
  },
  {
    id: "2",
    title: "Page mimics legitimate site",
    severity: "high" as const,
    description: "Visual analysis shows the page is designed to impersonate a legitimate login page with high similarity.",
    evidence: "Visual similarity: 94%\nLogo present: Yes\nForm action: External server\nScreenshot captured",
    recommendations: [
      "Report to hosting provider",
      "Add to blocklist",
      "Conduct user awareness campaign",
    ],
    timestamp: "Just now",
  },
  {
    id: "3",
    title: "Third-party tracking scripts",
    severity: "medium" as const,
    description: "The page loads multiple external scripts that may be collecting user data or performing additional malicious actions.",
    evidence: "External scripts: 8\nTracking domains:\n- analytics-malware.com\n- tracker.suspicious.net\n- cdn.evilsite.ru",
    recommendations: [
      "Block identified tracking domains",
      "Analyze script behavior",
      "Check for data exfiltration",
    ],
    timestamp: "Just now",
  },
  {
    id: "4",
    title: "Domain tree analysis complete",
    severity: "info" as const,
    description: "Full resource tree captured showing all domains and resources loaded by the page.",
    evidence: "Total requests: 47\nUnique domains: 12\nResources captured: All\nHAR file available",
    recommendations: [
      "Review the full domain tree",
      "Identify suspicious third-party resources",
      "Export evidence for incident response",
    ],
    timestamp: "Just now",
  },
];

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
      findings={sampleFindings}
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

