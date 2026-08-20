"use client";

import React, { useEffect, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import {
  Building2,
  Plus,
  MoreHorizontal,
  Edit,
  Trash2,
  AlertCircle,
} from "lucide-react";
import { DataTable } from "@/components/data-table/data-table";
import { EmptyState } from "@/components/feedback/empty-state";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { apiClient } from "@/lib/api-client";
import { formatRelativeTime } from "@/lib/utils";
import type { Organization, PaginatedResponse } from "@/types/api";
import { toast } from "sonner";

import { OrgEmptyIllustration } from "@/components/organizations/org-empty-illustration";
import { CreateOrganizationDialog } from "@/components/organizations/create-organization-dialog";
import { EditOrganizationDialog } from "@/components/organizations/edit-organization-dialog";

export default function OrganizationsPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingOrg, setEditingOrg] = useState<Organization | null>(null);

  const fetchOrganizations = async () => {
    setLoading(true);
    setError(null);
    try {
      const res =
        await apiClient.get<PaginatedResponse<Organization>>("/organizations");
      setOrganizations(res.items || []);
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load organizations";
      setError(errorMessage);
      setOrganizations([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await apiClient.delete(`/organizations/${id}`);
      toast.success("Organization deleted");
      fetchOrganizations();
    } catch {
      toast.error("Failed to delete organization");
    }
  };

  const columns: ColumnDef<Organization>[] = [
    {
      accessorKey: "name",
      header: "Organization Name",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-secondary">
            <Building2 className="h-3.5 w-3.5 text-primary" />
          </div>
          <div>
            <p className="font-medium text-foreground">{row.original.name}</p>
            <p className="font-mono text-2xs text-muted-foreground">
              {row.original.slug}
            </p>
          </div>
        </div>
      ),
    },
    {
      accessorKey: "description",
      header: "Description",
      cell: ({ row }) => (
        <span className="text-xs text-muted-foreground truncate max-w-[280px] inline-block">
          {row.original.description || "No description provided"}
        </span>
      ),
    },
    {
      accessorKey: "is_active",
      header: "Status",
      cell: ({ row }) => (
        <Badge variant={row.original.is_active ? "success" : "outline"}>
          {row.original.is_active ? "Active" : "Inactive"}
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
            <Button variant="ghost" size="icon" className="h-7 w-7">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setEditingOrg(row.original)}>
              <Edit className="mr-2 h-3.5 w-3.5" /> Edit Organization
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={() => handleDelete(row.original.id)}
            >
              <Trash2 className="mr-2 h-3.5 w-3.5" /> Delete Organization
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      {/* Render top header bar when organizations exist or loading/error */}
      {(loading || error || organizations.length > 0) && (
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-foreground">
              Organizations
            </h1>
            <p className="text-xs text-muted-foreground">
              Manage multi-tenant enterprise organizations.
            </p>
          </div>
          <Button size="sm" onClick={() => setIsCreateOpen(true)}>
            <Plus className="mr-1.5 h-3.5 w-3.5" /> Create Organization
          </Button>
        </div>
      )}

      {error ? (
        <EmptyState
          icon={AlertCircle}
          title="Failed to load organizations"
          description={error}
          action={{
            label: "Retry",
            onClick: fetchOrganizations,
          }}
        />
      ) : !loading && organizations.length === 0 ? (
        <section
          aria-label="Welcome and organization setup"
          className="flex min-h-[calc(100vh-11rem)] w-full items-center justify-center rounded-xl border border-border/40 bg-card/30 p-4 sm:p-8 backdrop-blur-xs"
        >
          <EmptyState
            illustration={<OrgEmptyIllustration />}
            title="Welcome to NexusBI"
            description="Create your first organization to start managing workspaces, datasets, dashboards, and reports."
            action={{
              label: "Create Organization",
              onClick: () => setIsCreateOpen(true),
              icon: Plus,
            }}
          />
        </section>
      ) : (
        <DataTable
          columns={columns}
          data={organizations}
          isLoading={loading}
          searchColumn="name"
          searchPlaceholder="Filter organizations..."
        />
      )}

      <CreateOrganizationDialog
        open={isCreateOpen}
        onOpenChange={setIsCreateOpen}
        onSuccess={fetchOrganizations}
      />

      <EditOrganizationDialog
        organization={editingOrg}
        open={!!editingOrg}
        onOpenChange={(open) => {
          if (!open) setEditingOrg(null);
        }}
        onSuccess={fetchOrganizations}
      />
    </div>
  );
}
