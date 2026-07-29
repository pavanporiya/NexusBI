"use client";

import React, { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { Clock, Plus, Play, Pause, Trash2 } from "lucide-react";
import { DataTable } from "@/components/data-table/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface ScheduleItem {
  id: string;
  name: string;
  target_report: string;
  cron_expression: string;
  recipient_email: string;
  is_active: boolean;
  last_run: string;
  next_run: string;
}

export default function SchedulesPage() {
  const [schedules] = useState<ScheduleItem[]>([
    {
      id: "sch_1",
      name: "Weekly Executive Revenue Digest",
      target_report: "Q3 Enterprise Financial Summary",
      cron_expression: "0 8 * * 1", // Every Monday at 8 AM
      recipient_email: "exec-team@nexusbi.io",
      is_active: true,
      last_run: new Date(Date.now() - 86400000 * 2).toISOString(),
      next_run: new Date(Date.now() + 86400000 * 5).toISOString(),
    },
    {
      id: "sch_2",
      name: "Daily Infrastructure Latency Alert",
      target_report: "Infrastructure & API Latency Monitor",
      cron_expression: "0 0 * * *", // Daily at Midnight
      recipient_email: "devops@nexusbi.io",
      is_active: true,
      last_run: new Date(Date.now() - 3600000 * 12).toISOString(),
      next_run: new Date(Date.now() + 3600000 * 12).toISOString(),
    },
  ]);

  const columns: ColumnDef<ScheduleItem>[] = [
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
              {row.original.target_report}
            </p>
          </div>
        </div>
      ),
    },
    {
      accessorKey: "cron_expression",
      header: "Cron Cadence",
      cell: ({ row }) => (
        <Badge variant="outline" className="font-mono text-2xs">
          {row.original.cron_expression}
        </Badge>
      ),
    },
    {
      accessorKey: "recipient_email",
      header: "Recipient",
      cell: ({ row }) => (
        <span className="text-xs text-muted-foreground">
          {row.original.recipient_email}
        </span>
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
      id: "actions",
      cell: ({ row }) => (
        <div className="flex items-center justify-end gap-1">
          <Button variant="ghost" size="icon" className="h-7 w-7">
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
            Automated report dispatch timers and email subscription cron tasks.
          </p>
        </div>
        <Button size="sm">
          <Plus className="mr-1.5 h-3.5 w-3.5" /> Create Schedule
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={schedules}
        searchColumn="name"
        searchPlaceholder="Filter schedules..."
      />
    </div>
  );
}
