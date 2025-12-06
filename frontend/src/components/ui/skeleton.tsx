"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, variant = "rectangular", width, height, style, ...props }, ref) => {
    const variants = {
      text: "rounded",
      circular: "rounded-full",
      rectangular: "rounded-xl",
    };

    return (
      <div
        ref={ref}
        className={cn(
          "bg-white/[0.05] animate-shimmer",
          variants[variant],
          className
        )}
        style={{
          width: width,
          height: height,
          ...style,
        }}
        {...props}
      />
    );
  }
);
Skeleton.displayName = "Skeleton";

// Pre-built skeleton components for common use cases
const SkeletonCard = () => (
  <div className="glass rounded-2xl p-5 space-y-4">
    <div className="flex items-center space-x-3">
      <Skeleton variant="circular" width={40} height={40} />
      <div className="space-y-2 flex-1">
        <Skeleton height={14} width="60%" />
        <Skeleton height={10} width="40%" />
      </div>
    </div>
    <Skeleton height={80} />
    <div className="flex space-x-2">
      <Skeleton height={32} width={80} />
      <Skeleton height={32} width={80} />
    </div>
  </div>
);

const SkeletonTable = ({ rows = 5 }: { rows?: number }) => (
  <div className="space-y-2">
    <div className="flex space-x-4 py-3 border-b border-white/10">
      {[1, 2, 3, 4].map((i) => (
        <Skeleton key={i} height={14} className="flex-1" />
      ))}
    </div>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="flex space-x-4 py-3">
        {[1, 2, 3, 4].map((j) => (
          <Skeleton key={j} height={12} className="flex-1" />
        ))}
      </div>
    ))}
  </div>
);

const SkeletonStat = () => (
  <div className="glass rounded-2xl p-5 space-y-3">
    <div className="flex justify-between items-start">
      <Skeleton height={12} width={80} />
      <Skeleton variant="circular" width={32} height={32} />
    </div>
    <Skeleton height={36} width={120} />
    <Skeleton height={10} width={60} />
  </div>
);

export { Skeleton, SkeletonCard, SkeletonTable, SkeletonStat };

