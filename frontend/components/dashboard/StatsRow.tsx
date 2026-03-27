"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Activity, TrendingUp, Search, Clock } from "lucide-react";
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

  const winRate = stats?.win_rate_7d ?? stats?.win_rate_pct;
  const pairsScanned = stats?.pairs_scanned ?? stats?.total_signals ?? 0;
  const nextScan = stats?.next_scan_in ?? "--";

  const cards = [
    {
      label: "Active Signals",
      value: stats?.active_signals ?? "--",
      icon: Activity,
      color: "text-purple",
      bg: "bg-purple/10",
      border: "border-purple/20",
    },
    {
      label: "Win Rate (7d)",
      value: winRate !== undefined ? `${winRate.toFixed(1)}%` : "--",
      icon: TrendingUp,
      color: "text-long",
      bg: "bg-long/10",
      border: "border-long/20",
    },
    {
      label: "Pairs Scanned",
      value: pairsScanned,
      icon: Search,
      color: "text-blue",
      bg: "bg-blue/10",
      border: "border-blue/20",
    },
    {
      label: "Next Scan",
      value: nextScan,
      icon: Clock,
      color: "text-gold",
      bg: "bg-gold/10",
      border: "border-gold/20",
    },
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-20 bg-surface border border-border rounded-xl animate-pulse"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.label}
            className={`bg-surface border ${card.border} rounded-xl p-4 flex items-center gap-3`}
          >
            <div className={`p-2 rounded-lg ${card.bg} flex-shrink-0`}>
              <Icon className={`w-5 h-5 ${card.color}`} />
            </div>
            <div>
              <p className={`text-xl font-bold font-mono ${card.color}`}>
                {card.value}
              </p>
              <p className="text-xs text-text-muted">{card.label}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
