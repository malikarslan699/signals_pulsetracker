"use client";
import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Signal } from "@/types/signal";
import { formatPrice, formatTimeAgo } from "@/lib/formatters";
import { TrendingUp, TrendingDown, Activity, Target, Crosshair, Clock, ArrowUp, ArrowDown, ArrowUpDown } from "lucide-react";
import { KPIChip } from "@/components/terminal/KPIChip";
import { Panel } from "@/components/terminal/Panel";
import { DirectionBadge, StatusBadge, ConfidenceBadge } from "@/components/terminal/Badges";
import { cn } from "@/lib/utils";
import { useUserStore } from "@/store/userStore";

type SortKey = "confidence" | "entry" | "take_profit_1" | "stop_loss" | "pnl_pct" | "fired_at";
type SortDir = "asc" | "desc" | null;

const COL = "grid-cols-[1fr_62px_46px_52px_88px_80px_80px_56px_72px_60px]";

function SortIcon({ dir }: { dir: SortDir }) {
  if (!dir) return <ArrowUpDown className="w-3 h-3 opacity-40" />;
  if (dir === "asc") return <ArrowUp className="w-3 h-3 text-long" />;
  return <ArrowDown className="w-3 h-3 text-long" />;
}

function SortTh({ label, sortKey, current, dir, onSort }: {
  label: string; sortKey: SortKey; current: SortKey | null; dir: SortDir;
  onSort: (k: SortKey) => void;
}) {
  return (
    <button onClick={() => onSort(sortKey)} className="flex items-center gap-1 justify-end hover:text-text-primary transition-colors cursor-pointer">
      <span>{label}</span>
      <SortIcon dir={current === sortKey ? dir : null} />
    </button>
  );
}

