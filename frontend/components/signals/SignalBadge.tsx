"use client";
import { TrendingUp, TrendingDown } from "lucide-react";

interface SignalBadgeProps {
  direction: "LONG" | "SHORT";
  size?: "sm" | "md";
}

export function SignalBadge({ direction, size = "md" }: SignalBadgeProps) {
  const isLong = direction === "LONG";
  const sizeClasses = size === "sm" ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1";
  const iconSize = size === "sm" ? "w-3 h-3" : "w-4 h-4";

  return (
    <span
      className={`inline-flex items-center gap-1 font-bold rounded-full ${sizeClasses} ${
        isLong
          ? "bg-long/20 text-long border border-long/30"
          : "bg-short/20 text-short border border-short/30"
      }`}
    >
      {isLong ? (
        <TrendingUp className={iconSize} />
      ) : (
        <TrendingDown className={iconSize} />
      )}
      {direction}
    </span>
  );
}
