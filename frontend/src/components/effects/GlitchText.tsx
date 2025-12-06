"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

interface GlitchTextProps {
  text: string;
  className?: string;
  glitchOnHover?: boolean;
  continuous?: boolean;
  intensity?: "low" | "medium" | "high";
}

export function GlitchText({
  text,
  className,
  glitchOnHover = true,
  continuous = false,
  intensity = "medium",
}: GlitchTextProps) {
  const [isGlitching, setIsGlitching] = useState(continuous);

  useEffect(() => {
    if (continuous) {
      const interval = setInterval(() => {
        setIsGlitching(true);
        setTimeout(() => setIsGlitching(false), 200);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [continuous]);

  const intensityValues = {
    low: { offset: 1, blur: 0 },
    medium: { offset: 2, blur: 1 },
    high: { offset: 4, blur: 2 },
  };

  const { offset, blur } = intensityValues[intensity];

  return (
    <span
      className={cn("relative inline-block", className)}
      onMouseEnter={() => glitchOnHover && setIsGlitching(true)}
      onMouseLeave={() => glitchOnHover && !continuous && setIsGlitching(false)}
    >
      <span className="relative z-10">{text}</span>
      
      {isGlitching && (
        <>
          {/* Red offset layer */}
          <span
            className="absolute inset-0 text-red-500 opacity-70 animate-glitch"
            style={{
              clipPath: "polygon(0 0, 100% 0, 100% 45%, 0 45%)",
              transform: `translate(${offset}px, 0)`,
              filter: `blur(${blur}px)`,
            }}
            aria-hidden="true"
          >
            {text}
          </span>
          
          {/* Cyan offset layer */}
          <span
            className="absolute inset-0 text-cyan-400 opacity-70 animate-glitch"
            style={{
              clipPath: "polygon(0 55%, 100% 55%, 100% 100%, 0 100%)",
              transform: `translate(-${offset}px, 0)`,
              filter: `blur(${blur}px)`,
              animationDelay: "50ms",
            }}
            aria-hidden="true"
          >
            {text}
          </span>
        </>
      )}
    </span>
  );
}

// Typing effect text component
interface TypingTextProps {
  text: string;
  speed?: number;
  className?: string;
  onComplete?: () => void;
  cursor?: boolean;
}

export function TypingText({
  text,
  speed = 50,
  className,
  onComplete,
  cursor = true,
}: TypingTextProps) {
  const [displayText, setDisplayText] = useState("");
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    let index = 0;
    setDisplayText("");
    setIsComplete(false);

    const timer = setInterval(() => {
      if (index < text.length) {
        setDisplayText(text.slice(0, index + 1));
        index++;
      } else {
        setIsComplete(true);
        clearInterval(timer);
        onComplete?.();
      }
    }, speed);

    return () => clearInterval(timer);
  }, [text, speed, onComplete]);

  return (
    <span className={cn("inline-block", className)}>
      {displayText}
      {cursor && (
        <span
          className={cn(
            "inline-block w-0.5 h-[1em] bg-amber-500 ml-0.5 align-middle",
            isComplete ? "animate-pulse" : "animate-[blink-caret_0.75s_step-end_infinite]"
          )}
        />
      )}
    </span>
  );
}

