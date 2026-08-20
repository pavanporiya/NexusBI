import React from "react";
import { type LucideIcon, Inbox } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface EmptyStateProps {
  icon?: LucideIcon;
  illustration?: React.ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: LucideIcon;
  };
  className?: string;
}

export function EmptyState({
  icon: Icon = Inbox,
  illustration,
  title,
  description,
  action,
  className = "",
}: EmptyStateProps) {
  const ActionIcon = action?.icon;

  return (
    <div
      className={`flex flex-col items-center justify-center text-center p-6 sm:p-10 ${className}`}
    >
      {illustration ? (
        <div className="mb-6 flex items-center justify-center">
          {illustration}
        </div>
      ) : (
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-muted/60 border border-border/50 shadow-inner">
          <Icon className="h-7 w-7 text-muted-foreground" />
        </div>
      )}
      <h3 className="mt-2 text-lg sm:text-xl font-semibold tracking-tight text-foreground">
        {title}
      </h3>
      <p className="mt-2 max-w-md text-sm text-muted-foreground leading-relaxed text-balance">
        {description}
      </p>
      {action && (
        <Button
          className="mt-6 font-medium shadow-sm transition-all hover:shadow-md cursor-pointer"
          size="lg"
          onClick={action.onClick}
        >
          {ActionIcon && <ActionIcon className="mr-2 h-4 w-4" />}
          {action.label}
        </Button>
      )}
    </div>
  );
}
