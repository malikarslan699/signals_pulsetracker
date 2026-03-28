import { cn } from "@/lib/utils";

interface ConfidenceBarProps {
  value: number;
  className?: string;
  showLabel?: boolean;
}

export function ConfidenceBar({ value, className, showLabel = true }: ConfidenceBarProps) {
  const color = value >= 75 ? "bg-long" : value >= 50 ? "bg-warning" : "bg-short";
  const textColor = value >= 75 ? "text-long" : value >= 50 ? "text-warning" : "text-short";

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="flex-1 h-1 bg-secondary rounded-full overflow-hidden min-w-[40px]">
        <div
          className={cn("h-full rounded-full transition-all", color)}
          style={{ width: `${value}%` }}
        />
      </div>
      {showLabel && (
        <span className={cn("font-mono text-2xs font-bold w-8 text-right", textColor)}>
          {value}%
        </span>
      )}
    </div>
  );
}
