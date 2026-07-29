import {
  LayoutDashboard,
  Building2,
  FolderKanban,
  Database,
  Table2,
  Terminal,
  History,
  BarChart3,
  LayoutGrid,
  FileText,
  Clock,
  Users,
  Shield,
  Lock,
  Settings,
  type LucideIcon,
} from "lucide-react";

// ─── Navigation ──────────────────────────────────────────────────────────────

export interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

export const SIDEBAR_NAV: NavGroup[] = [
  {
    label: "Platform",
    items: [
      { title: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { title: "Organizations", href: "/organizations", icon: Building2 },
      { title: "Workspaces", href: "/workspaces", icon: FolderKanban },
    ],
  },
  {
    label: "Data",
    items: [
      { title: "Data Sources", href: "/data-sources", icon: Database },
      { title: "Datasets", href: "/datasets", icon: Table2 },
      { title: "SQL Editor", href: "/sql-editor", icon: Terminal },
      { title: "Query History", href: "/query-history", icon: History },
    ],
  },
  {
    label: "Visualization",
    items: [
      { title: "Charts", href: "/charts", icon: BarChart3 },
      { title: "Dashboards", href: "/dashboards", icon: LayoutGrid },
      { title: "Reports", href: "/reports", icon: FileText },
      { title: "Schedules", href: "/schedules", icon: Clock },
    ],
  },
  {
    label: "Administration",
    items: [
      { title: "Users", href: "/users", icon: Users },
      { title: "Roles", href: "/roles", icon: Shield },
      { title: "Permissions", href: "/permissions", icon: Lock },
      { title: "Settings", href: "/settings", icon: Settings },
    ],
  },
];

// ─── App Metadata ────────────────────────────────────────────────────────────

export const APP_NAME = "NexusBI";
export const APP_DESCRIPTION = "Enterprise AI Analytics Platform";

// ─── Sidebar Dimensions ─────────────────────────────────────────────────────

export const SIDEBAR_WIDTH_EXPANDED = 240;
export const SIDEBAR_WIDTH_COLLAPSED = 64;

// ─── Status Colors ──────────────────────────────────────────────────────────

export const STATUS_COLORS: Record<string, string> = {
  healthy: "text-green-400",
  degraded: "text-yellow-400",
  unhealthy: "text-red-400",
  unavailable: "text-zinc-500",
};

export const STATUS_BG_COLORS: Record<string, string> = {
  healthy: "bg-green-500/10",
  degraded: "bg-yellow-500/10",
  unhealthy: "bg-red-500/10",
  unavailable: "bg-zinc-500/10",
};

export const STATUS_BORDER_COLORS: Record<string, string> = {
  healthy: "border-green-500/20",
  degraded: "border-yellow-500/20",
  unhealthy: "border-red-500/20",
  unavailable: "border-zinc-500/20",
};
