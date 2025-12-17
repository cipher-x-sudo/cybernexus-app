"use client";

import { cn } from "@/lib/utils";

interface RedirectBannerProps {
  originalUrl: string;
  finalUrl: string;
  className?: string;
}

export function RedirectBanner({
  originalUrl,
  finalUrl,
  className,
}: RedirectBannerProps) {
  return (
    <div
      className={cn(
        "p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30",
        "flex items-center gap-3",
        className
      )}
    >
      <svg
        className="w-5 h-5 text-yellow-400 flex-shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 7l5 5m0 0l-5 5m5-5H6"
        />
      </svg>
      <div className="flex-1 min-w-0">
        <div className="text-xs font-mono text-yellow-400/70 mb-1">
          Redirected
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-white/60 truncate">{originalUrl}</span>
          <svg
            className="w-4 h-4 text-yellow-400 flex-shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
          <a
            href={finalUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-yellow-400 hover:text-yellow-300 truncate underline"
          >
            {finalUrl}
          </a>
        </div>
      </div>
    </div>
  );
}

