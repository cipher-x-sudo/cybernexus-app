"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";

// Dynamic import for 3D component to avoid SSR issues
const Graph3D = dynamic(
  () => import("@/components/graph/Graph3D").then((mod) => mod.Graph3D),
  {
    ssr: false,
    loading: () => (
      <div className="w-full flex items-center justify-center bg-[#0a0e1a] rounded-2xl" style={{ height: "700px" }}>
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white/50 font-mono text-sm">Loading 3D Graph...</p>
          <p className="text-white/30 font-mono text-xs mt-2">Initializing WebGL engine</p>
        </div>
      </div>
    ),
  }
);

export default function GraphPage() {
  const [mounted, setMounted] = useState(false);
  const [graphData, setGraphData] = useState<{ nodes: any[]; edges: any[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
    
    // Fetch graph data from API
    const fetchGraphData = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getGraphData({ limit: 1000 });
        setGraphData(data);
      } catch (err: any) {
        console.error("Error fetching graph data:", err);
        setError(err.message || "Failed to load graph data");
      } finally {
        setLoading(false);
      }
    };

    fetchGraphData();

    // Poll for updates every 60 seconds
    const interval = setInterval(fetchGraphData, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-4">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-mono font-bold text-white">Threat Graph</h1>
          <p className="text-sm text-white/50">
            Interactive 3D visualization of threat relationships and connections
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-white/70 text-sm font-mono transition-all">
            Export
          </button>
          <button className="px-4 py-2 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/50 rounded-lg text-amber-500 text-sm font-mono transition-all">
            Add Entity
          </button>
        </div>
      </div>

      {/* 3D Graph */}
      <div className="bg-[#0a0e1a] rounded-2xl overflow-hidden border border-white/5">
        {loading && !graphData ? (
          <div className="w-full flex items-center justify-center bg-[#0a0e1a]" style={{ height: "700px" }}>
            <div className="text-center">
              <div className="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-white/50 font-mono text-sm">Loading graph data...</p>
              <p className="text-white/30 font-mono text-xs mt-2">Fetching from Redis storage</p>
            </div>
          </div>
        ) : error ? (
          <div className="w-full flex items-center justify-center bg-[#0a0e1a]" style={{ height: "700px" }}>
            <div className="text-center">
              <p className="text-red-400 font-mono mb-2">Error loading graph</p>
              <p className="text-white/50 font-mono text-sm">{error}</p>
            </div>
          </div>
        ) : mounted && graphData ? (
          <Graph3D graphData={graphData} />
        ) : (
          <div className="w-full flex items-center justify-center bg-[#0a0e1a]" style={{ height: "700px" }}>
            <div className="text-center">
              <div className="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-white/50 font-mono text-sm">Loading 3D Graph...</p>
              <p className="text-white/30 font-mono text-xs mt-2">Initializing WebGL engine</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

