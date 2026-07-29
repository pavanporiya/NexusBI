"use client";

import React, { useEffect, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { LayoutGrid, Plus, MoreHorizontal, Edit, Trash2, Globe, Lock } from "lucide-react";
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
import type { Dashboard, PaginatedResponse } from "@/types/api";
import { toast } from "sonner";

export default function DashboardsPage() {
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newDashboard, setNewDashboard] = useState({ name: "", dataset_id: "ds_sales_fact", description: "" });

  const fetchDashboards = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get<PaginatedResponse<Dashboard>>("/dashboards");
      setDashboards(res.items || []);
    } catch {
      // Mock data fallback
      setDashboards([
        {
          id: "db_executive",
          name: "Executive Overview & Revenue Telemetry",
          owner_id: "usr_1",
          dataset_id: "ds_sales_fact",
          description: "High-level ARR, churn, and regional sales metrics",
          layout_json: {},
          is_public: true,
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: "db_infra",
          name: "Infrastructure & API Latency Monitor",
          owner_id: "usr_1",
          dataset_id: "ds_customer_dim",
          description: "System health probes, Redis query hit rates, and database load",
          layout_json: {},
          is_public: false,
          is_active: true,
          created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
          updated_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboards();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post("/dashboards", newDashboard);
      toast.success("Dashboard created");
      setIsCreateOpen(false);
      fetchDashboards();
    } catch {
      toast.error("Failed to create dashboard");
    }
  };

  const columns: ColumnDef<Dashboard>[] = [
    {
      accessorKey: "name",
      header: "Dashboard Title",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-secondary">
            <LayoutGrid className="h-3.5 w-3.5 text-primary" />
          </div>
          <div>
            <p className="font-medium text-foreground">{row.original.name}</p>
            <p className="text-2xs text-muted-foreground">{row.original.description || "No description"}</p>
          </div>
        </div>
      ),
    },
    {
      accessorKey: "is_public",
      header: "Visibility",
      cell: ({ row }) => (
        <Badge variant={row.original.is_public ? "default" : "outline"} className="gap-1">
          {row.original.is_public ? <Globe className="h-3 w-3" /> : <Lock className="h-3 w-3" />}
          {row.original.is_public ? "Public" : "Private"}
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
      cell: () => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-7 w-7">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem><Edit className="mr-2 h-3.5 w-3.5" /> Edit Canvas Layout</DropdownMenuItem>
            <DropdownMenuItem className="text-destructive focus:text-destructive">
              <Trash2 className="mr-2 h-3.5 w-3.5" /> Delete Dashboard
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
          <h1 className="text-xl font-semibold tracking-tight text-foreground">Dashboards</h1>
          <p className="text-xs text-muted-foreground">Interactive analytical canvases and multi-widget monitoring boards.</p>
        </div>
        <Button size="sm" onClick={() => setIsCreateOpen(true)}>
          <Plus className="mr-1.5 h-3.5 w-3.5" /> Create Dashboard
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={dashboards}
        isLoading={loading}
        searchColumn="name"
        searchPlaceholder="Filter dashboards..."
      />

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <form onSubmit={handleCreate}>
            <DialogHeader>
              <DialogTitle>Create Dashboard</DialogTitle>
              <DialogDescription>Initialize a new interactive dashboard layout.</DialogDescription>
            </DialogHeader>
            <div className="space-y-3 py-4">
              <div className="space-y-1">
                <Label>Dashboard Title</Label>
                <Input
                  placeholder="ARR & Regional Sales"
                  required
                  value={newDashboard.name}
                  onChange={(e) => setNewDashboard({ ...newDashboard, name: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label>Description</Label>
                <Textarea
                  placeholder="Optional canvas summary..."
                  value={newDashboard.description}
                  onChange={(e) => setNewDashboard({ ...newDashboard, description: e.target.value })}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Create Dashboard</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
