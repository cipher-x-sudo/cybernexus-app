"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { GlassButton } from "@/components/ui";
import { Badge } from "@/components/ui";

interface TopBarProps {
  onMenuClick: () => void;
  onCommandPaletteOpen: () => void;
}

export function TopBar({ onMenuClick, onCommandPaletteOpen }: TopBarProps) {
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 h-16 bg-[#0a0e1a]/80 backdrop-blur-xl border-b border-white/[0.05]">
      <div className="flex items-center justify-between h-full px-4 lg:px-6">
        {/* Left side */}
        <div className="flex items-center gap-4">
          {/* Menu button (mobile) */}
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-lg text-white/60 hover:bg-white/[0.05] hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          {/* Search / Command palette trigger */}
          <button
            onClick={onCommandPaletteOpen}
            className="flex items-center gap-3 px-4 py-2 rounded-xl bg-white/[0.03] border border-white/[0.08] text-white/40 hover:bg-white/[0.05] hover:border-white/[0.12] transition-all w-64 lg:w-80"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span className="flex-1 text-left text-sm font-mono">Search threats...</span>
            <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded bg-white/[0.05] border border-white/[0.1] text-xs font-mono">
              <span>⌘</span>
              <span>K</span>
            </kbd>
          </button>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {/* Connection status */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-xs font-mono text-emerald-400">Live</span>
          </div>

          {/* Quick actions */}
          <GlassButton variant="ghost" size="sm" className="hidden sm:flex">
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Scan
          </GlassButton>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              className="relative p-2 rounded-lg text-white/60 hover:bg-white/[0.05] hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {/* Notification dot */}
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500" />
            </button>

            {/* Notification dropdown */}
            {notificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 glass rounded-xl border border-white/[0.08] shadow-xl overflow-hidden">
                <div className="p-4 border-b border-white/[0.05]">
                  <div className="flex items-center justify-between">
                    <h3 className="font-mono font-semibold text-white">Notifications</h3>
                    <Badge variant="critical" size="sm">3 New</Badge>
                  </div>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {[
                    {
                      title: "Critical threat detected",
                      message: "New APT activity targeting your domain",
                      time: "2 min ago",
                      severity: "critical",
                    },
                    {
                      title: "Credential leak found",
                      message: "5 employee credentials found on dark web",
                      time: "15 min ago",
                      severity: "high",
                    },
                    {
                      title: "Scan completed",
                      message: "Weekly threat scan finished",
                      time: "1 hour ago",
                      severity: "info",
                    },
                  ].map((notification, i) => (
                    <div
                      key={i}
                      className="p-4 border-b border-white/[0.05] hover:bg-white/[0.02] cursor-pointer transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div
                          className={cn(
                            "w-2 h-2 rounded-full mt-2 flex-shrink-0",
                            notification.severity === "critical" && "bg-red-500",
                            notification.severity === "high" && "bg-orange-500",
                            notification.severity === "info" && "bg-blue-500"
                          )}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="font-mono text-sm text-white">
                            {notification.title}
                          </p>
                          <p className="text-xs text-white/50 mt-0.5 truncate">
                            {notification.message}
                          </p>
                          <p className="text-xs text-white/30 mt-1">
                            {notification.time}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="p-3 border-t border-white/[0.05]">
                  <button className="w-full text-center text-sm font-mono text-amber-400 hover:text-amber-300 transition-colors">
                    View all notifications
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Profile */}
          <button className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-white/[0.05] transition-colors">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-mono text-sm font-bold">
              JD
            </div>
          </button>
        </div>
      </div>
    </header>
  );
}

