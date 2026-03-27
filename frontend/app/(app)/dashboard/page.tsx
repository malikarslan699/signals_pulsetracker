"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { RefreshCw, Activity, TrendingUp, Target, Crosshair, Clock, Zap } from "lucide-react";
import { useSignals } from "@/hooks/useSignals";
import { useScanner } from "@/hooks/useScanner";
import { MarketHeatmap } from "@/components/dashboard/MarketHeatmap";
import { LiveTicker } from "@/components/layout/LiveTicker";
import { KPIChip } from "@/components/terminal/KPIChip";
import { Panel } from "@/components/terminal/Panel";
import { DirectionBadge, StatusBadge } from "@/components/terminal/Badges";
import { ConfidenceBar } from "@/components/terminal/ConfidenceBar";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PlatformStats } from "@/types/signal";
import { formatPrice, formatTimeAgo } from "@/lib/formatters";

const COL = "grid-cols-[1fr_62px_46px_90px_88px_80px_80px_44px_56px_44px]";

export default function DashboardPage() {
  const router = useRouter();
  const [filterDir, setFilterDir] = useState("ALL");
  const [filterTf, setFilterTf] = useState("ALL");

  const { data: stats } = useQuery<PlatformStats>({
    queryKey: ["platform-stats"],
    queryFn: async () => (await api.get<PlatformStats>("/api/v1/signals/stats")).data,
    refetchInterval: 60_000,
    retry: false,
  });

  const { data: signals, isLoading, refetch } = useSignals({
    direction: filterDir === "ALL" ? undefined : filterDir,
    timeframe: filterTf === "ALL" ? undefined : filterTf,
    min_confidence: 78,
    limit: 50,
  });

  const { data: scanner } = useScanner();

  const rows = signals?.signals || [];
  const winRate = stats?.win_rate_7d ?? stats?.win_rate_pct ?? 0;
  const winRateTrend: "up" | "down" | "neutral" = winRate >= 60 ? "up" : winRate >= 40 ? "neutral" : "down";
  const isActive = scanner?.status === "active" || scanner?.status === "scanning";

  return (
    <div className="space-y-2 pb-20 lg:pb-4">
      <LiveTicker />

      {/* KPI Strip */}
      <div className="flex items-center gap-2 flex-wrap">
        <KPIChip label="Active" value={stats?.active_signals ?? "--"} icon={<Activity className="h-3 w-3" />} />
        <KPIChip label="Win Rate 7d" value={`${winRate.toFixed(1)}%`} icon={<TrendingUp className="h-3 w-3" />} trend={winRateTrend} />
        <KPIChip label="TP Hits" value={stats?.tp_hits_90d ?? "--"} icon={<Target className="h-3 w-3" />} trend="up" />
        <KPIChip label="SL Hits" value={stats?.sl_hits_90d ?? "--"} icon={<Crosshair className="h-3 w-3" />} trend="down" />
        <KPIChip label="Avg Conf" value={stats?.avg_confidence ?? "--"} />
        <KPIChip label="Next Scan" value={stats?.next_scan_in ?? "--"} icon={<Clock className="h-3 w-3" />} />
      </div>

      {/* Scanner status inline bar */}
      <div className={`flex items-center gap-3 px-3 py-1.5 rounded-lg border text-2xs font-mono ${
        isActive ? "bg-long/5 border-long/20" : "bg-surface border-border"
      }`}>
        <div className="flex items-center gap-1.5">
          <span className={`h-1.5 w-1.5 rounded-full ${isActive ? "bg-long animate-pulse" : "bg-text-muted"}`} />
          <span className={`font-bold tracking-widest ${isActive ? "text-long" : "text-text-muted"}`}>
            {isActive ? "SCANNING" : "IDLE"}
          </span>
        </div>
        {scanner?.last_scan && (
          <span className="text-text-muted">Last: <span className="text-text-primary font-bold">{formatTimeAgo(scanner.last_scan)}</span></span>
        )}
        <span className="text-text-muted">Next: <span className="text-gold font-bold">{stats?.next_scan_in ?? "--"}</span></span>
        {scanner?.pairs_scanned !== undefined && (
          <span className="text-text-muted"><span className="text-blue font-bold">{scanner.pairs_scanned}</span> pairs</span>
        )}
        {scanner?.signals_found !== undefined && (
          <span className="text-text-muted ml-auto"><span className="text-purple font-bold">{scanner.signals_found}</span> found</span>
        )}
      </div>

      {/* Main 3+1 grid layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">

        {/* Signal Table — 3 cols */}
        <div className="lg:col-span-3">
          <Panel
            title="Live Signals"
            actions={
              <button onClick={() => refetch()} className="p-1 rounded hover:bg-surface-2 text-text-muted hover:text-text-primary transition-colors">
                <RefreshCw className="h-3 w-3" />
              </button>
            }
            noPad
          >
            {/* Filter pills */}
            <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
              <div className="flex items-center gap-0.5">
                {["ALL", "LONG", "SHORT"].map((d) => (
                  <button
                    key={d}
                    onClick={() => setFilterDir(d)}
                    className={`filter-pill ${
                      filterDir === d
                        ? d === "LONG" ? "!bg-long !text-white"
                        : d === "SHORT" ? "!bg-short !text-white"
                        : "filter-pill-active"
                        : ""
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-0.5">
                {["ALL", "5m", "15m", "1H", "4H"].map((tf) => (
                  <button
                    key={tf}
                    onClick={() => setFilterTf(tf)}
                    className={`filter-pill ${filterTf === tf ? "filter-pill-active" : ""}`}
                  >
                    {tf}
                  </button>
                ))}
              </div>
              <span className="ml-auto text-2xs text-text-muted font-mono">{rows.length} signals</span>
            </div>

            {/* Column headers */}
            <div className={`grid ${COL} px-3 py-1.5 text-2xs font-semibold text-text-muted uppercase tracking-wider border-b border-border bg-surface-2/40`}>
              <span>Symbol</span>
              <span>Dir</span>
              <span>TF</span>
              <span>Confidence</span>
              <span className="text-right">Entry</span>
              <span className="text-right">SL</span>
              <span className="text-right">TP1</span>
              <span className="text-right">RR</span>
              <span>Status</span>
              <span className="text-right">Age</span>
            </div>

            {isLoading ? (
              Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className={`grid ${COL} px-3 py-2.5 border-b border-border/40 animate-pulse gap-2`}>
                  {Array.from({ length: 10 }).map((_, j) => (
                    <div key={j} className="h-2 bg-surface-2 rounded" />
                  ))}
                </div>
              ))
            ) : rows.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-14 text-text-muted">
                <Zap className="w-7 h-7 mb-2 opacity-25" />
                <p className="text-xs">No signals — adjust filters or wait for next scan</p>
              </div>
            ) : (
              rows.map((s) => (
                <div
                  key={s.id}
                  onClick={() => router.push(`/signal/${s.id}`)}
                  className={`data-row ${COL}`}
                >
                  <span className="font-bold text-text-primary truncate">{s.symbol}</span>
                  <DirectionBadge direction={s.direction as "LONG" | "SHORT"} />
                  <span className="text-text-muted">{s.timeframe}</span>
                  <ConfidenceBar value={s.confidence} />
                  <span className="text-right text-gold">{formatPrice(s.entry)}</span>
                  <span className="text-right text-short">{formatPrice(s.stop_loss)}</span>
                  <span className="text-right text-long">{formatPrice(s.take_profit_1)}</span>
                  <span className="text-right text-text-secondary">{s.rr_ratio}R</span>
                  <StatusBadge status={s.status} />
                  <span className="text-right text-text-muted">{formatTimeAgo(s.fired_at)}</span>
                </div>
              ))
            )}
          </Panel>
        </div>

        {/* Market Heatmap — 1 col */}
        <div>
          <MarketHeatmap signals={signals?.signals || []} />
        </div>
      </div>
    </div>
  );
}
