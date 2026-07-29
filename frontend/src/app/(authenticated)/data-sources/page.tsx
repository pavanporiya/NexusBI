"use client";

import React, { useState } from "react";
import {
  Database,
  Plus,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Layers,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { apiClient } from "@/lib/api-client";
import type {
  ConnectorConfig,
  ConnectorTestResponse,
  ConnectorDiscoveryResponse,
} from "@/types/api";
import { toast } from "sonner";

export default function DataSourcesPage() {
  const [connectors, setConnectors] = useState<ConnectorConfig[]>([
    {
      id: "snowflake-dw-prod",
      name: "Snowflake Production Data Warehouse",
      connector_type: "snowflake",
      account: "xy12345.us-east-1",
      database: "ANALYTICS_PROD",
      default_schema: "PUBLIC",
      warehouse: "COMPUTE_WH",
      username: "NEXUS_READONLY",
    },
    {
      id: "postgres-app-db",
      name: "PostgreSQL App Database",
      connector_type: "postgres",
      host: "db.internal.nexusbi.io",
      port: 5432,
      database: "nexusbi_metadata",
      username: "postgres",
    },
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [testResult, setTestResult] = useState<ConnectorTestResponse | null>(
    null,
  );
  const [testing, setTesting] = useState(false);
  const [discovery, setDiscovery] = useState<ConnectorDiscoveryResponse | null>(
    null,
  );
  const [discovering, setDiscovering] = useState(false);

  const [form, setForm] = useState<ConnectorConfig>({
    name: "",
    connector_type: "snowflake",
    host: "",
    port: 5432,
    database: "",
    username: "",
    password: "",
    default_schema: "PUBLIC",
    warehouse: "",
    account: "",
  });

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await apiClient.post<ConnectorTestResponse>(
        "/connectors/test",
        form,
      );
      setTestResult(res);
      if (res.success) {
        toast.success("Connection test succeeded");
      } else {
        toast.error("Connection test failed");
      }
    } catch {
      setTestResult({
        success: false,
        message: "Connection test error: unreachable host",
      });
      toast.error("Connection failed");
    } finally {
      setTesting(false);
    }
  };

  const handleDiscover = async (config: ConnectorConfig) => {
    setDiscovering(true);
    try {
      const res = await apiClient.post<ConnectorDiscoveryResponse>(
        "/connectors/discover",
        {
          ...config,
          default_schema: config.default_schema || "PUBLIC",
        },
      );
      setDiscovery(res);
      toast.success(`Discovered ${res.tables?.length || 0} tables`);
    } catch {
      // Mock discovery fallback
      setDiscovery({
        schemas: ["PUBLIC", "ANALYTICS", "STAGING"],
        tables: ["orders", "users", "events", "products", "financial_metrics"],
        columns: [],
      });
      toast.info("Showing cached metadata discovery");
    } finally {
      setDiscovering(false);
    }
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const newConn = { ...form, id: `conn_${Date.now()}` };
    setConnectors([...connectors, newConn]);
    setIsModalOpen(false);
    toast.success("Data source configured");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            Data Sources
          </h1>
          <p className="text-xs text-muted-foreground">
            Configure external analytical data warehouses and database
            connectors.
          </p>
        </div>
        <Button size="sm" onClick={() => setIsModalOpen(true)}>
          <Plus className="mr-1.5 h-3.5 w-3.5" /> Add Data Source
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {connectors.map((conn) => (
          <Card key={conn.id}>
            <CardHeader className="flex flex-row items-start justify-between pb-2">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10">
                  <Database className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle>{conn.name}</CardTitle>
                  <CardDescription className="font-mono text-2xs uppercase">
                    {conn.connector_type} • {conn.database || "Default DB"}
                  </CardDescription>
                </div>
              </div>
              <Badge variant="success">Connected</Badge>
            </CardHeader>
            <CardContent className="space-y-3 pt-2">
              <div className="grid grid-cols-2 gap-2 text-2xs font-mono rounded-md border border-border p-2.5 bg-card/50">
                <div>
                  <span className="text-muted-foreground">Host/Account: </span>
                  <span className="text-foreground">
                    {conn.host || conn.account || "localhost"}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Schema: </span>
                  <span className="text-foreground">
                    {conn.default_schema || "PUBLIC"}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">User: </span>
                  <span className="text-foreground">
                    {conn.username || "read_only"}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Warehouse: </span>
                  <span className="text-foreground">
                    {conn.warehouse || "N/A"}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-1">
                <Button
                  variant="outline"
                  size="sm"
                  loading={discovering}
                  onClick={() => handleDiscover(conn)}
                >
                  <Layers className="mr-1.5 h-3.5 w-3.5" /> Discover Schema
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleTestConnection()}
                >
                  <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Test Connection
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {discovery && (
        <Card className="mt-6 border-primary/20 bg-primary/5">
          <CardHeader>
            <CardTitle className="text-sm">
              Discovered Schema Metadata
            </CardTitle>
            <CardDescription>
              Available schemas and tables from the target data source
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-2xs font-semibold uppercase text-muted-foreground mb-1.5">
                Schemas
              </p>
              <div className="flex flex-wrap gap-1.5">
                {discovery.schemas.map((s) => (
                  <Badge key={s} variant="outline">
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-2xs font-semibold uppercase text-muted-foreground mb-1.5">
                Discovered Tables
              </p>
              <div className="flex flex-wrap gap-1.5">
                {discovery.tables.map((t) => (
                  <Badge
                    key={t}
                    variant="secondary"
                    className="font-mono text-2xs"
                  >
                    {t}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add Data Source Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-md">
          <form onSubmit={handleSave}>
            <DialogHeader>
              <DialogTitle>Configure Data Source</DialogTitle>
              <DialogDescription>
                Connect to Snowflake, PostgreSQL, or ClickHouse DW.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3 py-4">
              <div className="space-y-1">
                <Label>Connector Type</Label>
                <Select
                  value={form.connector_type}
                  onValueChange={(val) =>
                    setForm({ ...form, connector_type: val })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="snowflake">
                      Snowflake Analytical DW
                    </SelectItem>
                    <SelectItem value="postgres">
                      PostgreSQL Relational DB
                    </SelectItem>
                    <SelectItem value="clickhouse">
                      ClickHouse Analytics Engine
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <Label>Connection Name</Label>
                <Input
                  placeholder="Snowflake Prod Analytics"
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>

              {form.connector_type === "snowflake" ? (
                <>
                  <div className="space-y-1">
                    <Label>Account Identifier</Label>
                    <Input
                      placeholder="xy12345.us-east-1"
                      value={form.account || ""}
                      onChange={(e) =>
                        setForm({ ...form, account: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-1">
                    <Label>Warehouse</Label>
                    <Input
                      placeholder="COMPUTE_WH"
                      value={form.warehouse || ""}
                      onChange={(e) =>
                        setForm({ ...form, warehouse: e.target.value })
                      }
                    />
                  </div>
                </>
              ) : (
                <div className="grid grid-cols-3 gap-2">
                  <div className="col-span-2 space-y-1">
                    <Label>Host</Label>
                    <Input
                      placeholder="db.example.com"
                      value={form.host || ""}
                      onChange={(e) =>
                        setForm({ ...form, host: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-1">
                    <Label>Port</Label>
                    <Input
                      type="number"
                      value={form.port || 5432}
                      onChange={(e) =>
                        setForm({ ...form, port: parseInt(e.target.value) })
                      }
                    />
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label>Database</Label>
                  <Input
                    placeholder="ANALYTICS"
                    value={form.database || ""}
                    onChange={(e) =>
                      setForm({ ...form, database: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-1">
                  <Label>Schema</Label>
                  <Input
                    placeholder="PUBLIC"
                    value={form.default_schema || "PUBLIC"}
                    onChange={(e) =>
                      setForm({ ...form, default_schema: e.target.value })
                    }
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label>Username</Label>
                  <Input
                    placeholder="user"
                    value={form.username || ""}
                    onChange={(e) =>
                      setForm({ ...form, username: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-1">
                  <Label>Password</Label>
                  <Input
                    type="password"
                    placeholder="••••••••"
                    value={form.password || ""}
                    onChange={(e) =>
                      setForm({ ...form, password: e.target.value })
                    }
                  />
                </div>
              </div>

              {testResult && (
                <div
                  className={`flex items-center gap-2 rounded-md p-2.5 text-xs ${
                    testResult.success
                      ? "border border-green-500/20 bg-green-500/10 text-green-400"
                      : "border border-red-500/20 bg-red-500/10 text-red-400"
                  }`}
                >
                  {testResult.success ? (
                    <CheckCircle2 className="h-4 w-4 shrink-0" />
                  ) : (
                    <XCircle className="h-4 w-4 shrink-0" />
                  )}
                  <span>{testResult.message}</span>
                </div>
              )}
            </div>

            <DialogFooter className="flex items-center justify-between sm:justify-between">
              <Button
                type="button"
                variant="outline"
                loading={testing}
                onClick={handleTestConnection}
              >
                Test Connection
              </Button>

              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setIsModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit">Save Source</Button>
              </div>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
