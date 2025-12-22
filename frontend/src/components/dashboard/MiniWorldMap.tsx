"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

interface ThreatPoint {
  lat: number;
  lng: number;
  severity: "critical" | "high" | "medium" | "low";
  count: number;
}

interface ThreatData {
  id: string;
  title: string;
  severity: string;
  risk_score: number;
  target: string;
  capability: string;
  discovered_at: string;
}

interface MiniWorldMapProps {
  threats?: ThreatPoint[] | ThreatData[];
  className?: string;
}

// Helper to convert API threat data to ThreatPoint format
function convertThreatsToPoints(threats: ThreatPoint[] | ThreatData[] | undefined): ThreatPoint[] {
  if (!threats || threats.length === 0) {
    return [];
  }

  // If already in ThreatPoint format, return as is
  if (threats.length > 0 && 'lat' in threats[0]) {
    return threats as ThreatPoint[];
  }

  // Convert ThreatData to ThreatPoint
  const threatData = threats as ThreatData[];
  
  // Group by severity and assign locations
  // For now, we'll use a simple hash-based location assignment
  // In a real implementation, you'd geolocate based on target IP/domain
  const severityGroups: Record<string, ThreatData[]> = {
    critical: [],
    high: [],
    medium: [],
    low: [],
  };

  threatData.forEach((threat) => {
    const severity = threat.severity.toLowerCase() as keyof typeof severityGroups;
    if (severityGroups[severity]) {
      severityGroups[severity].push(threat);
    } else {
      severityGroups.medium.push(threat);
    }
  });

  // Assign locations based on severity (distribute across map)
  const locations: Array<{ lat: number; lng: number }> = [
    { lat: 40.7128, lng: -74.006 }, // NYC
    { lat: 51.5074, lng: -0.1278 }, // London
    { lat: 35.6762, lng: 139.6503 }, // Tokyo
    { lat: 55.7558, lng: 37.6173 }, // Moscow
    { lat: -23.5505, lng: -46.6333 }, // São Paulo
    { lat: 1.3521, lng: 103.8198 }, // Singapore
    { lat: 48.8566, lng: 2.3522 }, // Paris
    { lat: -33.8688, lng: 151.2093 }, // Sydney
    { lat: 39.9042, lng: 116.4074 }, // Beijing
    { lat: 28.6139, lng: 77.209 }, // Delhi
  ];

  const points: ThreatPoint[] = [];
  let locationIndex = 0;

  // Create points for each severity group
  Object.entries(severityGroups).forEach(([severity, group]) => {
    if (group.length > 0) {
      // Aggregate by location (simplified - in real app, geolocate targets)
      const location = locations[locationIndex % locations.length];
      points.push({
        lat: location.lat,
        lng: location.lng,
        severity: severity as "critical" | "high" | "medium" | "low",
        count: group.length,
      });
      locationIndex++;
    }
  });

  return points;
}

