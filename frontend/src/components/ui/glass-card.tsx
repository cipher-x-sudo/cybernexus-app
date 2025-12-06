"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "strong" | "subtle";
  hover?: boolean;
  glow?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
}

const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
  (
    {
      className,
      variant = "default",
      hover = true,
      glow = false,
      padding = "md",
      children,
      ...props
    },
    ref
  ) => {
    const variants = {
      default: "bg-white/[0.03] border-white/[0.08]",
      strong: "bg-white/[0.05] border-white/[0.12]",
      subtle: "bg-white/[0.02] border-white/[0.05]",
    };

    const paddings = {
      none: "",
      sm: "p-3",
      md: "p-5",
      lg: "p-8",
    };

    return (
      <div
        ref={ref}
        className={cn(
          "relative rounded-2xl backdrop-blur-xl border",
          "shadow-[0_8px_32px_rgba(0,0,0,0.4)]",
          "transition-all duration-300",
          variants[variant],
          paddings[padding],
          hover && [
            "hover:border-amber-500/40",
            "hover:shadow-[0_0_30px_rgba(245,158,11,0.15)]",
          ],
          glow && "shadow-[0_0_20px_rgba(245,158,11,0.15)]",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
GlassCard.displayName = "GlassCard";

interface GlassCardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {}

const GlassCardHeader = React.forwardRef<HTMLDivElement, GlassCardHeaderProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex flex-col space-y-1.5 pb-4", className)}
      {...props}
    />
  )
);
GlassCardHeader.displayName = "GlassCardHeader";

interface GlassCardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {}

const GlassCardTitle = React.forwardRef<HTMLHeadingElement, GlassCardTitleProps>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn(
        "font-mono text-lg font-semibold leading-none tracking-tight text-white/90",
        className
      )}
      {...props}
    />
  )
);
GlassCardTitle.displayName = "GlassCardTitle";

interface GlassCardDescriptionProps
  extends React.HTMLAttributes<HTMLParagraphElement> {}

const GlassCardDescription = React.forwardRef<
  HTMLParagraphElement,
  GlassCardDescriptionProps
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-white/50", className)}
    {...props}
  />
));
GlassCardDescription.displayName = "GlassCardDescription";

interface GlassCardContentProps extends React.HTMLAttributes<HTMLDivElement> {}

const GlassCardContent = React.forwardRef<HTMLDivElement, GlassCardContentProps>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("", className)} {...props} />
  )
);
GlassCardContent.displayName = "GlassCardContent";

interface GlassCardFooterProps extends React.HTMLAttributes<HTMLDivElement> {}

const GlassCardFooter = React.forwardRef<HTMLDivElement, GlassCardFooterProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex items-center pt-4", className)}
      {...props}
    />
  )
);
GlassCardFooter.displayName = "GlassCardFooter";

export {
  GlassCard,
  GlassCardHeader,
  GlassCardTitle,
  GlassCardDescription,
  GlassCardContent,
  GlassCardFooter,
};

