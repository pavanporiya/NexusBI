import React from "react";
import { Building2, Layers, Database, BarChart3, ShieldCheck } from "lucide-react";

export function OrgEmptyIllustration() {
  return (
    <div
      aria-hidden="true"
      className="relative flex items-center justify-center w-64 h-56 sm:w-72 sm:h-64 select-none pointer-events-none"
    >
      {/* Outer ambient glow circles */}
      <div className="absolute inset-0 bg-gradient-to-tr from-primary/30 via-primary/10 to-transparent rounded-full blur-3xl opacity-60 animate-pulse" />
      <div className="absolute -inset-4 bg-primary/10 rounded-full blur-2xl opacity-40" />

      {/* Decorative dashed boundary */}
      <div className="absolute w-52 h-52 sm:w-60 sm:h-60 rounded-full border border-dashed border-primary/20 animate-[spin_60s_linear_infinite]" />

      {/* Central Enterprise Card */}
      <div className="relative z-10 flex flex-col items-center justify-center p-6 rounded-2xl bg-card/80 border border-primary/30 shadow-2xl backdrop-blur-md transition-all duration-300 hover:scale-105">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/15 border border-primary/40 shadow-inner">
          <Building2 className="h-9 w-9 text-primary drop-shadow-[0_0_12px_rgba(59,130,246,0.5)]" />
        </div>
        <div className="mt-3 flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-2xs font-semibold tracking-wider uppercase">
          <ShieldCheck className="w-3 h-3" /> Enterprise Hub
        </div>
      </div>

      {/* Floating Node Badges around the central card */}
      {/* Top Left: Workspaces */}
      <div className="absolute top-2 left-2 z-20 flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-card/90 border border-border/80 shadow-lg backdrop-blur-sm transform -rotate-3 transition-transform duration-300 hover:rotate-0">
        <div className="p-1 rounded-md bg-secondary text-primary">
          <Layers className="h-3.5 w-3.5" />
        </div>
        <span className="text-2xs font-medium text-foreground">Workspaces</span>
      </div>

      {/* Top Right: Datasets */}
      <div className="absolute top-4 right-2 z-20 flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-card/90 border border-border/80 shadow-lg backdrop-blur-sm transform rotate-6 transition-transform duration-300 hover:rotate-0">
        <div className="p-1 rounded-md bg-secondary text-emerald-400">
          <Database className="h-3.5 w-3.5" />
        </div>
        <span className="text-2xs font-medium text-foreground">Datasets</span>
      </div>

      {/* Bottom Right: Dashboards & Reports */}
      <div className="absolute bottom-4 right-4 z-20 flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-card/90 border border-border/80 shadow-lg backdrop-blur-sm transform -rotate-3 transition-transform duration-300 hover:rotate-0">
        <div className="p-1 rounded-md bg-secondary text-amber-400">
          <BarChart3 className="h-3.5 w-3.5" />
        </div>
        <span className="text-2xs font-medium text-foreground">Dashboards</span>
      </div>

      {/* Bottom Left: Security / Compliance */}
      <div className="absolute bottom-2 left-4 z-20 flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-card/90 border border-border/80 shadow-lg backdrop-blur-sm transform rotate-3 transition-transform duration-300 hover:rotate-0">
        <div className="p-1 rounded-md bg-secondary text-indigo-400">
          <ShieldCheck className="h-3.5 w-3.5" />
        </div>
        <span className="text-2xs font-medium text-foreground">Multi-tenant</span>
      </div>
    </div>
  );
}
