"use client";
import { cn } from "@/lib/utils";

type Direction = "LONG" | "SHORT";

interface BadgeProps {
  className?: string;
}

export function DirectionBadge({ direction, className }: BadgeProps & { direction: Direction }) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider",
        direction === "LONG" ? "bg-long/15 text-long" : "bg-short/15 text-short",
        className
      )}
    >
      {direction}
    </span>
  );
}

export function StatusBadge({
  status,
  className,
}: BadgeProps & {
  status: "active" | "tp1_hit" | "tp2_hit" | "tp3_hit" | "sl_hit" | "expired" | "invalidated";
}) {
  const styles = {
    active: "bg-blue/15 text-blue",
    tp1_hit: "bg-long/15 text-long",
    tp2_hit: "bg-long/15 text-long",
    tp3_hit: "bg-long/15 text-long",
    sl_hit: "bg-short/15 text-short",
    expired: "bg-surface-2 text-text-muted",
    invalidated: "bg-surface-2 text-text-muted",
  } as const;

  return (
    <span
      className={cn(
        "inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider",
        styles[status],
        className
      )}
    >
      {status.replace("_", " ")}
    </span>
  );
}

export function ConfidenceBadge({ value, className }: BadgeProps & { value: number }) {
  const color = value >= 75 ? "text-long" : value >= 55 ? "text-gold" : "text-short";
  return <span className={cn("font-mono text-[10px] font-bold", color, className)}>{value}%</span>;
}
