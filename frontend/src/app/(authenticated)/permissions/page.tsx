"use client";

import React, { useEffect, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { Lock, Loader2 } from "lucide-react";
import { DataTable } from "@/components/data-table/data-table";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";

interface PermissionRule {
  id: string;
  domain: string;
  action: string;
  description: string;
  roles: string[];
}

interface RolePermission {
  id: string;
  resource: string;
  action: string;
  description: string;
}

interface Role {
  id: string;
  name: string;
  permissions: RolePermission[];
}

export default function PermissionsPage() {
  const [permissions, setPermissions] = useState<PermissionRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPermissions = async () => {
      try {
        setLoading(true);
        const roles = await apiClient.get<Role[]>("/roles");
        const permMap = new Map<
          string,
          {
            id: string;
            domain: string;
            action: string;
            description: string;
            roles: string[];
          }
        >();

        for (const role of Array.isArray(roles) ? roles : []) {
          for (const perm of role.permissions || []) {
            const key = `${perm.resource}:${perm.action}`;
            if (permMap.has(key)) {
              permMap.get(key)!.roles.push(role.name);
            } else {
              permMap.set(key, {
                id: perm.id,
                domain: perm.resource,
                action: `${perm.resource}:${perm.action}`,
                description: perm.description,
                roles: [role.name],
              });
            }
          }
        }

        setPermissions(Array.from(permMap.values()));
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Failed to load permissions";
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    fetchPermissions();
  }, []);

  const columns: ColumnDef<PermissionRule>[] = [
    {
      accessorKey: "action",
      header: "Action String",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <Lock className="h-3.5 w-3.5 text-primary shrink-0" />
          <Badge variant="outline" className="font-mono text-2xs">
            {row.original.action}
          </Badge>
        </div>
      ),
    },
    {
      accessorKey: "domain",
      header: "Domain",
      cell: ({ row }) => (
        <span className="text-xs font-medium text-foreground capitalize">
          {row.original.domain}
        </span>
      ),
    },
    {
      accessorKey: "description",
      header: "Description",
      cell: ({ row }) => (
        <span className="text-xs text-muted-foreground">
          {row.original.description}
        </span>
      ),
    },
    {
      accessorKey: "roles",
      header: "Assigned Roles",
      cell: ({ row }) => (
        <div className="flex flex-wrap gap-1">
          {row.original.roles.map((r) => (
            <Badge key={r} variant="secondary" className="text-2xs">
              {r}
            </Badge>
          ))}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            Permissions
          </h1>
          <p className="text-xs text-muted-foreground">
            Fine-grained RBAC permissions enforced across all API endpoints.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Loading permissions…
        </div>
      ) : error ? (
        <div className="text-center py-12 text-destructive text-sm">
          {error}
        </div>
      ) : permissions.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground text-sm">
          No permissions found.
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={permissions}
          searchColumn="action"
          searchPlaceholder="Filter permissions..."
        />
      )}
    </div>
  );
}
