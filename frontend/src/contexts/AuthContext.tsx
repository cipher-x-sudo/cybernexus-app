"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

interface User {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  disabled: boolean;
  role: string;
  onboarding_completed: boolean;
  created_at: string;
  updated_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Load auth state from localStorage on mount
  useEffect(() => {
    const loadAuthState = async () => {
      try {
        if (typeof window !== "undefined") {
          const storedToken = localStorage.getItem("auth_token");
          const storedUser = localStorage.getItem("auth_user");

          if (storedToken && storedUser) {
            setToken(storedToken);
            setUser(JSON.parse(storedUser));
            api.setToken(storedToken);

            // Verify token is still valid by fetching current user
            try {
              const currentUser = await api.getCurrentUser();
              setUser(currentUser);
              localStorage.setItem("auth_user", JSON.stringify(currentUser));
            } catch (error) {
              // Token invalid, clear auth state
              localStorage.removeItem("auth_token");
              localStorage.removeItem("auth_user");
              setToken(null);
              setUser(null);
              api.clearToken();
            }
          }
        }
      } catch (error) {
        console.error("Error loading auth state:", error);
        localStorage.removeItem("auth_token");
        localStorage.removeItem("auth_user");
        setToken(null);
        setUser(null);
        api.clearToken();
      } finally {
        setLoading(false);
      }
    };

    loadAuthState();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    try {
      const response = await api.login(username, password);
      setToken(response.token);
      api.setToken(response.token);

      // Fetch user info
      const currentUser = await api.getCurrentUser();
      setUser(currentUser);

      // Store in localStorage
      if (typeof window !== "undefined") {
        localStorage.setItem("auth_token", response.token);
        localStorage.setItem("auth_user", JSON.stringify(currentUser));
      }
    } catch (error: any) {
      console.error("Login error:", error);
      throw error;
    }
  }, []);

  const register = useCallback(async (username: string, email: string, password: string, fullName?: string) => {
    try {
      const newUser = await api.register(username, email, password, fullName);
      
      // Auto-login after registration
      await login(username, password);
    } catch (error: any) {
      console.error("Registration error:", error);
      throw error;
    }
  }, [login]);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    api.logout();
    router.push("/login");
  }, [router]);

  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await api.getCurrentUser();
      setUser(currentUser);
      if (typeof window !== "undefined") {
        localStorage.setItem("auth_user", JSON.stringify(currentUser));
      }
    } catch (error) {
      console.error("Error refreshing user data:", error);
    }
  }, []);

  const value: AuthContextType = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    refreshUser,
    isAuthenticated: !!user && !!token,
    isAdmin: user?.role === "admin",
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

