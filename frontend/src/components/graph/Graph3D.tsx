"use client";

import { useRef, useState, useMemo, useCallback, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Text, Line } from "@react-three/drei";
import * as THREE from "three";
import { cn } from "@/lib/utils";
import { GlassCard, GlassButton, GlassInput } from "@/components/ui";

// Entity types with unique colors
const entityTypes = {
  ip_address: { color: "#f59e0b", shape: "octahedron" },
  threat: { color: "#ef4444", shape: "box" },
  domain: { color: "#3b82f6", shape: "sphere" },
  asset: { color: "#10b981", shape: "cylinder" },
  credential: { color: "#f97316", shape: "cone" },
  email: { color: "#8b5cf6", shape: "torus" },
  actor: { color: "#ec4899", shape: "dodecahedron" },
  file_hash: { color: "#06b6d4", shape: "icosahedron" },
  vulnerability: { color: "#eab308", shape: "tetrahedron" },
};

// Sample data
const sampleNodes = [
  { id: "1", type: "threat", label: "APT29", x: 0, y: 0, z: 0 },
  { id: "2", type: "ip_address", label: "192.168.1.1", x: 3, y: 1, z: -2 },
  { id: "3", type: "domain", label: "malware.com", x: -3, y: 2, z: 1 },
  { id: "4", type: "credential", label: "admin@corp", x: 2, y: -2, z: 3 },
  { id: "5", type: "actor", label: "CozyBear", x: -2, y: 3, z: -1 },
  { id: "6", type: "asset", label: "Server-01", x: 4, y: -1, z: 2 },
  { id: "7", type: "vulnerability", label: "CVE-2024-001", x: -1, y: -3, z: -2 },
  { id: "8", type: "file_hash", label: "abc123...def", x: 1, y: 2, z: 4 },
];

const sampleEdges = [
  { source: "1", target: "2" },
  { source: "1", target: "3" },
  { source: "1", target: "5" },
  { source: "2", target: "6" },
  { source: "3", target: "4" },
  { source: "5", target: "7" },
  { source: "6", target: "8" },
  { source: "7", target: "8" },
];

interface NodeProps {
  node: typeof sampleNodes[0];
  isHovered: boolean;
  isSelected: boolean;
  onHover: (id: string | null) => void;
  onClick: (id: string) => void;
}

function Node3D({ node, isHovered, isSelected, onHover, onClick }: NodeProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const config = entityTypes[node.type as keyof typeof entityTypes];

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.01;
      if (isHovered || isSelected) {
        meshRef.current.scale.setScalar(1.3);
      } else {
        meshRef.current.scale.setScalar(1);
      }
    }
  });

  const geometry = useMemo(() => {
    switch (config.shape) {
      case "sphere":
        return <sphereGeometry args={[0.3, 16, 16]} />;
      case "box":
        return <boxGeometry args={[0.5, 0.5, 0.5]} />;
      case "octahedron":
        return <octahedronGeometry args={[0.35]} />;
      case "cylinder":
        return <cylinderGeometry args={[0.25, 0.25, 0.5, 16]} />;
      case "cone":
        return <coneGeometry args={[0.3, 0.5, 16]} />;
      case "torus":
        return <torusGeometry args={[0.25, 0.1, 8, 16]} />;
      case "dodecahedron":
        return <dodecahedronGeometry args={[0.35]} />;
      case "icosahedron":
        return <icosahedronGeometry args={[0.35]} />;
      case "tetrahedron":
        return <tetrahedronGeometry args={[0.4]} />;
      default:
        return <sphereGeometry args={[0.3, 16, 16]} />;
    }
  }, [config.shape]);

  return (
    <group position={[node.x, node.y, node.z]}>
      <mesh
        ref={meshRef}
        onPointerOver={() => onHover(node.id)}
        onPointerOut={() => onHover(null)}
        onClick={() => onClick(node.id)}
      >
        {geometry}
        <meshStandardMaterial
          color={config.color}
          emissive={config.color}
          emissiveIntensity={isHovered || isSelected ? 0.8 : 0.3}
          transparent
          opacity={0.9}
          wireframe={true}
        />
      </mesh>
      {/* Glow effect */}
      <mesh scale={1.5}>
        {geometry}
        <meshBasicMaterial
          color={config.color}
          transparent
          opacity={isHovered || isSelected ? 0.2 : 0.05}
        />
      </mesh>
      {/* Label */}
      <Text
        position={[0, 0.7, 0]}
        fontSize={0.2}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {node.label}
      </Text>
    </group>
  );
}

