"use client";

import React, { useEffect, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { FolderKanban, Plus, MoreHorizontal, Edit, Trash2 } from "lucide-react";
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
import type { Workspace, PaginatedResponse } from "@/types/api";
import { toast } from "sonner";

export default function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newWs, setNewWs] = useState({
    name: "",
    slug: "",
    description: "",
    organization_id: "org_default",
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchWorkspaces = async () => {
    setLoading(true);
    try {
      const res =
        await apiClient.get<PaginatedResponse<Workspace>>("/workspaces");
      setWorkspaces(res.items || []);
    } catch {
      // Mock data fallback
      setWorkspaces([
        {
          id: "ws_1",
          organization_id: "org_1",
          name: "Production Analytics",
          slug: "prod-analytics",
          description: "Live revenue & financial modeling workspace",
          is_default: true,
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: "ws_2",
          organization_id: "org_1",
          name: "Product & UX Research",
          slug: "product-research",
          description: "User behavior telemetry and funnel metrics",
          is_default: false,
          is_active: true,
          created_at: new Date(Date.now() - 86400000 * 15).toISOString(),
          updated_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiClient.post("/workspaces", newWs);
      toast.success("Workspace created");
      setIsCreateOpen(false);
      setNewWs({
        name: "",
        slug: "",
        description: "",
        organization_id: "org_default",
      });
      fetchWorkspaces();
    } catch {
      toast.error("Failed to create workspace");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiClient.delete(`/workspaces/${id}`);
      toast.success("Workspace deleted");
      fetchWorkspaces();
    } catch {
      toast.error("Failed to delete workspace");
    }
  };

  const columns: ColumnDef<Workspace>[] = [
    {
      accessorKey: "name",
      header: "Workspace Name",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-secondary">
            <FolderKanban className="h-3.5 w-3.5 text-primary" />
          </div>
          <div>
            <p className="font-medium text-foreground flex items-center gap-1.5">
              {row.original.name}
              {row.original.is_default && (
                <Badge variant="outline">Default</Badge>
              )}
            </p>
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
          {row.original.description || "No description"}
        </span>
      ),
    },
    {
      accessorKey: "is_active",
      header: "Status",
      cell: ({ row }) => (
        <Badge variant={row.original.is_active ? "success" : "outline"}>
          {row.original.is_active ? "Active" : "Archived"}
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
              <Edit className="mr-2 h-3.5 w-3.5" /> Edit Workspace
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={() => handleDelete(row.original.id)}
            >
              <Trash2 className="mr-2 h-3.5 w-3.5" /> Delete Workspace
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
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            Workspaces
          </h1>
          <p className="text-xs text-muted-foreground">
            Isolated analytics environments and team workspaces.
          </p>
        </div>
        <Button size="sm" onClick={() => setIsCreateOpen(true)}>
          <Plus className="mr-1.5 h-3.5 w-3.5" /> Create Workspace
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={workspaces}
        isLoading={loading}
        searchColumn="name"
        searchPlaceholder="Filter workspaces..."
      />

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <form onSubmit={handleCreate}>
            <DialogHeader>
              <DialogTitle>Create Workspace</DialogTitle>
              <DialogDescription>
                Add a new workspace for dataset and query isolation.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 py-4">
              <div className="space-y-1">
                <Label htmlFor="ws-name">Workspace Name</Label>
                <Input
                  id="ws-name"
                  placeholder="Sales Analytics"
                  required
                  value={newWs.name}
                  onChange={(e) =>
                    setNewWs({
                      ...newWs,
                      name: e.target.value,
                      slug: e.target.value
                        .toLowerCase()
                        .replace(/[^a-z0-9]/g, "-"),
                    })
                  }
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="ws-slug">Slug Identifier</Label>
                <Input
                  id="ws-slug"
                  placeholder="sales-analytics"
                  required
                  value={newWs.slug}
                  onChange={(e) => setNewWs({ ...newWs, slug: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="ws-desc">Description</Label>
                <Textarea
                  id="ws-desc"
                  placeholder="Optional workspace purpose..."
                  value={newWs.description}
                  onChange={(e) =>
                    setNewWs({ ...newWs, description: e.target.value })
                  }
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsCreateOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" loading={submitting}>
                Create Workspace
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
