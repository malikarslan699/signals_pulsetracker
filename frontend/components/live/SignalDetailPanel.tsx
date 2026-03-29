"use client";
import { TrendingUp, TrendingDown, CheckCircle, XCircle, Clock, MinusCircle } from "lucide-react";
import { Signal } from "@/types/signal";
import { formatPrice, formatTimeAgo, getStatusLabel, getStatusColor } from "@/lib/formatters";

interface SignalDetailPanelProps {
  signal: Signal | null;
  loading?: boolean;
}

const BAND_STYLES: Record<string, string> = {
  ULTRA_HIGH: "bg-long/15 text-long border-long/30",
  HIGH: "bg-emerald-500/10 text-emerald-400 border-emerald-500/25",
  MEDIUM: "bg-gold/10 text-gold border-gold/25",
  LOW: "bg-short/10 text-short border-short/25",
  NO_SIGNAL: "bg-surface-2 text-text-muted border-border",
};

const MTF_TIMEFRAMES = ["15m", "1H", "4H", "1D"];

function PriceRow({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-border/40 last:border-0">
      <span className="text-xs text-text-muted">{label}</span>
      <span className={`text-xs font-mono font-medium ${color ?? "text-text-primary"}`}>
        {value}
      </span>
    </div>
  );
}

function MtfRow({ tf, data }: { tf: string; data?: { direction: string; aligned: boolean; long_confidence: number; short_confidence: number } }) {
  if (!data) return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-text-muted">{tf}</span>
      <span className="text-text-muted">—</span>
    </div>
  );
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-text-muted font-mono">{tf}</span>
      <div className="flex items-center gap-1">
        <span className={data.direction === "LONG" ? "text-long" : "text-short"}>
          {data.direction}
        </span>
        {data.aligned ? (
          <CheckCircle className="w-3 h-3 text-long" />
        ) : (
          <XCircle className="w-3 h-3 text-short" />
        )}
      </div>
    </div>
  );
}

export function SignalDetailPanel({ signal, loading }: SignalDetailPanelProps) {
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-5 h-5 rounded-full border-2 border-long/30 border-t-long animate-spin" />
      </div>
    );
  }

  if (!signal) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-3 text-center px-4">
        <MinusCircle className="w-10 h-10 text-text-muted/40" />
        <div>
          <p className="text-sm font-medium text-text-muted">No Active Signal</p>
          <p className="text-xs text-text-muted/60 mt-1">
            Waiting for next ULTRA_HIGH setup on this pair
          </p>
        </div>
      </div>
    );
  }

  const isLong = signal.direction === "LONG";
  const bandStyle = BAND_STYLES[signal.confidence_band] ?? BAND_STYLES.NO_SIGNAL;
  const pwin = signal.pwin_tp1 ?? signal.confidence ?? 0;
  const rr = (signal.rr_tp1 ?? signal.rr_ratio ?? 0).toFixed(1);

  return (
    <div className="flex flex-col gap-3 h-full overflow-y-auto scrollbar-thin pr-0.5">
      {/* Direction + Band */}
      <div className="flex items-center justify-between">
        <div className={`flex items-center gap-1.5 font-bold text-sm ${isLong ? "text-long" : "text-short"}`}>
          {isLong ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          {signal.direction}
        </div>
        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${bandStyle}`}>
          {signal.confidence_band.replace("_", " ")}
        </span>
      </div>

      {/* Win probability */}
      <div className="rounded-xl bg-surface-2 border border-border p-3 text-center">
        <p className="text-xs text-text-muted mb-0.5">P(TP1)</p>
        <p className={`text-3xl font-black ${pwin >= 85 ? "text-long" : pwin >= 70 ? "text-gold" : "text-text-primary"}`}>
          {pwin}%
        </p>
        <p className="text-[10px] text-text-muted mt-0.5">Win probability</p>
      </div>

      {/* Price Levels */}
      <div className="rounded-xl bg-surface-2 border border-border p-3">
        <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">Trade Levels</p>
        <PriceRow label="Entry" value={formatPrice(signal.entry)} color="text-gold" />
        {signal.entry_zone_low && signal.entry_zone_high && (
          <PriceRow
            label="Zone"
            value={`${formatPrice(signal.entry_zone_low)} – ${formatPrice(signal.entry_zone_high)}`}
            color="text-gold/70"
          />
        )}
        <PriceRow label="Stop Loss" value={formatPrice(signal.stop_loss)} color="text-short" />
        <PriceRow label="TP1" value={formatPrice(signal.take_profit_1)} color="text-long" />
        <PriceRow label="TP2" value={formatPrice(signal.take_profit_2)} color="text-long" />
        <PriceRow label="R:R (TP1)" value={`1:${rr}`} />
      </div>

      {/* Status + Time */}
      <div className="flex items-center justify-between text-xs">
        <span className={`font-medium ${getStatusColor(signal.status)}`}>
          {getStatusLabel(signal.status)}
        </span>
        <span className="flex items-center gap-1 text-text-muted">
          <Clock className="w-3 h-3" />
          {formatTimeAgo(signal.fired_at)}
        </span>
      </div>

      {/* Top Confluences */}
      {signal.top_confluences && signal.top_confluences.length > 0 && (
        <div className="rounded-xl bg-surface-2 border border-border p-3">
          <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">Confluences</p>
          <ul className="space-y-1">
            {signal.top_confluences.slice(0, 6).map((c, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-text-primary">
                <span className="text-long flex-shrink-0 mt-0.5">•</span>
                <span className="leading-tight">{c}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* MTF Alignment */}
      {signal.mtf_analysis && (
        <div className="rounded-xl bg-surface-2 border border-border p-3">
          <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">MTF Alignment</p>
          <div className="space-y-1.5">
            {MTF_TIMEFRAMES.map((tf) => (
              <MtfRow key={tf} tf={tf} data={(signal.mtf_analysis as any)?.[tf]} />
            ))}
          </div>
        </div>
      )}

      {/* Signal ID (small) */}
      <p className="text-[9px] text-text-muted/40 font-mono mt-auto pt-1 text-center">
        #{String(signal.id).slice(0, 8)}
      </p>
    </div>
  );
}