function Edge3D({ source, target, highlighted }: { source: THREE.Vector3; target: THREE.Vector3; highlighted: boolean }) {
  return (
    <Line
      points={[source, target]}
      color={highlighted ? "#f59e0b" : "#ffffff"}
      lineWidth={highlighted ? 2 : 1}
      transparent
      opacity={highlighted ? 0.8 : 0.2}
    />
  );
}

function Scene({ nodes, edges, hoveredNode, selectedNode, onHover, onClick }: {
  nodes: typeof sampleNodes;
  edges: typeof sampleEdges;
  hoveredNode: string | null;
  selectedNode: string | null;
  onHover: (id: string | null) => void;
  onClick: (id: string) => void;
}) {
  const nodePositions = useMemo(() => {
    const positions: Record<string, THREE.Vector3> = {};
    nodes.forEach((node) => {
      positions[node.id] = new THREE.Vector3(node.x, node.y, node.z);
    });
    return positions;
  }, [nodes]);

  return (
    <>
      {/* Ambient light */}
      <ambientLight intensity={0.3} />
      {/* Point lights */}
      <pointLight position={[10, 10, 10]} intensity={0.8} color="#f59e0b" />
      <pointLight position={[-10, -10, -10]} intensity={0.5} color="#3b82f6" />

      {/* Grid */}
      <gridHelper args={[20, 20, "#f59e0b", "#1a1a2e"]} position={[0, -5, 0]} />

      {/* Edges */}
      {edges.map((edge, i) => {
        const highlighted = hoveredNode === edge.source || hoveredNode === edge.target ||
          selectedNode === edge.source || selectedNode === edge.target;
        return (
          <Edge3D
            key={i}
            source={nodePositions[edge.source]}
            target={nodePositions[edge.target]}
            highlighted={highlighted}
          />
        );
      })}

      {/* Nodes */}
      {nodes.map((node) => (
        <Node3D
          key={node.id}
          node={node}
          isHovered={hoveredNode === node.id}
          isSelected={selectedNode === node.id}
          onHover={onHover}
          onClick={onClick}
        />
      ))}

      {/* Controls */}
      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        minDistance={5}
        maxDistance={30}
      />
    </>
  );
}

