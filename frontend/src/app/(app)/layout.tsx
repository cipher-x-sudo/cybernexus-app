"use client";

import { useState, useEffect } from "react";
import { ParticlesBackground } from "@/components/effects";
import { Sidebar, TopBar, CommandPalette } from "@/components/layout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

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
        <ParticlesBackground particleCount={50} />

        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        <div className="lg:pl-64">
          <TopBar
            onMenuClick={() => setSidebarOpen(true)}
            onCommandPaletteOpen={() => setCommandPaletteOpen(true)}
          />

          <main className="relative z-10 p-4 lg:p-6">{children}</main>
        </div>

        <CommandPalette
          isOpen={commandPaletteOpen}
          onClose={() => setCommandPaletteOpen(false)}
        />
      </div>
    </ProtectedRoute>
  );
}

