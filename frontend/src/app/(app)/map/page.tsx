"use client";

import { useEffect, useRef, useState } from "react";
import { GlassCard, GlassButton, Badge } from "@/components/ui";
import { cn } from "@/lib/utils";

interface ThreatLocation {
  id: string;
  lat: number;
  lng: number;
  severity: "critical" | "high" | "medium" | "low";
  type: string;
  label: string;
  count: number;
}

async function fetchThreatLocations(): Promise<ThreatLocation[]> {
  try {
    const response = await fetch('/api/threats?with_location=true');
    if (!response.ok) {
      throw new Error('Failed to fetch threat locations');
    }
    const data = await response.json();
    return data.map((threat: any) => ({
      id: threat.id,
      lat: threat.metadata?.location?.lat || 0,
      lng: threat.metadata?.location?.lng || 0,
      severity: threat.severity,
      type: threat.category,
      label: threat.metadata?.location?.label || threat.title,
      count: 1
    })).filter((t: ThreatLocation) => t.lat !== 0 && t.lng !== 0);
  } catch (error) {
    console.error('Error fetching threat locations:', error);
    return [];
  }
}

export default function MapPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedThreat, setSelectedThreat] = useState<ThreatLocation | null>(null);
  const [hoveredThreat, setHoveredThreat] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [threats, setThreats] = useState<ThreatLocation[]>([]);

  useEffect(() => {
    fetchThreatLocations().then(setThreats);
  }, []);

  const filteredThreats = threats.filter(
    (t) => filter === "all" || t.severity === filter
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    };

    resize();
    window.addEventListener("resize", resize);

    const severityColors = {
      critical: { r: 239, g: 68, b: 68 },
      high: { r: 249, g: 115, b: 22 },
      medium: { r: 234, g: 179, b: 8 },
      low: { r: 59, g: 130, b: 246 },
    };

    const drawMap = (time: number) => {
      const width = canvas.width / window.devicePixelRatio;
      const height = canvas.height / window.devicePixelRatio;

      ctx.clearRect(0, 0, width, height);

      ctx.strokeStyle = "rgba(245, 158, 11, 0.03)";
      ctx.lineWidth = 1;

      for (let i = 0; i <= 18; i++) {
        ctx.beginPath();
        ctx.moveTo(0, (height / 18) * i);
        ctx.lineTo(width, (height / 18) * i);
        ctx.stroke();
      }

      for (let i = 0; i <= 36; i++) {
        ctx.beginPath();
        ctx.moveTo((width / 36) * i, 0);
        ctx.lineTo((width / 36) * i, height);
        ctx.stroke();
      }

      // Draw neon continent outlines
      ctx.strokeStyle = "rgba(245, 158, 11, 0.4)";
      ctx.lineWidth = 2;
      ctx.shadowColor = "#f59e0b";
      ctx.shadowBlur = 10;

      ctx.beginPath();
      ctx.moveTo(width * 0.1, height * 0.25);
      ctx.quadraticCurveTo(width * 0.15, height * 0.12, width * 0.28, height * 0.1);
      ctx.quadraticCurveTo(width * 0.38, height * 0.08, width * 0.35, height * 0.32);
      ctx.quadraticCurveTo(width * 0.32, height * 0.48, width * 0.18, height * 0.52);
      ctx.quadraticCurveTo(width * 0.1, height * 0.45, width * 0.1, height * 0.25);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(width * 0.2, height * 0.55);
      ctx.quadraticCurveTo(width * 0.28, height * 0.54, width * 0.32, height * 0.68);
      ctx.quadraticCurveTo(width * 0.3, height * 0.88, width * 0.24, height * 0.92);
      ctx.quadraticCurveTo(width * 0.18, height * 0.78, width * 0.2, height * 0.55);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(width * 0.45, height * 0.15);
      ctx.quadraticCurveTo(width * 0.56, height * 0.1, width * 0.58, height * 0.25);
      ctx.quadraticCurveTo(width * 0.54, height * 0.38, width * 0.44, height * 0.38);
      ctx.quadraticCurveTo(width * 0.4, height * 0.26, width * 0.45, height * 0.15);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(width * 0.44, height * 0.42);
      ctx.quadraticCurveTo(width * 0.56, height * 0.4, width * 0.6, height * 0.52);
      ctx.quadraticCurveTo(width * 0.58, height * 0.75, width * 0.5, height * 0.78);
      ctx.quadraticCurveTo(width * 0.42, height * 0.62, width * 0.44, height * 0.42);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(width * 0.58, height * 0.12);
      ctx.quadraticCurveTo(width * 0.78, height * 0.08, width * 0.92, height * 0.18);
      ctx.quadraticCurveTo(width * 0.98, height * 0.38, width * 0.9, height * 0.48);
      ctx.quadraticCurveTo(width * 0.72, height * 0.55, width * 0.6, height * 0.42);
      ctx.quadraticCurveTo(width * 0.55, height * 0.25, width * 0.58, height * 0.12);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(width * 0.8, height * 0.65);
      ctx.quadraticCurveTo(width * 0.92, height * 0.62, width * 0.95, height * 0.72);
      ctx.quadraticCurveTo(width * 0.92, height * 0.82, width * 0.82, height * 0.8);
      ctx.quadraticCurveTo(width * 0.76, height * 0.72, width * 0.8, height * 0.65);
      ctx.stroke();

      ctx.shadowBlur = 0;

      filteredThreats.forEach((threat) => {
        const x = ((threat.lng + 180) / 360) * width;
        const y = ((90 - threat.lat) / 180) * height;
        const color = severityColors[threat.severity];
        const isHovered = hoveredThreat === threat.id;
        const isSelected = selectedThreat?.id === threat.id;
        const pulse = Math.sin(time * 0.004 + threat.lat) * 0.3 + 0.7;
        const baseSize = 4 + threat.count * 0.3;
        const size = isHovered || isSelected ? baseSize * 1.5 : baseSize;

        const heatGradient = ctx.createRadialGradient(x, y, 0, x, y, size * 8);
        heatGradient.addColorStop(0, `rgba(${color.r}, ${color.g}, ${color.b}, ${0.3 * pulse})`);
        heatGradient.addColorStop(1, "transparent");
        ctx.fillStyle = heatGradient;
        ctx.beginPath();
        ctx.arc(x, y, size * 8, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${pulse})`;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();

        if (isHovered || isSelected) {
          ctx.strokeStyle = `rgba(${color.r}, ${color.g}, ${color.b}, 0.8)`;
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.arc(x, y, size + 4, 0, Math.PI * 2);
          ctx.stroke();
        }
      });
    };

    let animationId: number;
    const animate = (time: number) => {
      drawMap(time);
      animationId = requestAnimationFrame(animate);
    };

    animate(0);

    const handleClick = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const width = rect.width;
      const height = rect.height;

      for (const threat of filteredThreats) {
        const tx = ((threat.lng + 180) / 360) * width;
        const ty = ((90 - threat.lat) / 180) * height;
        const size = 4 + threat.count * 0.3;

        if (Math.sqrt((x - tx) ** 2 + (y - ty) ** 2) < size * 2) {
          setSelectedThreat(threat);
          return;
        }
      }
      setSelectedThreat(null);
    };

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const width = rect.width;
      const height = rect.height;

      for (const threat of filteredThreats) {
        const tx = ((threat.lng + 180) / 360) * width;
        const ty = ((90 - threat.lat) / 180) * height;
        const size = 4 + threat.count * 0.3;

        if (Math.sqrt((x - tx) ** 2 + (y - ty) ** 2) < size * 2) {
          setHoveredThreat(threat.id);
          canvas.style.cursor = "pointer";
          return;
        }
      }
      setHoveredThreat(null);
      canvas.style.cursor = "default";
    };

    canvas.addEventListener("click", handleClick);
    canvas.addEventListener("mousemove", handleMouseMove);

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationId);
      canvas.removeEventListener("click", handleClick);
      canvas.removeEventListener("mousemove", handleMouseMove);
    };
  }, [filteredThreats, hoveredThreat, selectedThreat]);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-mono font-bold text-white">Threat Map</h1>
          <p className="text-sm text-white/50">
            Geographic visualization of global threat activity
          </p>
        </div>

        {/* Filters */}
        <div className="flex gap-2">
          {["all", "critical", "high", "medium", "low"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "px-3 py-1.5 rounded-lg font-mono text-xs transition-all",
                filter === f
                  ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                  : "bg-white/[0.03] text-white/60 border border-white/[0.08] hover:bg-white/[0.05]"
              )}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="relative">
        <GlassCard padding="none" className="overflow-hidden">
          <canvas ref={canvasRef} className="w-full h-[500px]" />

          <div className="absolute bottom-4 left-4 glass rounded-xl p-3">
            <p className="text-[10px] font-mono text-white/40 mb-2 uppercase tracking-wider">
              Severity
            </p>
            <div className="flex flex-col gap-1.5">
              {[
                { label: "Critical", color: "bg-red-500" },
                { label: "High", color: "bg-orange-500" },
                { label: "Medium", color: "bg-yellow-500" },
                { label: "Low", color: "bg-blue-500" },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-2">
                  <span className={cn("w-2 h-2 rounded-full", item.color)} />
                  <span className="text-xs text-white/50">{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="absolute top-4 right-4 glass rounded-xl p-3">
            <p className="text-[10px] font-mono text-white/40 mb-2 uppercase tracking-wider">
              Active Threats
            </p>
            <p className="text-2xl font-mono font-bold text-white">
              {filteredThreats.reduce((acc, t) => acc + t.count, 0)}
            </p>
            <p className="text-xs text-white/40">
              across {filteredThreats.length} locations
            </p>
          </div>
        </GlassCard>

        {selectedThreat && (
          <div className="absolute top-4 left-4 w-72">
            <GlassCard>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-mono font-semibold text-white">Threat Details</h3>
                <button
                  onClick={() => setSelectedThreat(null)}
                  className="text-white/40 hover:text-white"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-white/50">Location</span>
                  <span className="font-mono text-white">{selectedThreat.label}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-white/50">Type</span>
                  <span className="font-mono text-white">{selectedThreat.type}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-white/50">Severity</span>
                  <Badge variant={selectedThreat.severity}>
                    {selectedThreat.severity}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-white/50">Count</span>
                  <span className="font-mono text-white">{selectedThreat.count}</span>
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
      </div>

      <GlassCard>
        <h3 className="font-mono font-semibold text-white mb-4">Active Threats</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/[0.05]">
                <th className="text-left text-xs font-mono text-white/40 pb-3">Location</th>
                <th className="text-left text-xs font-mono text-white/40 pb-3">Type</th>
                <th className="text-left text-xs font-mono text-white/40 pb-3">Severity</th>
                <th className="text-right text-xs font-mono text-white/40 pb-3">Count</th>
              </tr>
            </thead>
            <tbody>
              {filteredThreats.map((threat) => (
                <tr
                  key={threat.id}
                  className="border-b border-white/[0.03] hover:bg-white/[0.02] cursor-pointer transition-colors"
                  onClick={() => setSelectedThreat(threat)}
                >
                  <td className="py-3 text-sm text-white">{threat.label}</td>
                  <td className="py-3 text-sm text-white/70">{threat.type}</td>
                  <td className="py-3">
                    <Badge variant={threat.severity} size="sm">
                      {threat.severity}
                    </Badge>
                  </td>
                  <td className="py-3 text-sm text-right font-mono text-white">
                    {threat.count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  );
}

