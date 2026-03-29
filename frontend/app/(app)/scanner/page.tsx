"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, ExternalLink, Search, Star, Plus } from "lucide-react";
import { useSignals } from "@/hooks/useSignals";
import { useUserStore } from "@/store/userStore";
import { Signal } from "@/types/signal";
import { formatPrice, formatTimeAgo } from "@/lib/formatters";
import { ConfidenceBar } from "@/components/signals/ConfidenceBar";
import { DirectionBadge, ConfidenceBadge } from "@/components/terminal/Badges";
import { FilterBar } from "@/components/terminal/FilterBar";
import { Panel } from "@/components/terminal/Panel";
import { api } from "@/lib/api";

type SortField = "symbol" | "confidence" | "rr_tp1" | "fired_at" | "direction";
type SortDir = "asc" | "desc";
const FAVORITES_KEY = "scanner:favorites:v1";

interface PriceRow {
  symbol: string;
  price: number;
  change_pct: number;
}

interface AnalysisSnapshot {
  symbol: string;
  timeframe: string;
  overall_direction: "LONG" | "SHORT" | "NEUTRAL";
  confidence: number;
  signal_triggered: boolean;
  indicators?: {
    rsi_14?: number;
    adx?: number;
    macd_histogram?: number;
    volume_ratio?: number;
  };
}

interface SubscriptionPlan {
  id?: string;
  slug?: string;
  feature_flags?: {
    advanced_indicator_breakdown?: boolean;
  };
}

