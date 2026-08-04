import React from "react";
import { type LucideIcon, LayoutGrid } from "lucide-react";
import { EmptyState } from "@/components/feedback/empty-state";

interface EmptyDashboardProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyDashboard({
  icon = LayoutGrid,
  title,
  description,
  action,
}: EmptyDashboardProps) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <EmptyState
        icon={icon}
        title={title}
        description={description}
        action={action}
      />
    </div>
  );
}
