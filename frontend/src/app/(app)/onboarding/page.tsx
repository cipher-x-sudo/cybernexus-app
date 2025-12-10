"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { GlassCard, GlassButton } from "@/components/ui";
import { CompanyProfileWizard } from "@/components/company";
import { api } from "@/lib/api";

export default function OnboardingPage() {
  const router = useRouter();
  const [showWelcome, setShowWelcome] = useState(true);
  const [profileExists, setProfileExists] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if profile already exists
    const checkProfile = async () => {
      try {
        await api.getCompanyProfile();
        setProfileExists(true);
        // If profile exists, redirect to dashboard
        router.push("/dashboard");
      } catch (error) {
        // Profile doesn't exist, show onboarding
        setProfileExists(false);
      } finally {
        setLoading(false);
      }
    };

    checkProfile();
  }, [router]);

  const handleComplete = () => {
    // Redirect to dashboard on completion
    router.push("/dashboard");
  };

  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <GlassCard padding="lg" className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500 mx-auto"></div>
          <p className="mt-4 text-white/60">Loading...</p>
        </GlassCard>
      </div>
    );
  }

  if (profileExists) {
    return null; // Will redirect
  }

  if (showWelcome) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <div className="w-full max-w-2xl">
          <GlassCard className="text-center" padding="lg">
            <div className="space-y-6">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center mx-auto mb-6">
                <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h2 className="text-2xl font-mono font-bold text-white">
                Welcome to CyberNexus
              </h2>
              <p className="text-white/60 max-w-md mx-auto">
                Let's get you set up with your unified threat intelligence platform.
                This will only take a few minutes.
              </p>
              <div className="pt-6">
                <GlassButton variant="primary" onClick={() => setShowWelcome(false)}>
                  Get Started
                </GlassButton>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[80vh] py-8">
      <CompanyProfileWizard onComplete={handleComplete} mode="create" />
    </div>
  );
}

