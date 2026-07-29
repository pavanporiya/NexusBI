"use client";

import React, { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { Lock } from "lucide-react";
import { DataTable } from "@/components/data-table/data-table";
import { Badge } from "@/components/ui/badge";

interface PermissionRule {
  domain: string;
  action: string;
  description: string;
}

export default function PermissionsPage() {
  const [permissions] = useState<PermissionRule[]>([
    { domain: "Organizations", action: "organizations:read", description: "View organization lists and details" },
    { domain: "Organizations", action: "organizations:create", description: "Create new enterprise organizations" },
    { domain: "Organizations", action: "organizations:update", description: "Modify organization metadata" },
    { domain: "Organizations", action: "organizations:delete", description: "Permanently delete an organization" },

    { domain: "Workspaces", action: "workspaces:read", description: "View workspace details and members" },
    { domain: "Workspaces", action: "workspaces:create", description: "Create new analytical workspaces" },

    { domain: "Datasets", action: "datasets:read", description: "Query datasets and preview sample rows" },
    { domain: "Datasets", action: "datasets:create", description: "Register new physical tables or SQL queries" },

    { domain: "Query Engine", action: "query:execute", description: "Run interactive SELECT queries against DW" },
    { domain: "Query Engine", action: "query:explain", description: "View query execution plan AST" },

    { domain: "Dashboards", action: "dashboards:create", description: "Create and edit interactive dashboards" },
    { domain: "Reports", action: "reports:create", description: "Generate analytical reports and exports" },
  ]);

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
      header: "Domain Component",
      cell: ({ row }) => <span className="text-xs font-medium text-foreground">{row.original.domain}</span>,
    },
    {
      accessorKey: "description",
      header: "Description",
      cell: ({ row }) => <span className="text-xs text-muted-foreground">{row.original.description}</span>,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">Permissions</h1>
          <p className="text-xs text-muted-foreground">Fine-grained RBAC action strings enforced across all API endpoints.</p>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={permissions}
        searchColumn="action"
        searchPlaceholder="Filter permissions..."
      />
    </div>
  );
}
