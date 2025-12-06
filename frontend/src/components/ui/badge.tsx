"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "critical" | "high" | "medium" | "low" | "info" | "success";
  size?: "sm" | "md" | "lg";
  pulse?: boolean;
  icon?: React.ReactNode;
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  (
    {
      className,
      variant = "default",
      size = "md",
      pulse = false,
      icon,
      children,
      ...props
    },
    ref
  ) => {
    const variants = {
      default: "bg-white/10 text-white/80 border-white/20",
      critical: "bg-red-500/20 text-red-400 border-red-500/30",
      high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
      medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
      low: "bg-blue-500/20 text-blue-400 border-blue-500/30",
      info: "bg-purple-500/20 text-purple-400 border-purple-500/30",
      success: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    };

    const sizes = {
      sm: "h-5 px-2 text-[10px] gap-1",
      md: "h-6 px-2.5 text-xs gap-1.5",
      lg: "h-7 px-3 text-sm gap-2",
    };

    const pulseColors = {
      default: "bg-white/50",
      critical: "bg-red-400",
      high: "bg-orange-400",
      medium: "bg-yellow-400",
      low: "bg-blue-400",
      info: "bg-purple-400",
      success: "bg-emerald-400",
    };

    return (
      <span
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center",
          "font-mono font-medium uppercase tracking-wider",
          "rounded-full border backdrop-blur-sm",
          "whitespace-nowrap",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {pulse && (
          <span className="relative flex h-2 w-2 mr-1.5">
            <span
              className={cn(
                "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
                pulseColors[variant]
              )}
            />
            <span
              className={cn(
                "relative inline-flex rounded-full h-2 w-2",
                pulseColors[variant]
              )}
            />
          </span>
        )}
        {icon && <span className="flex-shrink-0">{icon}</span>}
        {children}
      </span>
    );
  }
);
Badge.displayName = "Badge";

export { Badge };

