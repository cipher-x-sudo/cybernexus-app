"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

const faqs = [
  {
    category: "General",
    questions: [
      {
        q: "What is CyberNexus?",
        a: "CyberNexus is a unified threat intelligence platform that helps security teams monitor, analyze, and respond to cyber threats in real-time. We aggregate data from multiple sources including the dark web, breach databases, and threat feeds.",
      },
      {
        q: "How does the 3D graph visualization work?",
        a: "Our 3D graph uses advanced visualization technology to map relationships between threat actors, indicators of compromise, and your assets. You can explore connections, filter by entity type, and discover attack patterns that would be invisible in traditional dashboards.",
      },
      {
        q: "What types of threats do you monitor?",
        a: "We monitor a wide range of threats including credential leaks, dark web mentions, phishing campaigns, malware indicators, vulnerability exploits, and threat actor activities targeting your organization.",
      },
    ],
  },
  {
    category: "Pricing & Plans",
    questions: [
      {
        q: "Is there a free trial?",
        a: "Yes! We offer a 14-day free trial with full access to all features. No credit card required. You can also request a personalized demo from our sales team.",
      },
      {
        q: "What's included in the Enterprise plan?",
        a: "Enterprise plans include unlimited users, dedicated account manager, custom integrations, SLA guarantees, on-premise deployment options, and advanced API access.",
      },
    ],
  },
  {
    category: "Technical",
    questions: [
      {
        q: "How do I integrate CyberNexus with my existing tools?",
        a: "We offer native integrations with popular SIEM, SOAR, and ticketing systems. For custom integrations, our REST API provides full access to all platform capabilities. Our team can also help with custom integration development.",
      },
      {
        q: "Where is my data stored?",
        a: "Your data is stored in SOC 2 compliant data centers. We offer data residency options for EU (GDPR), US, and APAC regions. Enterprise customers can also opt for on-premise deployment.",
      },
      {
        q: "What's the API rate limit?",
        a: "Rate limits depend on your plan. Starter plans have 1,000 requests/day, Professional has 10,000, and Enterprise has unlimited API access.",
      },
    ],
  },
];

export function FAQSection() {
  const [openItems, setOpenItems] = useState<string[]>([]);

  const toggleItem = (id: string) => {
    setOpenItems((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  return (
    <section id="faq" className="py-24 lg:py-32 relative">
      <div className="absolute inset-0 gradient-mesh opacity-30" />

      <div className="relative z-10 max-w-4xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <p className="text-amber-400 font-mono text-sm uppercase tracking-wider mb-4">
            FAQ
          </p>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-mono font-bold text-white mb-6">
            Frequently Asked{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-orange-500">
              Questions
            </span>
          </h2>
          <p className="text-lg text-white/60">
            Everything you need to know about CyberNexus
          </p>
        </div>

        {/* FAQ Accordion */}
        <div className="space-y-8">
          {faqs.map((category) => (
            <div key={category.category}>
              <h3 className="font-mono font-semibold text-amber-400 text-sm uppercase tracking-wider mb-4">
                {category.category}
              </h3>
              <div className="space-y-3">
                {category.questions.map((item, index) => {
                  const itemId = `${category.category}-${index}`;
                  const isOpen = openItems.includes(itemId);

                  return (
                    <div
                      key={index}
                      className="glass rounded-xl overflow-hidden"
                    >
                      <button
                        onClick={() => toggleItem(itemId)}
                        className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-white/[0.02] transition-colors"
                      >
                        <span className="font-mono text-white pr-8">
                          {item.q}
                        </span>
                        <svg
                          className={cn(
                            "w-5 h-5 text-amber-400 transition-transform duration-300 flex-shrink-0",
                            isOpen && "rotate-180"
                          )}
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 9l-7 7-7-7"
                          />
                        </svg>
                      </button>
                      <div
                        className={cn(
                          "overflow-hidden transition-all duration-300",
                          isOpen ? "max-h-96" : "max-h-0"
                        )}
                      >
                        <div className="px-6 pb-4 text-white/60 leading-relaxed">
                          {item.a}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Still have questions */}
        <div className="mt-16 text-center">
          <div className="glass rounded-2xl p-8 inline-block">
            <p className="text-white mb-4">Still have questions?</p>
            <a
              href="#"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-400 font-mono text-sm hover:bg-amber-500/30 transition-colors"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              Contact Support
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

