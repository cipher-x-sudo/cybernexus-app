"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading, user } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading) {
      if (!isAuthenticated) {
        router.push("/login");
        return;
      }
      
      // Check onboarding completion (except for onboarding page itself)
      if (user && !user.onboarding_completed && pathname !== "/onboarding") {
        router.push("/onboarding");
        return;
      }
      
      // If onboarding is completed and user is on onboarding page, redirect to dashboard
      if (user && user.onboarding_completed && pathname === "/onboarding") {
        router.push("/dashboard");
        return;
      }
    }
  }, [isAuthenticated, loading, user, pathname, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500 mx-auto"></div>
          <p className="mt-4 text-white/60">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  // Don't render children if onboarding is not completed (will redirect)
  if (user && !user.onboarding_completed && pathname !== "/onboarding") {
    return null;
  }

  return <>{children}</>;
}

