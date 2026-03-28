"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatTimeAgo, getStatusColor, getStatusLabel } from "@/lib/formatters";
import {
  FlaskConical, TrendingUp, TrendingDown, CheckCircle2, XCircle,
  AlertTriangle, BarChart3, Search, ChevronDown, ChevronRight,
  Shield, Zap, Activity
} from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

// ── Types ─────────────────────────────────────────────────────────────────
interface QASignal {
  id: string;
  symbol: string;
  market: string;
  direction: string;
  timeframe: string;
  confidence: number;
  setup_score?: number | null;
  pwin_tp1?: number | null;
  pwin_tp2?: number | null;
  ranking_score?: number | null;
  status: string;
  pnl_pct: number | null;
  fired_at: string;
  entry: number;
  stop_loss: number;
  take_profit_1: number;
  rr_ratio: number;
  qa: {
    why_generated: string;
    confirmations_present: string[];
    confirmations_missing: string[];
    triggered_indicators: string[];
    aligned_tfs: string[];
    conflicting_tfs: string[];
    tf_5m_confirmed: boolean;
    tf_15m_confirmed: boolean;
    tf_1h_confirmed: boolean;
    tf_4h_confirmed: boolean;
    category_scores: Record<string, { score: number; max: number; pct: number; triggered: number; total: number }>;
    strength_assessment: string;
    risk_assessment: string;
    outcome_summary: string;
    confirmation_count: number;
    missing_count: number;
  };
}

interface QAStats {
  days: number;
  overall: {
    total: number; wins: number; losses: number; expired: number;
    active: number; avg_confidence: number; avg_rr: number; win_rate: number | null;
  };
  by_timeframe: Array<{ timeframe: string; total: number; wins: number; losses: number; avg_confidence: number; win_rate: number | null }>;
  by_market: Array<{ market: string; total: number; wins: number; losses: number; win_rate: number | null }>;
  by_direction: Array<{ direction: string; total: number; wins: number; losses: number; avg_pnl: number; win_rate: number | null }>;
  noisy_pairs: Array<{ symbol: string; signal_count: number; avg_confidence: number; wins: number; losses: number; win_rate: number | null }>;
  confidence_bands: Array<{ band: string; count: number; wins: number; losses: number; win_rate: number | null }>;
  confidence_deciles: Array<{ decile: string; total: number; wins: number; losses: number; avg_pwin_tp1: number; avg_pwin_tp2: number; win_rate: number | null }>;
  confidence_vs_win_rate: Array<{ decile: string; total: number; wins: number; losses: number; avg_pwin_tp1: number; avg_pwin_tp2: number; win_rate: number | null }>;
  indicator_performance: Array<{ indicator: string; count: number; wins: number; losses: number; win_rate: number | null; quality_bias: number }>;
  pair_health: Array<{
    symbol: string;
    market: string;
    total_closed: number;
    wins: number;
    losses: number;
    win_rate: number | null;
    avg_pwin_tp1: number;
    avg_pnl: number;
    health_score: number;
    health_status: string;
    auto_disabled: boolean;
    manual_override: boolean;
    disable_reason?: string | null;
  }>;
}

