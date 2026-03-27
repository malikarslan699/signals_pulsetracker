import { cn } from "@/lib/utils";

interface ConfidenceBarProps {
  value: number;
  className?: string;
  showLabel?: boolean;
}

export function ConfidenceBar({ value, className, showLabel = true }: ConfidenceBarProps) {
  const barColor = value >= 78 ? "bg-long" : value >= 60 ? "bg-gold" : "bg-short";
  const textColor = value >= 78 ? "text-long" : value >= 60 ? "text-gold" : "text-short";

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="flex-1 h-1 bg-surface-2 rounded-full overflow-hidden min-w-[32px]">
        <div className={cn("h-full rounded-full transition-all", barColor)} style={{ width: `${value}%` }} />
      </div>
      {showLabel && (
        <span className={cn("font-mono text-2xs font-bold w-6 text-right", textColor)}>{value}</span>
      )}
    </div>
  );
}
