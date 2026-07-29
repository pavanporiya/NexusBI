import React from "react";
import { type LucideIcon, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";

interface KpiCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon: LucideIcon;
  trend?: {
    value: number;
    label: string;
  };
  className?: string;
}

export function KpiCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  className,
}: KpiCardProps) {
  const isPositive = trend && trend.value >= 0;

  return (
    <Card className={cn("p-4", className)}>
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground">{title}</p>
          <p className="text-2xl font-semibold tracking-tight text-foreground">
            {value}
          </p>
          {trend && (
            <div className="flex items-center gap-1">
              {isPositive ? (
                <TrendingUp className="h-3 w-3 text-green-400" />
              ) : (
                <TrendingDown className="h-3 w-3 text-red-400" />
              )}
              <span
                className={cn(
                  "text-2xs font-medium",
                  isPositive ? "text-green-400" : "text-red-400"
                )}
              >
                {isPositive ? "+" : ""}
                {trend.value}%
              </span>
              <span className="text-2xs text-muted-foreground">
                {trend.label}
              </span>
            </div>
          )}
          {description && (
            <p className="text-2xs text-muted-foreground">{description}</p>
          )}
        </div>
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10">
          <Icon className="h-4 w-4 text-primary" />
        </div>
      </div>
    </Card>
  );
}
