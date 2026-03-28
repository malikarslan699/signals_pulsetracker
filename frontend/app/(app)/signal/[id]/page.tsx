"use client";
import { useRouter } from "next/navigation";
import { useParams } from "next/navigation";
import { useSignal } from "@/hooks/useSignals";
import { TradingViewChart } from "@/components/charts/TradingViewChart";
import { IndicatorBreakdown } from "@/components/signals/IndicatorBreakdown";
import { Panel } from "@/components/terminal/Panel";
import { DirectionBadge, StatusBadge } from "@/components/terminal/Badges";
import { ConfidenceBar } from "@/components/terminal/ConfidenceBar";
import {
  ArrowLeft,
  Share2,
  Clock,
  Target,
  CheckCircle2,
  XCircle,
  Shield,
  Info,
} from "lucide-react";
import {
  formatPrice,
  formatTimeAgo,
  formatDateTime,
  confidenceBandLabel,
  confidenceBandColor,
} from "@/lib/formatters";
import Link from "next/link";
import { cn } from "@/lib/utils";
import toast from "react-hot-toast";

export default function SignalDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const signalId = Array.isArray(params?.id) ? params.id[0] : params?.id ?? "";
  const { data: signal, isLoading } = useSignal(signalId);

  if (isLoading) {
    return (
      <div className="p-3 space-y-3">
        <div className="h-8 w-48 bg-surface rounded animate-pulse" />
        <div className="h-24 bg-surface border border-border rounded animate-pulse" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-48 bg-surface border border-border rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!signal) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-text-muted">
        <XCircle className="w-12 h-12 mb-4 opacity-30" />
        <p className="text-lg font-medium">Signal not found</p>
        <Link href="/dashboard" className="mt-4 text-purple hover:underline text-sm">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const isLong = signal.direction === "LONG";
  const probabilityTp1 = signal.pwin_tp1 ?? signal.confidence;
  const bandColor = confidenceBandColor(probabilityTp1);
  const bandLabel = confidenceBandLabel(probabilityTp1);
  const htfEntries = Object.entries(signal.mtf_analysis || {}).filter(([tf]) => tf === "1H" || tf === "4H");
  const probabilityTp2 = signal.pwin_tp2 ?? null;
  const setupScore = signal.setup_score ?? signal.raw_score ?? signal.confidence;

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    toast.success("Signal URL copied to clipboard!");
  };

  return (
    <div className="p-3 space-y-3 pb-20 lg:pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-1 rounded hover:bg-surface-2 text-text-muted hover:text-text-primary transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div className="flex items-center gap-2">
            <span className="text-base font-bold text-text-primary font-mono">{signal.symbol}</span>
            <DirectionBadge direction={signal.direction as "LONG" | "SHORT"} />
            <StatusBadge status={signal.status as any} />
            <span className="text-2xs text-text-muted">{signal.timeframe}</span>
          </div>
        </div>
        <button onClick={handleShare} className="filter-pill gap-1">
          <Share2 className="h-3 w-3" />
          Share
        </button>
      </div>

      {/* Hero Stats Row */}
      <div className="flex items-center gap-4 px-3 py-2.5 bg-surface border border-border rounded flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-2xs text-text-muted uppercase">P(TP1)</span>
          <ConfidenceBar value={probabilityTp1} className="w-24" />
          <span className="text-2xs font-mono font-bold" style={{ color: bandColor }}>
            {probabilityTp1}
          </span>
          <span className="text-2xs px-1.5 py-0.5 rounded font-medium border" style={{
            color: bandColor,
            borderColor: bandColor + "40",
            background: bandColor + "10",
          }}>
            {bandLabel}
          </span>
        </div>
        <div className="h-4 w-px bg-border" />
        <div className="flex items-center gap-1.5">
          <span className="text-2xs text-text-muted uppercase">Setup</span>
          <span className="font-mono font-bold text-sm text-text-primary">{setupScore}/100</span>
        </div>
        {probabilityTp2 != null && (
          <>
            <div className="h-4 w-px bg-border" />
            <div className="flex items-center gap-1.5">
              <span className="text-2xs text-text-muted uppercase">P(TP2)</span>
              <span className="font-mono font-bold text-sm text-long">{probabilityTp2}%</span>
            </div>
          </>
        )}
        <div className="h-4 w-px bg-border" />
        <div className="flex items-center gap-1.5">
          <span className="text-2xs text-text-muted uppercase">RR TP1</span>
          <span className="font-mono font-bold text-sm text-gold">
            {signal.rr_tp1 != null ? `${signal.rr_tp1}:1` : "—"}
          </span>
        </div>
        <div className="h-4 w-px bg-border" />
        <div className="flex items-center gap-1.5">
          <span className="text-2xs text-text-muted uppercase">RR TP2</span>
          <span className="font-mono font-bold text-sm text-gold">
            {signal.rr_tp2 != null ? `${signal.rr_tp2}:1` : "—"}
          </span>
        </div>
        {signal.pnl_pct != null && (
          <>
            <div className="h-4 w-px bg-border" />
            <div className="flex items-center gap-1.5">
              <span className="text-2xs text-text-muted uppercase">PnL</span>
              <span className={cn(
                "font-mono font-bold text-sm",
                Number(signal.pnl_pct) >= 0 ? "text-long" : "text-short"
              )}>
                {Number(signal.pnl_pct) >= 0 ? "+" : ""}{Number(signal.pnl_pct).toFixed(2)}%
              </span>
            </div>
          </>
        )}
        <div className="h-4 w-px bg-border" />
        <div className="flex items-center gap-1.5">
          <Clock className="h-3 w-3 text-text-muted" />
          <span className="text-2xs text-text-muted">{formatTimeAgo(signal.fired_at)} · {formatDateTime(signal.fired_at)}</span>
        </div>
        {signal.ranking_score != null && (
          <>
            <div className="h-4 w-px bg-border" />
            <div className="flex items-center gap-1.5">
              <span className="text-2xs text-text-muted uppercase">Rank</span>
              <span className="font-mono font-bold text-sm text-purple">{signal.ranking_score}</span>
            </div>
          </>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* Chart Area */}
        <div className="lg:col-span-2">
          <Panel title="Chart" className="h-80">
            <TradingViewChart
              symbol={signal.symbol}
              timeframe={signal.timeframe}
              signal={{
                direction: signal.direction,
                entry: signal.entry,
                entry_zone_low: signal.entry_zone_low,
                entry_zone_high: signal.entry_zone_high,
                stop_loss: signal.stop_loss,
                invalidation_price: signal.invalidation_price,
                take_profit_1: signal.take_profit_1,
                take_profit_2: signal.take_profit_2,
              }}
            />
          </Panel>
        </div>

        {/* Price Levels + Confluences */}
        <div className="space-y-3">
          <Panel title="Price Levels" noPad>
            {[
              { label: "Entry", value: formatPrice(signal.entry), color: "text-gold" },
              ...(signal.entry_zone_low != null && signal.entry_zone_high != null ? [
                { label: "Entry Zone", value: `${formatPrice(signal.entry_zone_low)} - ${formatPrice(signal.entry_zone_high)}`, color: "text-gold" },
              ] : []),
              { label: "Stop Loss", value: formatPrice(signal.stop_loss), color: "text-short" },
              ...(signal.invalidation_price != null ? [{ label: "Invalidation", value: formatPrice(signal.invalidation_price), color: "text-short" }] : []),
              { label: "TP1", value: formatPrice(signal.take_profit_1), color: "text-long" },
              { label: "TP2", value: formatPrice(signal.take_profit_2), color: "text-long" },
              ...(signal.take_profit_3 ? [{ label: "TP3", value: formatPrice(signal.take_profit_3), color: "text-long" }] : []),
            ].map((level) => (
              <div
                key={level.label}
                className="flex items-center justify-between px-3 py-1.5 border-b border-border last:border-0 text-xs"
              >
                <span className="text-text-muted">{level.label}</span>
                <span className={cn("font-mono font-semibold", level.color)}>{level.value}</span>
              </div>
            ))}
          </Panel>

          <Panel title="Execution Plan" noPad>
            <div className="px-3 py-2 text-xs border-b border-border">
              <span className="text-text-muted">Entry Type</span>
              <p className="text-text-primary font-semibold mt-1">{signal.entry_type || "Market retest"}</p>
            </div>
            <div className="px-3 py-2 text-xs border-b border-border">
              <span className="text-text-muted">Trust Summary</span>
              <p className="text-text-primary mt-1">
                {signal.direction} setup with {setupScore}/100 structure quality and {probabilityTp1}% calibrated TP1 probability.
                {probabilityTp2 != null ? ` TP2 follow-through is estimated at ${probabilityTp2}%.` : ""}
              </p>
            </div>
            <div className="px-3 py-2 text-xs">
              <span className="text-text-muted">HTF Trend Lock</span>
              <div className="mt-2 flex flex-wrap gap-2">
                {htfEntries.length > 0 ? htfEntries.map(([tf, data]: [string, any]) => (
                  <span
                    key={tf}
                    className={cn(
                      "px-2 py-1 rounded border text-[11px] font-medium",
                      data.aligned ? "bg-long/10 text-long border-long/20" : "bg-short/10 text-short border-short/20"
                    )}
                  >
                    {tf}: {data.direction || "—"} {data.aligned ? "aligned" : "conflict"}
                  </span>
                )) : <span className="text-text-muted">No HTF bias snapshot</span>}
              </div>
            </div>
          </Panel>

          {signal.top_confluences && signal.top_confluences.length > 0 && (
            <Panel title="Top Confluences" noPad>
              {signal.top_confluences.map((c: string, i: number) => (
                <div key={i} className="flex items-start gap-2 px-3 py-1.5 border-b border-border last:border-0 text-2xs">
                  <Target className="h-3 w-3 text-purple shrink-0 mt-0.5" />
                  <span className="text-text-primary">{c}</span>
                </div>
              ))}
            </Panel>
          )}
        </div>
      </div>

      <Panel title="Signal Explanation" noPad>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-border">
          <div className="bg-surface px-3 py-3 text-xs">
            <div className="flex items-center gap-2 text-text-primary font-semibold mb-2">
              <Shield className="h-3.5 w-3.5 text-purple" />
              Why It Passed
            </div>
            <p className="text-text-secondary leading-5">
              Phase 2 gating accepted this setup only after HTF trend, structure, and entry-zone checks aligned. Phase 3 then ranked it with calibrated win probabilities instead of raw indicator inflation.
            </p>
          </div>
          <div className="bg-surface px-3 py-3 text-xs">
            <div className="flex items-center gap-2 text-text-primary font-semibold mb-2">
              <Info className="h-3.5 w-3.5 text-blue" />
              Execution Context
            </div>
            <p className="text-text-secondary leading-5">
              Planned entry uses the highlighted zone, invalidation sits at the broken structure edge, and TP1/TP2 are mapped to progressively deeper liquidity targets.
            </p>
          </div>
          <div className="bg-surface px-3 py-3 text-xs">
            <div className="flex items-center gap-2 text-text-primary font-semibold mb-2">
              <CheckCircle2 className="h-3.5 w-3.5 text-long" />
              What To Trust
            </div>
            <p className="text-text-secondary leading-5">
              Setup score measures structural quality. P(TP1) and P(TP2) estimate outcome likelihood. Rank decides which setups surface first when the scanner has multiple valid candidates.
            </p>
          </div>
        </div>
      </Panel>

      {/* MTF Analysis & Indicator Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Panel title="Multi-Timeframe Analysis" noPad>
          {signal.mtf_analysis && Object.keys(signal.mtf_analysis).length > 0 ? (
            <>
              <div className="grid grid-cols-[60px_60px_1fr_50px] px-3 py-1 text-2xs font-semibold text-text-muted uppercase border-b border-border">
                <span>TF</span>
                <span>Dir</span>
                <span>Alignment</span>
                <span>Status</span>
              </div>
              {Object.entries(signal.mtf_analysis).map(([tf, data]: [string, any]) => (
                <div key={tf} className="grid grid-cols-[60px_60px_1fr_50px] items-center px-3 py-1.5 border-b border-border last:border-0 text-xs">
                  <span className="font-mono text-text-primary">{tf}</span>
                  <span className={cn(
                    "text-2xs font-bold",
                    data.direction === "LONG" ? "text-long" : data.direction === "SHORT" ? "text-short" : "text-text-muted"
                  )}>
                    {data.direction || "—"}
                  </span>
                  <div className="flex gap-1 text-2xs font-mono">
                    <span className="text-long">{data.long_confidence}</span>
                    <span className="text-text-muted">/</span>
                    <span className="text-short">{data.short_confidence}</span>
                  </div>
                  <span className={cn("text-2xs font-semibold", data.aligned ? "text-long" : "text-short")}>
                    {data.aligned ? "✓" : "✗"}
                  </span>
                </div>
              ))}
            </>
          ) : (
            <div className="px-3 py-6 text-center text-sm text-text-muted">No MTF data available</div>
          )}
        </Panel>

        <Panel title="Indicator Breakdown" noPad>
          {signal.score_breakdown ? (
            <IndicatorBreakdown breakdown={signal.score_breakdown} />
          ) : (
            <div className="px-3 py-6 text-center text-sm text-text-muted">No breakdown data</div>
          )}
        </Panel>
      </div>
    </div>
  );
}
