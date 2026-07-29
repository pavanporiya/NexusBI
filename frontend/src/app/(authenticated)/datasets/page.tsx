"use client";

import React, { useEffect, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { Table2, Plus, Eye, MoreHorizontal, Edit, Trash2 } from "lucide-react";
import { DataTable } from "@/components/data-table/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import type { Dataset, PaginatedResponse, QueryResult } from "@/types/api";
import { toast } from "sonner";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [previewData, setPreviewData] = useState<QueryResult | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  const [newDataset, setNewDataset] = useState({
    name: "",
    source_type: "snowflake",
    object_type: "table",
    object_name: "",
    sql_query: "",
    description: "",
  });

  const fetchDatasets = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get<PaginatedResponse<Dataset>>("/datasets");
      setDatasets(res.items || []);
    } catch {
      // Mock datasets fallback
      setDatasets([
        {
          id: "ds_sales_fact",
          name: "Sales Fact Transactions",
          source_type: "snowflake",
          object_type: "table",
          object_name: "SALES_FACT",
          sql_query: null,
          connection_id: "conn_1",
          query_or_table: "SALES_FACT",
          owner_id: "usr_1",
          description: "Core sales transaction fact table with order metrics",
          schema_metadata: {},
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: "ds_customer_dim",
          name: "Customer Lifetime Analytics",
          source_type: "postgres",
          object_type: "query",
          object_name: null,
          sql_query:
            "SELECT c.id, c.email, COUNT(o.id) as total_orders FROM customers c LEFT JOIN orders o ON c.id = o.customer_id GROUP BY 1, 2",
          connection_id: "conn_2",
          query_or_table: "SELECT ...",
          owner_id: "usr_1",
          description: "Aggregated customer metrics and purchase counts",
          schema_metadata: {},
          is_active: true,
          created_at: new Date(Date.now() - 86400000 * 10).toISOString(),
          updated_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handlePreview = async (id: string) => {
    setPreviewing(true);
    setIsPreviewOpen(true);
    try {
      const res = await apiClient.get<QueryResult>(
        `/query/preview-dataset/${id}?limit=10`,
      );
      setPreviewData(res);
    } catch {
      // Mock result fallback
      setPreviewData({
        rows: [
          {
            id: "1001",
            region: "North America",
            revenue: 45200.0,
            margin: 0.34,
          },
          {
            id: "1002",
            region: "Europe Central",
            revenue: 38900.5,
            margin: 0.28,
          },
          {
            id: "1003",
            region: "Asia Pacific",
            revenue: 61200.0,
            margin: 0.42,
          },
        ],
        columns: [
          { name: "id", type: "INTEGER" },
          { name: "region", type: "VARCHAR" },
          { name: "revenue", type: "FLOAT" },
          { name: "margin", type: "FLOAT" },
        ],
        column_types: {
          id: "INTEGER",
          region: "VARCHAR",
          revenue: "FLOAT",
          margin: "FLOAT",
        },
        execution_time: 0.042,
        row_count: 3,
        metadata: {
          statistics: {
            query_plan: null,
            rows_scanned: 100,
            bytes_processed: 1024,
            cache_hit: true,
          },
          execution_time: 0.042,
          row_count: 3,
          columns: [
            { name: "id", type: "INTEGER" },
            { name: "region", type: "VARCHAR" },
          ],
          truncated: false,
          limit: 10,
          offset: 0,
        },
      });
    } finally {
      setPreviewing(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post("/datasets", {
        name: newDataset.name,
        source_type: newDataset.source_type,
        object_type: newDataset.object_type,
        object_name:
          newDataset.object_type === "table" ? newDataset.object_name : null,
        sql_query:
          newDataset.object_type === "query" ? newDataset.sql_query : null,
        description: newDataset.description,
      });
      toast.success("Dataset created");
      setIsCreateOpen(false);
      fetchDatasets();
    } catch {
      toast.error("Failed to create dataset");
    }
  };

  const columns: ColumnDef<Dataset>[] = [
    {
      accessorKey: "name",
      header: "Dataset Name",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-secondary">
            <Table2 className="h-3.5 w-3.5 text-primary" />
          </div>
          <div>
            <p className="font-medium text-foreground">{row.original.name}</p>
            <p className="font-mono text-2xs text-muted-foreground">
              {row.original.object_type === "table"
                ? row.original.object_name
                : "SQL Query"}
            </p>
          </div>
        </div>
      ),
    },
    {
      accessorKey: "source_type",
      header: "Source Adapter",
      cell: ({ row }) => (
        <Badge variant="outline" className="font-mono text-2xs uppercase">
          {row.original.source_type}
        </Badge>
      ),
    },
    {
      accessorKey: "object_type",
      header: "Type",
      cell: ({ row }) => (
        <Badge
          variant={
            row.original.object_type === "table" ? "secondary" : "default"
          }
        >
          {row.original.object_type}
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
            size="sm"
            onClick={() => handlePreview(row.original.id)}
          >
            <Eye className="mr-1 h-3.5 w-3.5 text-muted-foreground" /> Preview
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <Edit className="mr-2 h-3.5 w-3.5" /> Edit Schema
              </DropdownMenuItem>
              <DropdownMenuItem className="text-destructive focus:text-destructive">
                <Trash2 className="mr-2 h-3.5 w-3.5" /> Delete Dataset
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            Datasets
          </h1>
          <p className="text-xs text-muted-foreground">
            Semantic catalog of physical database tables, views, and custom SQL
            queries.
          </p>
        </div>
        <Button size="sm" onClick={() => setIsCreateOpen(true)}>
          <Plus className="mr-1.5 h-3.5 w-3.5" /> Add Dataset
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={datasets}
        isLoading={loading}
        searchColumn="name"
        searchPlaceholder="Filter datasets..."
      />

      {/* Dataset Preview Modal */}
      <Dialog open={isPreviewOpen} onOpenChange={setIsPreviewOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Dataset Preview</DialogTitle>
            <DialogDescription>
              Sample rows retrieved from the underlying query engine
            </DialogDescription>
          </DialogHeader>

          {previewing ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              Executing preview query...
            </div>
          ) : previewData ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-2xs font-mono text-muted-foreground bg-muted/40 p-2 rounded">
                <span>
                  Execution:{" "}
                  {previewData.execution_time
                    ? `${(previewData.execution_time * 1000).toFixed(1)} ms`
                    : "N/A"}
                </span>
                <span>Rows: {previewData.row_count}</span>
              </div>
              <div className="overflow-x-auto max-h-80 border border-border rounded">
                <table className="w-full text-xs text-left">
                  <thead className="bg-card border-b border-border sticky top-0">
                    <tr>
                      {previewData.columns.map((c) => (
                        <th
                          key={c.name}
                          className="p-2 font-mono text-2xs font-semibold text-muted-foreground border-r border-border last:border-r-0"
                        >
                          {c.name}{" "}
                          <span className="text-muted-foreground/60 font-normal">
                            ({c.type})
                          </span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {previewData.rows.map((row, i) => (
                      <tr key={i} className="hover:bg-muted/30">
                        {previewData.columns.map((c) => (
                          <td
                            key={c.name}
                            className="p-2 font-mono text-2xs border-r border-border last:border-r-0"
                          >
                            {String(row[c.name] ?? "")}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Create Dataset Modal */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="max-w-lg">
          <form onSubmit={handleCreate}>
            <DialogHeader>
              <DialogTitle>Create Dataset</DialogTitle>
              <DialogDescription>
                Register a new table or custom SQL query in the semantic layer.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3 py-4">
              <div className="space-y-1">
                <Label>Dataset Display Name</Label>
                <Input
                  placeholder="Orders Analytics Fact"
                  required
                  value={newDataset.name}
                  onChange={(e) =>
                    setNewDataset({ ...newDataset, name: e.target.value })
                  }
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label>Source Adapter</Label>
                  <Select
                    value={newDataset.source_type}
                    onValueChange={(val) =>
                      setNewDataset({ ...newDataset, source_type: val })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="snowflake">Snowflake</SelectItem>
                      <SelectItem value="postgres">PostgreSQL</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-1">
                  <Label>Object Classification</Label>
                  <Select
                    value={newDataset.object_type}
                    onValueChange={(val) =>
                      setNewDataset({ ...newDataset, object_type: val })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="table">
                        Physical Table / View
                      </SelectItem>
                      <SelectItem value="query">Custom SQL Query</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {newDataset.object_type === "table" ? (
                <div className="space-y-1">
                  <Label>Physical Table Name</Label>
                  <Input
                    placeholder="PUBLIC.SALES_FACT"
                    required
                    value={newDataset.object_name}
                    onChange={(e) =>
                      setNewDataset({
                        ...newDataset,
                        object_name: e.target.value,
                      })
                    }
                  />
                </div>
              ) : (
                <div className="space-y-1">
                  <Label>SQL Query String</Label>
                  <Textarea
                    placeholder="SELECT * FROM orders WHERE status = 'COMPLETED'"
                    className="font-mono text-xs"
                    required
                    value={newDataset.sql_query}
                    onChange={(e) =>
                      setNewDataset({
                        ...newDataset,
                        sql_query: e.target.value,
                      })
                    }
                  />
                </div>
              )}

              <div className="space-y-1">
                <Label>Description</Label>
                <Textarea
                  placeholder="Optional semantic description..."
                  value={newDataset.description}
                  onChange={(e) =>
                    setNewDataset({
                      ...newDataset,
                      description: e.target.value,
                    })
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
              <Button type="submit">Create Dataset</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
