"use client";

import React, { useState } from "react";
import { Plus } from "lucide-react";
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
import { NexusChart } from "@/components/chart/nexus-chart";

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

  const spec = {
    type: chartType,
    title:
      yAxis === "revenue"
        ? "Regional Revenue Distribution ($)"
        : "Order Volume by Region",
    x_axis: xAxis,
    y_axis: yAxis,
    data: SAMPLE_DATA,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            Chart Generator
          </h1>
          <p className="text-xs text-muted-foreground">
            Build interactive bar, line, area, pie, and table visual models
            backed by typed Universal Chart Engine specifications.
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
                  <SelectItem value="pie">Pie Chart</SelectItem>
                  <SelectItem value="table">Table</SelectItem>
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
        <div className="lg:col-span-3">
          <NexusChart spec={spec} />
        </div>
      </div>
    </div>
  );
}
