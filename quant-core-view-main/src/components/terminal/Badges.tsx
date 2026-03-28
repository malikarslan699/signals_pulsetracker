import { cn } from "@/lib/utils";

type Direction = "LONG" | "SHORT";
type Status = "active" | "tp1" | "tp2" | "tp3" | "sl" | "expired" | "pending";
type Plan = "trial" | "monthly" | "yearly" | "lifetime";
type Role = "user" | "admin" | "owner" | "superadmin";

interface BadgeProps {
  className?: string;
}

export function DirectionBadge({ direction, className }: BadgeProps & { direction: Direction }) {
  return (
    <span className={cn(
      "inline-flex items-center px-1.5 py-0.5 rounded text-2xs font-bold uppercase tracking-wider",
      direction === "LONG" 
        ? "bg-long/15 text-long" 
        : "bg-short/15 text-short",
      className
    )}>
      {direction}
    </span>
  );
}

export function StatusBadge({ status, className }: BadgeProps & { status: Status }) {
  const styles: Record<Status, string> = {
    active: "bg-primary/15 text-primary",
    tp1: "bg-long/15 text-long",
    tp2: "bg-long/15 text-long",
    tp3: "bg-long/15 text-long",
    sl: "bg-short/15 text-short",
    expired: "bg-muted text-muted-foreground",
    pending: "bg-warning/15 text-warning",
  };

  return (
    <span className={cn(
      "inline-flex items-center px-1.5 py-0.5 rounded text-2xs font-semibold uppercase tracking-wider",
      styles[status],
      className
    )}>
      {status.toUpperCase()}
    </span>
  );
}

export function PlanBadge({ plan, className }: BadgeProps & { plan: Plan }) {
  const styles: Record<Plan, string> = {
    trial: "bg-muted text-muted-foreground",
    monthly: "bg-info/15 text-info",
    yearly: "bg-primary/15 text-primary",
    lifetime: "bg-warning/15 text-warning",
  };

  return (
    <span className={cn(
      "inline-flex items-center px-1.5 py-0.5 rounded text-2xs font-semibold capitalize",
      styles[plan],
      className
    )}>
      {plan}
    </span>
  );
}

export function RoleBadge({ role, className }: BadgeProps & { role: Role }) {
  const styles: Record<Role, string> = {
    user: "bg-muted text-muted-foreground",
    admin: "bg-info/15 text-info",
    owner: "bg-warning/15 text-warning",
    superadmin: "bg-short/15 text-short",
  };

  return (
    <span className={cn(
      "inline-flex items-center px-1.5 py-0.5 rounded text-2xs font-semibold capitalize",
      styles[role],
      className
    )}>
      {role}
    </span>
  );
}

export function ConfidenceBadge({ value, className }: BadgeProps & { value: number }) {
  const color = value >= 75 ? "text-long" : value >= 50 ? "text-warning" : "text-short";
  return (
    <span className={cn("font-mono text-2xs font-bold", color, className)}>
      {value}%
    </span>
  );
}
