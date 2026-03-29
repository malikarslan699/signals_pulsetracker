"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Panel } from "@/components/terminal/Panel";
import { KPICard } from "@/components/terminal/KPIChip";
import { BarChart2, Target, Activity } from "lucide-react";

interface SignalsAnalytics {
  period_days: number;
  total_signals: number;
  avg_confidence: number;
  by_timeframe: Array<{ timeframe: string; count: number }>;
  by_direction: Array<{ direction: string; count: number }>;
  top_symbols: Array<{
    symbol: string;
    signal_count: number;
    win_rate_pct: number;
    tp_hits: number;
    sl_hits: number;
  }>;
}

export default function AdminAnalyticsPage() {
  const { data, isLoading, isError } = useQuery<SignalsAnalytics>({
    queryKey: ["admin-signals-analytics"],
    queryFn: () =>
      api.get("/api/v1/admin/analytics/signals?days=30").then((r) => r.data),
    refetchInterval: 60_000,
  });

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        <KPICard
          label="Total Signals (30d)"
          value={isLoading ? "--" : String(data?.total_signals ?? 0)}
          icon={<Activity className="h-3.5 w-3.5" />}
        />
        <KPICard
          label="Avg P(TP1)"
          value={isLoading ? "--" : `${data?.avg_confidence ?? 0}%`}
          icon={<Target className="h-3.5 w-3.5" />}
        />
        <KPICard
          label="Top Symbol"
          value={isLoading ? "--" : (data?.top_symbols?.[0]?.symbol ?? "—")}
          icon={<BarChart2 className="h-3.5 w-3.5" />}
          subtitle={data?.top_symbols?.[0] ? `${data.top_symbols[0].signal_count} signals` : undefined}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* By Timeframe */}
        <Panel title="By Timeframe" noPad>
          <div className="grid grid-cols-[60px_1fr_60px_60px] px-3 py-1 text-2xs font-semibold text-text-muted uppercase border-b border-border">
            <span>TF</span>
            <span>Signals</span>
            <span className="text-right">Win Rate</span>
            <span className="text-right">Count</span>
          </div>
          {isLoading ? (
            <div className="p-3 space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-6 bg-surface-2 rounded animate-pulse" />
              ))}
            </div>
          ) : isError ? (
            <div className="px-3 py-4 text-xs text-short">Failed to load analytics.</div>
          ) : (
            (data?.by_timeframe || []).map((row) => (
              <div
                key={row.timeframe}
                className="grid grid-cols-[60px_1fr_60px_60px] px-3 py-1.5 border-b border-border last:border-0 text-xs"
              >
                <span className="font-mono text-text-primary">{row.timeframe}</span>
                <div className="flex items-center pr-2">
                  <div className="h-1 bg-surface-2 rounded-full flex-1 overflow-hidden">
                    <div
                      className="h-full bg-purple rounded-full"
                      style={{
                        width: `${Math.min(100, (row.count / (data?.total_signals || 1)) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
                <span className="font-mono text-text-muted text-right">—</span>
                <span className="font-mono text-text-primary text-right">{row.count}</span>
              </div>
            ))
          )}
        </Panel>

        {/* Top Symbols */}
        <Panel title="Top Symbols" noPad>
          <div className="grid grid-cols-[1fr_60px_60px] px-3 py-1 text-2xs font-semibold text-text-muted uppercase border-b border-border">
            <span>Symbol</span>
            <span className="text-right">Signals</span>
            <span className="text-right">Win Rate</span>
          </div>
          {isLoading ? (
            <div className="p-3 space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-6 bg-surface-2 rounded animate-pulse" />
              ))}
            </div>
          ) : isError ? (
            <div className="px-3 py-4 text-xs text-short">Failed to load analytics.</div>
          ) : (
            (data?.top_symbols || []).slice(0, 10).map((row) => (
              <div
                key={row.symbol}
                className="grid grid-cols-[1fr_60px_60px] px-3 py-1.5 border-b border-border last:border-0 text-xs"
              >
                <span className="font-medium text-text-primary font-mono">{row.symbol}</span>
                <span className="font-mono text-text-primary text-right">{row.signal_count}</span>
                <span className="font-mono text-long text-right">{row.win_rate_pct}%</span>
              </div>
            ))
          )}
        </Panel>
      </div>
    </div>
  );
}
