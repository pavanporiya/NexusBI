"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

/**
 * Hook to require authentication. Redirects to /login if not authenticated.
 * Returns the auth state for conditional rendering.
 */
export function useRequireAuth() {
  const router = useRouter();
  const { isAuthenticated, isLoading, user } = useAuthStore();

  useEffect(() => {
    // Wait for hydration from localStorage
    const timer = setTimeout(() => {
      useAuthStore.setState({ isLoading: false });
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  return { isAuthenticated, isLoading, user };
}

/**
 * Hook to redirect away from auth pages if already authenticated.
 */
export function useRedirectIfAuthenticated() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthStore();

  useEffect(() => {
    const timer = setTimeout(() => {
      useAuthStore.setState({ isLoading: false });
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  return { isAuthenticated, isLoading };
}
