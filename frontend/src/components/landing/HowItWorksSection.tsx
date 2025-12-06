"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

const steps = [
  {
    number: "01",
    title: "Connect Your Assets",
    description:
      "Integrate your digital infrastructure in minutes. Connect domains, IPs, email addresses, and cloud assets through our intuitive dashboard or API.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
      </svg>
    ),
  },
  {
    number: "02",
    title: "Monitor Threats",
    description:
      "Our AI-powered engines continuously scan the surface, deep, and dark web for threats targeting your organization. Real-time alerts keep you informed.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
      </svg>
    ),
  },
  {
    number: "03",
    title: "Analyze & Correlate",
    description:
      "Visualize threat relationships in our 3D graph. Our correlation engine connects the dots between disparate threats to reveal attack patterns.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    number: "04",
    title: "Take Action",
    description:
      "Respond to threats with confidence. Generate reports, export IOCs, integrate with your SOAR platform, or take manual action—all from one place.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
];

export function HowItWorksSection() {
  const [activeStep, setActiveStep] = useState(0);
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      if (!sectionRef.current) return;

      const section = sectionRef.current;
      const rect = section.getBoundingClientRect();
      const sectionHeight = rect.height;
      const scrollProgress = Math.max(0, -rect.top) / (sectionHeight - window.innerHeight);
      
      const newActiveStep = Math.min(
        steps.length - 1,
        Math.floor(scrollProgress * steps.length)
      );
      
      if (rect.top < window.innerHeight && rect.bottom > 0) {
        setActiveStep(Math.max(0, newActiveStep));
      }
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <section
      id="how-it-works"
      ref={sectionRef}
      className="py-24 lg:py-32 relative"
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 lg:mb-20">
          <p className="text-amber-400 font-mono text-sm uppercase tracking-wider mb-4">
            How It Works
          </p>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-mono font-bold text-white mb-6">
            From Setup to{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-orange-500">
              Protection
            </span>{" "}
            in Minutes
          </h2>
          <p className="text-lg text-white/60">
            Get started quickly with our streamlined onboarding process.
            No complex configurations required.
          </p>
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-8 lg:left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-amber-500/50 via-amber-500/20 to-transparent" />

          {/* Steps */}
          <div className="space-y-16 lg:space-y-24">
            {steps.map((step, index) => (
              <div
                key={index}
                className={cn(
                  "relative flex flex-col lg:flex-row items-start lg:items-center gap-8",
                  index % 2 === 1 && "lg:flex-row-reverse"
                )}
              >
                {/* Number indicator */}
                <div className="absolute left-0 lg:left-1/2 lg:-translate-x-1/2 z-10">
                  <div
                    className={cn(
                      "w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-500",
                      activeStep >= index
                        ? "bg-amber-500 text-white shadow-[0_0_30px_rgba(245,158,11,0.4)]"
                        : "bg-white/5 border border-white/10 text-white/40"
                    )}
                  >
                    <span className="font-mono font-bold text-lg">{step.number}</span>
                  </div>
                </div>

                {/* Content */}
                <div
                  className={cn(
                    "flex-1 ml-24 lg:ml-0 lg:w-1/2",
                    index % 2 === 0 ? "lg:pr-20 lg:text-right" : "lg:pl-20"
                  )}
                >
                  <div
                    className={cn(
                      "glass rounded-2xl p-6 lg:p-8 transition-all duration-500",
                      activeStep >= index
                        ? "border-amber-500/30 shadow-[0_0_30px_rgba(245,158,11,0.1)]"
                        : ""
                    )}
                  >
                    <div
                      className={cn(
                        "flex items-center gap-4 mb-4",
                        index % 2 === 0 && "lg:flex-row-reverse"
                      )}
                    >
                      <div
                        className={cn(
                          "w-12 h-12 rounded-xl flex items-center justify-center transition-colors",
                          activeStep >= index
                            ? "bg-amber-500/20 text-amber-400"
                            : "bg-white/5 text-white/40"
                        )}
                      >
                        {step.icon}
                      </div>
                      <h3 className="text-xl lg:text-2xl font-mono font-semibold text-white">
                        {step.title}
                      </h3>
                    </div>
                    <p className="text-white/50 leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </div>

                {/* Spacer for alternating layout */}
                <div className="hidden lg:block flex-1 lg:w-1/2" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

