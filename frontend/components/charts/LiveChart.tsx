"use client";
import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { X, Zap, TrendingUp, TrendingDown } from "lucide-react";
import { api } from "@/lib/api";
import { TradingViewChart } from "@/components/charts/TradingViewChart";
import { Signal, SignalsResponse } from "@/types/signal";
import { useSignalWebSocket } from "@/hooks/useWebSocket";

interface LiveChartProps {
  symbol: string;
  timeframe: string;
  height?: number;
}

function fmt(p: number): string {
  if (p >= 1000) return `$${p.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  if (p >= 1) return `$${p.toFixed(4)}`;
  return `$${p.toFixed(6)}`;
}

export function LiveChart({ symbol, timeframe, height = 520 }: LiveChartProps) {
  const queryClient = useQueryClient();
  const [alertSignal, setAlertSignal] = useState<Signal | null>(null);
  const [alertVisible, setAlertVisible] = useState(false);

  // Fetch active signal for the current symbol (for chart overlay)
  const { data: activeSignal } = useQuery<Signal | null>({
    queryKey: ["live-signal", symbol],
    queryFn: async () => {
      const res = await api.get<SignalsResponse>(
        `/api/v1/signals/?symbol=${encodeURIComponent(symbol)}&limit=1`
      );
      const items = res.data?.signals || (res.data as any)?.items || [];
      const openStatuses = new Set(["CREATED", "ARMED", "FILLED", "TP1_REACHED"]);
      return items.find((s: Signal) => openStatuses.has(s.status)) ?? null;
    },
    refetchInterval: 15_000,
  });

  // WebSocket — fires when a new signal is generated anywhere
  const { lastSignal } = useSignalWebSocket();

  // Show alert banner when a new ULTRA_HIGH signal fires for this symbol
  useEffect(() => {
    if (
      lastSignal &&
      lastSignal.symbol === symbol &&
      lastSignal.confidence_band === "ULTRA_HIGH"
    ) {
      setAlertSignal(lastSignal);
      setAlertVisible(true);
    }
  }, [lastSignal, symbol]);

  // Auto-dismiss alert after 10 seconds
  useEffect(() => {
    if (!alertVisible) return;
    const timer = setTimeout(() => setAlertVisible(false), 10_000);
    return () => clearTimeout(timer);
  }, [alertVisible]);

  // Auto-refresh candles every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ["candles", symbol, timeframe] });
    }, 5_000);
    return () => clearInterval(interval);
  }, [queryClient, symbol, timeframe]);

  const signalOverlay = activeSignal
    ? {
        direction: activeSignal.direction,
        entry: activeSignal.entry,
        entry_zone_low: activeSignal.entry_zone_low,
        entry_zone_high: activeSignal.entry_zone_high,
        stop_loss: activeSignal.stop_loss,
        invalidation_price: activeSignal.invalidation_price,
        take_profit_1: activeSignal.take_profit_1,
        take_profit_2: activeSignal.take_profit_2,
      }
    : undefined;

  const isLong = alertSignal?.direction === "LONG";

  return (
    <div className="relative w-full">
      {/* Alert Banner */}
      {alertVisible && alertSignal && (
        <div
          className={`absolute top-3 left-3 right-3 z-20 rounded-xl border px-4 py-3 shadow-xl backdrop-blur-md
            flex items-start justify-between gap-3 animate-slide-up
            ${
              isLong
                ? "bg-long/10 border-long/30 text-long"
                : "bg-short/10 border-short/30 text-short"
            }`}
        >
          <div className="flex items-start gap-3 min-w-0">
            <Zap className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div className="min-w-0">
              <p className="font-bold text-sm leading-tight">
                {isLong ? "STRONG LONG ENTRY" : "STRONG SHORT ENTRY"} —{" "}
                {alertSignal.symbol}
              </p>
              <p className="text-xs mt-0.5 text-text-muted">
                P(TP1):{" "}
                <span className="font-semibold text-text-primary">
                  {alertSignal.pwin_tp1 ?? alertSignal.confidence}%
                </span>{" "}
                &nbsp;|&nbsp; Entry:{" "}
                <span className="font-semibold text-text-primary font-mono">
                  {fmt(alertSignal.entry)}
                </span>{" "}
                &nbsp;|&nbsp; R:R 1:
                <span className="font-semibold text-text-primary">
                  {(alertSignal.rr_tp1 ?? alertSignal.rr_ratio ?? 0).toFixed(1)}
                </span>
              </p>
            </div>
          </div>
          <button
            onClick={() => setAlertVisible(false)}
            className="flex-shrink-0 p-1 rounded hover:bg-surface-2 transition-colors text-text-muted hover:text-text-primary"
            aria-label="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Chart */}
      <TradingViewChart
        symbol={symbol}
        timeframe={timeframe}
        signal={signalOverlay}
        height={height}
      />

      {/* Active signal panel */}
      {activeSignal && (
        <div className="mt-3 rounded-xl border border-border bg-surface p-3 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div>
            <p className="text-text-muted mb-0.5">Direction</p>
            <span
              className={`inline-flex items-center gap-1 font-bold text-sm ${
                activeSignal.direction === "LONG" ? "text-long" : "text-short"
              }`}
            >
              {activeSignal.direction === "LONG" ? (
                <TrendingUp className="w-3.5 h-3.5" />
              ) : (
                <TrendingDown className="w-3.5 h-3.5" />
              )}
              {activeSignal.direction}
            </span>
          </div>
          <div>
            <p className="text-text-muted mb-0.5">P(TP1)</p>
            <p className="font-bold text-text-primary text-sm">
              {activeSignal.pwin_tp1 ?? activeSignal.confidence}%
            </p>
          </div>
          <div>
            <p className="text-text-muted mb-0.5">Entry</p>
            <p className="font-mono font-medium text-gold text-sm">
              {fmt(activeSignal.entry)}
            </p>
          </div>
          <div>
            <p className="text-text-muted mb-0.5">R:R (TP1)</p>
            <p className="font-medium text-text-primary text-sm">
              1:{(activeSignal.rr_tp1 ?? activeSignal.rr_ratio ?? 0).toFixed(1)}
            </p>
          </div>
          <div>
            <p className="text-text-muted mb-0.5">Stop Loss</p>
            <p className="font-mono text-short text-sm">{fmt(activeSignal.stop_loss)}</p>
          </div>
          <div>
            <p className="text-text-muted mb-0.5">TP1</p>
            <p className="font-mono text-long text-sm">{fmt(activeSignal.take_profit_1)}</p>
          </div>
          <div>
            <p className="text-text-muted mb-0.5">TP2</p>
            <p className="font-mono text-long text-sm">{fmt(activeSignal.take_profit_2)}</p>
          </div>
          <div>
            <p className="text-text-muted mb-0.5">Status</p>
            <p className="font-medium text-text-primary text-sm">{activeSignal.status}</p>
          </div>
        </div>
      )}
    </div>
  );
}
