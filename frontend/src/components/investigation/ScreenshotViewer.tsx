"use client";

import React, { useState } from "react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui";

interface ScreenshotViewerProps {
  screenshotUrl: string | null;
  className?: string;
  onExport?: () => void;
}

export function ScreenshotViewer({ screenshotUrl, className, onExport }: ScreenshotViewerProps) {
  const [zoom, setZoom] = useState(1);
  const [showAnnotations, setShowAnnotations] = useState(false);

  if (!screenshotUrl) {
    return (
      <GlassCard className={cn("p-6", className)} hover={false}>
        <div className="flex items-center justify-center h-[600px] text-white/50">
          <div className="text-center">
            <svg
              className="w-16 h-16 mx-auto mb-4 text-white/30"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <p className="text-sm">No screenshot available</p>
          </div>
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard className={cn("p-6", className)} hover={false}>
      <div className="space-y-4">
        {/* Controls */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setZoom(zoom - 0.25)}
              disabled={zoom <= 0.25}
              className="px-3 py-1.5 bg-white/[0.05] border border-white/[0.08] rounded-lg text-white text-sm hover:bg-white/[0.1] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Zoom Out
            </button>
            <span className="text-sm text-white/70">{Math.round(zoom * 100)}%</span>
            <button
              onClick={() => setZoom(zoom + 0.25)}
              disabled={zoom >= 3}
              className="px-3 py-1.5 bg-white/[0.05] border border-white/[0.08] rounded-lg text-white text-sm hover:bg-white/[0.1] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Zoom In
            </button>
            <button
              onClick={() => setZoom(1)}
              className="px-3 py-1.5 bg-white/[0.05] border border-white/[0.08] rounded-lg text-white text-sm hover:bg-white/[0.1]"
            >
              Reset
            </button>
          </div>
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-sm text-white/70 cursor-pointer">
              <input
                type="checkbox"
                checked={showAnnotations}
                onChange={(e) => setShowAnnotations(e.target.checked)}
                className="w-4 h-4 rounded bg-white/[0.05] border-white/[0.1]"
              />
              Show Annotations
            </label>
            {onExport && (
              <button
                onClick={onExport}
                className="px-3 py-1.5 bg-orange-500/20 border border-orange-500/40 text-orange-400 rounded-lg text-sm hover:bg-orange-500/30"
              >
                Export
              </button>
            )}
          </div>
        </div>

        {/* Screenshot Display */}
        <div className="border border-white/[0.08] rounded-lg bg-black/20 overflow-hidden">
          <TransformWrapper
            initialScale={zoom}
            minScale={0.25}
            maxScale={3}
            wheel={{ step: 0.1 }}
            doubleClick={{ disabled: false }}
          >
            <TransformComponent>
              <div className="relative">
                <img
                  src={screenshotUrl}
                  alt="Page screenshot"
                  className="max-w-full h-auto"
                />
                {showAnnotations && (
                  <div className="absolute inset-0 pointer-events-none">
                    {/* Example annotations - in production, these would come from analysis */}
                    <div className="absolute top-10 left-10 w-32 h-8 border-2 border-red-500 rounded">
                      <div className="absolute -top-6 left-0 text-xs text-red-400 bg-black/80 px-2 py-1 rounded">
                        Suspicious Element
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </TransformComponent>
          </TransformWrapper>
        </div>
      </div>
    </GlassCard>
  );
}

