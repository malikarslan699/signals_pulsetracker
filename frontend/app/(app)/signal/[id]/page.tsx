"use client";
import { useSignal } from "@/hooks/useSignals";
import { TradingViewChart } from "@/components/charts/TradingViewChart";
import { IndicatorBreakdown } from "@/components/signals/IndicatorBreakdown";
import {
  TrendingUp,
  TrendingDown,
  Share2,
  ArrowLeft,
  Clock,
  Target,
  Shield,
  Activity,
  CheckCircle2,
  XCircle,
  Minus,
} from "lucide-react";
import {
  formatPrice,
  formatTimeAgo,
  formatDateTime,
  confidenceBandLabel,
  confidenceBandColor,
} from "@/lib/formatters";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ConfidenceBar } from "@/components/signals/ConfidenceBar";
import toast from "react-hot-toast";

export default function SignalDetailPage() {
  const params = useParams<{ id: string }>();
  const signalId = Array.isArray(params?.id) ? params.id[0] : params?.id ?? "";
  const { data: signal, isLoading } = useSignal(signalId);

  if (isLoading) {
    return (
      <div className="space-y-5 pb-20 lg:pb-6">
        <div className="h-8 w-48 bg-surface rounded animate-pulse" />
        <div className="h-[400px] bg-surface border border-border rounded-xl animate-pulse" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-48 bg-surface border border-border rounded-xl animate-pulse" />
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
  const dirColor = isLong ? "text-long" : "text-short";
  const bandColor = confidenceBandColor(signal.confidence);
  const bandLabel = confidenceBandLabel(signal.confidence);

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    toast.success("Signal URL copied to clipboard!");
  };

  const statusColors: Record<string, string> = {
    active: "text-blue bg-blue/10 border-blue/20",
    tp1_hit: "text-long bg-long/10 border-long/20",
    tp2_hit: "text-long bg-long/10 border-long/20",
    tp3_hit: "text-long bg-long/10 border-long/20",
    sl_hit: "text-short bg-short/10 border-short/20",
    expired: "text-text-muted bg-surface-2 border-border",
  };

  return (
    <div className="space-y-5 pb-20 lg:pb-6">
      {/* Back + Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link href="/dashboard">
            <button className="p-2 bg-surface border border-border rounded-lg hover:border-purple transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </button>
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold font-mono text-text-primary">
                {signal.symbol}
              </h1>
              <span className="text-xs px-2 py-0.5 bg-surface-2 border border-border rounded-full text-text-muted">
                {signal.timeframe}
              </span>
              <span
                className={`text-xs px-2 py-0.5 border rounded-full ${statusColors[signal.status] || statusColors.expired}`}
              >
                {signal.status.replace("_", " ").toUpperCase()}
              </span>
            </div>
            <div className="flex items-center gap-3 mt-1 text-xs text-text-muted">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatTimeAgo(signal.fired_at)} · {formatDateTime(signal.fired_at)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleShare}
            className="flex items-center gap-2 px-4 py-2 bg-surface border border-border rounded-lg text-sm text-text-secondary hover:text-text-primary transition-colors"
          >
            <Share2 className="w-4 h-4" />
            Share
          </button>
        </div>
      </div>

      {/* Signal Direction Banner */}
      <div
        className={`flex items-center justify-between p-4 rounded-xl border ${
          isLong
            ? "bg-long/5 border-long/20"
            : "bg-short/5 border-short/20"
        }`}
      >
        <div className="flex items-center gap-4">
          <div
            className={`flex items-center gap-2 text-xl font-bold ${dirColor}`}
          >
            {isLong ? (
              <TrendingUp className="w-6 h-6" />
            ) : (
              <TrendingDown className="w-6 h-6" />
            )}
            {signal.direction}
          </div>
          <div className="h-8 w-px bg-border" />
          <div>
            <p className="text-xs text-text-muted mb-1">Confidence</p>
            <div className="flex items-center gap-2">
              <span
                className="text-2xl font-bold font-mono"
                style={{ color: bandColor }}
              >
                {signal.confidence}
              </span>
              <span
                className="text-xs px-2 py-0.5 rounded-full font-medium border"
                style={{
                  color: bandColor,
                  borderColor: bandColor + "40",
                  background: bandColor + "10",
                }}
              >
                {bandLabel}
              </span>
            </div>
          </div>
          <div className="w-32 hidden md:block">
            <ConfidenceBar value={signal.confidence} direction={signal.direction} />
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs text-text-muted">R:R Ratio</p>
          <p className="text-2xl font-bold font-mono text-gold">
            {signal.rr_ratio}:1
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h2 className="text-sm font-semibold text-text-primary">Chart</h2>
          <span className="text-xs text-text-muted">{signal.symbol} · {signal.timeframe}</span>
        </div>
        <TradingViewChart
          symbol={signal.symbol}
          timeframe={signal.timeframe}
          signal={{
            direction: signal.direction,
            entry: signal.entry,
            stop_loss: signal.stop_loss,
            take_profit_1: signal.take_profit_1,
            take_profit_2: signal.take_profit_2,
          }}
        />
      </div>

      {/* Price Levels + MTF + Confluences */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Price Levels */}
        <div className="bg-surface border border-border rounded-xl p-4">
          <h2 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
            <Target className="w-4 h-4 text-purple" />
            Price Levels
          </h2>
          <div className="space-y-3">
            <PriceLevel label="Entry" value={formatPrice(signal.entry)} color="text-gold" />
            <PriceLevel label="Stop Loss" value={formatPrice(signal.stop_loss)} color="text-short" icon={<Shield className="w-3 h-3" />} />
            <div className="h-px bg-border" />
            <PriceLevel label="Take Profit 1" value={formatPrice(signal.take_profit_1)} color="text-long" />
            <PriceLevel label="Take Profit 2" value={formatPrice(signal.take_profit_2)} color="text-long" />
            {signal.take_profit_3 && (
              <PriceLevel label="Take Profit 3" value={formatPrice(signal.take_profit_3)} color="text-long" />
            )}
          </div>

          {/* Potential PnL */}
          {signal.pnl_pct != null && (
            <div className="mt-4 pt-4 border-t border-border">
              <div className="flex items-center justify-between">
                <span className="text-xs text-text-muted">Current PnL</span>
                {(() => { const n = parseFloat(String(signal.pnl_pct)); return (
                  <span className={`font-mono font-bold text-sm ${n >= 0 ? "text-long" : "text-short"}`}>
                    {n >= 0 ? "+" : ""}{n.toFixed(2)}%
                  </span>
                ); })()}
              </div>
            </div>
          )}
        </div>

        {/* MTF Analysis */}
        <div className="bg-surface border border-border rounded-xl p-4">
          <h2 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue" />
            Multi-Timeframe Analysis
          </h2>
          {signal.mtf_analysis && Object.keys(signal.mtf_analysis).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(signal.mtf_analysis).map(([tf, data]: [string, any]) => (
                <div
                  key={tf}
                  className={`flex items-center justify-between p-2 rounded-lg ${
                    data.aligned ? "bg-long/5 border border-long/10" : "bg-surface-2"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {data.aligned ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-long" />
                    ) : (
                      <Minus className="w-3.5 h-3.5 text-text-muted" />
                    )}
                    <span className="text-xs font-mono font-medium text-text-secondary">
                      {tf}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <span
                        className={`text-xs font-bold ${
                          data.direction === "LONG" ? "text-long" : data.direction === "SHORT" ? "text-short" : "text-text-muted"
                        }`}
                      >
                        {data.direction}
                      </span>
                    </div>
                    <div className="flex gap-1 text-xs font-mono">
                      <span className="text-long">{data.long_confidence}</span>
                      <span className="text-text-faint">/</span>
                      <span className="text-short">{data.short_confidence}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-text-muted text-center py-6">No MTF data available</p>
          )}
        </div>

        {/* Top Confluences */}
        <div className="bg-surface border border-border rounded-xl p-4">
          <h2 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-long" />
            Top Confluences
          </h2>
          {signal.top_confluences && signal.top_confluences.length > 0 ? (
            <ul className="space-y-2">
              {signal.top_confluences.map((c: string, i: number) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <CheckCircle2 className="w-4 h-4 text-long mt-0.5 flex-shrink-0" />
                  <span className="text-text-secondary">{c}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-text-muted text-center py-6">No confluence data</p>
          )}

          {/* ICT Zones */}
          {signal.ict_zones?.premium_discount && (
            <div className="mt-4 pt-4 border-t border-border">
              <p className="text-xs text-text-muted mb-2">Premium/Discount Zone</p>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-text-primary capitalize">
                  {signal.ict_zones.premium_discount.zone}
                </span>
                <span className="text-xs font-mono text-text-secondary">
                  {signal.ict_zones.premium_discount.current_pct.toFixed(1)}%
                </span>
              </div>
            </div>
          )}
          {signal.ict_zones?.daily_bias && (
            <div className="mt-3">
              <p className="text-xs text-text-muted mb-2">Daily Bias</p>
              <div className="flex items-center justify-between">
                <span
                  className={`text-sm font-bold ${
                    signal.ict_zones.daily_bias.bias === "bullish" ? "text-long" : "text-short"
                  }`}
                >
                  {signal.ict_zones.daily_bias.bias.toUpperCase()}
                </span>
                <div className="text-xs text-text-muted font-mono">
                  H: {signal.ict_zones.daily_bias.pdh != null ? formatPrice(signal.ict_zones.daily_bias.pdh) : "N/A"} · L: {signal.ict_zones.daily_bias.pdl != null ? formatPrice(signal.ict_zones.daily_bias.pdl) : "N/A"}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Indicator Breakdown */}
      <IndicatorBreakdown breakdown={signal.score_breakdown} />
    </div>
  );
}

function PriceLevel({
  label,
  value,
  color,
  icon,
}: {
  label: string;
  value: string;
  color: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-1.5 text-xs text-text-muted">
        {icon}
        {label}
      </div>
      <span className={`font-mono font-bold text-sm ${color}`}>{value}</span>
    </div>
  );
}
