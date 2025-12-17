"use client";

import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: number;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const getStatusColor = (status: number) => {
    if (status >= 200 && status < 300) {
      return "bg-green-500/10 text-green-400 border-green-500/30";
    } else if (status >= 300 && status < 400) {
      return "bg-yellow-500/10 text-yellow-400 border-yellow-500/30";
    } else if (status >= 400 && status < 500) {
      return "bg-red-500/10 text-red-400 border-red-500/30";
    } else if (status >= 500) {
      return "bg-orange-500/10 text-orange-400 border-orange-500/30";
    }
    return "bg-slate-500/10 text-slate-400 border-slate-500/30";
  };

  return (
    <span
      className={cn(
        "px-2 py-0.5 text-xs font-mono rounded border",
        getStatusColor(status),
        className
      )}
    >
      {status}
    </span>
  );
}

