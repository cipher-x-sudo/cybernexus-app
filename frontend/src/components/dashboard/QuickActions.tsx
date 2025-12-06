"use client";

import { cn } from "@/lib/utils";

const actions = [
  {
    label: "New Scan",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    color: "from-amber-500 to-orange-600",
  },
  {
    label: "Add Asset",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
      </svg>
    ),
    color: "from-blue-500 to-cyan-600",
  },
  {
    label: "Generate Report",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    color: "from-purple-500 to-violet-600",
  },
  {
    label: "View Alerts",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
    ),
    color: "from-red-500 to-rose-600",
  },
  {
    label: "Search Threats",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    color: "from-emerald-500 to-teal-600",
  },
];

export function QuickActions() {
  return (
    <div className="flex flex-wrap gap-3">
      {actions.map((action) => (
        <button
          key={action.label}
          className={cn(
            "group flex items-center gap-2 px-4 py-2.5 rounded-xl",
            "bg-white/[0.03] border border-white/[0.08]",
            "hover:border-white/[0.2] hover:bg-white/[0.05]",
            "transition-all duration-200"
          )}
        >
          <div
            className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center text-white",
              "bg-gradient-to-br",
              action.color,
              "group-hover:scale-110 transition-transform"
            )}
          >
            {action.icon}
          </div>
          <span className="font-mono text-sm text-white/70 group-hover:text-white transition-colors">
            {action.label}
          </span>
        </button>
      ))}
    </div>
  );
}

