"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Activity, TrendingUp, TrendingDown, Target, Clock, BarChart2 } from "lucide-react";
import { PlatformStats } from "@/types/signal";
import { KPIChip } from "@/components/terminal/KPIChip";

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
    <div className="flex flex-wrap items-center gap-1.5">
      <KPIChip label="Active" value={stats?.active_signals ?? "--"} icon={<Activity className="w-3 h-3 text-long" />} />
      <KPIChip
        label="Win 7d"
        value={`${winRate7d.toFixed(1)}%`}
        icon={<BarChart2 className="w-3 h-3 text-text-secondary" />}
        trend={winRate7d >= 50 ? "up" : "down"}
      />
      <KPIChip label="TP" value={tp90} icon={<TrendingUp className="w-3 h-3 text-long" />} trend="up" />
      <KPIChip label="SL" value={sl90} icon={<TrendingDown className="w-3 h-3 text-short" />} trend="down" />
      <KPIChip label="Avg Conf" value={stats?.avg_confidence ?? "--"} icon={<Target className="w-3 h-3 text-blue" />} />
      <KPIChip label="Next Scan" value={stats?.next_scan_in ?? "--"} icon={<Clock className="w-3 h-3 text-gold" />} />
    </div>
  );
}
