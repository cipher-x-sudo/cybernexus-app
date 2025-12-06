"use client";

import { useEffect, useState, useRef } from "react";
import { cn } from "@/lib/utils";

interface AnimatedCounterProps {
  value: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  className?: string;
  formatter?: (value: number) => string;
}

export function AnimatedCounter({
  value,
  duration = 2000,
  prefix = "",
  suffix = "",
  decimals = 0,
  className,
  formatter,
}: AnimatedCounterProps) {
  const [count, setCount] = useState(0);
  const countRef = useRef(0);
  const startTimeRef = useRef<number | null>(null);
  const rafRef = useRef<number>();

  useEffect(() => {
    const startValue = countRef.current;
    const endValue = value;
    const difference = endValue - startValue;

    const easeOutQuart = (t: number): number => {
      return 1 - Math.pow(1 - t, 4);
    };

    const animate = (timestamp: number) => {
      if (!startTimeRef.current) {
        startTimeRef.current = timestamp;
      }

      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easeOutQuart(progress);

      const currentValue = startValue + difference * easedProgress;
      countRef.current = currentValue;
      setCount(currentValue);

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };

    startTimeRef.current = null;
    rafRef.current = requestAnimationFrame(animate);

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [value, duration]);

  const displayValue = formatter
    ? formatter(count)
    : count.toFixed(decimals);

  return (
    <span className={cn("tabular-nums", className)}>
      {prefix}
      {displayValue}
      {suffix}
    </span>
  );
}

// Specialized counter for large numbers
export function AnimatedStatCounter({
  value,
  className,
}: {
  value: number;
  className?: string;
}) {
  const formatLargeNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + "M";
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + "K";
    }
    return Math.round(num).toLocaleString();
  };

  return (
    <AnimatedCounter
      value={value}
      formatter={formatLargeNumber}
      className={className}
    />
  );
}

