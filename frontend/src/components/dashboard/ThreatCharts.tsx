"use client";

import { useEffect, useRef } from "react";
import { GlassCard } from "@/components/ui";
import { cn } from "@/lib/utils";

// Simple donut chart
export function DonutChart({ className }: { className?: string }) {
  const data = [
    { label: "Critical", value: 12, color: "#ef4444" },
    { label: "High", value: 28, color: "#f97316" },
    { label: "Medium", value: 45, color: "#eab308" },
    { label: "Low", value: 89, color: "#3b82f6" },
  ];

  const total = data.reduce((acc, d) => acc + d.value, 0);
  let cumulativePercent = 0;

  return (
    <GlassCard className={cn("h-full", className)} padding="lg">
      <h3 className="font-mono font-semibold text-white mb-4">Threats by Severity</h3>
      <div className="flex items-center gap-6">
        <div className="relative w-32 h-32">
          <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
            {data.map((segment, i) => {
              const percent = (segment.value / total) * 100;
              const circumference = 2 * Math.PI * 15.9155;
              const dashArray = (percent / 100) * circumference;
              const dashOffset = ((100 - cumulativePercent) / 100) * circumference;
              cumulativePercent += percent;

              return (
                <circle
                  key={i}
                  cx="18"
                  cy="18"
                  r="15.9155"
                  fill="transparent"
                  stroke={segment.color}
                  strokeWidth="3"
                  strokeDasharray={`${dashArray} ${circumference - dashArray}`}
                  strokeDashoffset={-dashOffset + circumference}
                  className="transition-all duration-1000"
                />
              );
            })}
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <p className="text-2xl font-mono font-bold text-white">{total}</p>
              <p className="text-[10px] text-white/50">Total</p>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          {data.map((item) => (
            <div key={item.label} className="flex items-center gap-2">
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-sm text-white/60">{item.label}</span>
              <span className="text-sm font-mono text-white ml-auto">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </GlassCard>
  );
}

// Line chart using canvas
export function LineChart({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const data = [12, 19, 15, 25, 22, 30, 28, 35, 32, 40, 38, 45];
    const labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
      draw();
    };

    const draw = () => {
      const width = canvas.width / window.devicePixelRatio;
      const height = canvas.height / window.devicePixelRatio;
      const padding = { top: 20, right: 20, bottom: 30, left: 40 };

      ctx.clearRect(0, 0, width, height);

      const chartWidth = width - padding.left - padding.right;
      const chartHeight = height - padding.top - padding.bottom;

      const maxValue = Math.max(...data) * 1.2;
      const stepX = chartWidth / (data.length - 1);

      // Grid lines
      ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
      ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {
        const y = padding.top + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();
      }

      // Line path
      ctx.beginPath();
      data.forEach((value, i) => {
        const x = padding.left + i * stepX;
        const y = padding.top + chartHeight - (value / maxValue) * chartHeight;
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.strokeStyle = "#f59e0b";
      ctx.lineWidth = 2;
      ctx.stroke();

      // Fill gradient
      ctx.lineTo(padding.left + (data.length - 1) * stepX, height - padding.bottom);
      ctx.lineTo(padding.left, height - padding.bottom);
      ctx.closePath();
      const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
      gradient.addColorStop(0, "rgba(245, 158, 11, 0.3)");
      gradient.addColorStop(1, "rgba(245, 158, 11, 0)");
      ctx.fillStyle = gradient;
      ctx.fill();

      // Points
      data.forEach((value, i) => {
        const x = padding.left + i * stepX;
        const y = padding.top + chartHeight - (value / maxValue) * chartHeight;

        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = "#f59e0b";
        ctx.fill();
        ctx.strokeStyle = "#0a0e1a";
        ctx.lineWidth = 2;
        ctx.stroke();
      });

      // X labels
      ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
      ctx.font = "10px JetBrains Mono, monospace";
      ctx.textAlign = "center";
      labels.forEach((label, i) => {
        const x = padding.left + i * stepX;
        ctx.fillText(label, x, height - 8);
      });
    };

    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);

  return (
    <GlassCard className={cn("h-full", className)} padding="lg">
      <h3 className="font-mono font-semibold text-white mb-4">Threats Over Time</h3>
      <div className="h-48">
        <canvas ref={canvasRef} className="w-full h-full" />
      </div>
    </GlassCard>
  );
}

// Bar chart
export function BarChart({ className }: { className?: string }) {
  const data = [
    { label: "Mon", value: 65 },
    { label: "Tue", value: 45 },
    { label: "Wed", value: 78 },
    { label: "Thu", value: 52 },
    { label: "Fri", value: 89 },
    { label: "Sat", value: 34 },
    { label: "Sun", value: 42 },
  ];

  const maxValue = Math.max(...data.map((d) => d.value));

  return (
    <GlassCard className={cn("h-full", className)} padding="lg">
      <h3 className="font-mono font-semibold text-white mb-4">Daily Scans</h3>
      <div className="flex items-end gap-2 h-40">
        {data.map((item, i) => (
          <div key={item.label} className="flex-1 flex flex-col items-center gap-2">
            <div
              className="w-full bg-gradient-to-t from-amber-500/80 to-amber-500/40 rounded-t-lg transition-all duration-1000"
              style={{
                height: `${(item.value / maxValue) * 100}%`,
                animationDelay: `${i * 100}ms`,
              }}
            />
            <span className="text-[10px] font-mono text-white/40">{item.label}</span>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

// Heatmap
export function HeatmapChart({ className }: { className?: string }) {
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const hours = Array.from({ length: 24 }, (_, i) => i);

  // Use seeded pseudo-random values to avoid hydration mismatch
  const data = days.map((_, dayIndex) =>
    hours.map((_, hourIndex) => {
      // Simple deterministic pseudo-random based on indices
      const seed = (dayIndex * 24 + hourIndex) * 9301 + 49297;
      return ((seed % 233280) / 233280);
    })
  );

  return (
    <GlassCard className={cn("h-full", className)} padding="lg">
      <h3 className="font-mono font-semibold text-white mb-4">Threat Activity Heatmap</h3>
      <div className="overflow-x-auto">
        <div className="flex gap-1 min-w-[500px]">
          <div className="flex flex-col gap-1 justify-end">
            {days.map((day) => (
              <div
                key={day}
                className="h-4 text-[10px] font-mono text-white/30 flex items-center pr-2"
              >
                {day}
              </div>
            ))}
          </div>
          <div className="flex-1">
            <div className="flex gap-1">
              {hours.map((hour) => (
                <div key={hour} className="flex-1 flex flex-col gap-1">
                  {days.map((day, dayIndex) => {
                    const value = data[dayIndex][hour];
                    const opacity = 0.1 + value * 0.9;
                    return (
                      <div
                        key={`${day}-${hour}`}
                        className="h-4 rounded-sm bg-amber-500 transition-all hover:scale-110"
                        style={{ opacity }}
                        title={`${day} ${hour}:00 - ${(value * 100).toFixed(0)}%`}
                      />
                    );
                  })}
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-2 text-[10px] font-mono text-white/30">
              <span>0:00</span>
              <span>6:00</span>
              <span>12:00</span>
              <span>18:00</span>
              <span>23:00</span>
            </div>
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

