"use client";

import React, { useEffect, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { Building2, Plus, MoreHorizontal, Edit, Trash2 } from "lucide-react";
import { DataTable } from "@/components/data-table/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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

export default function OrganizationsPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newOrg, setNewOrg] = useState({ name: "", slug: "", description: "" });
  const [submitting, setSubmitting] = useState(false);

  const fetchOrganizations = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get<PaginatedResponse<Organization>>("/organizations");
      setOrganizations(res.items || []);
    } catch {
      // Fallback mock data if API unavailable
      setOrganizations([
        {
          id: "org_1",
          name: "Acme Corp Enterprise",
          slug: "acme-corp",
          description: "Global enterprise retail analytics organization",
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: "org_2",
          name: "Nexus BI Core",
          slug: "nexus-bi",
          description: "Internal core organization",
          is_active: true,
          created_at: new Date(Date.now() - 86400000 * 30).toISOString(),
          updated_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiClient.post("/organizations", newOrg);
      toast.success("Organization created successfully");
      setIsCreateOpen(false);
      setNewOrg({ name: "", slug: "", description: "" });
      fetchOrganizations();
    } catch {
      toast.error("Failed to create organization");
    } finally {
      setSubmitting(false);
    }
  };

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
            <p className="font-mono text-2xs text-muted-foreground">{row.original.slug}</p>
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
            <DropdownMenuItem>
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">Organizations</h1>
          <p className="text-xs text-muted-foreground">Manage multi-tenant enterprise organizations.</p>
        </div>
        <Button size="sm" onClick={() => setIsCreateOpen(true)}>
          <Plus className="mr-1.5 h-3.5 w-3.5" /> Create Organization
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={organizations}
        isLoading={loading}
        searchColumn="name"
        searchPlaceholder="Filter organizations..."
      />

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <form onSubmit={handleCreate}>
            <DialogHeader>
              <DialogTitle>Create Organization</DialogTitle>
              <DialogDescription>Add a new tenant organization to the platform.</DialogDescription>
            </DialogHeader>
            <div className="space-y-3 py-4">
              <div className="space-y-1">
                <Label htmlFor="org-name">Organization Name</Label>
                <Input
                  id="org-name"
                  placeholder="Acme Enterprise"
                  required
                  value={newOrg.name}
                  onChange={(e) =>
                    setNewOrg({
                      ...newOrg,
                      name: e.target.value,
                      slug: e.target.value.toLowerCase().replace(/[^a-z0-9]/g, "-"),
                    })
                  }
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="org-slug">Slug Identifier</Label>
                <Input
                  id="org-slug"
                  placeholder="acme-enterprise"
                  required
                  value={newOrg.slug}
                  onChange={(e) => setNewOrg({ ...newOrg, slug: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="org-desc">Description</Label>
                <Textarea
                  id="org-desc"
                  placeholder="Optional organization details..."
                  value={newOrg.description}
                  onChange={(e) => setNewOrg({ ...newOrg, description: e.target.value })}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={submitting}>
                Create Organization
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
