"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

const testimonials = [
  {
    quote:
      "CyberNexus has transformed how we approach threat intelligence. The 3D graph visualization alone has helped us uncover attack patterns we never would have found otherwise.",
    author: "Sarah Chen",
    role: "CISO",
    company: "TechVault Inc.",
    avatar: "SC",
  },
  {
    quote:
      "The dark web monitoring capabilities are incredible. We detected leaked credentials within hours and prevented what could have been a major breach.",
    author: "Michael Torres",
    role: "Security Operations Lead",
    company: "FinSecure",
    avatar: "MT",
  },
  {
    quote:
      "Finally, a threat intelligence platform that doesn't require a PhD to operate. The interface is intuitive and the insights are actionable.",
    author: "Emma Williams",
    role: "Director of Security",
    company: "CloudShield",
    avatar: "EW",
  },
  {
    quote:
      "The automated reporting feature saves our team hours every week. Executive summaries are generated in seconds, not days.",
    author: "David Park",
    role: "VP of Engineering",
    company: "DataGuard Systems",
    avatar: "DP",
  },
];

const logos = [
  "TechVault",
  "FinSecure",
  "CloudShield",
  "DataGuard",
  "SecureNet",
  "CyberFlow",
];

export function TestimonialsSection() {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % testimonials.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="py-24 lg:py-32 relative overflow-hidden">
      <div className="absolute inset-0">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-amber-500/5 rounded-full blur-[150px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <p className="text-amber-400 font-mono text-sm uppercase tracking-wider mb-4">
            Testimonials
          </p>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-mono font-bold text-white mb-6">
            Trusted by{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-orange-500">
              Security Teams
            </span>{" "}
            Worldwide
          </h2>
        </div>

        <div className="relative max-w-4xl mx-auto">
          <div className="absolute -top-4 -left-4 text-amber-500/20">
            <svg className="w-24 h-24" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z" />
            </svg>
          </div>

          {/* Testimonials */}
          <div className="relative h-[300px]">
            {testimonials.map((testimonial, index) => (
              <div
                key={index}
                className={cn(
                  "absolute inset-0 transition-all duration-500 glass rounded-2xl p-8 lg:p-12",
                  activeIndex === index
                    ? "opacity-100 translate-x-0"
                    : index < activeIndex
                    ? "opacity-0 -translate-x-full"
                    : "opacity-0 translate-x-full"
                )}
              >
                <blockquote className="text-xl lg:text-2xl text-white/80 leading-relaxed mb-8">
                  "{testimonial.quote}"
                </blockquote>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-mono font-bold">
                    {testimonial.avatar}
                  </div>
                  <div>
                    <p className="font-mono font-semibold text-white">
                      {testimonial.author}
                    </p>
                    <p className="text-sm text-white/50">
                      {testimonial.role}, {testimonial.company}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-center gap-2 mt-8">
            {testimonials.map((_, index) => (
              <button
                key={index}
                onClick={() => setActiveIndex(index)}
                className={cn(
                  "w-2 h-2 rounded-full transition-all duration-300",
                  activeIndex === index
                    ? "bg-amber-500 w-8"
                    : "bg-white/20 hover:bg-white/40"
                )}
              />
            ))}
          </div>
        </div>

        <div className="mt-20 pt-12 border-t border-white/[0.05]">
          <p className="text-center text-sm text-white/40 font-mono mb-8">
            Trusted by leading organizations
          </p>
          <div className="flex flex-wrap justify-center items-center gap-8 lg:gap-16">
            {logos.map((logo, index) => (
              <div
                key={index}
                className="text-white/30 font-mono font-bold text-xl hover:text-amber-400/60 transition-colors cursor-default"
              >
                {logo}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