export default function HistoryPage() {
  const router = useRouter();
  const user = useUserStore((s) => s.user);
  const [direction, setDirection] = useState("ALL");
  const [timeframe, setTimeframe] = useState("ALL");
  const [sortKey, setSortKey] = useState<SortKey | null>("fired_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const requestedDays =
    user?.plan === "trial"
      ? 7
      : user?.plan === "yearly"
        ? 180
        : user?.plan === "lifetime"
          ? 365
          : 90;

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["signal-history", requestedDays],
    queryFn: () =>
      api.get(`/api/v1/signals/history?days=${requestedDays}`).then((r) => r.data),
  });
  const errorMessage =
    (error as any)?.response?.data?.detail || "Could not load signal history.";

  const allSignals: Signal[] = Array.isArray(data) ? data : data?.signals || data?.items || [];
  const filtered = allSignals.filter((s) => {
    if (direction !== "ALL" && s.direction !== direction) return false;
    if (timeframe !== "ALL" && s.timeframe !== timeframe) return false;
    return true;
  });

  const signals = useMemo(() => {
    if (!sortKey || !sortDir) return filtered;
    return [...filtered].sort((a, b) => {
      let av: number, bv: number;
      if (sortKey === "fired_at") {
        av = new Date(a.fired_at).getTime(); bv = new Date(b.fired_at).getTime();
      } else if (sortKey === "pnl_pct") {
        av = a.pnl_pct != null ? parseFloat(String(a.pnl_pct)) : -Infinity;
        bv = b.pnl_pct != null ? parseFloat(String(b.pnl_pct)) : -Infinity;
      } else {
        av = parseFloat(String((a as any)[sortKey] ?? 0));
        bv = parseFloat(String((b as any)[sortKey] ?? 0));
      }
      return sortDir === "asc" ? av - bv : bv - av;
    });
  }, [filtered, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      if (sortDir === "desc") setSortDir("asc");
      else if (sortDir === "asc") { setSortKey(null); setSortDir(null); }
      else setSortDir("desc");
    } else { setSortKey(key); setSortDir("desc"); }
  };

  const total = signals.length;
  const wins = signals.filter((s) => s.status?.includes("tp")).length;
  const losses = signals.filter((s) => s.status === "sl_hit").length;
  const expired = signals.filter((s) => s.status === "expired" || s.status === "invalidated").length;
  const closed = wins + losses;
  const winRate = closed > 0 ? Math.round((wins / closed) * 100) : 0;
  const winRateTrend: "up" | "down" | "neutral" = winRate >= 60 ? "up" : winRate >= 40 ? "neutral" : "down";

  return (
    <div className="space-y-2 pb-20 lg:pb-4">
      <h1 className="text-xs font-bold text-text-muted uppercase tracking-widest">
        Signal History · Last {requestedDays} Days
      </h1>

      {/* KPI Strip */}
      <div className="flex items-center gap-2 flex-wrap">
        <KPIChip label="Total" value={total} icon={<Activity className="h-3 w-3" />} />
        <KPIChip label="Win Rate" value={`${winRate}%`} icon={<TrendingUp className="h-3 w-3" />} trend={winRateTrend} />
        <KPIChip label="TP Hits" value={wins} icon={<Target className="h-3 w-3" />} trend="up" />
        <KPIChip label="SL Hits" value={losses} icon={<Crosshair className="h-3 w-3" />} trend="down" />
        <KPIChip label="Expired" value={expired} icon={<Clock className="h-3 w-3" />} />
        {closed > 0 && <KPIChip label="W/L" value={`${wins}/${losses}`} />}
      </div>

      <Panel noPad>
        {/* Filters */}
        <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
          <div className="flex items-center gap-0.5">
            {["ALL", "LONG", "SHORT"].map((d) => (
              <button key={d} onClick={() => setDirection(d)}
                className={`filter-pill ${direction === d ? (d === "LONG" ? "!bg-long !text-white" : d === "SHORT" ? "!bg-short !text-white" : "filter-pill-active") : ""}`}>
                {d}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-0.5">
            {["ALL", "5m", "15m", "1H", "4H"].map((tf) => (
              <button key={tf} onClick={() => setTimeframe(tf)}
                className={`filter-pill ${timeframe === tf ? "filter-pill-active" : ""}`}>
                {tf}
              </button>
            ))}
          </div>
          <span className="ml-auto text-2xs text-text-muted font-mono">{signals.length} records</span>
        </div>

        {/* Column headers */}
        <div className={`grid ${COL} px-3 py-1.5 text-2xs font-semibold text-text-muted uppercase tracking-wider border-b border-border bg-surface-2/40`}>
          <span>Pair</span>
          <span>Dir</span>
          <span>TF</span>
          <div className="flex justify-end">
            <SortTh label="Conf" sortKey="confidence" current={sortKey} dir={sortDir} onSort={handleSort} />
          </div>
          <div className="flex justify-end">
            <SortTh label="Entry" sortKey="entry" current={sortKey} dir={sortDir} onSort={handleSort} />
          </div>
          <span className="text-right">TP1</span>
          <span className="text-right">SL</span>
          <span>Status</span>
          <div className="flex justify-end">
            <SortTh label="PnL" sortKey="pnl_pct" current={sortKey} dir={sortDir} onSort={handleSort} />
          </div>
          <div className="flex justify-end">
            <SortTh label="Time" sortKey="fired_at" current={sortKey} dir={sortDir} onSort={handleSort} />
          </div>
        </div>

        {isLoading ? (
          Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className={`grid ${COL} px-3 py-2.5 border-b border-border/40 animate-pulse gap-2`}>
              {Array.from({ length: 10 }).map((_, j) => <div key={j} className="h-2 bg-surface-2 rounded" />)}
            </div>
          ))
        ) : isError ? (
          <div className="p-8 text-center text-text-muted text-xs">
            {errorMessage}
          </div>
        ) : signals.length === 0 ? (
          <div className="p-12 text-center text-text-muted text-xs">No signals found</div>
        ) : (
          signals.map((s) => {
            const pnlN = s.pnl_pct != null ? parseFloat(String(s.pnl_pct)) : null;
            return (
              <div
                key={s.id}
                onClick={() => router.push(`/signal/${s.id}`)}
                className={cn(
                  `data-row ${COL}`,
                  s.status?.includes("tp") && "row-win",
                  s.status === "sl_hit" && "row-loss"
                )}
              >
                <span className="font-bold text-text-primary truncate">{s.symbol}</span>
                <DirectionBadge direction={s.direction as "LONG" | "SHORT"} />
                <span className="text-text-muted">{s.timeframe}</span>
                <span className="text-right"><ConfidenceBadge value={s.confidence} /></span>
                <span className="text-right text-gold">{formatPrice(s.entry)}</span>
                <span className="text-right text-long">{formatPrice(s.take_profit_1)}</span>
                <span className="text-right text-short">{formatPrice(s.stop_loss)}</span>
                <StatusBadge status={s.status} />
                <span className={cn(
                  "text-right font-semibold",
                  pnlN != null && pnlN > 0 ? "text-long" : pnlN != null && pnlN < 0 ? "text-short" : "text-text-muted"
                )}>
                  {pnlN != null ? `${pnlN > 0 ? "+" : ""}${pnlN.toFixed(2)}%` : "—"}
                </span>
                <span className="text-right text-text-muted">{formatTimeAgo(s.fired_at)}</span>
              </div>
            );
          })
        )}

        {signals.length > 0 && (
          <div className="px-3 py-2 border-t border-border text-2xs text-text-muted font-mono">
            {signals.length} records · click column headers to sort
          </div>
        )}
      </Panel>
    </div>
  );
}