// ── Signal Row ─────────────────────────────────────────────────────────────
function SignalQARow({ signal }: { signal: QASignal }) {
  const [expanded, setExpanded] = useState(false);
  const isLong = signal.direction === "LONG";
  const qa = signal.qa;

  const statusColors: Record<string, string> = {
    active: "text-blue-400", tp1_hit: "text-emerald-400", tp2_hit: "text-emerald-500",
    tp3_hit: "text-emerald-600", sl_hit: "text-red-400", expired: "text-gray-400",
  };

  const tfBadge = (label: string, ok: boolean) => (
    <span key={label} className={`text-xs px-1.5 py-0.5 rounded font-mono ${ok ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/10 text-red-400/60"}`}>
      {label} {ok ? "✓" : "✗"}
    </span>
  );

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 bg-surface hover:bg-surface-2 transition-colors text-left"
      >
        <div className="flex-shrink-0">
          {expanded ? <ChevronDown className="w-4 h-4 text-text-muted" /> : <ChevronRight className="w-4 h-4 text-text-muted" />}
        </div>
        <span className="font-mono font-bold text-text-primary w-24">{signal.symbol}</span>
        <span className={`text-xs font-bold w-12 ${isLong ? "text-long" : "text-short"}`}>
          {isLong ? "↑ LONG" : "↓ SHORT"}
        </span>
        <span className="text-xs bg-surface-2 px-2 py-0.5 rounded text-text-muted w-10">{signal.timeframe}</span>
        <div className="w-20 leading-tight">
          <span className="block font-mono text-sm text-text-primary">{signal.pwin_tp1 ?? signal.confidence}</span>
          <span className="block text-[10px] text-text-faint">S{signal.setup_score ?? "—"}</span>
        </div>
        <span className={`text-xs w-20 ${statusColors[signal.status] || "text-text-muted"}`}>
          {getStatusLabel(signal.status)}
        </span>
        <span className={`text-xs font-mono w-16 ${signal.pnl_pct != null && signal.pnl_pct > 0 ? "text-long" : signal.pnl_pct != null && signal.pnl_pct < 0 ? "text-short" : "text-text-muted"}`}>
          {signal.pnl_pct != null ? `${signal.pnl_pct > 0 ? "+" : ""}${signal.pnl_pct.toFixed(2)}%` : "—"}
        </span>
        <div className="flex gap-1 ml-2">
          {tfBadge("5m", qa.tf_5m_confirmed)}
          {tfBadge("15m", qa.tf_15m_confirmed)}
          {tfBadge("1H", qa.tf_1h_confirmed)}
          {tfBadge("4H", qa.tf_4h_confirmed)}
        </div>
        <span className="text-xs text-text-muted ml-auto">{formatTimeAgo(signal.fired_at)}</span>
      </button>

      {expanded && (
        <div className="border-t border-border bg-surface-2/50 px-4 py-4 space-y-4">
          {/* Why Generated */}
          <div className="bg-surface border border-border rounded-lg px-4 py-3">
            <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">Why Generated</p>
            <p className="text-sm text-text-secondary">{qa.why_generated}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Confirmations */}
            <div>
              <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">Confirmations ({qa.confirmation_count}/{qa.confirmation_count + qa.missing_count})</p>
              <div className="space-y-1">
                {qa.confirmations_present.map((c) => (
                  <div key={c} className="flex items-center gap-2 text-xs text-emerald-400">
                    <CheckCircle2 className="w-3 h-3 flex-shrink-0" />{c}
                  </div>
                ))}
                {qa.confirmations_missing.map((c) => (
                  <div key={c} className="flex items-center gap-2 text-xs text-text-faint">
                    <XCircle className="w-3 h-3 flex-shrink-0" />{c}
                  </div>
                ))}
              </div>
            </div>

            {/* Category Scores */}
            <div>
              <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">Category Scores</p>
              <div className="space-y-1.5">
                {Object.entries(qa.category_scores).map(([cat, data]) => (
                  <div key={cat}>
                    <div className="flex justify-between text-xs mb-0.5">
                      <span className="text-text-secondary">{cat}</span>
                      <span className={`font-mono ${data.pct >= 50 ? "text-emerald-400" : "text-text-muted"}`}>{data.pct}%</span>
                    </div>
                    <div className="h-1 bg-surface rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${data.pct >= 70 ? "bg-emerald-500" : data.pct >= 50 ? "bg-yellow-500" : "bg-red-500/50"}`}
                        style={{ width: `${data.pct}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Assessment row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="bg-surface border border-border rounded-lg px-3 py-2">
              <p className="text-xs text-text-muted mb-1">Strength</p>
              <p className="text-xs text-text-secondary">{qa.strength_assessment}</p>
            </div>
            <div className="bg-surface border border-border rounded-lg px-3 py-2">
              <p className="text-xs text-text-muted mb-1">Risk</p>
              <p className="text-xs text-text-secondary">{qa.risk_assessment}</p>
            </div>
            <div className="bg-surface border border-border rounded-lg px-3 py-2">
              <p className="text-xs text-text-muted mb-1">Outcome</p>
              <p className="text-xs text-text-secondary">{qa.outcome_summary}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-1">
            <Link href={`/signal/${signal.id}`}
              className="text-xs px-3 py-1.5 bg-purple/10 border border-purple/30 text-purple rounded-lg hover:bg-purple/20 transition-colors">
              View Signal Detail →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Stats Card ─────────────────────────────────────────────────────────────
function StatCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div className="bg-surface border border-border rounded-xl p-4">
      <p className="text-xs text-text-muted mb-1">{label}</p>
      <p className={`text-2xl font-bold font-mono ${color || "text-text-primary"}`}>{value}</p>
      {sub && <p className="text-xs text-text-muted mt-1">{sub}</p>}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────
export default function QALabPage() {
  const [days, setDays] = useState(7);
  const [filterStatus, setFilterStatus] = useState("ALL");
  const [filterTf, setFilterTf] = useState("ALL");
  const [filterMarket, setFilterMarket] = useState("ALL");
  const [activeTab, setActiveTab] = useState<"signals" | "stats" | "noisy" | "failures">("signals");
  const queryClient = useQueryClient();

  const { data: logData, isLoading: logLoading } = useQuery({
    queryKey: ["qa-log", days, filterStatus, filterTf, filterMarket],
    queryFn: () => api.get("/api/v1/admin/qa/signal-log", {
      params: {
        days,
        limit: 100,
        ...(filterStatus !== "ALL" && { status: filterStatus }),
        ...(filterTf !== "ALL" && { timeframe: filterTf }),
        ...(filterMarket !== "ALL" && { market: filterMarket }),
      }
    }).then((r) => r.data),
  });

  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ["qa-stats", days],
    queryFn: () => api.get("/api/v1/admin/qa/stats", { params: { days } }).then((r) => r.data),
  });

  const { data: failureData, isLoading: failureLoading } = useQuery({
    queryKey: ["qa-failures", days],
    queryFn: () => api.get("/api/v1/admin/qa/failure-analysis", { params: { days } }).then((r) => r.data),
    enabled: activeTab === "failures",
  });

  const signals: QASignal[] = logData?.signals || [];
  const stats: QAStats | null = statsData || null;

  const overrideMutation = useMutation({
    mutationFn: async ({ symbol, enabled }: { symbol: string; enabled: boolean }) => {
      const res = await api.patch(`/api/v1/admin/qa/pair-health/${symbol}/override`, null, {
        params: { enabled },
      });
      return res.data;
    },
    onSuccess: (data) => {
      toast.success(`${data.symbol} override ${data.manual_override ? "enabled" : "disabled"}.`);
      queryClient.invalidateQueries({ queryKey: ["qa-stats"] });
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || "Override update failed.");
    },
  });

  const winRate = (wins: number, losses: number) =>
    wins + losses > 0 ? `${Math.round((wins / (wins + losses)) * 100)}%` : "—";

  return (
    <div className="space-y-6 pb-20 lg:pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple/10 border border-purple/20 rounded-lg">
            <FlaskConical className="w-5 h-5 text-purple" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-text-primary">QA Lab</h2>
            <p className="text-sm text-text-muted">Internal signal research & quality testing</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {[3, 7, 14, 30].map((d) => (
            <button key={d} onClick={() => setDays(d)}
              className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${days === d ? "bg-purple text-white border-purple" : "bg-surface border-border text-text-muted hover:text-text-primary"}`}>
              {d}d
            </button>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border">
        {(["signals", "stats", "noisy", "failures"] as const).map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors capitalize ${activeTab === tab ? "border-purple text-purple" : "border-transparent text-text-muted hover:text-text-primary"}`}>
            {tab === "signals" ? "Signal Log" : tab === "stats" ? "QA Stats" : tab === "noisy" ? "Noisy Pairs" : "Failure Analysis"}
          </button>
        ))}
      </div>

      {/* ── TAB: Signal Log ───────────────────────────────────────────────── */}
      {activeTab === "signals" && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-2">
            {["ALL", "active", "tp1_hit", "tp2_hit", "sl_hit", "expired"].map((s) => (
              <button key={s} onClick={() => setFilterStatus(s)}
                className={`px-3 py-1 text-xs rounded-lg border transition-all ${filterStatus === s ? "bg-purple text-white border-purple" : "bg-surface border-border text-text-muted"}`}>
                {s === "ALL" ? "All Status" : getStatusLabel(s)}
              </button>
            ))}
            <div className="ml-auto flex gap-2">
              {["ALL", "5m", "15m", "1H", "4H"].map((tf) => (
                <button key={tf} onClick={() => setFilterTf(tf)}
                  className={`px-2.5 py-1 text-xs rounded border transition-all ${filterTf === tf ? "bg-blue text-white border-blue" : "bg-surface border-border text-text-muted"}`}>
                  {tf}
                </button>
              ))}
              {["ALL", "crypto", "forex"].map((m) => (
                <button key={m} onClick={() => setFilterMarket(m)}
                  className={`px-2.5 py-1 text-xs rounded border transition-all capitalize ${filterMarket === m ? "bg-surface-2 text-text-primary border-purple" : "bg-surface border-border text-text-muted"}`}>
                  {m}
                </button>
              ))}
            </div>
          </div>

          {/* Column headers */}
          <div className="flex items-center gap-3 px-4 py-2 text-xs text-text-faint font-medium">
            <span className="w-5" />
            <span className="w-24">Pair</span>
            <span className="w-12">Dir</span>
            <span className="w-10">TF</span>
            <span className="w-20">P(TP1)</span>
            <span className="w-20">Status</span>
            <span className="w-16">PnL</span>
            <span>TF Alignment</span>
            <span className="ml-auto">Time</span>
          </div>

          {logLoading ? (
            <div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-12 bg-surface border border-border rounded-lg animate-pulse" />
            ))}</div>
          ) : signals.length === 0 ? (
            <div className="flex flex-col items-center py-16 text-text-muted">
              <FlaskConical className="w-10 h-10 mb-3 opacity-30" />
              <p>No signals found for selected filters</p>
            </div>
          ) : (
            <div className="space-y-2">
              {signals.map((sig) => <SignalQARow key={sig.id} signal={sig} />)}
            </div>
          )}
          <p className="text-xs text-text-faint text-center">{signals.length} signals · last {days} days · click row to expand QA breakdown</p>
        </div>
      )}

      {/* ── TAB: QA Stats ────────────────────────────────────────────────── */}
      {activeTab === "stats" && (
        <div className="space-y-6">
          {statsLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-24 bg-surface border border-border rounded-xl animate-pulse" />
            ))}</div>
          ) : stats ? (
            <>
              {/* Overall */}
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
                <StatCard label="Total Signals" value={stats.overall.total} />
                <StatCard label="Win Rate" value={winRate(stats.overall.wins, stats.overall.losses)} color="text-long" />
                <StatCard label="Wins (TP Hit)" value={stats.overall.wins} color="text-long" />
                <StatCard label="Losses (SL)" value={stats.overall.losses} color="text-short" />
                <StatCard label="Expired" value={stats.overall.expired} color="text-text-muted" />
                <StatCard label="Avg Confidence" value={`${stats.overall.avg_confidence ?? "—"}%`} />
                <StatCard label="Avg R/R" value={`${stats.overall.avg_rr ?? "—"}R`} />
              </div>

              {/* By Timeframe */}
              <div className="bg-surface border border-border rounded-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-border">
                  <p className="text-sm font-semibold text-text-primary flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-purple" /> Performance by Timeframe
                  </p>
                </div>
                <table className="w-full text-sm">
                  <thead><tr className="bg-surface-2 border-b border-border text-xs text-text-muted">
                    <th className="px-4 py-2 text-left">TF</th>
                    <th className="px-4 py-2 text-right">Signals</th>
                    <th className="px-4 py-2 text-right">Wins</th>
                    <th className="px-4 py-2 text-right">Losses</th>
                    <th className="px-4 py-2 text-right">Win Rate</th>
                    <th className="px-4 py-2 text-right">Avg Conf</th>
                  </tr></thead>
                  <tbody>
                    {stats.by_timeframe.map((row) => (
                      <tr key={row.timeframe} className="border-b border-border hover:bg-surface-2">
                        <td className="px-4 py-2 font-mono text-text-primary">{row.timeframe}</td>
                        <td className="px-4 py-2 text-right text-text-secondary">{row.total}</td>
                        <td className="px-4 py-2 text-right text-long">{row.wins}</td>
                        <td className="px-4 py-2 text-right text-short">{row.losses}</td>
                        <td className="px-4 py-2 text-right font-mono">
                          <span className={row.win_rate != null && row.win_rate >= 50 ? "text-long" : "text-short"}>
                            {row.win_rate != null ? `${row.win_rate}%` : "—"}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right font-mono text-text-muted">{row.avg_confidence}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Confidence bands */}
              <div className="bg-surface border border-border rounded-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-border">
                  <p className="text-sm font-semibold text-text-primary flex items-center gap-2">
                    <Zap className="w-4 h-4 text-purple" /> Confidence Band Distribution
                  </p>
                </div>
                <table className="w-full text-sm">
                  <thead><tr className="bg-surface-2 border-b border-border text-xs text-text-muted">
                    <th className="px-4 py-2 text-left">Band</th>
                    <th className="px-4 py-2 text-right">Count</th>
                    <th className="px-4 py-2 text-right">Wins</th>
                    <th className="px-4 py-2 text-right">Losses</th>
                    <th className="px-4 py-2 text-right">Win Rate</th>
                  </tr></thead>
                  <tbody>
                    {stats.confidence_bands.map((row) => (
                      <tr key={row.band} className="border-b border-border hover:bg-surface-2">
                        <td className="px-4 py-2 text-text-primary text-xs">{row.band}</td>
                        <td className="px-4 py-2 text-right text-text-secondary">{row.count}</td>
                        <td className="px-4 py-2 text-right text-long">{row.wins}</td>
                        <td className="px-4 py-2 text-right text-short">{row.losses}</td>
                        <td className="px-4 py-2 text-right font-mono">
                          <span className={row.win_rate != null && row.win_rate >= 50 ? "text-long" : "text-short"}>
                            {row.win_rate != null ? `${row.win_rate}%` : "—"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                <div className="bg-surface border border-border rounded-xl overflow-hidden">
                  <div className="px-4 py-3 border-b border-border">
                    <p className="text-sm font-semibold text-text-primary">Confidence Deciles</p>
                    <p className="text-xs text-text-muted mt-0.5">Calibrated TP1 probability grouped into deciles</p>
                  </div>
                  <table className="w-full text-sm">
                    <thead><tr className="bg-surface-2 border-b border-border text-xs text-text-muted">
                      <th className="px-4 py-2 text-left">Decile</th>
                      <th className="px-4 py-2 text-right">Signals</th>
                      <th className="px-4 py-2 text-right">Win Rate</th>
                      <th className="px-4 py-2 text-right">Avg P1</th>
                      <th className="px-4 py-2 text-right">Avg P2</th>
                    </tr></thead>
                    <tbody>
                      {stats.confidence_deciles.map((row) => (
                        <tr key={row.decile} className="border-b border-border hover:bg-surface-2">
                          <td className="px-4 py-2 font-mono text-text-primary">{row.decile}</td>
                          <td className="px-4 py-2 text-right text-text-secondary">{row.total}</td>
                          <td className="px-4 py-2 text-right font-mono">
                            <span className={row.win_rate != null && row.win_rate >= 50 ? "text-long" : "text-short"}>
                              {row.win_rate != null ? `${row.win_rate}%` : "—"}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-right font-mono text-blue">{row.avg_pwin_tp1 ?? "—"}%</td>
                          <td className="px-4 py-2 text-right font-mono text-long">{row.avg_pwin_tp2 ?? "—"}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="bg-surface border border-border rounded-xl overflow-hidden">
                  <div className="px-4 py-3 border-b border-border">
                    <p className="text-sm font-semibold text-text-primary">Indicator Performance Visibility</p>
                    <p className="text-xs text-text-muted mt-0.5">Triggered indicators ranked by outcome quality</p>
                  </div>
                  <table className="w-full text-sm">
                    <thead><tr className="bg-surface-2 border-b border-border text-xs text-text-muted">
                      <th className="px-4 py-2 text-left">Indicator</th>
                      <th className="px-4 py-2 text-right">Count</th>
                      <th className="px-4 py-2 text-right">Win Rate</th>
                      <th className="px-4 py-2 text-right">Bias</th>
                    </tr></thead>
                    <tbody>
                      {stats.indicator_performance.slice(0, 12).map((row) => (
                        <tr key={row.indicator} className="border-b border-border hover:bg-surface-2">
                          <td className="px-4 py-2 text-text-primary text-xs font-mono">{row.indicator}</td>
                          <td className="px-4 py-2 text-right text-text-secondary">{row.count}</td>
                          <td className="px-4 py-2 text-right font-mono">
                            <span className={row.win_rate != null && row.win_rate >= 50 ? "text-long" : "text-short"}>
                              {row.win_rate != null ? `${row.win_rate}%` : "—"}
                            </span>
                          </td>
                          <td className={`px-4 py-2 text-right font-mono ${row.quality_bias >= 0 ? "text-long" : "text-short"}`}>
                            {row.quality_bias > 0 ? "+" : ""}{row.quality_bias}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* ── TAB: Noisy Pairs ──────────────────────────────────────────────── */}
      {activeTab === "noisy" && (
        <div className="space-y-4">
          {statsLoading ? (
            <div className="h-64 bg-surface border border-border rounded-xl animate-pulse" />
          ) : stats ? (
            <div className="space-y-4">
              <div className="bg-surface border border-border rounded-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-border">
                  <p className="text-sm font-semibold text-text-primary flex items-center gap-2">
                    <Activity className="w-4 h-4 text-short" /> Most Active Pairs (last {days}d) — sorted by signal volume
                  </p>
                  <p className="text-xs text-text-muted mt-0.5">High count + low win rate = noisy pair needing tighter filters</p>
                </div>
                <table className="w-full text-sm">
                  <thead><tr className="bg-surface-2 border-b border-border text-xs text-text-muted">
                    <th className="px-4 py-2 text-left">Pair</th>
                    <th className="px-4 py-2 text-right">Signals</th>
                    <th className="px-4 py-2 text-right">Wins</th>
                    <th className="px-4 py-2 text-right">Losses</th>
                    <th className="px-4 py-2 text-right">Win Rate</th>
                    <th className="px-4 py-2 text-right">Avg Conf</th>
                    <th className="px-4 py-2 text-right">Verdict</th>
                  </tr></thead>
                  <tbody>
                    {stats.noisy_pairs.map((row) => {
                      const wr = row.win_rate;
                      const isNoisy = row.signal_count >= 5 && (wr == null || wr < 40);
                      const isGood = row.signal_count >= 3 && wr != null && wr >= 60;
                      return (
                        <tr key={row.symbol} className="border-b border-border hover:bg-surface-2">
                          <td className="px-4 py-2 font-mono font-bold text-text-primary">{row.symbol}</td>
                          <td className="px-4 py-2 text-right font-mono">{row.signal_count}</td>
                          <td className="px-4 py-2 text-right text-long">{row.wins}</td>
                          <td className="px-4 py-2 text-right text-short">{row.losses}</td>
                          <td className="px-4 py-2 text-right font-mono">
                            <span className={wr != null && wr >= 50 ? "text-long" : "text-short"}>
                              {wr != null ? `${wr}%` : "—"}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-right text-text-muted">{row.avg_confidence}%</td>
                          <td className="px-4 py-2 text-right">
                            {isNoisy && <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-short">Noisy</span>}
                            {isGood && <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-long">Strong</span>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="bg-surface border border-border rounded-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-border">
                  <p className="text-sm font-semibold text-text-primary">Pair Health & Auto-Filtering</p>
                  <p className="text-xs text-text-muted mt-0.5">Admin override keeps a pair tradable even when auto-filtering would disable it.</p>
                </div>
                <table className="w-full text-sm">
                  <thead><tr className="bg-surface-2 border-b border-border text-xs text-text-muted">
                    <th className="px-4 py-2 text-left">Pair</th>
                    <th className="px-4 py-2 text-right">Health</th>
                    <th className="px-4 py-2 text-right">Win Rate</th>
                    <th className="px-4 py-2 text-right">Avg P(TP1)</th>
                    <th className="px-4 py-2 text-right">State</th>
                    <th className="px-4 py-2 text-right">Override</th>
                  </tr></thead>
                  <tbody>
                    {stats.pair_health.slice(0, 20).map((row) => (
                      <tr key={row.symbol} className="border-b border-border hover:bg-surface-2">
                        <td className="px-4 py-2">
                          <div className="font-mono font-bold text-text-primary">{row.symbol}</div>
                          {row.disable_reason && (
                            <div className="text-[10px] text-text-faint mt-0.5">{row.disable_reason}</div>
                          )}
                        </td>
                        <td className="px-4 py-2 text-right font-mono text-text-primary">{row.health_score}</td>
                        <td className="px-4 py-2 text-right font-mono">
                          <span className={row.win_rate != null && row.win_rate >= 50 ? "text-long" : "text-short"}>
                            {row.win_rate != null ? `${row.win_rate}%` : "—"}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right font-mono text-blue">{row.avg_pwin_tp1 ? `${row.avg_pwin_tp1}%` : "—"}</td>
                        <td className="px-4 py-2 text-right">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${
                            row.health_status === "healthy" ? "bg-emerald-500/10 text-long" :
                            row.health_status === "disabled" ? "bg-red-500/10 text-short" :
                            row.health_status === "weak" ? "bg-yellow-500/10 text-yellow-400" :
                            "bg-surface-2 text-text-muted"
                          }`}>
                            {row.health_status}{row.auto_disabled ? " · auto-off" : ""}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right">
                          <button
                            onClick={() => overrideMutation.mutate({ symbol: row.symbol, enabled: !row.manual_override })}
                            className={`text-xs px-2 py-1 rounded border ${
                              row.manual_override
                                ? "bg-blue/10 text-blue border-blue/20"
                                : "bg-surface-2 text-text-muted border-border"
                            }`}
                            disabled={overrideMutation.isPending}
                          >
                            {row.manual_override ? "Forced On" : "Auto"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* ── TAB: Failure Analysis ─────────────────────────────────────────── */}
      {activeTab === "failures" && (
        <div className="space-y-6">
          {failureLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-24 bg-surface border border-border rounded-xl animate-pulse" />
            ))}</div>
          ) : failureData ? (
            <>
              {/* Summary banners */}
              {failureData.summary?.noisy_indicators?.length > 0 && (
                <div className="bg-short/5 border border-short/20 rounded-xl p-4">
                  <p className="text-sm font-semibold text-short mb-2 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" /> Noisy Indicators (appear more in losses than wins)
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {failureData.summary.noisy_indicators.map((ind: string) => (
                      <span key={ind} className="text-xs px-2 py-0.5 bg-short/10 text-short rounded-full font-mono">{ind}</span>
                    ))}
                  </div>
                </div>
              )}
              {failureData.summary?.reliable_indicators?.length > 0 && (
                <div className="bg-long/5 border border-long/20 rounded-xl p-4">
                  <p className="text-sm font-semibold text-long mb-2 flex items-center gap-2">
                    <Shield className="w-4 h-4" /> Reliable Indicators (appear more in wins)
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {failureData.summary.reliable_indicators.map((ind: string) => (
                      <span key={ind} className="text-xs px-2 py-0.5 bg-long/10 text-long rounded-full font-mono">{ind}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Direction bias */}
              <div className="grid grid-cols-2 gap-4">
                {failureData.direction_bias?.map((row: any) => {
                  const wr = row.win_rate;
                  const isLong = row.direction === "LONG";
                  return (
                    <div key={row.direction} className={`bg-surface border ${isLong ? "border-long/20" : "border-short/20"} rounded-xl p-4`}>
                      <p className={`text-sm font-bold ${isLong ? "text-long" : "text-short"} mb-2`}>
                        {isLong ? "↑ LONG" : "↓ SHORT"} signals
                      </p>
                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div><p className="text-lg font-bold font-mono text-long">{row.tp_hits}</p><p className="text-xs text-text-muted">TP Hits</p></div>
                        <div><p className="text-lg font-bold font-mono text-short">{row.sl_hits}</p><p className="text-xs text-text-muted">SL Hits</p></div>
                        <div>
                          <p className={`text-lg font-bold font-mono ${wr != null && wr >= 50 ? "text-long" : "text-short"}`}>{wr != null ? `${wr}%` : "—"}</p>
                          <p className="text-xs text-text-muted">Win Rate</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* SL hits by timeframe */}
              <div className="bg-surface border border-border rounded-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-border">
                  <p className="text-sm font-semibold text-text-primary flex items-center gap-2">
                    <TrendingDown className="w-4 h-4 text-short" /> SL Hits by Timeframe
                  </p>
                </div>
                <table className="w-full text-sm">
                  <thead><tr className="bg-surface-2 border-b border-border text-xs text-text-muted">
                    <th className="px-4 py-2 text-left">TF</th>
                    <th className="px-4 py-2 text-right">TP Hits</th>
                    <th className="px-4 py-2 text-right">SL Hits</th>
                    <th className="px-4 py-2 text-right">Win Rate</th>
                    <th className="px-4 py-2 text-right">Avg Conf Win</th>
                    <th className="px-4 py-2 text-right">Avg Conf Loss</th>
                  </tr></thead>
                  <tbody>
                    {failureData.sl_by_timeframe?.map((row: any) => (
                      <tr key={row.timeframe} className="border-b border-border hover:bg-surface-2">
                        <td className="px-4 py-2 font-mono font-bold text-text-primary">{row.timeframe}</td>
                        <td className="px-4 py-2 text-right text-long">{row.tp_hits ?? 0}</td>
                        <td className="px-4 py-2 text-right text-short">{row.sl_hits ?? 0}</td>
                        <td className="px-4 py-2 text-right font-mono">
                          <span className={row.win_rate != null && row.win_rate >= 50 ? "text-long" : "text-short"}>
                            {row.win_rate != null ? `${row.win_rate}%` : "—"}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right font-mono text-text-muted">{row.avg_conf_win ?? "—"}</td>
                        <td className="px-4 py-2 text-right font-mono text-text-muted">{row.avg_conf_loss ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Indicator noise analysis */}
              <div className="bg-surface border border-border rounded-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-border">
                  <p className="text-sm font-semibold text-text-primary flex items-center gap-2">
                    <Search className="w-4 h-4 text-purple" /> Indicator Noise Analysis
                  </p>
                  <p className="text-xs text-text-muted mt-0.5">Noise score = % in losses − % in wins. Positive = found more in losing trades.</p>
                </div>
                <table className="w-full text-sm">
                  <thead><tr className="bg-surface-2 border-b border-border text-xs text-text-muted">
                    <th className="px-4 py-2 text-left">Indicator</th>
                    <th className="px-4 py-2 text-right">In Losses %</th>
                    <th className="px-4 py-2 text-right">In Wins %</th>
                    <th className="px-4 py-2 text-right">Noise Score</th>
                    <th className="px-4 py-2 text-right">Assessment</th>
                  </tr></thead>
                  <tbody>
                    {failureData.indicator_noise_analysis?.map((row: any) => (
                      <tr key={row.indicator} className="border-b border-border hover:bg-surface-2">
                        <td className="px-4 py-2 font-mono text-text-primary text-xs">{row.indicator}</td>
                        <td className="px-4 py-2 text-right font-mono text-short text-xs">{row.in_losses_pct}%</td>
                        <td className="px-4 py-2 text-right font-mono text-long text-xs">{row.in_wins_pct}%</td>
                        <td className={`px-4 py-2 text-right font-mono font-bold text-xs ${row.noise_score > 5 ? "text-short" : row.noise_score < -5 ? "text-long" : "text-text-muted"}`}>
                          {row.noise_score > 0 ? "+" : ""}{row.noise_score}
                        </td>
                        <td className="px-4 py-2 text-right">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${
                            row.assessment === "noisy" ? "bg-short/10 text-short" :
                            row.assessment === "reliable" ? "bg-long/10 text-long" :
                            "bg-surface-2 text-text-muted"
                          }`}>{row.assessment}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Overconfident losses */}
              {failureData.overconfident_losses?.length > 0 && (
                <div className="bg-surface border border-short/20 rounded-xl overflow-hidden">
                  <div className="px-4 py-3 border-b border-border">
                    <p className="text-sm font-semibold text-short flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" /> High-Confidence Losses (conf ≥85 but SL hit)
                    </p>
                  </div>
                  <table className="w-full text-sm">
                    <thead><tr className="bg-surface-2 border-b border-border text-xs text-text-muted">
                      <th className="px-4 py-2 text-left">Pair</th>
                      <th className="px-4 py-2">Dir</th>
                      <th className="px-4 py-2">TF</th>
                      <th className="px-4 py-2 text-right">Conf</th>
                      <th className="px-4 py-2 text-right">R:R</th>
                      <th className="px-4 py-2 text-right">PnL</th>
                      <th className="px-4 py-2 text-right">Held (hrs)</th>
                    </tr></thead>
                    <tbody>
                      {failureData.overconfident_losses.map((row: any, i: number) => (
                        <tr key={i} className="border-b border-border hover:bg-surface-2">
                          <td className="px-4 py-2 font-mono font-bold text-text-primary">{row.symbol}</td>
                          <td className="px-4 py-2 text-center">
                            <span className={`text-xs font-bold ${row.direction === "LONG" ? "text-long" : "text-short"}`}>{row.direction}</span>
                          </td>
                          <td className="px-4 py-2 text-center text-text-muted text-xs">{row.timeframe}</td>
                          <td className="px-4 py-2 text-right font-mono text-short">{row.confidence}</td>
                          <td className="px-4 py-2 text-right font-mono text-text-secondary">{row.rr_ratio}R</td>
                          <td className="px-4 py-2 text-right font-mono text-short">{row.pnl_pct != null ? `${Number(row.pnl_pct).toFixed(2)}%` : "—"}</td>
                          <td className="px-4 py-2 text-right font-mono text-text-muted">{row.hours_held != null ? Number(row.hours_held).toFixed(1) : "—"}h</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}
