"use client";

import React, { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { History, Play } from "lucide-react";
import { DataTable } from "@/components/data-table/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatRelativeTime } from "@/lib/utils";
import { useRouter } from "next/navigation";

interface QueryLog {
  id: string;
  sql: string;
  user: string;
  execution_time_ms: number;
  row_count: number;
  status: "success" | "error";
  cache_hit: boolean;
  created_at: string;
}

export default function QueryHistoryPage() {
  const router = useRouter();
  const [history] = useState<QueryLog[]>([
    {
      id: "qh_1",
      sql: "SELECT region, SUM(revenue) FROM sales_fact GROUP BY 1 ORDER BY 2 DESC LIMIT 10",
      user: "pavan@nexusbi.io",
      execution_time_ms: 142,
      row_count: 10,
      status: "success",
      cache_hit: true,
      created_at: new Date().toISOString(),
    },
    {
      id: "qh_2",
      sql: "SELECT customer_id, COUNT(*) FROM orders WHERE created_at >= NOW() - INTERVAL '30 days' GROUP BY 1",
      user: "alex.m@nexusbi.io",
      execution_time_ms: 854,
      row_count: 4291,
      status: "success",
      cache_hit: false,
      created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    },
    {
      id: "qh_3",
      sql: "SELECT * FROM invalid_table_name WHERE id = 100",
      user: "sarah.c@nexusbi.io",
      execution_time_ms: 22,
      row_count: 0,
      status: "error",
      cache_hit: false,
      created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
    },
  ]);

  const columns: ColumnDef<QueryLog>[] = [
    {
      accessorKey: "sql",
      header: "SQL Query",
      cell: ({ row }) => (
        <div className="flex items-center gap-2 max-w-[380px]">
          <History className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
          <span className="font-mono text-2xs text-foreground truncate">{row.original.sql}</span>
        </div>
      ),
    },
    {
      accessorKey: "user",
      header: "Executed By",
      cell: ({ row }) => <span className="text-xs text-muted-foreground">{row.original.user}</span>,
    },
    {
      accessorKey: "execution_time_ms",
      header: "Duration",
      cell: ({ row }) => (
        <span className="font-mono text-2xs text-muted-foreground">
          {row.original.execution_time_ms} ms
        </span>
      ),
    },
    {
      accessorKey: "row_count",
      header: "Rows Returned",
      cell: ({ row }) => (
        <span className="font-mono text-2xs text-muted-foreground">
          {row.original.row_count.toLocaleString()}
        </span>
      ),
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => (
        <div className="flex items-center gap-1.5">
          <Badge variant={row.original.status === "success" ? "success" : "destructive"}>
            {row.original.status}
          </Badge>
          {row.original.cache_hit && <Badge variant="outline">Cache Hit</Badge>}
        </div>
      ),
    },
    {
      accessorKey: "created_at",
      header: "Time",
      cell: ({ row }) => (
        <span className="text-xs text-muted-foreground">
          {formatRelativeTime(row.original.created_at)}
        </span>
      ),
    },
    {
      id: "actions",
      cell: ({ row }) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push(`/sql-editor?query=${encodeURIComponent(row.original.sql)}`)}
        >
          <Play className="mr-1 h-3.5 w-3.5" /> Open in Editor
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">Query History</h1>
          <p className="text-xs text-muted-foreground">Audit log of all interactive SQL queries and execution telemetry.</p>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={history}
        searchColumn="sql"
        searchPlaceholder="Filter query history..."
      />
    </div>
  );
}
