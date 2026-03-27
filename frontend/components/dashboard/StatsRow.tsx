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
      <div className="flex flex-wrap gap-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-7 w-28 bg-surface border border-border rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-surface border border-purple/25 rounded-lg text-xs font-mono">
        <Activity className="w-3 h-3 text-purple shrink-0" />
        <span className="text-text-muted">Active</span>
        <span className="font-bold text-purple">{stats?.active_signals ?? "--"}</span>
      </div>

      <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-surface border border-border rounded-lg text-xs font-mono">
        <BarChart2 className="w-3 h-3 text-text-secondary shrink-0" />
        <span className="text-text-muted">Win Rate 7d</span>
        <span className={`font-bold ${winRateColor}`}>{winRate7d.toFixed(1)}%</span>
      </div>

      <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-surface border border-long/20 rounded-lg text-xs font-mono">
        <TrendingUp className="w-3 h-3 text-long shrink-0" />
        <span className="text-text-muted">TP</span>
        <span className="font-bold text-long">{tp90}</span>
      </div>

      <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-surface border border-short/20 rounded-lg text-xs font-mono">
        <TrendingDown className="w-3 h-3 text-short shrink-0" />
        <span className="text-text-muted">SL</span>
        <span className="font-bold text-short">{sl90}</span>
      </div>

      <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-surface border border-border rounded-lg text-xs font-mono">
        <Target className="w-3 h-3 text-blue shrink-0" />
        <span className="text-text-muted">Avg Conf</span>
        <span className="font-bold text-blue">{stats?.avg_confidence ?? "--"}</span>
      </div>

      <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-surface border border-border rounded-lg text-xs font-mono">
        <Clock className="w-3 h-3 text-gold shrink-0" />
        <span className="text-text-muted">Next Scan</span>
        <span className="font-bold text-gold">{stats?.next_scan_in ?? "--"}</span>
      </div>
    </div>
  );
}
