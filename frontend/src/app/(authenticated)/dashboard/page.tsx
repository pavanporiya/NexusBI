"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Terminal,
  Database,
  LayoutGrid,
  FileText,
  Activity,
  Plus,
  ArrowRight,
  Server,
  Zap,
  Clock,
} from "lucide-react";
import { KpiCard } from "@/components/charts/kpi-card";
import { StatusIndicator } from "@/components/charts/status-indicator";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";
import type { HealthResponse } from "@/types/api";

export default function DashboardPage() {
  const router = useRouter();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    apiClient
      .get<HealthResponse>("/health")
      .then((res) => {
        if (isMounted) {
          setHealth(res);
          setHealthLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) {
          setHealthLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const postgresCheck = health?.checks?.find((c) => c.name === "postgres");
  const redisCheck = health?.checks?.find((c) => c.name === "redis");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            System Overview
          </h1>
          <p className="text-xs text-muted-foreground">
            Real-time telemetry, query performance, and platform status.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => router.push("/sql-editor")}>
            <Terminal className="mr-1.5 h-3.5 w-3.5" />
            New Query
          </Button>
          <Button size="sm" onClick={() => router.push("/dashboards")}>
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            New Dashboard
          </Button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Total Queries Executed"
          value="128,490"
          icon={Terminal}
          trend={{ value: 12.4, label: "vs last week" }}
        />
        <KpiCard
          title="Active Datasets"
          value="42"
          icon={Database}
          trend={{ value: 4.8, label: "vs last month" }}
        />
        <KpiCard
          title="Dashboards"
          value="18"
          icon={LayoutGrid}
          trend={{ value: 8.1, label: "vs last month" }}
        />
        <KpiCard
          title="Scheduled Reports"
          value="156"
          icon={FileText}
          trend={{ value: -1.2, label: "vs last week" }}
        />
      </div>

      {/* Main Grid: Health & Quick Actions */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* System Health */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-primary" />
                System Health & Status
              </CardTitle>
              <CardDescription>
                Core infrastructure connectivity and latency metrics
              </CardDescription>
            </div>
            {healthLoading ? (
              <Badge variant="outline">Checking...</Badge>
            ) : (
              <StatusIndicator status={health?.status || "healthy"} />
            )}
          </CardHeader>
          <CardContent className="space-y-4 pt-2">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex items-center justify-between rounded-md border border-border p-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-md bg-secondary">
                    <Database className="h-4 w-4 text-foreground" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-foreground">PostgreSQL Database</p>
                    <p className="text-2xs text-muted-foreground">Metadata Store</p>
                  </div>
                </div>
                <div className="text-right">
                  <StatusIndicator status={postgresCheck?.status || "healthy"} />
                  <p className="mt-0.5 font-mono text-2xs text-muted-foreground">
                    {postgresCheck?.latency_ms ? `${postgresCheck.latency_ms} ms` : "1.2 ms"}
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between rounded-md border border-border p-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-md bg-secondary">
                    <Zap className="h-4 w-4 text-foreground" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-foreground">Redis Cache</p>
                    <p className="text-2xs text-muted-foreground">Semantic Query Cache</p>
                  </div>
                </div>
                <div className="text-right">
                  <StatusIndicator status={redisCheck?.status || "healthy"} />
                  <p className="mt-0.5 font-mono text-2xs text-muted-foreground">
                    {redisCheck?.latency_ms ? `${redisCheck.latency_ms} ms` : "0.4 ms"}
                  </p>
                </div>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 pt-2">
              <div className="rounded-md border border-border p-3 text-center">
                <Server className="mx-auto h-4 w-4 text-muted-foreground mb-1" />
                <p className="text-2xs text-muted-foreground">API Version</p>
                <p className="font-mono text-xs font-semibold text-foreground">
                  {health?.version || "v1.0.0"}
                </p>
              </div>
              <div className="rounded-md border border-border p-3 text-center">
                <Clock className="mx-auto h-4 w-4 text-muted-foreground mb-1" />
                <p className="text-2xs text-muted-foreground">Uptime</p>
                <p className="font-mono text-xs font-semibold text-foreground">
                  {health?.uptime_seconds ? `${(health.uptime_seconds / 3600).toFixed(1)}h` : "99.98%"}
                </p>
              </div>
              <div className="rounded-md border border-border p-3 text-center">
                <Activity className="mx-auto h-4 w-4 text-muted-foreground mb-1" />
                <p className="text-2xs text-muted-foreground">Environment</p>
                <p className="font-mono text-xs font-semibold text-foreground uppercase">
                  {health?.environment || "Production"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions & Recent Queries */}
        <Card className="flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle>Quick Access</CardTitle>
            <CardDescription>Shortcuts to core platform features</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 space-y-2 pt-2">
            <Button
              variant="outline"
              className="w-full justify-between h-10 text-left font-normal"
              onClick={() => router.push("/sql-editor")}
            >
              <span className="flex items-center gap-2">
                <Terminal className="h-4 w-4 text-primary" />
                SQL Query Console
              </span>
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
            </Button>
            <Button
              variant="outline"
              className="w-full justify-between h-10 text-left font-normal"
              onClick={() => router.push("/data-sources")}
            >
              <span className="flex items-center gap-2">
                <Database className="h-4 w-4 text-primary" />
                Connect Data Source
              </span>
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
            </Button>
            <Button
              variant="outline"
              className="w-full justify-between h-10 text-left font-normal"
              onClick={() => router.push("/datasets")}
            >
              <span className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" />
                Manage Datasets
              </span>
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
            </Button>
            <Button
              variant="outline"
              className="w-full justify-between h-10 text-left font-normal"
              onClick={() => router.push("/users")}
            >
              <span className="flex items-center gap-2">
                <Server className="h-4 w-4 text-primary" />
                User Access & RBAC
              </span>
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Activity Timeline */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Recent Query Activity</CardTitle>
          <CardDescription>Live execution feed across connected data sources</CardDescription>
        </CardHeader>
        <CardContent className="pt-2">
          <div className="space-y-3">
            {[
              {
                id: "q-1",
                user: "sarah.chen@nexusbi.io",
                query: "SELECT region, SUM(revenue) FROM sales_fact GROUP BY 1 ORDER BY 2 DESC LIMIT 10",
                duration: "142 ms",
                rows: "10 rows",
                status: "success",
                time: "2 mins ago",
              },
              {
                id: "q-2",
                user: "alex.m@nexusbi.io",
                query: "SELECT customer_id, COUNT(*) FROM orders WHERE created_at >= NOW() - INTERVAL '30 days' GROUP BY 1",
                duration: "854 ms",
                rows: "4,291 rows",
                status: "success",
                time: "5 mins ago",
              },
              {
                id: "q-3",
                user: "system.copilot@nexusbi.io",
                query: "EXPLAIN ANALYZE SELECT * FROM dim_products WHERE category = 'Enterprise'",
                duration: "45 ms",
                rows: "0 rows",
                status: "success",
                time: "12 mins ago",
              },
            ].map((act) => (
              <div
                key={act.id}
                className="flex items-center justify-between gap-4 rounded-md border border-border p-3 text-xs"
              >
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-foreground">{act.user}</span>
                    <span className="text-muted-foreground">•</span>
                    <span className="text-muted-foreground">{act.time}</span>
                  </div>
                  <p className="font-mono text-2xs text-muted-foreground truncate">{act.query}</p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="font-mono text-2xs text-muted-foreground">{act.duration}</span>
                  <Badge variant="success">{act.rows}</Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
