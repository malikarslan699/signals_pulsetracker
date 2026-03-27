"use client";
import Link from "next/link";
import { TrendingUp, TrendingDown, Clock, Target } from "lucide-react";
import { Signal } from "@/types/signal";
import { formatPrice, formatTimeAgo, confidenceBandColor } from "@/lib/formatters";
import { ConfidenceBar } from "./ConfidenceBar";

interface SignalCardProps {
  signal: Signal;
}

export function SignalCard({ signal }: SignalCardProps) {
  const isLong = signal.direction === "LONG";
  const bandColor = confidenceBandColor(signal.confidence);

  return (
    <Link href={`/signal/${signal.id}`}>
      <div
        className={`card-hover bg-surface border border-border rounded-xl p-4 cursor-pointer h-full flex flex-col gap-3 ${
          isLong ? "signal-card-long" : "signal-card-short"
        }`}
      >
        {/* Header: symbol + direction + timeframe */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-mono font-bold text-lg text-text-primary">
              {signal.symbol}
            </span>
            <span className="text-xs px-2 py-0.5 bg-surface-2 rounded-full text-text-muted capitalize border border-border">
              {signal.market}
            </span>
          </div>
          <span
            className={`flex items-center gap-1 text-sm font-bold px-2.5 py-1 rounded-full border ${
              isLong
                ? "bg-long/15 text-long border-long/25"
                : "bg-short/15 text-short border-short/25"
            }`}
          >
            {isLong ? (
              <TrendingUp className="w-3.5 h-3.5" />
            ) : (
              <TrendingDown className="w-3.5 h-3.5" />
            )}
            {signal.direction}
          </span>
        </div>

        {/* Timeframe + status */}
        <div className="flex items-center gap-2">
          <span className="text-xs px-2 py-0.5 bg-surface-2 border border-border rounded-full text-text-muted">
            {signal.timeframe}
          </span>
          {signal.status !== "active" && (
            <span
              className={`text-xs px-2 py-0.5 rounded-full border ${
                signal.status === "sl_hit"
                  ? "bg-short/10 text-short border-short/20"
                  : signal.status === "expired"
                  ? "bg-surface-2 text-text-muted border-border"
                  : "bg-long/10 text-long border-long/20"
              }`}
            >
              {signal.status.replace("_", " ").toUpperCase()}
            </span>
          )}
        </div>

        {/* Confidence */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-text-muted">Confidence</span>
            <span
              className="text-xs font-mono font-bold"
              style={{ color: bandColor }}
            >
              {signal.confidence}
            </span>
          </div>
          <ConfidenceBar value={signal.confidence} direction={signal.direction} />
        </div>

        {/* Price levels */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="bg-surface-2 rounded-lg px-2 py-2">
            <p className="text-xs text-text-muted mb-0.5">Entry</p>
            <p className="text-xs font-mono font-bold text-gold">
              {formatPrice(signal.entry)}
            </p>
          </div>
          <div className="bg-surface-2 rounded-lg px-2 py-2">
            <p className="text-xs text-text-muted mb-0.5">SL</p>
            <p className="text-xs font-mono font-bold text-short">
              {formatPrice(signal.stop_loss)}
            </p>
          </div>
          <div className="bg-surface-2 rounded-lg px-2 py-2">
            <p className="text-xs text-text-muted mb-0.5">TP1</p>
            <p className="text-xs font-mono font-bold text-long">
              {formatPrice(signal.take_profit_1)}
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between mt-auto pt-1">
          <div className="flex items-center gap-1 text-xs text-text-muted">
            <Clock className="w-3 h-3" />
            {formatTimeAgo(signal.fired_at)}
          </div>
          <div className="flex items-center gap-1 text-xs font-mono font-medium text-gold">
            <Target className="w-3 h-3" />
            {signal.rr_ratio}:1
          </div>
        </div>
      </div>
    </Link>
  );
}
