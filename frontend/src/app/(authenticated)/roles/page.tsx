"use client";

import React, { useEffect, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { Shield, Plus, MoreHorizontal, Edit, Trash2 } from "lucide-react";
import { DataTable } from "@/components/data-table/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";
import { formatRelativeTime } from "@/lib/utils";
import type { Role, PaginatedResponse } from "@/types/api";

export default function RolesPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRoles = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get<PaginatedResponse<Role>>("/roles");
      setRoles(res.items || []);
    } catch {
      setRoles([
        {
          id: "role_admin",
          name: "Administrator",
          description: "Full system administration and permission delegation",
          permissions: ["*"],
          is_system: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: "role_analyst",
          name: "Analyst",
          description: "Execute SQL queries, create datasets, and build dashboards",
          permissions: ["datasets:read", "datasets:create", "query:execute", "dashboards:create"],
          is_system: false,
          created_at: new Date(Date.now() - 86400000 * 30).toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: "role_viewer",
          name: "Viewer",
          description: "Read-only access to published dashboards and reports",
          permissions: ["dashboards:read", "reports:read"],
          is_system: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  const columns: ColumnDef<Role>[] = [
    {
      accessorKey: "name",
      header: "Role Name",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-secondary">
            <Shield className="h-3.5 w-3.5 text-primary" />
          </div>
          <div>
            <p className="font-medium text-foreground flex items-center gap-1.5">
              {row.original.name}
              {row.original.is_system && <Badge variant="outline">System</Badge>}
            </p>
            <p className="text-2xs text-muted-foreground">{row.original.description}</p>
          </div>
        </div>
      ),
    },
    {
      accessorKey: "permissions",
      header: "Permissions",
      cell: ({ row }) => (
        <Badge variant="secondary" className="font-mono text-2xs">
          {row.original.permissions.includes("*") ? "All Permissions (*)" : `${row.original.permissions.length} Action String(s)`}
        </Badge>
      ),
    },
    {
      accessorKey: "created_at",
      header: "Created",
      cell: ({ row }) => (
        <span className="text-xs text-muted-foreground">
          {formatRelativeTime(row.original.created_at)}
        </span>
      ),
    },
    {
      id: "actions",
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-7 w-7" disabled={row.original.is_system}>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem><Edit className="mr-2 h-3.5 w-3.5" /> Edit Permissions</DropdownMenuItem>
            <DropdownMenuItem className="text-destructive focus:text-destructive">
              <Trash2 className="mr-2 h-3.5 w-3.5" /> Delete Role
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">Roles</h1>
          <p className="text-xs text-muted-foreground">RBAC role definitions and permission mapping.</p>
        </div>
        <Button size="sm">
          <Plus className="mr-1.5 h-3.5 w-3.5" /> Create Role
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={roles}
        isLoading={loading}
        searchColumn="name"
        searchPlaceholder="Filter roles..."
      />
    </div>
  );
}

// Helper dropdown import
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
