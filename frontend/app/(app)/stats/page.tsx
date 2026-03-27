"use client";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
} from "recharts";
import { Activity, Target, BarChart2, ShieldCheck } from "lucide-react";

type SignalItem = {
  id: string;
  symbol: string;
  direction: "LONG" | "SHORT";
  timeframe: string;
  confidence: number;
  status: string;
  fired_at: string;
  pnl_pct?: number | null;
};

type SignalListResponse = {
  items: SignalItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
};

type PlatformStats = {
  total_signals: number;
  signals_last_30d: number;
  active_signals: number;
  win_rate_pct: number;
  avg_confidence: number;
  tp_hits_90d: number;
  sl_hits_90d: number;
  closed_total_90d: number;
  scanner_queue_length: number;
};

function startOfDay(d: Date) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

export default function StatsPage() {
  const [days, setDays] = useState<7 | 30 | 90>(30);

  const { data: stats, isLoading: statsLoading } = useQuery<PlatformStats>({
    queryKey: ["platform-stats", days],
    queryFn: () => api.get("/api/v1/signals/stats").then((r) => r.data),
    refetchInterval: 60_000,
  });

  const { data: signalList, isLoading: signalsLoading } = useQuery<SignalListResponse>({
    queryKey: ["signals-for-stats", days],
    queryFn: () =>
      api
        .get("/api/v1/signals/", {
          params: { limit: 200, page: 1, min_confidence: 0 },
        })
        .then((r) => r.data),
    refetchInterval: 60_000,
  });

  const signals = signalList?.items || [];
  const now = new Date();
  const cutoff = new Date(now);
  cutoff.setDate(cutoff.getDate() - days);
  const filtered = signals.filter((s) => new Date(s.fired_at) >= cutoff);

  const closed = filtered.filter((s) => s.status !== "active");
  const wins = closed.filter((s) => s.status.includes("tp")).length;
  const losses = closed.filter((s) => s.status === "sl_hit").length;
  const localWinRate = wins + losses > 0 ? (wins / (wins + losses)) * 100 : 0;

  const byTimeframe = useMemo(() => {
    const map = new Map<string, number>();
    for (const s of filtered) {
      map.set(s.timeframe, (map.get(s.timeframe) || 0) + 1);
    }
    return Array.from(map.entries())
      .map(([timeframe, count]) => ({ timeframe, count }))
      .sort((a, b) => b.count - a.count);
  }, [filtered]);

  const dailySeries = useMemo(() => {
    const map = new Map<string, { day: string; total: number; wins: number; losses: number }>();
    const start = new Date();
    start.setDate(start.getDate() - 13);
    for (let i = 0; i < 14; i += 1) {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      const key = startOfDay(d).toISOString().slice(0, 10);
      map.set(key, { day: key.slice(5), total: 0, wins: 0, losses: 0 });
    }

    for (const s of filtered) {
      const key = startOfDay(new Date(s.fired_at)).toISOString().slice(0, 10);
      const row = map.get(key);
      if (!row) continue;
      row.total += 1;
      if (s.status.includes("tp")) row.wins += 1;
      if (s.status === "sl_hit") row.losses += 1;
    }

    return Array.from(map.values());
  }, [filtered]);

  const loading = statsLoading || signalsLoading;

  return (
    <div className="space-y-6 pb-20 lg:pb-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Trading Stats</h1>
          <p className="text-sm text-text-muted mt-0.5">
            100% real platform data (no mock values)
          </p>
        </div>
        <div className="flex items-center gap-1 bg-surface rounded-lg p-1 border border-border">
          {[7, 30, 90].map((p) => (
            <button
              key={p}
              onClick={() => setDays(p as 7 | 30 | 90)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                days === p ? "bg-purple text-white" : "text-text-muted hover:text-text-primary"
              }`}
            >
              {p}d
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs text-text-muted mb-2">
            <Target className="w-4 h-4" /> Win Rate
          </div>
          <p className="text-2xl font-bold font-mono text-long">
            {loading ? "--" : `${localWinRate.toFixed(1)}%`}
          </p>
        </div>
        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs text-text-muted mb-2">
            <BarChart2 className="w-4 h-4" /> Signals ({days}d)
          </div>
          <p className="text-2xl font-bold font-mono text-text-primary">
            {loading ? "--" : filtered.length}
          </p>
        </div>
        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs text-text-muted mb-2">
            <Activity className="w-4 h-4" /> Active Signals
          </div>
          <p className="text-2xl font-bold font-mono text-purple">
            {stats?.active_signals ?? "--"}
          </p>
        </div>
        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs text-text-muted mb-2">
            <ShieldCheck className="w-4 h-4" /> Avg Confidence
          </div>
          <p className="text-2xl font-bold font-mono text-gold">
            {stats ? `${stats.avg_confidence.toFixed(1)}%` : "--"}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="bg-surface border border-border rounded-xl p-4">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Daily Signal Activity (14d)</h2>
          {loading ? (
            <div className="h-[240px] bg-surface-2 rounded animate-pulse" />
          ) : dailySeries.every((d) => d.total === 0) ? (
            <div className="h-[240px] flex items-center justify-center text-sm text-text-muted">
              No real signals available yet.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={dailySeries} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="day" tick={{ fill: "#6B7280", fontSize: 11 }} />
                <YAxis tick={{ fill: "#6B7280", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: "#111827", border: "1px solid #374151" }}
                  labelStyle={{ color: "#9CA3AF" }}
                />
                <Area type="monotone" dataKey="total" stroke="#8B5CF6" fill="#8B5CF633" />
                <Area type="monotone" dataKey="wins" stroke="#10B981" fill="#10B98122" />
                <Area type="monotone" dataKey="losses" stroke="#EF4444" fill="#EF444422" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-surface border border-border rounded-xl p-4">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Signals by Timeframe</h2>
          {loading ? (
            <div className="h-[240px] bg-surface-2 rounded animate-pulse" />
          ) : byTimeframe.length === 0 ? (
            <div className="h-[240px] flex items-center justify-center text-sm text-text-muted">
              No timeframe data available yet.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={byTimeframe}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="timeframe" tick={{ fill: "#6B7280", fontSize: 11 }} />
                <YAxis tick={{ fill: "#6B7280", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: "#111827", border: "1px solid #374151" }}
                  labelStyle={{ color: "#9CA3AF" }}
                />
                <Bar dataKey="count" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