export function MiniWorldMap({ threats, className }: MiniWorldMapProps) {
  const threatPoints = convertThreatsToPoints(threats);
  const canvasRef = useRef<HTMLCanvasElement>(null);

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

    // World map simplified path (continents outline)
    const drawMap = () => {
      const width = canvas.width / window.devicePixelRatio;
      const height = canvas.height / window.devicePixelRatio;

      ctx.clearRect(0, 0, width, height);

      // Grid
      ctx.strokeStyle = "rgba(245, 158, 11, 0.05)";
      ctx.lineWidth = 1;

      // Horizontal lines
      for (let i = 0; i <= 6; i++) {
        ctx.beginPath();
        ctx.moveTo(0, (height / 6) * i);
        ctx.lineTo(width, (height / 6) * i);
        ctx.stroke();
      }

      // Vertical lines
      for (let i = 0; i <= 12; i++) {
        ctx.beginPath();
        ctx.moveTo((width / 12) * i, 0);
        ctx.lineTo((width / 12) * i, height);
        ctx.stroke();
      }

      // Draw simplified continent outlines (neon style)
      ctx.strokeStyle = "rgba(245, 158, 11, 0.3)";
      ctx.lineWidth = 1.5;

      // North America
      ctx.beginPath();
      ctx.moveTo(width * 0.12, height * 0.25);
      ctx.quadraticCurveTo(width * 0.15, height * 0.15, width * 0.25, height * 0.12);
      ctx.quadraticCurveTo(width * 0.35, height * 0.1, width * 0.32, height * 0.3);
      ctx.quadraticCurveTo(width * 0.3, height * 0.45, width * 0.2, height * 0.5);
      ctx.quadraticCurveTo(width * 0.12, height * 0.45, width * 0.12, height * 0.25);
      ctx.stroke();

      // South America
      ctx.beginPath();
      ctx.moveTo(width * 0.22, height * 0.55);
      ctx.quadraticCurveTo(width * 0.28, height * 0.55, width * 0.3, height * 0.65);
      ctx.quadraticCurveTo(width * 0.28, height * 0.85, width * 0.24, height * 0.9);
      ctx.quadraticCurveTo(width * 0.2, height * 0.75, width * 0.22, height * 0.55);
      ctx.stroke();

      // Europe
      ctx.beginPath();
      ctx.moveTo(width * 0.45, height * 0.15);
      ctx.quadraticCurveTo(width * 0.55, height * 0.12, width * 0.55, height * 0.25);
      ctx.quadraticCurveTo(width * 0.52, height * 0.35, width * 0.45, height * 0.35);
      ctx.quadraticCurveTo(width * 0.42, height * 0.25, width * 0.45, height * 0.15);
      ctx.stroke();

      // Africa
      ctx.beginPath();
      ctx.moveTo(width * 0.45, height * 0.4);
      ctx.quadraticCurveTo(width * 0.55, height * 0.38, width * 0.58, height * 0.5);
      ctx.quadraticCurveTo(width * 0.55, height * 0.7, width * 0.48, height * 0.75);
      ctx.quadraticCurveTo(width * 0.42, height * 0.6, width * 0.45, height * 0.4);
      ctx.stroke();

      // Asia
      ctx.beginPath();
      ctx.moveTo(width * 0.58, height * 0.15);
      ctx.quadraticCurveTo(width * 0.75, height * 0.1, width * 0.85, height * 0.2);
      ctx.quadraticCurveTo(width * 0.9, height * 0.35, width * 0.85, height * 0.45);
      ctx.quadraticCurveTo(width * 0.7, height * 0.5, width * 0.6, height * 0.4);
      ctx.quadraticCurveTo(width * 0.55, height * 0.25, width * 0.58, height * 0.15);
      ctx.stroke();

      // Australia
      ctx.beginPath();
      ctx.moveTo(width * 0.78, height * 0.65);
      ctx.quadraticCurveTo(width * 0.88, height * 0.62, width * 0.9, height * 0.7);
      ctx.quadraticCurveTo(width * 0.88, height * 0.8, width * 0.8, height * 0.78);
      ctx.quadraticCurveTo(width * 0.75, height * 0.72, width * 0.78, height * 0.65);
      ctx.stroke();
    };

    const drawThreats = (time: number) => {
      const width = canvas.width / window.devicePixelRatio;
      const height = canvas.height / window.devicePixelRatio;

      const severityColors = {
        critical: { r: 239, g: 68, b: 68 },
        high: { r: 249, g: 115, b: 22 },
        medium: { r: 234, g: 179, b: 8 },
        low: { r: 59, g: 130, b: 246 },
      };

      threatPoints.forEach((threat) => {
        // Convert lat/lng to x/y (simplified Mercator)
        const x = ((threat.lng + 180) / 360) * width;
        const y = ((90 - threat.lat) / 180) * height;

        const color = severityColors[threat.severity];
        const pulse = Math.sin(time * 0.003 + threat.lat) * 0.3 + 0.7;
        const size = 3 + threat.count * 0.5;

        // Glow
        const gradient = ctx.createRadialGradient(x, y, 0, x, y, size * 4);
        gradient.addColorStop(0, `rgba(${color.r}, ${color.g}, ${color.b}, ${0.4 * pulse})`);
        gradient.addColorStop(1, "transparent");
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(x, y, size * 4, 0, Math.PI * 2);
        ctx.fill();

        // Core
        ctx.fillStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${pulse})`;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();
      });
    };

    let animationId: number;
    const animate = (time: number) => {
      drawMap();
      drawThreats(time);
      animationId = requestAnimationFrame(animate);
    };

    animate(0);

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationId);
    };
  }, [threatPoints]);

  if (threatPoints.length === 0) {
    return (
      <div className={cn("relative w-full h-full min-h-[200px] flex items-center justify-center", className)}>
        <div className="text-center">
          <p className="text-sm text-white/50 font-mono">No threat data available</p>
          <p className="text-xs text-white/30 mt-1">Threat locations will appear here</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("relative w-full h-full min-h-[200px]", className)}>
      <canvas ref={canvasRef} className="w-full h-full" />

      <div className="absolute bottom-4 left-4 flex items-center gap-4">
        {[
          { label: "Critical", color: "bg-red-500" },
          { label: "High", color: "bg-orange-500" },
          { label: "Medium", color: "bg-yellow-500" },
          { label: "Low", color: "bg-blue-500" },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-1.5">
            <span className={cn("w-2 h-2 rounded-full", item.color)} />
            <span className="text-[10px] font-mono text-white/40">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}


