"use client";

interface ConfidenceBarProps {
  value: number;
  direction?: string;
  showLabel?: boolean;
}

function getBarColor(value: number): string {
  if (value >= 90) return "#10B981";
  if (value >= 70) return "#34D399";
  if (value >= 55) return "#F59E0B";
  return "#EF4444";
}

export function ConfidenceBar({ value, showLabel = false }: ConfidenceBarProps) {
  const color = getBarColor(value);
  const pct = Math.min(100, Math.max(0, value));

  return (
    <div className="w-full">
      <div className="confidence-bar relative overflow-hidden">
        <div
          className="h-full rounded-sm transition-all duration-500"
          style={{
            width: `${pct}%`,
            background: color,
            height: "4px",
          }}
        />
      </div>
      {showLabel && (
        <p className="text-xs font-mono mt-1" style={{ color }}>
          {value}
        </p>
      )}
    </div>
  );
}
