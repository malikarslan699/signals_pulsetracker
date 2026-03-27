import { cn } from "@/lib/utils";
import { ReactNode } from "react";

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
      <span className={cn(
        "font-semibold",
        trend === "up" ? "text-long" : trend === "down" ? "text-short" : "text-text-primary"
      )}>
        {value}
      </span>
    </div>
  );
}
