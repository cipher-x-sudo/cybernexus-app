"use client";

import { CapabilityPage } from "@/components/capabilities/CapabilityPage";

const sampleFindings = [
  {
    id: "1",
    title: "Exposed admin panel discovered",
    severity: "critical" as const,
    description: "An administrative interface was found publicly accessible without authentication. This could allow attackers to gain unauthorized access to your systems.",
    evidence: "URL: https://example.com/wp-admin\nStatus: 200 OK\nAuthentication: None required",
    recommendations: [
      "Restrict access to admin panels by IP",
      "Implement strong authentication",
      "Consider moving admin to a separate subdomain",
      "Enable rate limiting",
    ],
    timestamp: "1h ago",
  },
  {
    id: "2",
    title: "Backup file exposed",
    severity: "high" as const,
    description: "A database backup file was found accessible on the web server. This could contain sensitive data including credentials.",
    evidence: "URL: https://example.com/backup.sql.gz\nFile size: 45MB\nLast modified: 2024-01-10",
    recommendations: [
      "Remove backup files from web root",
      "Implement access controls",
      "Use proper backup storage solutions",
    ],
    timestamp: "1h ago",
  },
  {
    id: "3",
    title: "Git repository exposed",
    severity: "high" as const,
    description: "The .git directory is accessible, potentially exposing source code and commit history including sensitive information.",
    evidence: "URL: https://example.com/.git/config\nRepository detected: Yes",
    recommendations: [
      "Block access to .git directory",
      "Add .git to .htaccess deny rules",
      "Review git history for secrets",
    ],
    timestamp: "1h ago",
  },
  {
    id: "4",
    title: "Sensitive file indexed by search engines",
    severity: "medium" as const,
    description: "Sensitive documents were found indexed by Google, making them discoverable via search queries.",
    evidence: 'Query: site:example.com filetype:pdf "confidential"\nResults: 12 documents found',
    recommendations: [
      "Remove sensitive files from public directories",
      "Request removal from search engine indices",
      "Implement robots.txt restrictions",
    ],
    timestamp: "1h ago",
  },
];

export default function ExposureDiscoveryPage() {
  return (
    <CapabilityPage
      id="exposure_discovery"
      name="Exposure Discovery"
      question="What can attackers find about us online?"
      description="Search for leaked documents, exposed configurations, and sensitive data accessible to attackers"
      icon={
        <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      }
      color="cyan"
      inputLabel="Target domain"
      inputPlaceholder="example.com"
      findings={sampleFindings}
      configOptions={
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-cyan-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Search engine dorking</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-cyan-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Sensitive file detection</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-cyan-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Admin panel discovery</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-cyan-500"
              />
              <span className="text-xs text-white/60 group-hover:text-white/80">Source code exposure</span>
            </label>
          </div>
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              type="checkbox"
              defaultChecked
              className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1] text-cyan-500"
            />
            <span className="text-xs text-white/60 group-hover:text-white/80">Include subdomains</span>
          </label>
        </div>
      }
    />
  );
}

