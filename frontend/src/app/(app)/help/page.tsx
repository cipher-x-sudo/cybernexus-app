"use client";

import { useState } from "react";
import { GlassCard, GlassButton, GlassInput, GlassTextarea } from "@/components/ui";
import { cn } from "@/lib/utils";

const categories = [
  { id: "getting-started", label: "Getting Started", icon: "🚀" },
  { id: "dashboard", label: "Dashboard", icon: "📊" },
  { id: "threats", label: "Threat Monitoring", icon: "🔍" },
  { id: "credentials", label: "Credentials", icon: "🔑" },
  { id: "darkweb", label: "Dark Web", icon: "🌐" },
  { id: "reports", label: "Reports", icon: "📝" },
  { id: "api", label: "API Reference", icon: "🔌" },
];

const articles = [
  {
    id: "1",
    category: "getting-started",
    title: "Quick Start Guide",
    description: "Get up and running with CyberNexus in minutes",
  },
  {
    id: "2",
    category: "getting-started",
    title: "Adding Your First Asset",
    description: "Learn how to add domains, IPs, and emails for monitoring",
  },
  {
    id: "3",
    category: "dashboard",
    title: "Understanding Your Dashboard",
    description: "Navigate and customize your threat overview",
  },
  {
    id: "4",
    category: "threats",
    title: "Interpreting Threat Severity",
    description: "What critical, high, medium, and low mean for your org",
  },
  {
    id: "5",
    category: "credentials",
    title: "Responding to Leaked Credentials",
    description: "Best practices for credential leak incidents",
  },
  {
    id: "6",
    category: "api",
    title: "Authentication & API Keys",
    description: "How to authenticate your API requests",
  },
];

export default function HelpPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const filteredArticles = articles.filter((article) => {
    if (selectedCategory && article.category !== selectedCategory) return false;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        article.title.toLowerCase().includes(query) ||
        article.description.toLowerCase().includes(query)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="text-center max-w-2xl mx-auto">
        <h1 className="text-3xl font-mono font-bold text-white mb-4">
          How can we help?
        </h1>
        <p className="text-white/50 mb-6">
          Search our knowledge base or browse categories below
        </p>
        <GlassInput
          placeholder="Search for help articles..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="max-w-lg mx-auto"
          icon={
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          }
        />
      </div>

      {/* Categories */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {categories.map((category) => (
          <GlassCard
            key={category.id}
            onClick={() =>
              setSelectedCategory(
                selectedCategory === category.id ? null : category.id
              )
            }
            className={cn(
              "cursor-pointer text-center py-4",
              selectedCategory === category.id && "border-amber-500/50"
            )}
            padding="sm"
          >
            <div className="text-2xl mb-2">{category.icon}</div>
            <p className="text-xs font-mono text-white/70">{category.label}</p>
          </GlassCard>
        ))}
      </div>

      <GlassCard>
        <h2 className="font-mono text-lg text-white mb-4">
          {selectedCategory
            ? categories.find((c) => c.id === selectedCategory)?.label
            : "Popular Articles"}
        </h2>
        <div className="space-y-3">
          {filteredArticles.map((article) => (
            <div
              key={article.id}
              className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] cursor-pointer transition-colors"
            >
              <h3 className="font-mono text-white mb-1">{article.title}</h3>
              <p className="text-sm text-white/50">{article.description}</p>
            </div>
          ))}
          {filteredArticles.length === 0 && (
            <p className="text-center text-white/40 py-8">
              No articles found. Try a different search.
            </p>
          )}
        </div>
      </GlassCard>

      <div className="grid md:grid-cols-2 gap-6">
        <GlassCard>
          <h2 className="font-mono text-lg text-white mb-4">Contact Support</h2>
          <div className="space-y-4">
            <GlassInput label="Subject" placeholder="Brief description of your issue" />
            <GlassTextarea
              label="Message"
              placeholder="Describe your issue in detail..."
              rows={4}
            />
            <GlassButton variant="primary" className="w-full">
              Send Message
            </GlassButton>
          </div>
        </GlassCard>

        <GlassCard>
          <h2 className="font-mono text-lg text-white mb-4">Other Ways to Get Help</h2>
          <div className="space-y-4">
            {[
              { icon: "📧", label: "Email Support", value: "support@cybernexus.io" },
              { icon: "💬", label: "Live Chat", value: "Available 9am-6pm EST" },
              { icon: "📞", label: "Phone", value: "+1 (555) 123-4567" },
              { icon: "🎮", label: "Discord Community", value: "discord.gg/cybernexus" },
            ].map((item) => (
              <div
                key={item.label}
                className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.02]"
              >
                <span className="text-xl">{item.icon}</span>
                <div>
                  <p className="font-mono text-sm text-white">{item.label}</p>
                  <p className="text-xs text-white/50">{item.value}</p>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}

