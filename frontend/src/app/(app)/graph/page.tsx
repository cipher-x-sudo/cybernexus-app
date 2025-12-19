"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
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
  const searchParams = useSearchParams();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [graphData, setGraphData] = useState<{ nodes: any[]; edges: any[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
  const [findingInfo, setFindingInfo] = useState<{ id: string; title: string } | null>(null);
  const [depth, setDepth] = useState<number>(2);

  useEffect(() => {
    setMounted(true);
    
    // Read query parameters
    const findingId = searchParams.get("findingId");
    const nodeId = searchParams.get("nodeId");
    const depthParam = searchParams.get("depth");
    
    if (depthParam) {
      const parsedDepth = parseInt(depthParam, 10);
      if (!isNaN(parsedDepth) && parsedDepth >= 1 && parsedDepth <= 5) {
        setDepth(parsedDepth);
      }
    }
    
    // Fetch graph data from API
    const fetchGraphData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        if (findingId) {
          // Fetch finding-focused graph
          const [graphDataResult, findingResult] = await Promise.all([
            api.getGraphDataForFinding(findingId, depth),
            api.getFinding(findingId).catch(() => null)
          ]);
          
          setGraphData(graphDataResult);
          
          if (findingResult) {
            setFindingInfo({ id: findingId, title: findingResult.title });
            // Set focused node to first affected asset if available
            if (findingResult.affected_assets && findingResult.affected_assets.length > 0) {
              setFocusedNodeId(findingResult.affected_assets[0]);
            } else if (findingResult.target) {
              setFocusedNodeId(findingResult.target);
            }
          }
        } else if (nodeId) {
          // Fetch node-focused graph
          const data = await api.getGraphDataForNode(nodeId, depth);
          setGraphData(data);
          setFocusedNodeId(nodeId);
          setFindingInfo(null);
        } else {
          // Fetch full graph
          const data = await api.getGraphData({ limit: 1000 });
          setGraphData(data);
          setFocusedNodeId(null);
          setFindingInfo(null);
        }
      } catch (err: any) {
        console.error("Error fetching graph data:", err);
        setError(err.message || "Failed to load graph data");
      } finally {
        setLoading(false);
      }
    };

    fetchGraphData();

    // Poll for updates every 60 seconds (only if not in focused mode)
    if (!findingId && !nodeId) {
      const interval = setInterval(fetchGraphData, 60000);
      return () => clearInterval(interval);
    }
  }, [searchParams, depth]);
  
  const handleShowFullGraph = () => {
    router.push("/graph");
  };
  
  const handleDepthChange = (newDepth: number) => {
    setDepth(newDepth);
    const findingId = searchParams.get("findingId");
    const nodeId = searchParams.get("nodeId");
    
    if (findingId) {
      router.push(`/graph?findingId=${findingId}&depth=${newDepth}`);
    } else if (nodeId) {
      router.push(`/graph?nodeId=${nodeId}&depth=${newDepth}`);
    }
  };

  return (
    <div className="space-y-4">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-mono font-bold text-white">Threat Graph</h1>
          <p className="text-sm text-white/50">
            Interactive 3D visualization of threat relationships and connections
          </p>
          {findingInfo && (
            <div className="mt-2 flex items-center gap-2">
              <span className="text-xs text-white/40 font-mono">Viewing:</span>
              <span className="text-xs text-amber-400 font-mono">{findingInfo.title}</span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {(findingInfo || focusedNodeId) && (
            <button
              onClick={handleShowFullGraph}
              className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-white/70 text-sm font-mono transition-all"
            >
              Show Full Graph
            </button>
          )}
          <div className="flex items-center gap-2 px-3 py-2 bg-white/5 border border-white/10 rounded-lg">
            <span className="text-xs text-white/50 font-mono">Depth:</span>
            <select
              value={depth}
              onChange={(e) => handleDepthChange(parseInt(e.target.value, 10))}
              className="bg-transparent text-white/70 text-xs font-mono border-none outline-none cursor-pointer"
            >
              <option value={1}>1 hop</option>
              <option value={2}>2 hops</option>
              <option value={3}>3 hops</option>
            </select>
          </div>
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
              <p className="text-white/30 font-mono text-xs mt-2">Fetching from database</p>
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
          <Graph3D graphData={graphData} focusedNodeId={focusedNodeId || undefined} />
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