export default function ScannerPage() {
  const user = useUserStore((s) => s.user);
  const [search, setSearch] = useState("");
  const [filterDir, setFilterDir] = useState<"ALL" | "LONG" | "SHORT">("ALL");
  const [filterTf, setFilterTf] = useState("ALL");
  const [filterMarket, setFilterMarket] = useState("ALL");
  const [minConfidence, setMinConfidence] = useState(75);
  const [sortField, setSortField] = useState<SortField>("fired_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [watchTf, setWatchTf] = useState("1H");
  const [favorites, setFavorites] = useState<string[]>([]);
  const [favoriteInput, setFavoriteInput] = useState("");

  const { data: signalsData, isLoading } = useSignals({
    direction: filterDir === "ALL" ? undefined : filterDir,
    timeframe: filterTf === "ALL" ? undefined : filterTf,
    market: filterMarket === "ALL" ? undefined : filterMarket,
    min_confidence: minConfidence,
    limit: 100,
  });

  const signals = signalsData?.signals || [];

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = localStorage.getItem(FAVORITES_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        setFavorites(
          parsed
            .map((v) => String(v).trim().toUpperCase())
            .filter((v) => Boolean(v))
            .slice(0, 12)
        );
      }
    } catch {
      // ignore localStorage parsing issues
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
  }, [favorites]);

  const { data: liveSignalsPayload } = useQuery({
    queryKey: ["signals", "live", "all"],
    queryFn: async () => {
      const res = await api.get<{ signals: Signal[] }>(
        "/api/v1/signals/live?min_confidence=75"
      );
      return res.data;
    },
    refetchInterval: 10_000,
  });

  const { data: plansPayload } = useQuery<{ plans?: SubscriptionPlan[] }>({
    queryKey: ["subscription-plans"],
    queryFn: async () => {
      const res = await api.get<{ plans?: SubscriptionPlan[] }>("/api/v1/subscriptions/plans");
      return res.data;
    },
    staleTime: 60_000,
  });

  const { data: favoritePrices = [] } = useQuery<PriceRow[]>({
    queryKey: ["favorite-prices", favorites],
    queryFn: async () => {
      if (!favorites.length) return [];
      const symbols = encodeURIComponent(favorites.join(","));
      const res = await api.get<PriceRow[]>(`/api/v1/pairs/prices?symbols=${symbols}`);
      return res.data;
    },
    enabled: favorites.length > 0,
    refetchInterval: 5_000,
  });

  const liveBySymbol = useMemo(() => {
    const m = new Map<string, Signal>();
    for (const s of liveSignalsPayload?.signals || []) {
      const key = s.symbol.toUpperCase();
      const existing = m.get(key);
      const candidate = s.pwin_tp1 ?? s.confidence;
      const existingScore = existing ? (existing.pwin_tp1 ?? existing.confidence) : -1;
      if (!existing || candidate > existingScore) {
        m.set(key, s);
      }
    }
    return m;
  }, [liveSignalsPayload?.signals]);

  const priceBySymbol = useMemo(() => {
    const m = new Map<string, PriceRow>();
    for (const row of favoritePrices) {
      m.set(row.symbol.toUpperCase(), row);
    }
    return m;
  }, [favoritePrices]);

  const canSeeIndicators = useMemo(() => {
    if (!user) return false;
    if (["admin", "owner", "superadmin"].includes(user.role)) return true;
    const plans = plansPayload?.plans || [];
    const activePlan = plans.find(
      (p) => (p.id || p.slug || "").toLowerCase() === user.plan.toLowerCase()
    );
    if (activePlan?.feature_flags) {
      return Boolean(activePlan.feature_flags.advanced_indicator_breakdown);
    }
    return ["monthly", "yearly", "lifetime"].includes(user.plan);
  }, [plansPayload?.plans, user]);

  const { data: favoriteAnalyses = {} } = useQuery<Record<string, AnalysisSnapshot | null>>({
    queryKey: ["favorite-analyses", favorites, watchTf, canSeeIndicators],
    queryFn: async () => {
      if (!canSeeIndicators || !favorites.length) return {};
      const symbols = favorites.slice(0, 6);
      const rows = await Promise.all(
        symbols.map(async (sym) => {
          try {
            const res = await api.get<AnalysisSnapshot>(
              `/api/v1/pairs/${encodeURIComponent(sym)}/analysis?timeframe=${encodeURIComponent(watchTf)}`
            );
            return [sym, res.data] as const;
          } catch {
            return [sym, null] as const;
          }
        })
      );
      return Object.fromEntries(rows);
    },
    enabled: favorites.length > 0 && canSeeIndicators,
    refetchInterval: 30_000,
  });

  const fmt = (n?: number, digits = 1) =>
    typeof n === "number" && Number.isFinite(n) ? n.toFixed(digits) : "—";

  const toggleFavorite = (symbol: string) => {
    const normalized = symbol.trim().toUpperCase();
    setFavorites((prev) =>
      prev.includes(normalized)
        ? prev.filter((s) => s !== normalized)
        : [...prev, normalized].slice(0, 12)
    );
  };

  const addFavoriteFromInput = () => {
    const normalized = favoriteInput.trim().toUpperCase();
    if (!normalized) return;
    if (!/^[A-Z0-9]{3,15}$/.test(normalized)) return;
    if (favorites.includes(normalized)) {
      setFavoriteInput("");
      return;
    }
    setFavorites((prev) => [...prev, normalized].slice(0, 12));
    setFavoriteInput("");
  };

  const filteredSorted = useMemo(() => {
    const bestByKey = new Map<string, Signal>();
    for (const s of signals) {
      const key = `${s.symbol}:${s.direction}:${s.timeframe}`;
      const existing = bestByKey.get(key);
      const candidate = s.pwin_tp1 ?? s.confidence;
      const existingScore = existing ? (existing.pwin_tp1 ?? existing.confidence) : -1;
      if (!existing || candidate > existingScore) {
        bestByKey.set(key, s);
      }
    }

    let result = Array.from(bestByKey.values()).filter((s) =>
      search ? s.symbol.toLowerCase().includes(search.toLowerCase()) : true
    );

    result = [...result].sort((a, b) => {
      let aVal: string | number =
        sortField === "rr_tp1"
          ? a.rr_tp1 ?? -1
          : sortField === "confidence"
            ? a.pwin_tp1 ?? a.confidence
            : (a[sortField] as string | number);
      let bVal: string | number =
        sortField === "rr_tp1"
          ? b.rr_tp1 ?? -1
          : sortField === "confidence"
            ? b.pwin_tp1 ?? b.confidence
            : (b[sortField] as string | number);
      if (typeof aVal === "string") aVal = aVal.toLowerCase();
      if (typeof bVal === "string") bVal = bVal.toLowerCase();
      if (aVal < bVal) return sortDir === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDir === "asc" ? 1 : -1;
      return 0;
    });

    return result;
  }, [signals, search, sortField, sortDir]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((p) => (p === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <ChevronUp className="w-3 h-3 opacity-30" />;
    return sortDir === "asc" ? <ChevronUp className="w-3 h-3 text-long" /> : <ChevronDown className="w-3 h-3 text-long" />;
  };

  return (
    <div className="space-y-3 pb-20 lg:pb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-semibold text-text-primary">Scanner</h1>
          <span className="text-xs text-text-muted font-mono">{filteredSorted.length} signals</span>
        </div>
      </div>

      <Panel title="Favorites Watchlist">
        <div className="space-y-2">
          <div className="flex flex-col md:flex-row md:items-center gap-2">
            <input
              type="text"
              value={favoriteInput}
              onChange={(e) => setFavoriteInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addFavoriteFromInput();
                }
              }}
              placeholder="Add symbol (e.g. BTCUSDT)"
              className="h-8 w-full max-w-xs bg-surface-2 border border-border rounded px-2.5 text-xs text-text-primary focus:outline-none focus:border-long"
            />
            <button
              onClick={addFavoriteFromInput}
              className="h-8 px-2.5 rounded bg-surface-2 border border-border text-xs text-text-muted hover:text-text-primary inline-flex items-center gap-1"
            >
              <Plus className="w-3 h-3" />
              Add
            </button>
            <div className="inline-flex items-center gap-1">
              {["15m", "1H", "4H"].map((tf) => (
                <button
                  key={tf}
                  onClick={() => setWatchTf(tf)}
                  className={`filter-pill ${watchTf === tf ? "filter-pill-active" : ""}`}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>

          {favorites.length === 0 ? (
            <p className="text-xs text-text-muted">
              Add favorite coins to monitor live price and latest active signal confirmation.
            </p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
              {favorites.map((symbol) => {
                const p = priceBySymbol.get(symbol);
                const s = liveBySymbol.get(symbol);
                const a = favoriteAnalyses[symbol];
                const activeProbability = s ? (s.pwin_tp1 ?? s.confidence) : null;
                const hasAnalysisAttempt = Object.prototype.hasOwnProperty.call(favoriteAnalyses, symbol);
                return (
                  <div
                    key={symbol}
                    className="border border-border rounded-lg px-2.5 py-2 bg-surface-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-semibold text-text-primary">
                        {symbol}
                      </span>
                      <button
                        onClick={() => toggleFavorite(symbol)}
                        className="text-text-muted hover:text-gold"
                        title="Remove favorite"
                      >
                        <Star className="w-3.5 h-3.5 fill-gold text-gold" />
                      </button>
                    </div>
                    <div className="mt-1 text-xs">
                      <span className="text-text-secondary font-mono">
                        {p ? formatPrice(p.price) : "—"}
                      </span>
                      <span
                        className={`ml-2 font-mono ${
                          (p?.change_pct || 0) >= 0 ? "text-long" : "text-short"
                        }`}
                      >
                        {p ? `${p.change_pct >= 0 ? "+" : ""}${p.change_pct.toFixed(2)}%` : ""}
                      </span>
                    </div>
                    <div className="mt-1 text-[11px] text-text-muted">
                      {s ? (
                        <span>
                          Active setup: <span className={s.direction === "LONG" ? "text-long" : "text-short"}>{s.direction}</span>{" "}
                          {s.timeframe} · P(TP1) {activeProbability}%
                        </span>
                      ) : (
                        <span>No active setup yet</span>
                      )}
                    </div>
                    <div className="mt-1 text-[11px] text-text-muted">
                      {!canSeeIndicators ? (
                        <span>Indicator panel: monthly/yearly/lifetime required</span>
                      ) : a ? (
                        <span>
                          Indicators ({watchTf}): {a.overall_direction} · Setup {a.confidence}/100 · RSI {fmt(a.indicators?.rsi_14)} · ADX{" "}
                          {fmt(a.indicators?.adx)} · Vol x{fmt(a.indicators?.volume_ratio, 2)}
                        </span>
                      ) : hasAnalysisAttempt ? (
                        <span>Indicator snapshot unavailable for this symbol</span>
                      ) : favorites.indexOf(symbol) >= 6 ? (
                        <span>Indicator panel tracks first 6 favorites to keep it real-time</span>
                      ) : (
                        <span>Indicators loading...</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </Panel>

      <Panel noPad>
        <div className="px-3 py-2 border-b border-border space-y-2">
          <FilterBar
            onSearch={setSearch}
            searchPlaceholder="Search pair..."
            showAdvanced={filtersOpen}
            onAdvancedToggle={() => setFiltersOpen((p) => !p)}
            segments={[
              {
                label: "Direction",
                options: [
                  { label: "All", value: "ALL" },
                  { label: "Long", value: "LONG" },
                  { label: "Short", value: "SHORT" },
                ],
                value: filterDir,
                onChange: (v) => setFilterDir(v as "ALL" | "LONG" | "SHORT"),
              },
              {
                label: "Market",
                options: [
                  { label: "All", value: "ALL" },
                  { label: "Crypto", value: "crypto" },
                  { label: "Forex", value: "forex" },
                ],
                value: filterMarket,
                onChange: setFilterMarket,
              },
            ]}
          />

          {filtersOpen && (
            <div className="bg-surface-2 border border-border rounded-lg p-3 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-text-muted mb-1.5 block">Timeframe</label>
                <div className="flex flex-wrap gap-1">
                  {["ALL", "15m", "1H", "4H"].map((tf) => (
                    <button
                      key={tf}
                      onClick={() => setFilterTf(tf)}
                      className={`filter-pill ${filterTf === tf ? "filter-pill-active" : ""}`}
                    >
                      {tf}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs text-text-muted mb-1.5 block">
                  Min P(TP1): <span className="font-mono text-long">{minConfidence}%</span>
                </label>
                <input
                  type="range"
                  min={0}
                  max={100}
                  step={5}
                  value={minConfidence}
                  onChange={(e) => setMinConfidence(Number(e.target.value))}
                  className="w-full accent-long"
                />
                <div className="flex justify-between text-[10px] text-text-faint mt-0.5">
                  <span>0</span>
                  <span>50</span>
                  <span>100</span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="overflow-x-auto">
          <div className="min-w-[1080px]">
            <div className="grid grid-cols-[minmax(150px,1fr)_68px_48px_120px_92px_92px_92px_58px_62px_76px] items-center gap-2 px-3 py-1.5 bg-surface-2 border-b border-border text-[10px] font-semibold text-text-muted uppercase tracking-wider">
              <button onClick={() => handleSort("symbol")} className="flex items-center gap-1 text-left hover:text-text-primary">Pair <SortIcon field="symbol" /></button>
              <button onClick={() => handleSort("direction")} className="flex items-center gap-1 hover:text-text-primary">Dir <SortIcon field="direction" /></button>
              <span>TF</span>
              <button onClick={() => handleSort("confidence")} className="flex items-center gap-1 hover:text-text-primary">P(TP1) <SortIcon field="confidence" /></button>
              <span className="text-right">Entry</span>
              <span className="text-right">SL</span>
              <span className="text-right">TP1</span>
              <button onClick={() => handleSort("rr_tp1")} className="flex items-center justify-end gap-1 hover:text-text-primary text-right">RR1 <SortIcon field="rr_tp1" /></button>
              <button onClick={() => handleSort("fired_at")} className="flex items-center justify-end gap-1 hover:text-text-primary text-right">Age <SortIcon field="fired_at" /></button>
              <span className="text-right">Details</span>
            </div>

            <div>
              {isLoading
                ? Array.from({ length: 10 }).map((_, i) => (
                    <div key={i} className="h-10 border-b border-border px-3 flex items-center gap-2 animate-pulse">
                      <div className="w-28 h-2 bg-surface-2 rounded" />
                      <div className="w-16 h-2 bg-surface-2 rounded" />
                      <div className="w-10 h-2 bg-surface-2 rounded" />
                      <div className="w-28 h-2 bg-surface-2 rounded" />
                    </div>
                  ))
                : filteredSorted.map((signal) => {
                    const probability = signal.pwin_tp1 ?? signal.confidence;
                    return (
                      <div key={signal.id} className="data-row grid grid-cols-[minmax(150px,1fr)_68px_48px_120px_92px_92px_92px_58px_62px_76px] items-center gap-2 px-3 py-2 border-b border-border text-xs font-mono">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => toggleFavorite(signal.symbol)}
                            title={favorites.includes(signal.symbol.toUpperCase()) ? "Remove favorite" : "Add to favorites"}
                            className="text-text-faint hover:text-gold transition-colors"
                          >
                            <Star
                              className={`w-3.5 h-3.5 ${
                                favorites.includes(signal.symbol.toUpperCase())
                                  ? "fill-gold text-gold"
                                  : ""
                              }`}
                            />
                          </button>
                          <span className="font-semibold text-text-primary">{signal.symbol}</span>
                          <span className="text-[10px] px-1.5 py-0.5 bg-surface-2 rounded text-text-muted capitalize">{signal.market}</span>
                        </div>

                        <DirectionBadge direction={signal.direction} />

                        <span className="text-[10px] text-text-muted">{signal.timeframe}</span>

                        <div className="flex items-center gap-2 min-w-0">
                          <div className="flex-1 min-w-[56px]"><ConfidenceBar value={probability} showLabel={false} /></div>
                          <ConfidenceBadge value={probability} className="w-8 text-right" />
                        </div>

                        <span className="text-right text-text-secondary">{formatPrice(signal.entry)}</span>
                        <span className="text-right text-short">{formatPrice(signal.stop_loss)}</span>
                        <span className="text-right text-long">{formatPrice(signal.take_profit_1)}</span>
                        <span className="text-right text-text-secondary">
                          {signal.rr_tp1 != null ? `${signal.rr_tp1}:1` : "—"}
                        </span>
                        <span className="text-right text-text-muted text-[10px]">{formatTimeAgo(signal.fired_at)}</span>

                        <div className="text-right">
                          <Link href={`/signal/${signal.id}`}>
                            <button className="inline-flex items-center gap-1 px-2 py-1 bg-surface-2 border border-border rounded text-[10px] text-text-muted hover:text-text-primary hover:border-long transition-colors">
                              <ExternalLink className="w-3 h-3" />
                              View
                            </button>
                          </Link>
                        </div>
                      </div>
                    );
                  })}
            </div>

            {!isLoading && filteredSorted.length === 0 && (
              <div className="flex flex-col items-center justify-center py-16 text-text-muted">
                <Search className="w-10 h-10 mb-3 opacity-30" />
                <p className="font-medium">No signals match your filters</p>
                <p className="text-sm mt-1">Try adjusting filters. New scans refresh every 10 minutes.</p>
              </div>
            )}
          </div>
        </div>
      </Panel>
    </div>
  );
}