export function Graph3D() {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [visibleTypes, setVisibleTypes] = useState<string[]>(Object.keys(entityTypes));
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    // Check WebGL support
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) {
        setHasError(true);
        return;
      }
      setIsLoaded(true);
    } catch (e) {
      setHasError(true);
    }
  }, []);

  const filteredNodes = useMemo(() => {
    return sampleNodes.filter((node) => {
      if (!visibleTypes.includes(node.type)) return false;
      if (searchQuery && !node.label.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    });
  }, [searchQuery, visibleTypes]);

  const filteredEdges = useMemo(() => {
    const nodeIds = new Set(filteredNodes.map((n) => n.id));
    return sampleEdges.filter(
      (edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target)
    );
  }, [filteredNodes]);

  const toggleType = (type: string) => {
    setVisibleTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const selectedNodeData = selectedNode
    ? sampleNodes.find((n) => n.id === selectedNode)
    : null;

  if (hasError) {
    return (
      <div className="relative w-full h-full min-h-[600px] flex items-center justify-center bg-[#0a0e1a] rounded-2xl">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 text-red-500">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-white font-mono mb-2">WebGL Not Supported</h3>
          <p className="text-white/50 text-sm">Your browser doesn&apos;t support 3D graphics.</p>
        </div>
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="relative w-full h-full min-h-[600px] flex items-center justify-center bg-[#0a0e1a] rounded-2xl">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white/50 font-mono text-sm">Initializing 3D Graph...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full min-h-[600px]">
      {/* 3D Canvas */}
      <Canvas
        camera={{ position: [10, 8, 10], fov: 50 }}
        className="bg-[#0a0e1a]"
        onCreated={() => setIsLoaded(true)}
        fallback={
          <div className="w-full h-full flex items-center justify-center bg-[#0a0e1a]">
            <p className="text-white/50 font-mono">Loading 3D Engine...</p>
          </div>
        }
      >
        <Scene
          nodes={filteredNodes}
          edges={filteredEdges}
          hoveredNode={hoveredNode}
          selectedNode={selectedNode}
          onHover={setHoveredNode}
          onClick={setSelectedNode}
        />
      </Canvas>

      {/* Control panel */}
      <div className="absolute top-4 left-4 w-64 space-y-4">
        {/* Search */}
        <GlassCard padding="sm">
          <GlassInput
            placeholder="Search entities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            }
          />
        </GlassCard>

        {/* Entity type filters */}
        <GlassCard padding="sm">
          <p className="text-xs font-mono text-white/50 mb-3 uppercase tracking-wider">
            Entity Types
          </p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(entityTypes).map(([type, config]) => (
              <button
                key={type}
                onClick={() => toggleType(type)}
                className={cn(
                  "px-2 py-1 rounded-lg text-xs font-mono transition-all",
                  visibleTypes.includes(type)
                    ? "bg-white/10 text-white"
                    : "bg-transparent text-white/30"
                )}
                style={{
                  borderColor: visibleTypes.includes(type) ? config.color : "transparent",
                  borderWidth: 1,
                }}
              >
                {type.replace("_", " ")}
              </button>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Node details panel */}
      {selectedNodeData && (
        <div className="absolute top-4 right-4 w-72">
          <GlassCard>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-mono font-semibold text-white">Entity Details</h3>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-white/40 hover:text-white"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: entityTypes[selectedNodeData.type as keyof typeof entityTypes].color }}
                />
                <span className="font-mono text-sm text-white/70">
                  {selectedNodeData.type.replace("_", " ")}
                </span>
              </div>

              <div>
                <p className="text-xs text-white/40 mb-1">Label</p>
                <p className="font-mono text-white">{selectedNodeData.label}</p>
              </div>

              <div>
                <p className="text-xs text-white/40 mb-1">Connections</p>
                <p className="font-mono text-white">
                  {sampleEdges.filter(
                    (e) => e.source === selectedNode || e.target === selectedNode
                  ).length}
                </p>
              </div>

              <div className="pt-3 border-t border-white/[0.05]">
                <GlassButton variant="primary" size="sm" className="w-full">
                  View Details
                </GlassButton>
              </div>
            </div>
          </GlassCard>
        </div>
      )}

      {/* Instructions */}
      <div className="absolute bottom-4 left-4">
        <GlassCard padding="sm" className="text-xs text-white/40 space-y-1">
          <p>🖱️ Drag to rotate</p>
          <p>🔍 Scroll to zoom</p>
          <p>👆 Click node for details</p>
        </GlassCard>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 right-4">
        <GlassCard padding="sm">
          <p className="text-xs font-mono text-white/50 mb-2 uppercase tracking-wider">
            Legend
          </p>
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(entityTypes).map(([type, config]) => (
              <div key={type} className="flex items-center gap-1.5">
                <div
                  className="w-2 h-2 rounded-sm"
                  style={{ backgroundColor: config.color }}
                />
                <span className="text-[10px] text-white/40">
                  {type.split("_")[0]}
                </span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
