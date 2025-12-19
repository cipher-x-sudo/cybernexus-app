"use client";

import { useState, useEffect } from "react";
import { ParticlesBackground } from "@/components/effects";
import { Sidebar, TopBar, CommandPalette } from "@/components/layout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  // Keyboard shortcut for command palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[#0a0e1a]">
        {/* Background */}
        <ParticlesBackground particleCount={50} />

        {/* Sidebar */}
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        {/* Main content */}
        <div className="lg:pl-64">
          {/* Top bar */}
          <TopBar
            onMenuClick={() => setSidebarOpen(true)}
            onCommandPaletteOpen={() => setCommandPaletteOpen(true)}
          />

          {/* Page content */}
          <main className="relative z-10 p-4 lg:p-6">{children}</main>
        </div>

        {/* Command palette */}
        <CommandPalette
          isOpen={commandPaletteOpen}
          onClose={() => setCommandPaletteOpen(false)}
        />
      </div>
    </ProtectedRoute>
  );
}

