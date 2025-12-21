"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface GlassSelectOption {
  value: string;
  label: string;
}

interface GlassSelectProps {
  value: string;
  onChange: (value: string) => void;
  options: GlassSelectOption[];
  placeholder?: string;
  className?: string;
  disabled?: boolean;
  label?: string;
  error?: string;
  hint?: string;
}

const GlassSelect = React.forwardRef<HTMLDivElement, GlassSelectProps>(
  (
    {
      value,
      onChange,
      options,
      placeholder = "Select...",
      className,
      disabled = false,
      label,
      error,
      hint,
      ...props
    },
    ref
  ) => {
    const [isOpen, setIsOpen] = React.useState(false);
    const [focusedIndex, setFocusedIndex] = React.useState(-1);
    const selectRef = React.useRef<HTMLDivElement>(null);
    const listRef = React.useRef<HTMLUListElement>(null);
    const id = React.useId();

    // Find selected option label
    const selectedOption = options.find((opt) => opt.value === value);
    const displayValue = selectedOption?.label || placeholder;

    // Close dropdown when clicking outside
    React.useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (
          selectRef.current &&
          !selectRef.current.contains(event.target as Node)
        ) {
          setIsOpen(false);
          setFocusedIndex(-1);
        }
      };

      if (isOpen) {
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
      }
    }, [isOpen]);

    // Keyboard navigation
    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (disabled) return;

      switch (e.key) {
        case "Enter":
        case " ":
          e.preventDefault();
          if (isOpen && focusedIndex >= 0) {
            onChange(options[focusedIndex].value);
            setIsOpen(false);
            setFocusedIndex(-1);
          } else {
            setIsOpen(!isOpen);
          }
          break;
        case "Escape":
          e.preventDefault();
          setIsOpen(false);
          setFocusedIndex(-1);
          break;
        case "ArrowDown":
          e.preventDefault();
          if (!isOpen) {
            setIsOpen(true);
          } else {
            setFocusedIndex((prev) =>
              prev < options.length - 1 ? prev + 1 : prev
            );
          }
          break;
        case "ArrowUp":
          e.preventDefault();
          if (isOpen) {
            setFocusedIndex((prev) => (prev > 0 ? prev - 1 : 0));
          }
          break;
      }
    };

    // Scroll focused option into view
    React.useEffect(() => {
      if (isOpen && focusedIndex >= 0 && listRef.current) {
        const focusedElement = listRef.current.children[focusedIndex] as HTMLElement;
        if (focusedElement) {
          focusedElement.scrollIntoView({ block: "nearest" });
        }
      }
    }, [focusedIndex, isOpen]);

    return (
      <div className="w-full" ref={ref} {...props}>
        {label && (
          <label
            htmlFor={id}
            className="block text-sm font-mono text-white/70 mb-2"
          >
            {label}
          </label>
        )}
        <div className="relative" ref={selectRef}>
          <button
            id={id}
            type="button"
            disabled={disabled}
            onClick={() => !disabled && setIsOpen(!isOpen)}
            onKeyDown={handleKeyDown}
            className={cn(
              "w-full h-11 px-4 py-2",
              "bg-white/[0.03] backdrop-blur-sm",
              "border border-white/[0.08] rounded-xl",
              "text-white/90",
              "font-mono text-sm",
              "transition-all duration-200",
              "flex items-center justify-between",
              "focus:outline-none focus:border-amber-500/50",
              "focus:shadow-[0_0_15px_rgba(245,158,11,0.15)]",
              "hover:border-amber-500/40",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              error && "border-red-500/50 focus:border-red-500/70",
              isOpen && "border-amber-500/50 shadow-[0_0_15px_rgba(245,158,11,0.15)]",
              !selectedOption && "text-white/30",
              className
            )}
            aria-expanded={isOpen}
            aria-haspopup="listbox"
            aria-labelledby={label ? `${id}-label` : undefined}
          >
            <span className="truncate">{displayValue}</span>
            <svg
              className={cn(
                "w-4 h-4 text-white/40 transition-transform duration-200 flex-shrink-0 ml-2",
                isOpen && "rotate-180"
              )}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>

          {isOpen && (
            <ul
              ref={listRef}
              role="listbox"
              className={cn(
                "absolute z-[100] w-full mt-1",
                "bg-slate-900/95 backdrop-blur-xl",
                "border border-white/[0.1] rounded-xl",
                "shadow-[0_8px_32px_rgba(0,0,0,0.4)]",
                "max-h-60 overflow-auto",
                "py-1"
              )}
              style={{ scrollbarWidth: "thin" }}
            >
              {options.map((option, index) => {
                const isSelected = option.value === value;
                const isFocused = index === focusedIndex;
                return (
                  <li
                    key={option.value}
                    role="option"
                    aria-selected={isSelected}
                    onClick={() => {
                      onChange(option.value);
                      setIsOpen(false);
                      setFocusedIndex(-1);
                    }}
                    onMouseEnter={() => setFocusedIndex(index)}
                    className={cn(
                      "px-4 py-2 cursor-pointer",
                      "text-sm font-mono",
                      "transition-colors duration-150",
                      isSelected
                        ? "bg-amber-500/20 text-amber-400"
                        : "text-white/80",
                      isFocused && !isSelected && "bg-white/[0.05] text-white"
                    )}
                  >
                    {option.label}
                  </li>
                );
              })}
            </ul>
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
GlassSelect.displayName = "GlassSelect";

export { GlassSelect, type GlassSelectOption };









