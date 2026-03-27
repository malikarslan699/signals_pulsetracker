"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Activity, TrendingUp, TrendingDown, Target, Clock, BarChart2 } from "lucide-react";
import { PlatformStats } from "@/types/signal";

export function StatsRow() {
  const { data: stats, isLoading } = useQuery<PlatformStats>({
    queryKey: ["platform-stats"],
    queryFn: async () => {
      const res = await api.get<PlatformStats>("/api/v1/signals/stats");
      return res.data;
    },
    refetchInterval: 60_000,
    retry: false,
  });

  const winRate7d = stats?.win_rate_7d ?? stats?.win_rate_pct ?? 0;
  const tp90 = stats?.tp_hits_90d ?? 0;
  const sl90 = stats?.sl_hits_90d ?? 0;
  const winRateColor =
    winRate7d >= 65 ? "text-long" : winRate7d >= 50 ? "text-gold" : "text-short";

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-20 bg-surface border border-border rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
      {/* Active Signals */}
      <div className="bg-surface border border-purple/20 rounded-xl p-3 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-purple/10 flex-shrink-0">
          <Activity className="w-4 h-4 text-purple" />
        </div>
        <div>
          <p className="text-xl font-bold font-mono text-purple">{stats?.active_signals ?? "--"}</p>
          <p className="text-xs text-text-muted">Active</p>
        </div>
      </div>

      {/* Win Rate 7d */}
      <div className="bg-surface border border-border rounded-xl p-3 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-surface-2 flex-shrink-0">
          <BarChart2 className="w-4 h-4 text-text-secondary" />
        </div>
        <div>
          <p className={`text-xl font-bold font-mono ${winRateColor}`}>
            {winRate7d.toFixed(1)}%
          </p>
          <p className="text-xs text-text-muted">Win Rate 7d</p>
        </div>
      </div>

      {/* TP Hits 90d */}
      <div className="bg-surface border border-long/20 rounded-xl p-3 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-long/10 flex-shrink-0">
          <TrendingUp className="w-4 h-4 text-long" />
        </div>
        <div>
          <p className="text-xl font-bold font-mono text-long">{tp90}</p>
          <p className="text-xs text-text-muted">TP Hits 90d</p>
        </div>
      </div>

      {/* SL Hits 90d */}
      <div className="bg-surface border border-short/20 rounded-xl p-3 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-short/10 flex-shrink-0">
          <TrendingDown className="w-4 h-4 text-short" />
        </div>
        <div>
          <p className="text-xl font-bold font-mono text-short">{sl90}</p>
          <p className="text-xs text-text-muted">SL Hits 90d</p>
        </div>
      </div>

      {/* Avg Confidence */}
      <div className="bg-surface border border-border rounded-xl p-3 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-surface-2 flex-shrink-0">
          <Target className="w-4 h-4 text-blue" />
        </div>
        <div>
          <p className="text-xl font-bold font-mono text-blue">
            {stats?.avg_confidence ? `${stats.avg_confidence}` : "--"}
          </p>
          <p className="text-xs text-text-muted">Avg Conf 30d</p>
        </div>
      </div>

      {/* Next Scan */}
      <div className="bg-surface border border-border rounded-xl p-3 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-surface-2 flex-shrink-0">
          <Clock className="w-4 h-4 text-gold" />
        </div>
        <div>
          <p className="text-xl font-bold font-mono text-gold">
            {stats?.next_scan_in ?? "--"}
          </p>
          <p className="text-xs text-text-muted">Next Scan</p>
        </div>
      </div>
    </div>
  );
}
