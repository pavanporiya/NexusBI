"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PanelLeftClose, PanelLeft, Hexagon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import { SIDEBAR_NAV, APP_NAME } from "@/lib/constants";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "@/components/ui/tooltip";

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-border bg-card transition-all duration-200 ease-in-out",
          sidebarCollapsed ? "w-16" : "w-60"
        )}
      >
        {/* Brand */}
        <div className="flex h-12 shrink-0 items-center border-b border-border px-4">
          <Link href="/dashboard" className="flex items-center gap-2.5 overflow-hidden">
            <Hexagon className="h-5 w-5 shrink-0 text-primary" />
            {!sidebarCollapsed && (
              <span className="text-sm font-semibold tracking-tight text-foreground">
                {APP_NAME}
              </span>
            )}
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-2 py-3">
          {SIDEBAR_NAV.map((group) => (
            <div key={group.label} className="mb-4">
              {!sidebarCollapsed && (
                <span className="mb-1.5 block px-2 text-2xs font-semibold uppercase tracking-wider text-muted-foreground">
                  {group.label}
                </span>
              )}
              <ul className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive =
                    pathname === item.href ||
                    (item.href !== "/dashboard" && pathname.startsWith(item.href));
                  const Icon = item.icon;

                  const linkContent = (
                    <Link
                      href={item.href}
                      className={cn(
                        "flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm font-medium transition-colors",
                        isActive
                          ? "bg-primary/10 text-primary"
                          : "text-muted-foreground hover:bg-accent hover:text-foreground",
                        sidebarCollapsed && "justify-center px-0"
                      )}
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      {!sidebarCollapsed && (
                        <span className="truncate">{item.title}</span>
                      )}
                    </Link>
                  );

                  if (sidebarCollapsed) {
                    return (
                      <li key={item.href}>
                        <Tooltip>
                          <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
                          <TooltipContent side="right" className="font-medium">
                            {item.title}
                          </TooltipContent>
                        </Tooltip>
                      </li>
                    );
                  }

                  return <li key={item.href}>{linkContent}</li>;
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Collapse Toggle */}
        <div className="shrink-0 border-t border-border p-2">
          <button
            onClick={toggleSidebar}
            className="flex w-full items-center justify-center gap-2 rounded-md px-2 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {sidebarCollapsed ? (
              <PanelLeft className="h-4 w-4" />
            ) : (
              <>
                <PanelLeftClose className="h-4 w-4" />
                <span className="text-xs">Collapse</span>
              </>
            )}
          </button>
        </div>
      </aside>
    </TooltipProvider>
  );
}
