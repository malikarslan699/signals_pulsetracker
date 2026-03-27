"use client";
import { useState, useMemo } from "react";
import { useSignals } from "@/hooks/useSignals";
import { Signal } from "@/types/signal";
import {
  Search,
  TrendingUp,
  TrendingDown,
  ChevronUp,
  ChevronDown,
  ExternalLink,
  Filter,
  SlidersHorizontal,
} from "lucide-react";
import { formatPrice, formatTimeAgo, confidenceBandColor } from "@/lib/formatters";
import Link from "next/link";
import { ConfidenceBar } from "@/components/signals/ConfidenceBar";

type SortField = "symbol" | "confidence" | "rr_ratio" | "fired_at" | "direction";
type SortDir = "asc" | "desc";

export default function ScannerPage() {
  const [search, setSearch] = useState("");
  const [filterDir, setFilterDir] = useState<"ALL" | "LONG" | "SHORT">("ALL");
  const [filterTf, setFilterTf] = useState("ALL");
  const [filterMarket, setFilterMarket] = useState("ALL");
  const [minConfidence, setMinConfidence] = useState(75);
  const [sortField, setSortField] = useState<SortField>("fired_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [filtersOpen, setFiltersOpen] = useState(false);

  const { data: signalsData, isLoading } = useSignals({
    direction: filterDir === "ALL" ? undefined : filterDir,
    timeframe: filterTf === "ALL" ? undefined : filterTf,
    market: filterMarket === "ALL" ? undefined : filterMarket,
    min_confidence: minConfidence,
    limit: 100,
  });

  const signals = signalsData?.signals || [];

  const filteredSorted = useMemo(() => {
    // Deduplicate: keep only the highest-confidence signal per symbol+direction+timeframe
    const bestByKey = new Map<string, Signal>();
    for (const s of signals) {
      const key = `${s.symbol}:${s.direction}:${s.timeframe}`;
      const existing = bestByKey.get(key);
      if (!existing || s.confidence > existing.confidence) {
        bestByKey.set(key, s);
      }
    }
    let result = Array.from(bestByKey.values()).filter((s: Signal) =>
      search ? s.symbol.toLowerCase().includes(search.toLowerCase()) : true
    );

    result = [...result].sort((a: Signal, b: Signal) => {
      let aVal: string | number = a[sortField] as string | number;
      let bVal: string | number = b[sortField] as string | number;
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
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field)
      return <ChevronUp className="w-3 h-3 opacity-30" />;
    return sortDir === "asc" ? (
      <ChevronUp className="w-3 h-3 text-purple" />
    ) : (
      <ChevronDown className="w-3 h-3 text-purple" />
    );
  };

  return (
    <div className="space-y-5 pb-20 lg:pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Scanner</h1>
          <p className="text-sm text-text-muted mt-0.5">
            {filteredSorted.length} signals found
          </p>
        </div>
        <button
          onClick={() => setFiltersOpen(!filtersOpen)}
          className="flex items-center gap-2 px-4 py-2 bg-surface border border-border rounded-lg text-sm text-text-secondary hover:text-text-primary transition-colors"
        >
          <SlidersHorizontal className="w-4 h-4" />
          Filters
        </button>
      </div>

      {/* Search + Quick Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search pair (BTC, ETH...)"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-surface border border-border rounded-lg text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-purple transition-colors"
          />
        </div>

        <div className="flex items-center gap-1 bg-surface rounded-lg p-1 border border-border">
          {["ALL", "LONG", "SHORT"].map((dir) => (
            <button
              key={dir}
              onClick={() => setFilterDir(dir as "ALL" | "LONG" | "SHORT")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                filterDir === dir
                  ? dir === "LONG"
                    ? "bg-long text-white"
                    : dir === "SHORT"
                    ? "bg-short text-white"
                    : "bg-purple text-white"
                  : "text-text-muted hover:text-text-primary"
              }`}
            >
              {dir}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1 bg-surface rounded-lg p-1 border border-border">
          {["ALL", "crypto", "forex"].map((m) => (
            <button
              key={m}
              onClick={() => setFilterMarket(m)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all capitalize ${
                filterMarket === m
                  ? "bg-blue text-white"
                  : "text-text-muted hover:text-text-primary"
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {/* Advanced Filters Panel */}
      {filtersOpen && (
        <div className="bg-surface border border-border rounded-xl p-4 space-y-4">
          <div className="flex items-center gap-2 text-sm font-medium text-text-secondary mb-3">
            <Filter className="w-4 h-4" />
            Advanced Filters
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Timeframe */}
            <div>
              <label className="text-xs text-text-muted mb-1.5 block">Timeframe</label>
              <div className="flex flex-wrap gap-1">
                {["ALL", "5m", "15m", "30m", "1H", "4H", "1D"].map((tf) => (
                  <button
                    key={tf}
                    onClick={() => setFilterTf(tf)}
                    className={`px-2 py-1 rounded text-xs font-medium transition-all ${
                      filterTf === tf
                        ? "bg-blue text-white"
                        : "bg-surface-2 text-text-muted hover:text-text-primary"
                    }`}
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </div>

            {/* Min Confidence */}
            <div className="col-span-2">
              <label className="text-xs text-text-muted mb-1.5 block">
                Min Confidence:{" "}
                <span className="font-mono text-purple">{minConfidence}</span>
              </label>
              <input
                type="range"
                min={0}
                max={100}
                step={5}
                value={minConfidence}
                onChange={(e) => setMinConfidence(Number(e.target.value))}
                className="w-full accent-purple"
              />
              <div className="flex justify-between text-xs text-text-faint mt-0.5">
                <span>0</span>
                <span>50</span>
                <span>100</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-surface-2">
                <th
                  className="text-left px-4 py-3 text-xs font-medium text-text-muted cursor-pointer hover:text-text-primary"
                  onClick={() => handleSort("symbol")}
                >
                  <div className="flex items-center gap-1">
                    Pair <SortIcon field="symbol" />
                  </div>
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-text-muted">
                  Entry
                </th>
                <th
                  className="text-left px-4 py-3 text-xs font-medium text-text-muted cursor-pointer hover:text-text-primary"
                  onClick={() => handleSort("direction")}
                >
                  <div className="flex items-center gap-1">
                    Signal <SortIcon field="direction" />
                  </div>
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-text-muted">
                  TF
                </th>
                <th
                  className="text-left px-4 py-3 text-xs font-medium text-text-muted cursor-pointer hover:text-text-primary min-w-32"
                  onClick={() => handleSort("confidence")}
                >
                  <div className="flex items-center gap-1">
                    Confidence <SortIcon field="confidence" />
                  </div>
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-text-muted">
                  Entry
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-text-muted">
                  SL
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-text-muted">
                  TP1
                </th>
                <th
                  className="text-left px-4 py-3 text-xs font-medium text-text-muted cursor-pointer hover:text-text-primary"
                  onClick={() => handleSort("rr_ratio")}
                >
                  <div className="flex items-center gap-1">
                    R:R <SortIcon field="rr_ratio" />
                  </div>
                </th>
                <th
                  className="text-left px-4 py-3 text-xs font-medium text-text-muted cursor-pointer hover:text-text-primary"
                  onClick={() => handleSort("fired_at")}
                >
                  <div className="flex items-center gap-1">
                    Time <SortIcon field="fired_at" />
                  </div>
                </th>
                <th className="text-right px-4 py-3 text-xs font-medium text-text-muted">
                  Details
                </th>
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? Array.from({ length: 10 }).map((_, i) => (
                    <tr key={i} className="border-b border-border">
                      {Array.from({ length: 11 }).map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <div className="h-4 bg-surface-2 rounded animate-pulse" />
                        </td>
                      ))}
                    </tr>
                  ))
                : filteredSorted.map((signal: Signal) => {
                    const isLong = signal.direction === "LONG";
                    return (
                      <tr
                        key={signal.id}
                        className={`border-b border-border hover:bg-surface-2 transition-colors ${
                          isLong ? "row-long" : "row-short"
                        }`}
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-text-primary">
                              {signal.symbol}
                            </span>
                            <span className="text-xs px-1.5 py-0.5 bg-surface-2 rounded text-text-muted capitalize">
                              {signal.market}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div
                            className={`flex items-center gap-1 font-bold text-sm ${
                              isLong ? "text-long" : "text-short"
                            }`}
                          >
                            {isLong ? (
                              <TrendingUp className="w-3.5 h-3.5" />
                            ) : (
                              <TrendingDown className="w-3.5 h-3.5" />
                            )}
                            {signal.direction}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-xs px-2 py-0.5 bg-surface-2 rounded-full text-text-muted">
                            {signal.timeframe}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2 min-w-28">
                            <div className="flex-1">
                              <ConfidenceBar
                                value={signal.confidence}
                                direction={signal.direction}
                              />
                            </div>
                            <span
                              className="text-xs font-mono font-bold w-8 text-right"
                              style={{
                                color: confidenceBandColor(signal.confidence),
                              }}
                            >
                              {signal.confidence}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 font-mono text-text-secondary text-xs">
                          {formatPrice(signal.entry)}
                        </td>
                        <td className="px-4 py-3 font-mono text-short text-xs">
                          {formatPrice(signal.stop_loss)}
                        </td>
                        <td className="px-4 py-3 font-mono text-long text-xs">
                          {formatPrice(signal.take_profit_1)}
                        </td>
                        <td className="px-4 py-3 font-mono text-text-secondary text-xs">
                          {signal.rr_ratio}:1
                        </td>
                        <td className="px-4 py-3 text-text-muted text-xs">
                          {formatTimeAgo(signal.fired_at)}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <Link href={`/signal/${signal.id}`}>
                            <button className="flex items-center gap-1 ml-auto px-3 py-1 bg-surface-2 border border-border rounded-md text-xs text-text-muted hover:text-text-primary hover:border-purple transition-colors">
                              <ExternalLink className="w-3 h-3" />
                              View
                            </button>
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
            </tbody>
          </table>
        </div>

        {!isLoading && filteredSorted.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-text-muted">
            <Search className="w-10 h-10 mb-3 opacity-30" />
            <p className="font-medium">No signals match your filters</p>
            <p className="text-sm mt-1">Try adjusting the filters above</p>
          </div>
        )}
      </div>
    </div>
  );
}
