"use client";
import Link from "next/link";
import { TrendingUp, TrendingDown, Clock, Target, Zap } from "lucide-react";
import { Signal } from "@/types/signal";
import { formatPrice, formatTimeAgo, confidenceBandLabel, confidenceBandColor } from "@/lib/formatters";

interface SignalCardProps {
  signal: Signal;
}

const STATUS_STYLE: Record<string, string> = {
  CREATED:     "bg-blue/10 text-blue border-blue/20",
  ARMED:       "bg-gold/10 text-gold border-gold/20",
  FILLED:      "bg-blue/15 text-blue border-blue/25",
  TP1_REACHED: "bg-gold/10 text-gold border-gold/20",
  TP2_REACHED: "bg-long/15 text-long border-long/25",
  STOPPED:     "bg-short/10 text-short border-short/20",
  EXPIRED:     "bg-surface-2 text-text-muted border-border",
  INVALIDATED: "bg-surface-2 text-text-muted border-border",
};

const STATUS_LABEL: Record<string, string> = {
  CREATED:     "Created",
  ARMED:       "Armed",
  FILLED:      "Filled",
  TP1_REACHED: "TP1 Reached",
  TP2_REACHED: "TP2 Reached",
  STOPPED:     "Stopped",
  EXPIRED:     "Expired",
  INVALIDATED: "Invalidated",
};

export function SignalCard({ signal }: SignalCardProps) {
  const isLong = signal.direction === "LONG";
  const probability = signal.pwin_tp1 ?? signal.confidence;
  const bandColor = confidenceBandColor(probability);
  const bandLabel = confidenceBandLabel(probability);
  const pnl = signal.pnl_pct != null ? parseFloat(String(signal.pnl_pct)) : null;

  return (
    <Link href={`/signal/${signal.id}`}>
      <div
        className={`card-hover bg-surface border border-border rounded-2xl cursor-pointer h-full flex flex-col overflow-hidden ${
          isLong ? "signal-card-long" : "signal-card-short"
        }`}
      >
        {/* ── Header ─────────────────────────────── */}
        <div className="px-4 pt-4 pb-3 flex items-start justify-between gap-2">
          <div className="flex flex-col gap-1">
            <span className="font-mono font-bold text-base text-text-primary leading-none">
              {signal.symbol}
            </span>
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-xs px-1.5 py-0.5 bg-surface-2 border border-border rounded text-text-muted capitalize">
                {signal.market}
              </span>
              <span className="text-xs px-1.5 py-0.5 bg-surface-2 border border-border rounded text-text-muted">
                {signal.timeframe}
              </span>
              {signal.status !== "FILLED" && (
                <span className={`text-xs px-1.5 py-0.5 rounded border font-medium ${STATUS_STYLE[signal.status] ?? STATUS_STYLE.EXPIRED}`}>
                  {STATUS_LABEL[signal.status] ?? signal.status}
                </span>
              )}
            </div>
          </div>

          <span className={`flex items-center gap-1 text-sm font-bold px-3 py-1.5 rounded-xl border flex-shrink-0 ${
            isLong
              ? "bg-long/15 text-long border-long/25"
              : "bg-short/15 text-short border-short/25"
          }`}>
            {isLong ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
            {signal.direction}
          </span>
        </div>

        {/* ── Confidence ─────────────────────────── */}
        <div className="px-4 pb-3">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-1.5">
              <Zap className="w-3 h-3 text-text-muted" />
              <span className="text-xs text-text-muted">P(TP1)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium px-1.5 py-0.5 rounded" style={{
                color: bandColor,
                background: `${bandColor}18`,
              }}>
                {bandLabel}
              </span>
              <span className="text-sm font-mono font-bold" style={{ color: bandColor }}>
                {probability}%
              </span>
            </div>
          </div>
          {/* Progress bar */}
          <div className="confidence-bar">
            <div
              className="confidence-bar-fill"
              style={{
                width: `${probability}%`,
                background: `linear-gradient(90deg, ${bandColor}99, ${bandColor})`,
              }}
            />
          </div>
        </div>

        {/* ── Price grid ─────────────────────────── */}
        <div className="px-4 pb-3 grid grid-cols-3 gap-2">
          {[
            { label: "Entry", value: signal.entry, color: "text-gold" },
            { label: "Stop Loss", value: signal.stop_loss, color: "text-short" },
            { label: "Take Profit", value: signal.take_profit_1, color: "text-long" },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-surface-2 rounded-xl px-2 py-2.5 text-center border border-border/50">
              <p className="text-[10px] text-text-muted mb-1 uppercase tracking-wide">{label}</p>
              <p className={`text-xs font-mono font-bold ${color} leading-none`}>
                {formatPrice(value)}
              </p>
            </div>
          ))}
        </div>

        {/* ── Footer ─────────────────────────────── */}
        <div className="mt-auto px-4 py-2.5 border-t border-border/60 flex items-center justify-between bg-surface-2/40">
          <div className="flex items-center gap-1.5 text-xs text-text-muted">
            <Clock className="w-3 h-3" />
            <span>{formatTimeAgo(signal.fired_at)}</span>
          </div>

          <div className="flex items-center gap-3">
            {pnl != null && (
              <span className={`text-xs font-mono font-semibold ${pnl > 0 ? "text-long" : pnl < 0 ? "text-short" : "text-text-muted"}`}>
                {pnl > 0 ? "+" : ""}{pnl.toFixed(2)}%
              </span>
            )}
            <div className="flex items-center gap-2 text-xs font-mono font-semibold">
              {signal.setup_score != null && (
                <span className="text-text-secondary">S{signal.setup_score}</span>
              )}
              <span className="flex items-center gap-1 text-gold">
              <Target className="w-3 h-3" />
              <span>{signal.rr_tp1 != null ? `${signal.rr_tp1}:1` : "—"}</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}
