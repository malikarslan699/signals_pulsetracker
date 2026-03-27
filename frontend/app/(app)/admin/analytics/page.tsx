"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
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
    queryFn: () => api.get("/api/v1/admin/analytics/signals?days=30").then((r) => r.data),
    refetchInterval: 60_000,
  });

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="flex items-center gap-2 text-text-muted text-xs mb-2">
            <BarChart2 className="w-4 h-4" />
            Total Signals (30d)
          </div>
          <p className="text-2xl font-mono font-bold text-text-primary">
            {data?.total_signals ?? 0}
          </p>
        </div>
        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="flex items-center gap-2 text-text-muted text-xs mb-2">
            <Target className="w-4 h-4" />
            Avg Confidence
          </div>
          <p className="text-2xl font-mono font-bold text-gold">
            {data?.avg_confidence ?? 0}%
          </p>
        </div>
        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="flex items-center gap-2 text-text-muted text-xs mb-2">
            <Activity className="w-4 h-4" />
            Top Symbol Count
          </div>
          <p className="text-2xl font-mono font-bold text-purple">
            {data?.top_symbols?.[0]?.signal_count ?? 0}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="bg-surface border border-border rounded-xl p-5">
          <h2 className="font-semibold text-text-primary mb-4">By Timeframe</h2>
          {isLoading ? (
            <p className="text-sm text-text-muted">Loading...</p>
          ) : isError ? (
            <p className="text-sm text-short">Failed to load analytics.</p>
          ) : (
            <div className="space-y-3">
              {(data?.by_timeframe || []).map((row) => (
                <div key={row.timeframe} className="flex items-center justify-between text-sm">
                  <span className="text-text-secondary">{row.timeframe}</span>
                  <span className="font-mono text-text-primary">{row.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-surface border border-border rounded-xl p-5">
          <h2 className="font-semibold text-text-primary mb-4">Top Symbols</h2>
          {isLoading ? (
            <p className="text-sm text-text-muted">Loading...</p>
          ) : isError ? (
            <p className="text-sm text-short">Failed to load analytics.</p>
          ) : (
            <div className="space-y-3">
              {(data?.top_symbols || []).slice(0, 10).map((row) => (
                <div key={row.symbol} className="flex items-center justify-between text-sm">
                  <span className="text-text-secondary">{row.symbol}</span>
                  <span className="font-mono text-text-primary">
                    {row.signal_count} | WR {row.win_rate_pct}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
