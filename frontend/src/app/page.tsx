"use client";

import { ParticlesBackground } from "@/components/effects";
import {
  LandingNav,
  HeroSection,
  FeaturesSection,
  HowItWorksSection,
  TestimonialsSection,
  IntegrationsSection,
  SecuritySection,
  TeamSection,
  FAQSection,
  Footer,
} from "@/components/landing";

export default function LandingPage() {
  return (
    <main className="relative min-h-screen">
      {/* Particle background */}
      <ParticlesBackground particleCount={80} />

      {/* Content */}
      <div className="relative z-10">
        <LandingNav />
        <HeroSection />
        <FeaturesSection />
        <HowItWorksSection />
        <TestimonialsSection />
        <IntegrationsSection />
        <SecuritySection />
        <TeamSection />
        <FAQSection />
        <Footer />
      </div>
    </main>
  );
}
