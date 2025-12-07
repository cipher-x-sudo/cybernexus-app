"use client";

import { CapabilityPage } from "@/components/capabilities/CapabilityPage";

const sampleFindings = [
  {
    id: "1",
    title: "CRLF injection vulnerability",
    severity: "high" as const,
    description: "The server is vulnerable to CRLF injection via the redirect mechanism. This could allow HTTP response splitting attacks.",
    evidence: "URL: https://example.com/redirect?url=%0d%0aSet-Cookie:malicious=true\nResponse: HTTP headers injected successfully",
    recommendations: [
      "Sanitize user input in redirects",
      "Use URL encoding properly",
      "Implement strict redirect validation",
    ],
    timestamp: "30m ago",
  },
  {
    id: "2",
    title: "Path traversal via misconfigured alias",
    severity: "high" as const,
    description: "Nginx alias misconfiguration allows path traversal attacks, potentially exposing sensitive files outside the web root.",
    evidence: "URL: https://example.com/static../etc/passwd\nVulnerable: Yes\nServer: nginx/1.18.0",
    recommendations: [
      "Fix alias configuration in nginx",
      "Ensure trailing slashes are consistent",
      "Review all location blocks",
    ],
    timestamp: "30m ago",
  },
  {
    id: "3",
    title: "Outdated Nginx version with known CVEs",
    severity: "medium" as const,
    description: "The server is running an outdated version of Nginx with known security vulnerabilities.",
    evidence: "Server: nginx/1.14.2\nCVE-2019-20372: Integer overflow\nCVE-2021-23017: DNS resolver vulnerability",
    recommendations: [
      "Upgrade Nginx to latest stable version",
      "Subscribe to security advisories",
      "Implement automated patching",
    ],
    timestamp: "30m ago",
  },
  {
    id: "4",
    title: "HTTP PURGE method enabled",
    severity: "low" as const,
    description: "The PURGE HTTP method is accessible from external networks. This could be used for cache poisoning attacks.",
    evidence: "Method: PURGE /index.html\nResponse: 200 OK\nCache cleared: Yes",
    recommendations: [
      "Restrict PURGE method to internal IPs",
      "Add authentication for cache operations",
    ],
    timestamp: "30m ago",
  },
];

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
      findings={sampleFindings}
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

