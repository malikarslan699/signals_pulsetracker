"use client";
import Link from "next/link";
import { TrendingUp, TrendingDown } from "lucide-react";
import { Signal } from "@/types/signal";
import { formatPrice, formatTimeAgo, confidenceBandColor } from "@/lib/formatters";

interface SignalRowProps {
  signal: Signal;
}

const STATUS_STYLE: Record<string, string> = {
  active:      "",
  tp1_hit:     "text-long",
  tp2_hit:     "text-long",
  tp3_hit:     "text-long",
  sl_hit:      "text-short",
  expired:     "text-text-muted",
  invalidated: "text-text-muted",
};

const STATUS_LABEL: Record<string, string> = {
  active:      "",
  tp1_hit:     "TP1",
  tp2_hit:     "TP2",
  tp3_hit:     "TP3",
  sl_hit:      "SL",
  expired:     "EXP",
  invalidated: "INV",
};

export function SignalRow({ signal }: SignalRowProps) {
  const isLong = signal.direction === "LONG";
  const bandColor = confidenceBandColor(signal.confidence);
  const statusLabel = STATUS_LABEL[signal.status];
  const statusStyle = STATUS_STYLE[signal.status] ?? "text-text-muted";

  return (
    <Link href={`/signal/${signal.id}`}>
      <div className={`group flex items-center gap-0 px-3 py-2 border-b border-border/40 hover:bg-surface-2/50 transition-colors cursor-pointer text-xs font-mono ${
        isLong ? "border-l-2 border-l-long/30 hover:border-l-long/60" : "border-l-2 border-l-short/30 hover:border-l-short/60"
      }`}>

        {/* Direction indicator */}
        <div className="w-5 shrink-0 flex justify-center">
          {isLong
            ? <TrendingUp className="w-3 h-3 text-long" />
            : <TrendingDown className="w-3 h-3 text-short" />
          }
        </div>

        {/* Symbol */}
        <div className="w-28 shrink-0 font-bold text-text-primary">
          {signal.symbol}
        </div>

        {/* Direction label + timeframe */}
        <div className="w-20 shrink-0 flex items-center gap-1.5">
          <span className={`px-1 py-0.5 rounded text-[10px] font-bold leading-none ${
            isLong ? "bg-long/15 text-long" : "bg-short/15 text-short"
          }`}>
            {signal.direction}
          </span>
          <span className="text-text-muted text-[10px]">{signal.timeframe}</span>
        </div>

        {/* Confidence bar + value */}
        <div className="w-28 shrink-0 flex items-center gap-2">
          <div className="flex-1 h-1 bg-surface-2 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{ width: `${signal.confidence}%`, background: bandColor }}
            />
          </div>
          <span className="w-6 text-right font-bold" style={{ color: bandColor }}>
            {signal.confidence}
          </span>
        </div>

        {/* Price levels */}
        <div className="flex-1 flex items-center gap-4 px-3">
          <span className="text-text-muted">
            E: <span className="text-gold">{formatPrice(signal.entry)}</span>
          </span>
          <span className="text-text-muted">
            SL: <span className="text-short">{formatPrice(signal.stop_loss)}</span>
          </span>
          <span className="text-text-muted">
            TP: <span className="text-long">{formatPrice(signal.take_profit_1)}</span>
          </span>
        </div>

        {/* RR */}
        <div className="w-12 shrink-0 text-right text-gold">
          {signal.rr_ratio}R
        </div>

        {/* Status */}
        <div className="w-8 shrink-0 text-center">
          {statusLabel && (
            <span className={`text-[10px] font-bold ${statusStyle}`}>
              {statusLabel}
            </span>
          )}
        </div>

        {/* Time */}
        <div className="w-16 shrink-0 text-right text-text-muted text-[10px]">
          {formatTimeAgo(signal.fired_at)}
        </div>
      </div>
    </Link>
  );
}
