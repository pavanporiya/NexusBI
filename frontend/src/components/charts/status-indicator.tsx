import React from "react";
import { cn } from "@/lib/utils";
import type { HealthStatus } from "@/types/api";

interface StatusIndicatorProps {
  status: HealthStatus;
  label?: string;
  showLabel?: boolean;
  size?: "sm" | "md";
}

const STATUS_CONFIG: Record<
  HealthStatus,
  { color: string; bg: string; text: string }
> = {
  healthy: { color: "bg-green-400", bg: "bg-green-400/20", text: "text-green-400" },
  degraded: { color: "bg-yellow-400", bg: "bg-yellow-400/20", text: "text-yellow-400" },
  unhealthy: { color: "bg-red-400", bg: "bg-red-400/20", text: "text-red-400" },
  unavailable: { color: "bg-zinc-500", bg: "bg-zinc-500/20", text: "text-zinc-500" },
};

export function StatusIndicator({
  status,
  label,
  showLabel = true,
  size = "sm",
}: StatusIndicatorProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.unavailable;
  const dotSize = size === "sm" ? "h-2 w-2" : "h-2.5 w-2.5";

  return (
    <div className="flex items-center gap-2">
      <span className={cn("relative flex", dotSize)}>
        {status === "healthy" && (
          <span
            className={cn(
              "absolute inline-flex h-full w-full animate-ping rounded-full opacity-75",
              config.color
            )}
          />
        )}
        <span className={cn("relative inline-flex rounded-full", dotSize, config.color)} />
      </span>
      {showLabel && (
        <span className={cn("text-xs font-medium capitalize", config.text)}>
          {label || status}
        </span>
      )}
    </div>
  );
}
