"use client";

import React from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { useRequireAuth } from "@/hooks/use-auth";

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading } = useRequireAuth();

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-primary" />
      </div>
    );
  }

  return <AppLayout>{children}</AppLayout>;
}
