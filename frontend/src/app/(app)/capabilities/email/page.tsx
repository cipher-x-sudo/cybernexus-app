"use client";

import { CapabilityPage } from "@/components/capabilities/CapabilityPage";

const sampleFindings = [
  {
    id: "1",
    title: "SPF record allows any sender (+all)",
    severity: "critical" as const,
    description: "Your SPF record ends with '+all' which allows any server to send email on behalf of your domain. This makes email spoofing trivial.",
    evidence: "v=spf1 include:_spf.google.com +all\n\nThe '+all' mechanism should be '-all' (hard fail) or '~all' (soft fail)",
    recommendations: [
      "Change '+all' to '-all' in your SPF record",
      "Test email delivery after change",
      "Monitor for bounce rate changes",
    ],
    timestamp: "Just now",
  },
  {
    id: "2",
    title: "DMARC policy set to 'none'",
    severity: "high" as const,
    description: "Your DMARC policy is set to 'none' which means failed authentication emails are still delivered. This provides no protection against spoofing.",
    evidence: "v=DMARC1; p=none; rua=mailto:dmarc@company.com\n\nPolicy 'none' = monitoring only, no enforcement",
    recommendations: [
      "Upgrade DMARC policy to 'quarantine' or 'reject'",
      "Review DMARC reports before changing policy",
      "Ensure all legitimate sending sources are authorized",
    ],
    timestamp: "Just now",
  },
  {
    id: "3",
    title: "No DKIM records found",
    severity: "high" as const,
    description: "No DKIM records were found for common selectors. Without DKIM, recipients cannot verify that emails were not modified in transit.",
    evidence: "Checked selectors: default, google, selector1, selector2, k1, k2\nResult: No valid DKIM records found",
    recommendations: [
      "Configure DKIM signing for your domain",
      "Publish DKIM public key in DNS",
      "Verify DKIM alignment with SPF",
    ],
    timestamp: "Just now",
  },
  {
    id: "4",
    title: "Missing aggregate report URI",
    severity: "medium" as const,
    description: "Your DMARC record does not have an aggregate report URI (rua). You won't receive reports about email authentication results.",
    evidence: "Current: v=DMARC1; p=none\nRecommended: v=DMARC1; p=none; rua=mailto:dmarc@company.com",
    recommendations: [
      "Add rua= tag to receive aggregate reports",
      "Set up a mailbox to receive DMARC reports",
      "Use a DMARC analysis service",
    ],
    timestamp: "Just now",
  },
];

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
      findings={sampleFindings}
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

