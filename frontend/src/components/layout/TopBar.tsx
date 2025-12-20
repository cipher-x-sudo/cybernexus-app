"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { cn, formatRelativeTime } from "@/lib/utils";
import { GlassButton } from "@/components/ui";
import { Badge } from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { useNotifications } from "@/lib/notifications";

interface TopBarProps {
  onMenuClick: () => void;
  onCommandPaletteOpen: () => void;
}

export function TopBar({ onMenuClick, onCommandPaletteOpen }: TopBarProps) {
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { logout, user } = useAuth();
  
  // Get real notifications
  const { notifications, unreadCount, markAsRead, loading } = useNotifications({
    limit: 10,
    autoPoll: true,
  });

  // Close profile menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target as Node)) {
        setProfileMenuOpen(false);
      }
    };

    if (profileMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [profileMenuOpen]);

  const handleLogout = () => {
    logout();
    setProfileMenuOpen(false);
  };

  const handleSettings = () => {
    router.push("/settings");
    setProfileMenuOpen(false);
  };

  // Get user initials
  const getUserInitials = () => {
    if (user?.full_name) {
      const names = user.full_name.split(" ");
      if (names.length >= 2) {
        return `${names[0][0]}${names[names.length - 1][0]}`.toUpperCase();
      }
      return user.full_name.substring(0, 2).toUpperCase();
    }
    if (user?.username) {
      return user.username.substring(0, 2).toUpperCase();
    }
    return "JD";
  };

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
          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              className="relative p-2 rounded-lg text-white/60 hover:bg-white/[0.05] hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {/* Notification dot - only show if there are unread notifications */}
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500" />
              )}
            </button>

            {/* Notification dropdown */}
            {notificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-[#0a0e1a] rounded-xl border border-white/[0.08] shadow-xl overflow-hidden">
                <div className="p-4 border-b border-white/[0.05]">
                  <div className="flex items-center justify-between">
                    <h3 className="font-mono font-semibold text-white">Notifications</h3>
                    {unreadCount > 0 && (
                      <Badge 
                        variant={unreadCount > 5 ? "critical" : "high"} 
                        size="sm"
                      >
                        {unreadCount} New
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {loading && notifications.length === 0 ? (
                    <div className="p-4 text-center text-white/50 text-sm">
                      Loading notifications...
                    </div>
                  ) : notifications.length === 0 ? (
                    <div className="p-4 text-center text-white/50 text-sm">
                      No notifications
                    </div>
                  ) : (
                    notifications.map((notification) => (
                      <div
                        key={notification.id}
                        onClick={() => {
                          if (!notification.read) {
                            markAsRead(notification.id);
                          }
                        }}
                        className={cn(
                          "p-4 border-b border-white/[0.05] hover:bg-white/[0.02] cursor-pointer transition-colors",
                          !notification.read && "bg-white/[0.01]"
                        )}
                      >
                        <div className="flex items-start gap-3">
                          <div
                            className={cn(
                              "w-2 h-2 rounded-full mt-2 flex-shrink-0",
                              notification.severity === "critical" && "bg-red-500",
                              notification.severity === "high" && "bg-orange-500",
                              notification.severity === "medium" && "bg-yellow-500",
                              notification.severity === "low" && "bg-blue-500",
                              notification.severity === "info" && "bg-blue-400"
                            )}
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p className="font-mono text-sm text-white">
                                {notification.title}
                              </p>
                              {!notification.read && (
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" />
                              )}
                            </div>
                            <p className="text-xs text-white/50 mt-0.5 truncate">
                              {notification.message}
                            </p>
                            <p className="text-xs text-white/30 mt-1">
                              {formatRelativeTime(notification.timestamp)}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Profile */}
          <div className="relative" ref={profileMenuRef}>
            <button
              onClick={() => setProfileMenuOpen(!profileMenuOpen)}
              className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-white/[0.05] transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-mono text-sm font-bold">
                {getUserInitials()}
              </div>
            </button>

            {/* Profile dropdown menu */}
            {profileMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-[#0a0e1a] rounded-xl border border-white/[0.08] shadow-xl overflow-hidden z-50 backdrop-blur-xl">
                <div className="p-4 border-b border-white/[0.05]">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-mono text-sm font-bold">
                      {getUserInitials()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-mono text-sm text-white truncate">
                        {user?.full_name || user?.username || "User"}
                      </p>
                      <p className="text-xs text-white/50 truncate">
                        {user?.email || "user@company.com"}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="py-2">
                  <button
                    onClick={handleSettings}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-white/[0.05] transition-colors"
                  >
                    <svg className="w-4 h-4 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span className="font-mono text-sm text-white">Settings</span>
                  </button>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-white/[0.05] transition-colors text-red-400 hover:text-red-300"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    <span className="font-mono text-sm">Logout</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

