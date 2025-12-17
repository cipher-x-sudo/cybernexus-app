"use client";

import React, { useEffect, useRef, useState } from "react";
// @ts-ignore - vis-network doesn't have complete TypeScript definitions
import { Network } from "vis-network/standalone";
// @ts-ignore - vis-network doesn't have complete TypeScript definitions
import { Data, Options, Node, Edge } from "vis-network";
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
  const networkRef = useRef<Network | null>(null);
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

  // Get node color for vis-network
  const getNodeColor = (node: DomainNode) => {
    if (node.type === "root") {
      return {
        background: "rgba(251, 146, 60, 0.2)",
        border: "rgba(251, 146, 60, 0.6)",
        highlight: { background: "rgba(251, 146, 60, 0.4)", border: "rgba(251, 146, 60, 0.8)" },
        hover: { background: "rgba(251, 146, 60, 0.3)", border: "rgba(251, 146, 60, 0.7)" },
      };
    }
    if (node.type === "tracker") {
      return {
        background: "rgba(239, 68, 68, 0.2)",
        border: "rgba(239, 68, 68, 0.6)",
        highlight: { background: "rgba(239, 68, 68, 0.4)", border: "rgba(239, 68, 68, 0.8)" },
        hover: { background: "rgba(239, 68, 68, 0.3)", border: "rgba(239, 68, 68, 0.7)" },
      };
    }
    if (node.type === "third_party") {
      return {
        background: "rgba(245, 158, 11, 0.2)",
        border: "rgba(245, 158, 11, 0.6)",
        highlight: { background: "rgba(245, 158, 11, 0.4)", border: "rgba(245, 158, 11, 0.8)" },
        hover: { background: "rgba(245, 158, 11, 0.3)", border: "rgba(245, 158, 11, 0.7)" },
      };
    }
    return {
      background: "rgba(59, 130, 246, 0.2)",
      border: "rgba(59, 130, 246, 0.6)",
      highlight: { background: "rgba(59, 130, 246, 0.4)", border: "rgba(59, 130, 246, 0.8)" },
      hover: { background: "rgba(59, 130, 246, 0.3)", border: "rgba(59, 130, 246, 0.7)" },
    };
  };

  const getNodeSize = (node: DomainNode) => {
    const baseSize = 30;
    const requestMultiplier = Math.min((node.requests || 0) * 2, 40);
    return baseSize + requestMultiplier;
  };

  // Helper function to convert nodes/edges to vis-network format
  const createNetworkData = (nodes: DomainNode[], edges: DomainEdge[]): Data => {
    const visNodes: Node[] = nodes.map((node) => {
      const size = getNodeSize(node);
      const color = getNodeColor(node);
      return {
        id: node.id,
        label: node.label.length > 30 ? node.label.substring(0, 30) + "..." : node.label,
        color: color,
        size: size,
        shape: "box",
        font: { color: "#ffffff", size: 12, face: "monospace" },
        borderWidth: 2,
        shadow: {
          enabled: true,
          color: "rgba(0, 0, 0, 0.3)",
          size: 5,
          x: 2,
          y: 2,
        },
        data: {
          originalNode: node,
        },
      };
    });

    const visEdges: Edge[] = edges.map((edge) => ({
      from: edge.source,
      to: edge.target,
      arrows: "to",
      color: { color: "rgba(255, 255, 255, 0.3)", highlight: "rgba(255, 255, 255, 0.5)" },
      width: 1.5,
      smooth: {
        enabled: true,
        type: "curvedCW",
        roundness: 0.2,
      },
    }));

    return {
      nodes: visNodes,
      edges: visEdges,
    };
  };

  // Initialize and update vis-network
  useEffect(() => {
    if (!containerRef.current) return;

    const data = createNetworkData(filteredNodes, filteredEdges);

    const options: Options = {
      layout: {
        hierarchical: {
          direction: "UD", // Up-Down tree layout
          sortMethod: "directed",
          nodeSpacing: 150,
          levelSeparation: 200,
          treeSpacing: 200,
          blockShifting: true,
          edgeMinimization: true,
          parentCentralization: true,
        },
      },
      physics: {
        enabled: false, // Disable physics for hierarchical layout
      },
      interaction: {
        zoomView: true,
        dragView: true,
        selectConnectedEdges: false,
      },
      nodes: {
        chosen: {
          node: (values: any, id: string | number, selected: boolean, hovering: boolean) => {
            if (selected || hovering) {
              values.borderWidth = 3;
            }
          },
        },
      },
      edges: {
        arrows: {
          to: {
            enabled: true,
            scaleFactor: 0.8,
          },
        },
      },
    };

    // Create or update network
    if (!networkRef.current) {
      // Create new network
      const network = new Network(containerRef.current, data, options);
      networkRef.current = network;

      // Handle node selection (only register once)
      network.on("selectNode", (params: any) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const node = filteredNodes.find((n) => n.id === nodeId);
          if (node) {
            setSelectedNode(node);
          }
        }
      });

      // Handle node deselection
      network.on("deselectNode", () => {
        setSelectedNode(null);
      });

      // Fit network to container on initial load
      setTimeout(() => {
        network.fit({
          animation: {
            duration: 500,
            easingFunction: "easeInOutQuad",
          },
        });
      }, 100);
    } else {
      // Update existing network with new data
      networkRef.current.setData(data);
      setTimeout(() => {
        networkRef.current?.fit({
          animation: {
            duration: 500,
            easingFunction: "easeInOutQuad",
          },
        });
      }, 100);
    }

    // Cleanup only on unmount
    return () => {
      // Don't destroy on every update, only on unmount
      // The network will be updated via setData above
    };
  }, [filteredNodes, filteredEdges]);

  // Separate effect for cleanup on unmount
  useEffect(() => {
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, []);

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
        <div className="relative">
          <div
            ref={containerRef}
            className="w-full h-[600px] border border-white/[0.08] rounded-lg bg-black/20"
          />
          {/* Zoom Controls */}
          <div className="absolute top-2 right-2 flex flex-col gap-2 z-10">
            <button
              onClick={() => {
                if (networkRef.current) {
                  networkRef.current.zoomIn({
                    animation: {
                      duration: 300,
                      easingFunction: "easeInOutQuad",
                    },
                  });
                }
              }}
              className="p-2 bg-white/[0.1] border border-white/[0.2] rounded-lg text-white hover:bg-white/[0.15] transition-colors"
              title="Zoom In"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
            <button
              onClick={() => {
                if (networkRef.current) {
                  networkRef.current.zoomOut({
                    animation: {
                      duration: 300,
                      easingFunction: "easeInOutQuad",
                    },
                  });
                }
              }}
              className="p-2 bg-white/[0.1] border border-white/[0.2] rounded-lg text-white hover:bg-white/[0.15] transition-colors"
              title="Zoom Out"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </button>
            <button
              onClick={() => {
                if (networkRef.current) {
                  networkRef.current.fit({
                    animation: {
                      duration: 500,
                      easingFunction: "easeInOutQuad",
                    },
                  });
                }
              }}
              className="p-2 bg-white/[0.1] border border-white/[0.2] rounded-lg text-white hover:bg-white/[0.15] transition-colors"
              title="Fit to Screen"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            </button>
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

