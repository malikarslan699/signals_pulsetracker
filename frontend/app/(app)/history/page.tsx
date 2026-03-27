"use client";
import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Signal } from "@/types/signal";
import { formatPrice, formatTimeAgo, getStatusLabel, getStatusColor } from "@/lib/formatters";
import { History, TrendingUp, TrendingDown, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import Link from "next/link";

type SortKey = "confidence" | "entry" | "take_profit_1" | "stop_loss" | "pnl_pct" | "fired_at";
type SortDir = "asc" | "desc" | null;

function SortIcon({ dir }: { dir: SortDir }) {
  if (!dir) return <ArrowUpDown className="w-3.5 h-3.5 opacity-40" />;
  if (dir === "asc") return <ArrowUp className="w-3.5 h-3.5 text-purple" />;
  return <ArrowDown className="w-3.5 h-3.5 text-purple" />;
}

function SortTh({
  label, sortKey, current, dir, onSort, right,
}: {
  label: string; sortKey: SortKey; current: SortKey | null; dir: SortDir;
  onSort: (k: SortKey) => void; right?: boolean;
}) {
  return (
    <th
      className={`px-4 py-3 font-medium cursor-pointer select-none hover:text-text-primary transition-colors ${right ? "text-right" : ""}`}
      onClick={() => onSort(sortKey)}
    >
      <span className={`flex items-center gap-1 ${right ? "justify-end" : ""}`}>
        <span className="text-text-muted">{label}</span>
        <SortIcon dir={current === sortKey ? dir : null} />
      </span>
    </th>
  );
}

export default function HistoryPage() {
  const [direction, setDirection] = useState<string>("ALL");
  const [timeframe, setTimeframe] = useState<string>("ALL");
  const [page, setPage] = useState(1);
  const [sortKey, setSortKey] = useState<SortKey | null>("fired_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["signal-history", direction, timeframe, page],
    queryFn: () => api.get(`/api/v1/signals/history?days=90`).then((r) => r.data),
  });

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

  const total = signals.length;
  const wins = signals.filter((s) => s.status?.includes("tp")).length;
  const losses = signals.filter((s) => s.status === "sl_hit").length;
  const winRate = wins + losses > 0 ? Math.round((wins / (wins + losses)) * 100) : 0;

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      if (sortDir === "desc") setSortDir("asc");
      else if (sortDir === "asc") { setSortKey(null); setSortDir(null); }
      else setSortDir("desc");
    } else {
      setSortKey(key); setSortDir("desc");
    }
  };

  return (
    <div className="space-y-6 pb-20 lg:pb-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Signal History</h1>
        <p className="text-text-muted text-sm mt-1">All past signals with outcomes</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-surface border border-border rounded-xl p-4 text-center">
          <p className="text-2xl font-bold font-mono text-text-primary">{total}</p>
          <p className="text-xs text-text-muted mt-1">Total Signals</p>
        </div>
        <div className="bg-surface border border-long/20 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold font-mono text-long">{winRate}%</p>
          <p className="text-xs text-text-muted mt-1">Win Rate</p>
        </div>
        <div className="bg-surface border border-border rounded-xl p-4 text-center">
          <p className="text-2xl font-bold font-mono text-text-primary">{wins}</p>
          <p className="text-xs text-text-muted mt-1">TP Hits</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="flex items-center gap-1 bg-surface border border-border rounded-lg p-1">
          {["ALL", "LONG", "SHORT"].map((d) => (
            <button key={d} onClick={() => { setDirection(d); setPage(1); }}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-all ${
                direction === d
                  ? d === "LONG" ? "bg-long text-white" : d === "SHORT" ? "bg-short text-white" : "bg-purple text-white"
                  : "text-text-muted hover:text-text-primary"
              }`}>{d}</button>
          ))}
        </div>
        <div className="flex items-center gap-1 bg-surface border border-border rounded-lg p-1">
          {["ALL", "5m", "15m", "1H", "4H"].map((tf) => (
            <button key={tf} onClick={() => { setTimeframe(tf); setPage(1); }}
              className={`px-3 py-1.5 rounded text-sm transition-all ${
                timeframe === tf ? "bg-blue text-white" : "text-text-muted hover:text-text-primary"
              }`}>{tf}</button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">{Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="h-14 bg-surface border border-border rounded-lg animate-pulse" />
        ))}</div>
      ) : isError ? (
        <div className="bg-surface border border-border rounded-xl p-8 text-center text-text-muted">
          <p>Signal history requires a Pro subscription.</p>
          <Link href="/pricing" className="text-purple text-sm mt-2 block hover:underline">Upgrade to Pro →</Link>
        </div>
      ) : signals.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-text-muted">
          <History className="w-12 h-12 mb-4 opacity-30" /><p>No signals found</p>
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-surface-2">
                  <th className="text-left px-4 py-3 text-text-muted font-medium">Pair</th>
                  <th className="text-left px-4 py-3 text-text-muted font-medium">Dir</th>
                  <th className="text-left px-4 py-3 text-text-muted font-medium">TF</th>
                  <SortTh label="Conf" sortKey="confidence" current={sortKey} dir={sortDir} onSort={handleSort} right />
                  <SortTh label="Entry" sortKey="entry" current={sortKey} dir={sortDir} onSort={handleSort} right />
                  <SortTh label="TP1" sortKey="take_profit_1" current={sortKey} dir={sortDir} onSort={handleSort} right />
                  <SortTh label="SL" sortKey="stop_loss" current={sortKey} dir={sortDir} onSort={handleSort} right />
                  <th className="text-center px-4 py-3 text-text-muted font-medium">Status</th>
                  <SortTh label="PnL" sortKey="pnl_pct" current={sortKey} dir={sortDir} onSort={handleSort} right />
                  <SortTh label="Time" sortKey="fired_at" current={sortKey} dir={sortDir} onSort={handleSort} right />
                </tr>
              </thead>
              <tbody>
                {signals.map((signal, i) => {
                  const isLong = signal.direction === "LONG";
                  const pnlN = signal.pnl_pct != null ? parseFloat(String(signal.pnl_pct)) : null;
                  return (
                    <tr key={signal.id} className={`border-b border-border hover:bg-surface-2 transition-colors ${i % 2 === 0 ? "" : "bg-surface-2/30"}`}>
                      <td className="px-4 py-3">
                        <Link href={`/signal/${signal.id}`} className="font-mono font-semibold text-text-primary hover:text-purple">
                          {signal.symbol}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`flex items-center gap-1 text-xs font-medium ${isLong ? "text-long" : "text-short"}`}>
                          {isLong ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                          {signal.direction}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-text-muted">{signal.timeframe}</td>
                      <td className="px-4 py-3 text-right font-mono text-text-primary">{signal.confidence}</td>
                      <td className="px-4 py-3 text-right font-mono text-text-secondary">{formatPrice(signal.entry)}</td>
                      <td className="px-4 py-3 text-right font-mono text-long">{formatPrice(signal.take_profit_1)}</td>
                      <td className="px-4 py-3 text-right font-mono text-short">{formatPrice(signal.stop_loss)}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(signal.status)}`}>
                          {getStatusLabel(signal.status)}
                        </span>
                      </td>
                      <td className={`px-4 py-3 text-right font-mono text-sm ${pnlN != null && pnlN > 0 ? "text-long" : pnlN != null && pnlN < 0 ? "text-short" : "text-text-muted"}`}>
                        {pnlN != null ? `${pnlN > 0 ? "+" : ""}${pnlN.toFixed(2)}%` : "—"}
                      </td>
                      <td className="px-4 py-3 text-right text-text-muted text-xs">{formatTimeAgo(signal.fired_at)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 border-t border-border text-xs text-text-muted">
            Showing {signals.length} resolved signals (last 90 days) · Click column headers to sort
          </div>
        </div>
      )}
    </div>
  );
}
