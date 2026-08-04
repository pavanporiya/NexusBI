"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { EmptyDashboard } from "@/components/dashboard/empty-dashboard";

export default function DashboardPage() {
  const router = useRouter();

  return (
    <EmptyDashboard
      title="Welcome to NexusBI"
      description="Your analytics workspace is empty. Create your first organization to get started."
      action={{
        label: "Create Organization",
        onClick: () => router.push("/organizations"),
      }}
    />
  );
}
