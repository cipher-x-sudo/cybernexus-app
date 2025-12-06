"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface GlassButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
}

const GlassButton = React.forwardRef<HTMLButtonElement, GlassButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      loading = false,
      icon,
      iconPosition = "left",
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const variants = {
      primary: [
        "bg-amber-500/20 border-amber-500/40 text-amber-400",
        "hover:bg-amber-500/30 hover:border-amber-500/60",
        "hover:shadow-[0_0_20px_rgba(245,158,11,0.3)]",
        "active:bg-amber-500/40",
      ],
      secondary: [
        "bg-white/[0.05] border-white/[0.1] text-white/90",
        "hover:bg-white/[0.08] hover:border-white/[0.2]",
        "hover:shadow-[0_0_15px_rgba(255,255,255,0.1)]",
        "active:bg-white/[0.1]",
      ],
      ghost: [
        "bg-transparent border-transparent text-white/70",
        "hover:bg-white/[0.05] hover:text-white/90",
        "active:bg-white/[0.08]",
      ],
      danger: [
        "bg-red-500/20 border-red-500/40 text-red-400",
        "hover:bg-red-500/30 hover:border-red-500/60",
        "hover:shadow-[0_0_20px_rgba(239,68,68,0.3)]",
        "active:bg-red-500/40",
      ],
    };

    const sizes = {
      sm: "h-8 px-3 text-xs gap-1.5",
      md: "h-10 px-4 text-sm gap-2",
      lg: "h-12 px-6 text-base gap-2.5",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          "relative inline-flex items-center justify-center",
          "font-mono font-medium",
          "rounded-xl border backdrop-blur-sm",
          "transition-all duration-200",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500/50",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {loading ? (
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        ) : (
          <>
            {icon && iconPosition === "left" && (
              <span className="flex-shrink-0">{icon}</span>
            )}
            {children}
            {icon && iconPosition === "right" && (
              <span className="flex-shrink-0">{icon}</span>
            )}
          </>
        )}
      </button>
    );
  }
);
GlassButton.displayName = "GlassButton";

export { GlassButton };

