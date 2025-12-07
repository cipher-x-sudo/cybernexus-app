"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";

// Dynamic import for 3D component to avoid SSR issues
const Graph3D = dynamic(
  () => import("@/components/graph/Graph3D").then((mod) => mod.Graph3D),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[600px] glass rounded-2xl flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white/50 font-mono text-sm">Loading 3D Graph...</p>
        </div>
      </div>
    ),
  }
);

export default function GraphPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-mono font-bold text-white">Threat Graph</h1>
        <p className="text-sm text-white/50">
          Interactive 3D visualization of threat relationships and connections
        </p>
      </div>

      {/* 3D Graph */}
      <div className="glass rounded-2xl overflow-hidden">
        {mounted ? (
          <Graph3D />
        ) : (
          <div className="w-full h-[600px] flex items-center justify-center bg-[#0a0e1a]">
            <div className="text-center">
              <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-white/50 font-mono text-sm">Loading 3D Graph...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

