"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  Search,
  Bell,
  LogOut,
  User,
  Settings,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getInitials } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import { useAuthStore } from "@/stores/auth-store";
import { SIDEBAR_NAV } from "@/lib/constants";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

function getBreadcrumbs(pathname: string) {
  const segments = pathname.split("/").filter(Boolean);
  const crumbs: { label: string; href: string }[] = [];

  let currentPath = "";
  for (const segment of segments) {
    currentPath += `/${segment}`;
    const label = segment
      .replace(/-/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
    crumbs.push({ label, href: currentPath });
  }
  return crumbs;
}

export function TopBar() {
  const pathname = usePathname();
  const router = useRouter();
  const { sidebarCollapsed, setCommandPaletteOpen } = useUIStore();
  const { user, logout } = useAuthStore();

  const breadcrumbs = getBreadcrumbs(pathname);

  // Find current page title
  const allNavItems = SIDEBAR_NAV.flatMap((g) => g.items);
  const currentNav = allNavItems.find(
    (item) =>
      pathname === item.href ||
      (item.href !== "/dashboard" && pathname.startsWith(item.href)),
  );
  const pageTitle =
    currentNav?.title ||
    breadcrumbs[breadcrumbs.length - 1]?.label ||
    "Dashboard";

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header
      className={cn(
        "sticky top-0 z-30 flex h-12 shrink-0 items-center border-b border-border bg-background/80 backdrop-blur-sm transition-all duration-200",
        sidebarCollapsed ? "pl-16" : "pl-60",
      )}
    >
      <div className="flex flex-1 items-center justify-between px-4">
        {/* Left: Breadcrumbs */}
        <div className="flex items-center gap-1.5 text-sm">
          {breadcrumbs.map((crumb, index) => (
            <React.Fragment key={crumb.href}>
              {index > 0 && (
                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
              )}
              <span
                className={cn(
                  "font-medium",
                  index === breadcrumbs.length - 1
                    ? "text-foreground"
                    : "text-muted-foreground",
                )}
              >
                {index === breadcrumbs.length - 1 ? pageTitle : crumb.label}
              </span>
            </React.Fragment>
          ))}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-1">
          {/* Search */}
          <Button
            variant="ghost"
            size="sm"
            className="gap-2 text-muted-foreground"
            onClick={() => setCommandPaletteOpen(true)}
          >
            <Search className="h-4 w-4" />
            <span className="hidden text-xs sm:inline-flex">Search</span>
            <kbd className="pointer-events-none hidden h-5 select-none items-center gap-0.5 rounded border border-border bg-muted px-1.5 font-mono text-2xs font-medium text-muted-foreground sm:inline-flex">
              ⌘K
            </kbd>
          </Button>

          <Separator orientation="vertical" className="mx-1 h-5" />

          {/* Notifications */}
          <Button variant="ghost" size="icon" className="text-muted-foreground">
            <Bell className="h-4 w-4" />
          </Button>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-md">
                <Avatar className="h-6 w-6">
                  <AvatarFallback className="text-2xs">
                    {user?.email ? getInitials(user.email) : "U"}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {user?.full_name || user?.email || "User"}
                  </p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user?.email}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push("/settings")}>
                <User className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => router.push("/settings")}>
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleLogout}
                className="text-destructive focus:text-destructive"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
