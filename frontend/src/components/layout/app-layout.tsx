"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import { Sidebar } from "./sidebar";
import { TopBar } from "./top-bar";
import { CommandPalette } from "./command-palette";
import { Toaster } from "sonner";

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const { sidebarCollapsed } = useUIStore();

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div
        className={cn(
          "flex flex-1 flex-col transition-all duration-200",
          sidebarCollapsed ? "ml-16" : "ml-60",
        )}
      >
        <TopBar />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-[1440px] p-6">{children}</div>
        </main>
      </div>
      <CommandPalette />
      <Toaster
        position="bottom-right"
        toastOptions={{
          className: "border-border bg-card text-foreground text-sm",
        }}
      />
    </div>
  );
}
