"use client";

import React, { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { NexusChart } from "@/components/chart/nexus-chart";
import { apiClient } from "@/lib/api-client";

interface DatasetColumn {
  name: string;
  type: string;
}

interface Dataset {
  id: string;
  name: string;
  schema_metadata?: { columns?: DatasetColumn[] };
}

export default function ChartsPage() {
  const [chartType, setChartType] = useState("bar");
  const [xAxis, setXAxis] = useState("");
  const [yAxis, setYAxis] = useState("");
  const [selectedDataset, setSelectedDataset] = useState("");
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [columns, setColumns] = useState<DatasetColumn[]>([]);
  const [previewData, setPreviewData] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [previewLoading, setPreviewLoading] = useState(false);

  // Fetch datasets on mount
  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const data = await apiClient.get<{ items: Dataset[] }>("/datasets?limit=20");
        const items = data?.items || (Array.isArray(data) ? data : []);
        setDatasets(items);
        if (items.length > 0) {
          setSelectedDataset(items[0].id);
          setColumns(items[0].schema_metadata?.columns || []);
          if (items[0].schema_metadata?.columns?.length) {
            const cols = items[0].schema_metadata.columns;
            setXAxis(cols[0]?.name || "");
            setYAxis(cols.length > 1 ? cols[1]?.name : cols[0]?.name || "");
          }
        }
      } catch {
        // silent
      } finally {
        setLoading(false);
      }
    };
    fetchDatasets();
  }, []);

  // Fetch preview data when dataset changes
  useEffect(() => {
    if (!selectedDataset) return;
    const fetchPreview = async () => {
      setPreviewLoading(true);
      try {
        const data = await apiClient.get<Record<string, unknown>[]>(
          `/query/preview-dataset/${selectedDataset}`,
        );
        setPreviewData(Array.isArray(data) ? data.slice(0, 20) : []);
        // Update columns from first row keys
        if (data && Array.isArray(data) && data.length > 0) {
          const cols = Object.keys(data[0]).map((k) => ({
            name: k,
            type: typeof data[0][k] === "number" ? "number" : "string",
          }));
          setColumns(cols);
          if (cols.length > 0) setXAxis(cols[0].name);
          if (cols.length > 1) setYAxis(cols[1].name);
        }
      } catch {
        setPreviewData([]);
      } finally {
        setPreviewLoading(false);
      }
    };
    fetchPreview();
  }, [selectedDataset]);

  const currentDataset = datasets.find((d) => d.id === selectedDataset);
  const numericColumns = columns.filter(
    (c) => c.type === "number" || c.type === "integer" || c.type === "float",
  );
  const spec = {
    type: chartType,
    title: currentDataset
      ? `${currentDataset.name} — ${yAxis || "Metric"} by ${xAxis || "Category"}`
      : "Select a dataset",
    x_axis: xAxis,
    y_axis: yAxis,
    data: previewData.length > 0
      ? previewData
      : [{ [xAxis || "label"]: "No data", [yAxis || "value"]: 0 }],
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            Chart Generator
          </h1>
          <p className="text-xs text-muted-foreground">
            Build interactive visualizations backed by real dataset data.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Loading datasets…
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-4">
          {/* Controls */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="text-sm">Chart Configuration</CardTitle>
              <CardDescription>Select dataset and dimensions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1">
                <Label>Dataset</Label>
                <Select value={selectedDataset} onValueChange={setSelectedDataset}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select dataset" />
                  </SelectTrigger>
                  <SelectContent>
                    {datasets.map((ds) => (
                      <SelectItem key={ds.id} value={ds.id}>
                        {ds.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <Label>Chart Type</Label>
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
                    {columns.map((c) => (
                      <SelectItem key={c.name} value={c.name}>
                        {c.name} <span className="text-muted-foreground ml-1 text-2xs">({c.type})</span>
                      </SelectItem>
                    ))}
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
                    {(numericColumns.length > 0 ? numericColumns : columns).map((c) => (
                      <SelectItem key={c.name} value={c.name}>
                        {c.name} <span className="text-muted-foreground ml-1 text-2xs">({c.type})</span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {previewLoading && (
                <div className="flex items-center text-xs text-muted-foreground">
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" /> Loading preview…
                </div>
              )}

              {previewData.length > 0 && (
                <p className="text-2xs text-muted-foreground">
                  {previewData.length} rows previewed
                </p>
              )}
            </CardContent>
          </Card>

          {/* Chart Visualization */}
          <div className="lg:col-span-3">
            <NexusChart spec={spec} />
          </div>
        </div>
      )}
    </div>
  );
}
