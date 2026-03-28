"use client";
import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface KPIChipProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  trend?: "up" | "down" | "neutral";
  className?: string;
}

export function KPIChip({ label, value, icon, trend, className }: KPIChipProps) {
  return (
    <div className={cn("kpi-chip", className)}>
      {icon && <span className="text-text-muted">{icon}</span>}
      <span className="text-text-muted">{label}</span>
      <span
        className={cn(
          "font-mono font-semibold",
          trend === "up" ? "text-long" : trend === "down" ? "text-short" : "text-text-primary"
        )}
      >
        {value}
      </span>
    </div>
  );
}

interface KPICardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: "up" | "down" | "neutral";
  className?: string;
}

export function KPICard({ label, value, subtitle, icon, trend, className }: KPICardProps) {
  return (
    <div className={cn("terminal-panel p-3", className)}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] font-medium text-text-muted uppercase tracking-wider">{label}</span>
        {icon && <span className="text-text-muted">{icon}</span>}
      </div>
      <div
        className={cn(
          "text-lg font-bold font-mono",
          trend === "up" ? "text-long" : trend === "down" ? "text-short" : "text-text-primary"
        )}
      >
        {value}
      </div>
      {subtitle && <span className="text-[10px] text-text-muted">{subtitle}</span>}
    </div>
  );
}
