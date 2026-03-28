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
  status:
    | "CREATED"
    | "ARMED"
    | "FILLED"
    | "TP1_REACHED"
    | "TP2_REACHED"
    | "STOPPED"
    | "EXPIRED"
    | "INVALIDATED";
}) {
  const styles = {
    CREATED: "bg-blue/15 text-blue",
    ARMED: "bg-gold/15 text-gold",
    FILLED: "bg-blue/20 text-blue",
    TP1_REACHED: "bg-gold/15 text-gold",
    TP2_REACHED: "bg-long/15 text-long",
    STOPPED: "bg-short/15 text-short",
    EXPIRED: "bg-surface-2 text-text-muted",
    INVALIDATED: "bg-surface-2 text-text-muted",
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
