"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

interface CommandItem {
  id: string;
  title: string;
  subtitle?: string;
  icon: React.ReactNode;
  action: () => void;
  category: string;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);

  const commands: CommandItem[] = [
    // Navigation
    {
      id: "nav-dashboard",
      title: "Go to Dashboard",
      subtitle: "View threat overview",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
        </svg>
      ),
      action: () => router.push("/dashboard"),
      category: "Navigation",
    },
    {
      id: "nav-graph",
      title: "Go to Threat Graph",
      subtitle: "3D visualization",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      action: () => router.push("/graph"),
      category: "Navigation",
    },
    {
      id: "nav-map",
      title: "Go to Threat Map",
      subtitle: "Geographic view",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      action: () => router.push("/map"),
      category: "Navigation",
    },
    {
      id: "nav-credentials",
      title: "Go to Credentials",
      subtitle: "Leaked credentials",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
        </svg>
      ),
      action: () => router.push("/credentials"),
      category: "Navigation",
    },
    {
      id: "nav-darkweb",
      title: "Go to Dark Web",
      subtitle: "Monitor mentions",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
        </svg>
      ),
      action: () => router.push("/darkweb"),
      category: "Navigation",
    },
    // Actions
    {
      id: "action-scan",
      title: "Start New Scan",
      subtitle: "Scan assets for threats",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      ),
      action: () => console.log("Start scan"),
      category: "Actions",
    },
    {
      id: "action-report",
      title: "Generate Report",
      subtitle: "Create threat report",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      action: () => router.push("/reports"),
      category: "Actions",
    },
    {
      id: "action-asset",
      title: "Add New Asset",
      subtitle: "Register asset to monitor",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
        </svg>
      ),
      action: () => console.log("Add asset"),
      category: "Actions",
    },
    // Settings
    {
      id: "settings-profile",
      title: "Profile Settings",
      subtitle: "Manage your account",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      ),
      action: () => router.push("/settings"),
      category: "Settings",
    },
    {
      id: "settings-api",
      title: "API Keys",
      subtitle: "Manage API access",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
        </svg>
      ),
      action: () => router.push("/settings"),
      category: "Settings",
    },
  ];

  const filteredCommands = query
    ? commands.filter(
        (cmd) =>
          cmd.title.toLowerCase().includes(query.toLowerCase()) ||
          cmd.subtitle?.toLowerCase().includes(query.toLowerCase())
      )
    : commands;

  const groupedCommands = filteredCommands.reduce(
    (acc, cmd) => {
      if (!acc[cmd.category]) {
        acc[cmd.category] = [];
      }
      acc[cmd.category].push(cmd);
      return acc;
    },
    {} as Record<string, CommandItem[]>
  );

  const flatCommands = Object.values(groupedCommands).flat();

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((i) => (i + 1) % flatCommands.length);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((i) => (i - 1 + flatCommands.length) % flatCommands.length);
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (flatCommands[selectedIndex]) {
          flatCommands[selectedIndex].action();
          onClose();
        }
      } else if (e.key === "Escape") {
        onClose();
      }
    },
    [flatCommands, selectedIndex, onClose]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [isOpen, handleKeyDown]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    if (!isOpen) {
      setQuery("");
      setSelectedIndex(0);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-xl mx-4 glass rounded-2xl border border-white/[0.1] shadow-2xl overflow-hidden animate-scale-in">
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-white/[0.05]">
          <svg
            className="w-5 h-5 text-white/40"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            placeholder="Type a command or search..."
            className="flex-1 bg-transparent text-white placeholder:text-white/40 outline-none font-mono"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
          <kbd className="px-2 py-1 rounded bg-white/[0.05] border border-white/[0.1] text-xs font-mono text-white/40">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto p-2">
          {Object.entries(groupedCommands).map(([category, items]) => (
            <div key={category} className="mb-2">
              <div className="px-3 py-2 text-xs font-mono text-white/30 uppercase tracking-wider">
                {category}
              </div>
              {items.map((cmd) => {
                const index = flatCommands.findIndex((c) => c.id === cmd.id);
                const isSelected = index === selectedIndex;

                return (
                  <button
                    key={cmd.id}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors",
                      isSelected
                        ? "bg-amber-500/20 text-amber-400"
                        : "text-white/70 hover:bg-white/[0.05]"
                    )}
                    onClick={() => {
                      cmd.action();
                      onClose();
                    }}
                    onMouseEnter={() => setSelectedIndex(index)}
                  >
                    <div
                      className={cn(
                        "w-8 h-8 rounded-lg flex items-center justify-center",
                        isSelected
                          ? "bg-amber-500/20 text-amber-400"
                          : "bg-white/[0.05] text-white/50"
                      )}
                    >
                      {cmd.icon}
                    </div>
                    <div className="flex-1 text-left">
                      <p className="font-mono text-sm">{cmd.title}</p>
                      {cmd.subtitle && (
                        <p className="text-xs text-white/40">{cmd.subtitle}</p>
                      )}
                    </div>
                    {isSelected && (
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M13 7l5 5m0 0l-5 5m5-5H6"
                        />
                      </svg>
                    )}
                  </button>
                );
              })}
            </div>
          ))}

          {flatCommands.length === 0 && (
            <div className="px-4 py-8 text-center text-white/40">
              <p className="font-mono">No results found</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-white/[0.05] flex items-center gap-4 text-xs text-white/30">
          <div className="flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 rounded bg-white/[0.05] border border-white/[0.1]">
              ↑
            </kbd>
            <kbd className="px-1.5 py-0.5 rounded bg-white/[0.05] border border-white/[0.1]">
              ↓
            </kbd>
            <span className="ml-1">Navigate</span>
          </div>
          <div className="flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 rounded bg-white/[0.05] border border-white/[0.1]">
              ↵
            </kbd>
            <span className="ml-1">Select</span>
          </div>
        </div>
      </div>
    </div>
  );
}

