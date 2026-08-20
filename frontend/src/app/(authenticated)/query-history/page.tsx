"use client";

import React, { useEffect, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { History, Play, Loader2 } from "lucide-react";
import { DataTable } from "@/components/data-table/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatRelativeTime } from "@/lib/utils";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";

interface AgentRun {
  run_id: string;
  status: string;
  agent_role: string;
  natural_language_query: string;
  generated_sql: string;
  confidence: number;
  total_tokens: number;
  created_at: string;
}

export default function QueryHistoryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const data = await apiClient.get<AgentRun[]>("/agents/runs?limit=50");
        setHistory(Array.isArray(data) ? data : []);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Failed to load query history";
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const columns: ColumnDef<AgentRun>[] = [
    {
      accessorKey: "natural_language_query",
      header: "Query",
      cell: ({ row }) => (
        <div className="flex items-center gap-2 max-w-[380px]">
          <History className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
          <span className="text-xs text-foreground truncate">
            {row.original.natural_language_query}
          </span>
        </div>
      ),
    },
    {
      accessorKey: "generated_sql",
      header: "Generated SQL",
      cell: ({ row }) => (
        <span className="font-mono text-2xs text-muted-foreground truncate max-w-[260px] block">
          {row.original.generated_sql || "—"}
        </span>
      ),
    },
    {
      accessorKey: "agent_role",
      header: "Persona",
      cell: ({ row }) => (
        <Badge variant="outline" className="text-2xs">
          {row.original.agent_role}
        </Badge>
      ),
    },
    {
      accessorKey: "total_tokens",
      header: "Tokens",
      cell: ({ row }) => (
        <span className="font-mono text-2xs text-muted-foreground">
          {row.original.total_tokens.toLocaleString()}
        </span>
      ),
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => (
        <Badge
          variant={
            row.original.status === "completed" ? "success" : "destructive"
          }
        >
          {row.original.status}
        </Badge>
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
          onClick={() =>
            router.push(
              `/sql-editor?query=${encodeURIComponent(row.original.natural_language_query)}`,
            )
          }
        >
          <Play className="mr-1 h-3.5 w-3.5" /> Re-run
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            Query History
          </h1>
          <p className="text-xs text-muted-foreground">
            Audit log of all agent query executions and telemetry.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Loading query history…
        </div>
      ) : error ? (
        <div className="text-center py-12 text-destructive text-sm">
          {error}
        </div>
      ) : history.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground text-sm">
          No query history yet. Execute an agent query to see results here.
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={history}
          searchColumn="natural_language_query"
          searchPlaceholder="Filter query history..."
        />
      )}
    </div>
  );
}
