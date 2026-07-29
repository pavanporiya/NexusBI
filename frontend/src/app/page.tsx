"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

export default function RootPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    const timer = setTimeout(() => {
      if (isAuthenticated) {
        router.replace("/dashboard");
      } else {
        router.replace("/login");
      }
    }, 100);
    return () => clearTimeout(timer);
  }, [isAuthenticated, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-primary" />
    </div>
  );
}
