"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface GlassInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
}

const GlassInput = React.forwardRef<HTMLInputElement, GlassInputProps>(
  (
    {
      className,
      type = "text",
      label,
      error,
      hint,
      icon,
      iconPosition = "left",
      ...props
    },
    ref
  ) => {
    const id = React.useId();

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={id}
            className="block text-sm font-mono text-white/70 mb-2"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {icon && iconPosition === "left" && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40">
              {icon}
            </div>
          )}
          <input
            id={id}
            type={type}
            ref={ref}
            className={cn(
              "w-full h-11 px-4 py-2",
              "bg-white/[0.03] backdrop-blur-sm",
              "border border-white/[0.08] rounded-xl",
              "text-white/90 placeholder:text-white/30",
              "font-mono text-sm",
              "transition-all duration-200",
              "focus:outline-none focus:border-amber-500/50",
              "focus:shadow-[0_0_15px_rgba(245,158,11,0.15)]",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              icon && iconPosition === "left" && "pl-10",
              icon && iconPosition === "right" && "pr-10",
              error && "border-red-500/50 focus:border-red-500/70",
              className
            )}
            {...props}
          />
          {icon && iconPosition === "right" && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40">
              {icon}
            </div>
          )}
        </div>
        {error && (
          <p className="mt-1.5 text-xs text-red-400 font-mono">{error}</p>
        )}
        {hint && !error && (
          <p className="mt-1.5 text-xs text-white/40">{hint}</p>
        )}
      </div>
    );
  }
);
GlassInput.displayName = "GlassInput";

interface GlassTextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
}

const GlassTextarea = React.forwardRef<HTMLTextAreaElement, GlassTextareaProps>(
  ({ className, label, error, hint, ...props }, ref) => {
    const id = React.useId();

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={id}
            className="block text-sm font-mono text-white/70 mb-2"
          >
            {label}
          </label>
        )}
        <textarea
          id={id}
          ref={ref}
          className={cn(
            "w-full min-h-[120px] px-4 py-3",
            "bg-white/[0.03] backdrop-blur-sm",
            "border border-white/[0.08] rounded-xl",
            "text-white/90 placeholder:text-white/30",
            "font-mono text-sm",
            "transition-all duration-200 resize-y",
            "focus:outline-none focus:border-amber-500/50",
            "focus:shadow-[0_0_15px_rgba(245,158,11,0.15)]",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            error && "border-red-500/50 focus:border-red-500/70",
            className
          )}
          {...props}
        />
        {error && (
          <p className="mt-1.5 text-xs text-red-400 font-mono">{error}</p>
        )}
        {hint && !error && (
          <p className="mt-1.5 text-xs text-white/40">{hint}</p>
        )}
      </div>
    );
  }
);
GlassTextarea.displayName = "GlassTextarea";

export { GlassInput, GlassTextarea };

