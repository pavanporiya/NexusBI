"use client";

import React, { useState } from "react";
import { BarChart3, LineChart, AreaChart, Plus } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart as ReLineChart,
  Line,
  AreaChart as ReAreaChart,
  Area,
} from "recharts";

const SAMPLE_DATA = [
  { region: "North America", revenue: 45200, orders: 1240 },
  { region: "Europe Central", revenue: 38900, orders: 980 },
  { region: "Asia Pacific", revenue: 61200, orders: 2150 },
  { region: "Latin America", revenue: 19400, orders: 410 },
  { region: "Middle East", revenue: 28100, orders: 630 },
];

export default function ChartsPage() {
  const [chartType, setChartType] = useState("bar");
  const [xAxis, setXAxis] = useState("region");
  const [yAxis, setYAxis] = useState("revenue");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            Chart Generator
          </h1>
          <p className="text-xs text-muted-foreground">
            Build interactive bar, line, and area charts backed by typed
            Universal Chart Engine strategies.
          </p>
        </div>
        <Button size="sm">
          <Plus className="mr-1.5 h-3.5 w-3.5" /> Save Chart Model
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Controls */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm">Chart Configuration</CardTitle>
            <CardDescription>
              Select metric dimension parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <Label>Chart Strategy</Label>
              <Select value={chartType} onValueChange={setChartType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bar">Bar Chart</SelectItem>
                  <SelectItem value="line">Line Chart</SelectItem>
                  <SelectItem value="area">Area Chart</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1">
              <Label>X-Axis (Category)</Label>
              <Select value={xAxis} onValueChange={setXAxis}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="region">Region</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1">
              <Label>Y-Axis (Metric)</Label>
              <Select value={yAxis} onValueChange={setYAxis}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="revenue">Revenue ($)</SelectItem>
                  <SelectItem value="orders">Order Count</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Chart Visualization */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              {chartType === "bar" && (
                <BarChart3 className="h-4 w-4 text-primary" />
              )}
              {chartType === "line" && (
                <LineChart className="h-4 w-4 text-primary" />
              )}
              {chartType === "area" && (
                <AreaChart className="h-4 w-4 text-primary" />
              )}
              {yAxis === "revenue"
                ? "Regional Revenue Distribution ($)"
                : "Order Volume by Region"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80 w-full pt-4">
              <ResponsiveContainer width="100%" height="100%">
                {chartType === "bar" ? (
                  <BarChart data={SAMPLE_DATA}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#232329" />
                    <XAxis dataKey={xAxis} stroke="#a1a1aa" fontSize={11} />
                    <YAxis stroke="#a1a1aa" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#111113",
                        borderColor: "#232329",
                        color: "#fafafa",
                      }}
                    />
                    <Bar dataKey={yAxis} fill="#3B82F6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                ) : chartType === "line" ? (
                  <ReLineChart data={SAMPLE_DATA}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#232329" />
                    <XAxis dataKey={xAxis} stroke="#a1a1aa" fontSize={11} />
                    <YAxis stroke="#a1a1aa" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#111113",
                        borderColor: "#232329",
                        color: "#fafafa",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey={yAxis}
                      stroke="#3B82F6"
                      strokeWidth={2}
                      dot={{ fill: "#3B82F6" }}
                    />
                  </ReLineChart>
                ) : (
                  <ReAreaChart data={SAMPLE_DATA}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#232329" />
                    <XAxis dataKey={xAxis} stroke="#a1a1aa" fontSize={11} />
                    <YAxis stroke="#a1a1aa" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#111113",
                        borderColor: "#232329",
                        color: "#fafafa",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey={yAxis}
                      stroke="#3B82F6"
                      fill="#3B82F6"
                      fillOpacity={0.2}
                    />
                  </ReAreaChart>
                )}
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
