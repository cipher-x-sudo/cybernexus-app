import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // CyberNexus Glassmorphism Colors
        cyber: {
          navy: "#0a0e1a",
          dark: "#0d1321",
          slate: "#1a2035",
          blue: "#3b82f6",
          cyan: "#06b6d4",
          purple: "#8b5cf6",
          pink: "#ec4899",
          green: "#10b981",
          yellow: "#f59e0b",
          orange: "#f97316",
          red: "#ef4444",
        },
        glass: {
          DEFAULT: "rgba(255, 255, 255, 0.05)",
          light: "rgba(255, 255, 255, 0.1)",
          dark: "rgba(0, 0, 0, 0.3)",
          border: "rgba(255, 255, 255, 0.1)",
        },
        glow: {
          cyan: "#06b6d4",
          blue: "#3b82f6",
          purple: "#8b5cf6",
          pink: "#ec4899",
        },
        severity: {
          critical: "#dc2626",
          high: "#f97316",
          medium: "#f59e0b",
          low: "#22c55e",
          info: "#3b82f6",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        xl: "1rem",
        "2xl": "1.5rem",
        "3xl": "2rem",
      },
      fontFamily: {
        sans: ["Plus Jakarta Sans", "Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        display: ["Plus Jakarta Sans", "sans-serif"],
      },
      backdropBlur: {
        xs: "2px",
        glass: "12px",
        "glass-lg": "20px",
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
        "glass-sm": "0 4px 16px 0 rgba(0, 0, 0, 0.25)",
        "glass-lg": "0 12px 48px 0 rgba(0, 0, 0, 0.5)",
        "glow-cyan": "0 0 20px rgba(6, 182, 212, 0.4), 0 0 40px rgba(6, 182, 212, 0.2)",
        "glow-blue": "0 0 20px rgba(59, 130, 246, 0.4), 0 0 40px rgba(59, 130, 246, 0.2)",
        "glow-purple": "0 0 20px rgba(139, 92, 246, 0.4), 0 0 40px rgba(139, 92, 246, 0.2)",
        "glow-pink": "0 0 20px rgba(236, 72, 153, 0.4), 0 0 40px rgba(236, 72, 153, 0.2)",
        "glow-red": "0 0 20px rgba(239, 68, 68, 0.4), 0 0 40px rgba(239, 68, 68, 0.2)",
        "glow-green": "0 0 20px rgba(16, 185, 129, 0.4), 0 0 40px rgba(16, 185, 129, 0.2)",
        "inner-glow": "inset 0 0 20px rgba(6, 182, 212, 0.1)",
        neon: "0 0 5px theme(colors.cyber.cyan), 0 0 20px theme(colors.cyber.cyan), 0 0 40px theme(colors.cyber.blue)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "pulse-glow": {
          "0%, 100%": {
            boxShadow: "0 0 5px rgba(6, 182, 212, 0.4), 0 0 20px rgba(6, 182, 212, 0.2)",
          },
          "50%": {
            boxShadow: "0 0 20px rgba(6, 182, 212, 0.6), 0 0 40px rgba(6, 182, 212, 0.4)",
          },
        },
        "pulse-slow": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        "scan-line": {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "border-glow": {
          "0%, 100%": { borderColor: "rgba(6, 182, 212, 0.5)" },
          "50%": { borderColor: "rgba(139, 92, 246, 0.5)" },
        },
        "rotate-glow": {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        fadeIn: {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        slideIn: {
          from: { opacity: "0", transform: "translateX(-10px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        scaleIn: {
          from: { opacity: "0", transform: "scale(0.95)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        "counter-up": {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "ripple": {
          "0%": { transform: "scale(0)", opacity: "1" },
          "100%": { transform: "scale(4)", opacity: "0" },
        },
        "ping-slow": {
          "75%, 100%": { transform: "scale(2)", opacity: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
        "pulse-slow": "pulse-slow 3s ease-in-out infinite",
        float: "float 6s ease-in-out infinite",
        "scan-line": "scan-line 3s linear infinite",
        shimmer: "shimmer 2s linear infinite",
        "border-glow": "border-glow 3s ease-in-out infinite",
        "rotate-glow": "rotate-glow 10s linear infinite",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-in": "slideIn 0.3s ease-out",
        "scale-in": "scaleIn 0.2s ease-out",
        "counter-up": "counter-up 0.5s ease-out",
        ripple: "ripple 0.6s ease-out",
        "ping-slow": "ping-slow 2s cubic-bezier(0, 0, 0.2, 1) infinite",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        "glass-gradient": "linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)",
        "glow-gradient": "linear-gradient(135deg, rgba(6,182,212,0.2) 0%, rgba(139,92,246,0.2) 100%)",
        "cyber-gradient": "linear-gradient(135deg, #0a0e1a 0%, #1a2035 50%, #0d1321 100%)",
        "mesh-gradient": `
          radial-gradient(at 40% 20%, rgba(6, 182, 212, 0.15) 0px, transparent 50%),
          radial-gradient(at 80% 0%, rgba(139, 92, 246, 0.1) 0px, transparent 50%),
          radial-gradient(at 0% 50%, rgba(59, 130, 246, 0.1) 0px, transparent 50%),
          radial-gradient(at 80% 50%, rgba(236, 72, 153, 0.05) 0px, transparent 50%),
          radial-gradient(at 0% 100%, rgba(16, 185, 129, 0.1) 0px, transparent 50%)
        `,
        "noise": "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E\")",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
