"use client";

import React, { useEffect, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { Clock, Loader2, Play, Pause, Trash2 } from "lucide-react";
import { DataTable } from "@/components/data-table/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatRelativeTime } from "@/lib/utils";
import { apiClient } from "@/lib/api-client";

interface Report {
  id: string;
  name: string;
  dataset_id: string;
  report_type: string;
  schedule: string | null;
  is_active: boolean;
  created_at: string;
}

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSchedules = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<{ items: Report[] }>(
        "/reports?limit=100",
      );
      const items = data?.items || (Array.isArray(data) ? data : []);
      // Show only reports that have a schedule configured
      setSchedules(items.filter((r) => r.schedule && r.schedule.trim() !== ""));
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to load schedules";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedules();
  }, []);

  const handleToggleActive = async (report: Report) => {
    try {
      await apiClient.patch(`/reports/${report.id}`, {
        is_active: !report.is_active,
      });
      fetchSchedules();
    } catch {
      // Silently fail — UI stays unchanged
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this schedule?")) return;
    try {
      await apiClient.delete(`/reports/${id}`);
      fetchSchedules();
    } catch {
      // Silently fail
    }
  };

  const columns: ColumnDef<Report>[] = [
    {
      accessorKey: "name",
      header: "Schedule Name",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-secondary">
            <Clock className="h-3.5 w-3.5 text-primary" />
          </div>
          <div>
            <p className="font-medium text-foreground">{row.original.name}</p>
            <p className="text-2xs text-muted-foreground">
              {row.original.report_type} report
            </p>
          </div>
        </div>
      ),
    },
    {
      accessorKey: "schedule",
      header: "Cron Cadence",
      cell: ({ row }) => (
        <Badge variant="outline" className="font-mono text-2xs">
          {row.original.schedule || "—"}
        </Badge>
      ),
    },
    {
      accessorKey: "report_type",
      header: "Type",
      cell: ({ row }) => (
        <Badge variant="secondary" className="text-2xs">
          {row.original.report_type}
        </Badge>
      ),
    },
    {
      accessorKey: "is_active",
      header: "Status",
      cell: ({ row }) => (
        <Badge variant={row.original.is_active ? "success" : "outline"}>
          {row.original.is_active ? "Active" : "Paused"}
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
        <div className="flex items-center justify-end gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => handleToggleActive(row.original)}
          >
            {row.original.is_active ? (
              <Pause className="h-3.5 w-3.5" />
            ) : (
              <Play className="h-3.5 w-3.5" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-destructive"
            onClick={() => handleDelete(row.original.id)}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            Schedules
          </h1>
          <p className="text-xs text-muted-foreground">
            Automated report dispatch timers. Configure schedules on the Reports
            page.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Loading schedules…
        </div>
      ) : error ? (
        <div className="text-center py-12 text-destructive text-sm">
          {error}
        </div>
      ) : schedules.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground text-sm">
          No scheduled reports yet. Create a report with a schedule to see it
          here.
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={schedules}
          searchColumn="name"
          searchPlaceholder="Filter schedules..."
        />
      )}
    </div>
  );
}
