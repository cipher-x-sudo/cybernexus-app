"use client";

import React, { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";

interface DomainNode {
  id: string;
  label: string;
  type: string;
  depth?: number;
  requests?: number;
  risk?: number;
  resource_type?: string;
}

interface DomainEdge {
  source: string;
  target: string;
  type?: string;
}

interface DomainTreeViewProps {
  nodes: DomainNode[];
  edges: DomainEdge[];
  className?: string;
}

export function DomainTreeView({ nodes, edges, className }: DomainTreeViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedNode, setSelectedNode] = useState<DomainNode | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");

  // Filter nodes based on type and search
  const filteredNodes = nodes.filter((node) => {
    if (filter !== "all" && node.type !== filter) return false;
    if (searchTerm && !node.label.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  const filteredEdges = edges.filter(
    (edge) =>
      filteredNodes.some((n) => n.id === edge.source) &&
      filteredNodes.some((n) => n.id === edge.target)
  );

  const getNodeColor = (node: DomainNode) => {
    if (node.type === "root") return "bg-orange-500/20 border-orange-500/40 text-orange-400";
    if (node.type === "tracker") return "bg-red-500/20 border-red-500/40 text-red-400";
    if (node.type === "third_party") return "bg-amber-500/20 border-amber-500/40 text-amber-400";
    return "bg-blue-500/20 border-blue-500/40 text-blue-400";
  };

  const getNodeSize = (node: DomainNode) => {
    const baseSize = 60;
    const requestMultiplier = (node.requests || 0) * 2;
    return Math.min(baseSize + requestMultiplier, 120);
  };

  return (
    <GlassCard className={cn("p-6", className)} hover={false}>
      <div className="space-y-4">
        {/* Controls */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search domains..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 bg-white/[0.03] border border-white/[0.08] rounded-lg text-white placeholder-white/30 text-sm"
            />
          </div>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-2 bg-white/[0.03] border border-white/[0.08] rounded-lg text-white text-sm"
          >
            <option value="all">All Types</option>
            <option value="root">Root</option>
            <option value="tracker">Trackers</option>
            <option value="third_party">Third Party</option>
            <option value="domain">Domains</option>
          </select>
        </div>

        {/* Graph Visualization */}
        <div
          ref={containerRef}
          className="w-full h-[600px] border border-white/[0.08] rounded-lg bg-black/20 overflow-auto relative"
        >
          {/* Simple node-link visualization */}
          <svg width="100%" height="100%" className="absolute inset-0">
            {/* Edges */}
            {filteredEdges.map((edge, idx) => {
              const sourceNode = filteredNodes.find((n) => n.id === edge.source);
              const targetNode = filteredNodes.find((n) => n.id === edge.target);
              if (!sourceNode || !targetNode) return null;

              // Simple positioning (in production, use D3.js or vis-network for proper layout)
              const sourceX = 100 + (sourceNode.depth || 0) * 200;
              const sourceY = 100 + (idx % 10) * 50;
              const targetX = 100 + (targetNode.depth || 0) * 200;
              const targetY = 100 + ((idx + 1) % 10) * 50;

              return (
                <line
                  key={`${edge.source}-${edge.target}`}
                  x1={sourceX}
                  y1={sourceY}
                  x2={targetX}
                  y2={targetY}
                  stroke="rgba(255,255,255,0.2)"
                  strokeWidth="1"
                />
              );
            })}

            {/* Nodes */}
            {filteredNodes.map((node, idx) => {
              const x = 100 + (node.depth || 0) * 200;
              const y = 100 + (idx % 10) * 50;
              const size = getNodeSize(node);

              return (
                <g key={node.id}>
                  <circle
                    cx={x}
                    cy={y}
                    r={size / 2}
                    className={cn(
                      "cursor-pointer transition-all hover:scale-110",
                      getNodeColor(node),
                      selectedNode?.id === node.id && "ring-2 ring-orange-500"
                    )}
                    onClick={() => setSelectedNode(node)}
                  />
                  <text
                    x={x}
                    y={y + size / 2 + 15}
                    textAnchor="middle"
                    className="text-xs fill-white/70"
                    style={{ fontSize: "10px" }}
                  >
                    {node.label.length > 20 ? node.label.substring(0, 20) + "..." : node.label}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Fallback: List view for better mobile/accessibility */}
          <div className="md:hidden p-4 space-y-2">
            {filteredNodes.map((node) => (
              <div
                key={node.id}
                className={cn(
                  "p-3 rounded-lg border cursor-pointer",
                  getNodeColor(node),
                  selectedNode?.id === node.id && "ring-2 ring-orange-500"
                )}
                onClick={() => setSelectedNode(node)}
              >
                <div className="font-mono text-sm">{node.label}</div>
                <div className="text-xs text-white/50 mt-1">
                  Type: {node.type} • Requests: {node.requests || 0}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Node Details */}
        {selectedNode && (
          <div className="p-4 bg-white/[0.02] border border-white/[0.08] rounded-lg">
            <h3 className="font-mono font-semibold text-white mb-2">{selectedNode.label}</h3>
            <div className="grid grid-cols-2 gap-2 text-sm text-white/70">
              <div>
                <span className="text-white/50">Type:</span> {selectedNode.type}
              </div>
              <div>
                <span className="text-white/50">Depth:</span> {selectedNode.depth || 0}
              </div>
              <div>
                <span className="text-white/50">Requests:</span> {selectedNode.requests || 0}
              </div>
              {selectedNode.risk !== undefined && (
                <div>
                  <span className="text-white/50">Risk:</span> {Math.round(selectedNode.risk * 100)}%
                </div>
              )}
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs text-white/50 flex-wrap">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-500/20 border border-orange-500/40" />
            <span>Root Domain</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/40" />
            <span>Tracker</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-amber-500/20 border border-amber-500/40" />
            <span>Third Party</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500/20 border border-blue-500/40" />
            <span>Domain</span>
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

