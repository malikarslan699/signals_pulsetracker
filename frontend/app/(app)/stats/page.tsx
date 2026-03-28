"use client";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Panel } from "@/components/terminal/Panel";
import { KPICard } from "@/components/terminal/KPIChip";
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
import { Activity, Target, BarChart2, ShieldCheck, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

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
  const [days, setDays] = useState<7 | 14 | 30 | 90>(30);

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
          params: { limit: 100, page: 1, min_confidence: 0 },
        })
        .then((r) => r.data),
    refetchInterval: 60_000,
  });

  const signals = signalList?.items || [];
  const now = new Date();
  const cutoff = new Date(now);
  cutoff.setDate(cutoff.getDate() - days);
  const filtered = signals.filter((s) => new Date(s.fired_at) >= cutoff);

  const closed = filtered.filter((s) => !["active", "CREATED", "ARMED", "FILLED"].includes(s.status));
  const wins = closed.filter((s) => s.status.includes("tp")).length;
  const losses = closed.filter((s) => s.status === "sl_hit" || s.status === "STOPPED").length;
  const localWinRate = wins + losses > 0 ? (wins / (wins + losses)) * 100 : 0;

  const byTimeframe = useMemo(() => {
    const map = new Map<string, number>();
    for (const s of filtered) {
      map.set(s.timeframe, (map.get(s.timeframe) || 0) + 1);
    }
    return Array.from(map.entries())
      .map(([tf, count]) => ({ tf, count }))
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
      if (s.status === "sl_hit" || s.status === "STOPPED") row.losses += 1;
    }
    return Array.from(map.values());
  }, [filtered]);

  const loading = statsLoading || signalsLoading;

  return (
    <div className="p-3 space-y-3 pb-20 lg:pb-6">
      <div className="flex items-center justify-between">
        <h1 className="text-sm font-semibold text-text-primary">Trading Stats</h1>
        <div className="flex items-center gap-0.5">
          {([7, 14, 30, 90] as const).map((r) => (
            <button
              key={r}
              onClick={() => setDays(r)}
              className={cn("filter-pill", days === r && "filter-pill-active")}
            >
              {r}d
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KPICard
          label="Win Rate"
          value={loading ? "--" : `${localWinRate.toFixed(1)}%`}
          icon={<TrendingUp className="h-3.5 w-3.5" />}
          trend={localWinRate >= 50 ? "up" : "down"}
          subtitle={`${wins}W / ${losses}L`}
        />
        <KPICard
          label="Total Signals"
          value={loading ? "--" : String(filtered.length)}
          icon={<Activity className="h-3.5 w-3.5" />}
          subtitle={`${days}-day period`}
        />
        <KPICard
          label="Active"
          value={stats?.active_signals ?? "--"}
          icon={<Target className="h-3.5 w-3.5" />}
          trend="up"
        />
        <KPICard
          label="Avg Confidence"
          value={stats ? `${stats.avg_confidence.toFixed(1)}%` : "--"}
          icon={<ShieldCheck className="h-3.5 w-3.5" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* Daily Activity Chart */}
        <Panel title="Daily Activity (14d)" className="lg:col-span-2">
          <div className="h-52">
            {loading ? (
              <div className="h-full bg-surface-2 rounded animate-pulse" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={dailySeries}>
                  <XAxis
                    dataKey="day"
                    tick={{ fontSize: 10, fill: "rgb(107 114 128)" }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: "rgb(107 114 128)" }}
                    tickLine={false}
                    axisLine={false}
                    width={24}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "rgb(17 24 39)",
                      border: "1px solid rgb(55 65 81)",
                      borderRadius: "6px",
                      fontSize: "11px",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="wins"
                    stackId="1"
                    stroke="rgb(16 185 129)"
                    fill="rgb(16 185 129)"
                    fillOpacity={0.3}
                    name="wins"
                  />
                  <Area
                    type="monotone"
                    dataKey="losses"
                    stackId="1"
                    stroke="rgb(239 68 68)"
                    fill="rgb(239 68 68)"
                    fillOpacity={0.3}
                    name="losses"
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </Panel>

        {/* Timeframe Distribution */}
        <Panel title="By Timeframe">
          <div className="h-52">
            {loading ? (
              <div className="h-full bg-surface-2 rounded animate-pulse" />
            ) : byTimeframe.length === 0 ? (
              <div className="h-full flex items-center justify-center text-sm text-text-muted">
                No data yet
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={byTimeframe}>
                  <XAxis
                    dataKey="tf"
                    tick={{ fontSize: 10, fill: "rgb(107 114 128)" }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: "rgb(107 114 128)" }}
                    tickLine={false}
                    axisLine={false}
                    width={24}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "rgb(17 24 39)",
                      border: "1px solid rgb(55 65 81)",
                      borderRadius: "6px",
                      fontSize: "11px",
                    }}
                  />
                  <Bar dataKey="count" fill="rgb(16 185 129)" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}
