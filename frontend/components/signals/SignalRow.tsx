"use client";
import Link from "next/link";
import { Signal } from "@/types/signal";
import { formatPrice, formatTimeAgo } from "@/lib/formatters";
import { ConfidenceBar } from "@/components/signals/ConfidenceBar";
import { DirectionBadge, StatusBadge, ConfidenceBadge } from "@/components/terminal/Badges";

interface SignalRowProps {
  signal: Signal;
}

export function SignalRow({ signal }: SignalRowProps) {
  const isLong = signal.direction === "LONG";

  return (
    <Link href={`/signal/${signal.id}`}>
      <div
        className={`data-row grid grid-cols-[minmax(140px,1fr)_64px_48px_116px_86px_86px_86px_52px_78px_52px] items-center gap-2 px-3 py-2 border-b border-border text-xs font-mono cursor-pointer ${
          isLong ? "border-l-2 border-l-long/25 hover:border-l-long/60" : "border-l-2 border-l-short/25 hover:border-l-short/60"
        }`}
      >
        <span className="font-semibold text-text-primary truncate">{signal.symbol}</span>

        <DirectionBadge direction={signal.direction} />

        <span className="text-text-muted text-[10px]">{signal.timeframe}</span>

        <div className="flex items-center gap-2 min-w-0">
          <div className="flex-1 min-w-[56px]">
            <ConfidenceBar value={signal.confidence} showLabel={false} />
          </div>
          <ConfidenceBadge value={signal.confidence} className="w-8 text-right" />
        </div>

        <span className="text-right text-gold">{formatPrice(signal.entry)}</span>
        <span className="text-right text-short">{formatPrice(signal.stop_loss)}</span>
        <span className="text-right text-long">{formatPrice(signal.take_profit_1)}</span>

        <span className="text-right text-text-secondary">{signal.rr_ratio}R</span>

        <StatusBadge status={signal.status} />

        <span className="text-right text-[10px] text-text-muted">{formatTimeAgo(signal.fired_at)}</span>
      </div>
    </Link>
  );
}
