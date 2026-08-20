"use client";

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { BarChart3, LineChart as LineChartIcon, AreaChart as AreaChartIcon, PieChart as PieChartIcon, Table as TableIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface ChartSpecProps {
  spec: {
    type: "line" | "bar" | "area" | "pie" | "table" | string;
    title: string;
    x_axis?: string | null;
    y_axis?: string | string[] | null;
    data: Record<string, unknown>[];
    series?: Record<string, unknown>[] | null;
    labels?: string[] | null;
    metadata?: Record<string, unknown>;
  };
  className?: string;
}

const DEFAULT_PALETTE = [
  "#3B82F6", // Blue
  "#10B981", // Emerald
  "#F59E0B", // Amber
  "#EF4444", // Red
  "#8B5CF6", // Purple
  "#EC4899", // Pink
  "#14B8A6", // Teal
  "#F97316", // Orange
];

export function NexusChart({ spec, className }: ChartSpecProps) {
  if (!spec || !spec.data || spec.data.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="text-sm">{spec?.title || "Chart Specification"}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="py-8 text-center text-xs text-muted-foreground">
            No data available for visualization.
          </div>
        </CardContent>
      </Card>
    );
  }

  const chartType = spec.type.toLowerCase().replace("_chart", "");
  const xAxisKey = spec.x_axis || Object.keys(spec.data[0])[0];
  
  let yAxisKeys: string[] = [];
  if (Array.isArray(spec.y_axis)) {
    yAxisKeys = spec.y_axis;
  } else if (spec.y_axis) {
    yAxisKeys = [spec.y_axis];
  } else {
    yAxisKeys = Object.keys(spec.data[0]).filter((k) => k !== xAxisKey);
  }

  const colors = (spec.metadata?.recommended_colors as string[]) || DEFAULT_PALETTE;

  return (
    <Card className={className}>
      <CardHeader className="py-3 px-4 flex flex-row items-center justify-between border-b border-border">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          {chartType === "line" && <LineChartIcon className="h-4 w-4 text-primary" />}
          {chartType === "bar" && <BarChart3 className="h-4 w-4 text-primary" />}
          {chartType === "area" && <AreaChartIcon className="h-4 w-4 text-primary" />}
          {chartType === "pie" && <PieChartIcon className="h-4 w-4 text-primary" />}
          {chartType === "table" && <TableIcon className="h-4 w-4 text-primary" />}
          {spec.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        {chartType === "table" ? (
          <div className="overflow-x-auto max-h-80">
            <table className="w-full text-xs text-left">
              <thead className="bg-muted/50 sticky top-0">
                <tr>
                  {Object.keys(spec.data[0]).map((col) => (
                    <th key={col} className="p-2 font-mono text-2xs font-semibold border-b">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {spec.data.map((row, i) => (
                  <tr key={i} className="hover:bg-muted/30">
                    {Object.keys(spec.data[0]).map((col) => (
                      <td key={col} className="p-2 font-mono text-2xs">
                        {row[col] !== null && row[col] !== undefined ? String(row[col]) : "null"}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              {chartType === "line" ? (
                <LineChart data={spec.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#232329" />
                  <XAxis dataKey={xAxisKey} stroke="#a1a1aa" fontSize={11} />
                  <YAxis stroke="#a1a1aa" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#111113",
                      borderColor: "#232329",
                      color: "#fafafa",
                      fontSize: 12,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  {yAxisKeys.map((yKey, idx) => (
                    <Line
                      key={yKey}
                      type="monotone"
                      dataKey={yKey}
                      stroke={colors[idx % colors.length]}
                      strokeWidth={2}
                      dot={{ fill: colors[idx % colors.length] }}
                    />
                  ))}
                </LineChart>
              ) : chartType === "area" ? (
                <AreaChart data={spec.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#232329" />
                  <XAxis dataKey={xAxisKey} stroke="#a1a1aa" fontSize={11} />
                  <YAxis stroke="#a1a1aa" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#111113",
                      borderColor: "#232329",
                      color: "#fafafa",
                      fontSize: 12,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  {yAxisKeys.map((yKey, idx) => (
                    <Area
                      key={yKey}
                      type="monotone"
                      dataKey={yKey}
                      stroke={colors[idx % colors.length]}
                      fill={colors[idx % colors.length]}
                      fillOpacity={0.2}
                    />
                  ))}
                </AreaChart>
              ) : chartType === "pie" ? (
                <PieChart>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#111113",
                      borderColor: "#232329",
                      color: "#fafafa",
                      fontSize: 12,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Pie
                    data={spec.data}
                    dataKey={yAxisKeys[0] || Object.keys(spec.data[0])[1]}
                    nameKey={xAxisKey}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label
                  >
                    {spec.data.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                    ))}
                  </Pie>
                </PieChart>
              ) : (
                /* Default fallback: Bar Chart */
                <BarChart data={spec.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#232329" />
                  <XAxis dataKey={xAxisKey} stroke="#a1a1aa" fontSize={11} />
                  <YAxis stroke="#a1a1aa" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#111113",
                      borderColor: "#232329",
                      color: "#fafafa",
                      fontSize: 12,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  {yAxisKeys.map((yKey, idx) => (
                    <Bar
                      key={yKey}
                      dataKey={yKey}
                      fill={colors[idx % colors.length]}
                      radius={[4, 4, 0, 0]}
                    />
                  ))}
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
