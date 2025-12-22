"use client";

import { useEffect, useState } from "react";
import { GlitchText } from "@/components/effects";

const loadingSteps = [
  "Initializing secure connection...",
  "Loading threat intelligence...",
  "Connecting to data sources...",
  "Preparing dashboard...",
];

export default function Loading() {
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 2;
      });
    }, 50);

    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % loadingSteps.length);
    }, 800);

    return () => {
      clearInterval(interval);
      clearInterval(stepInterval);
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50 bg-[#0a0e1a] flex flex-col items-center justify-center">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-amber-500/10 rounded-full blur-[150px] animate-pulse" />
      </div>

      <div className="relative z-10 flex flex-col items-center">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center mb-8 animate-pulse-glow">
          <svg
            className="w-12 h-12 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
        </div>

        <h1 className="font-mono font-bold text-3xl text-white mb-2">
          <GlitchText text="CyberNexus" continuous intensity="low" />
        </h1>
        <p className="text-white/50 text-sm font-mono mb-12">
          Threat Intelligence Platform
        </p>

        <div className="w-64 h-1 bg-white/10 rounded-full overflow-hidden mb-4">
          <div
            className="h-full bg-gradient-to-r from-amber-500 to-orange-600 transition-all duration-100 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>

        <p className="text-white/40 text-sm font-mono h-5">
          {loadingSteps[currentStep]}
        </p>
      </div>

      <div className="absolute inset-0 pointer-events-none opacity-[0.02]">
        <div
          className="w-full h-full"
          style={{
            backgroundImage:
              "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.03) 2px, rgba(255,255,255,0.03) 4px)",
          }}
        />
      </div>
    </div>
  );
}

