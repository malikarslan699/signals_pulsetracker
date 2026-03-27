import { cn } from "@/lib/utils";

interface BadgeProps { className?: string; }

export function DirectionBadge({ direction, className }: BadgeProps & { direction: "LONG" | "SHORT" }) {
  return (
    <span className={cn(
      "inline-flex items-center px-1.5 py-0.5 rounded text-2xs font-bold uppercase tracking-wider",
      direction === "LONG" ? "bg-long/15 text-long" : "bg-short/15 text-short",
      className
    )}>
      {direction}
    </span>
  );
}

type SignalStatus = string;
export function StatusBadge({ status, className }: BadgeProps & { status: SignalStatus }) {
  const isTP = status?.includes("tp");
  const isSL = status === "sl_hit";
  const isActive = status === "active";
  return (
    <span className={cn(
      "inline-flex items-center px-1.5 py-0.5 rounded text-2xs font-semibold uppercase tracking-wider",
      isTP  ? "bg-long/15 text-long"
      : isSL  ? "bg-short/15 text-short"
      : isActive ? "bg-purple/15 text-purple"
      : "bg-surface-2 text-text-muted",
      className
    )}>
      {isTP ? status.replace("_hit","").toUpperCase()
        : isSL ? "SL"
        : isActive ? "LIVE"
        : (status ?? "—").replace("_"," ").toUpperCase()}
    </span>
  );
}

export function ConfidenceBadge({ value, className }: BadgeProps & { value: number }) {
  const color = value >= 78 ? "text-long" : value >= 60 ? "text-gold" : "text-short";
  return (
    <span className={cn("font-mono text-2xs font-bold", color, className)}>
      {value}
    </span>
  );
}
