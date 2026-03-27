"use client";
import { useSignals } from "@/hooks/useSignals";
import { useScanner } from "@/hooks/useScanner";
import { SignalCard } from "@/components/signals/SignalCard";
import { ScannerStatus } from "@/components/scanner/ScannerStatus";
import { StatsRow } from "@/components/dashboard/StatsRow";
import { MarketHeatmap } from "@/components/dashboard/MarketHeatmap";
import { LiveTicker } from "@/components/layout/LiveTicker";
import { RefreshCw, Zap } from "lucide-react";
import { useState } from "react";

export default function DashboardPage() {
  const [filterDir, setFilterDir] = useState<"ALL" | "LONG" | "SHORT">("ALL");
  const [filterTf, setFilterTf] = useState<string>("ALL");

  const { data: signals, isLoading, refetch } = useSignals({
    direction: filterDir === "ALL" ? undefined : filterDir,
    timeframe: filterTf === "ALL" ? undefined : filterTf,
    min_confidence: 75,
    limit: 30,
  });

  const { data: scannerStatus } = useScanner();

  const filteredSignals = signals?.signals || [];

  return (
    <div className="space-y-6 pb-20 lg:pb-6">
      {/* Live Ticker */}
      <LiveTicker />

      {/* Stats Row */}
      <StatsRow />

      {/* Scanner Status Bar */}
      <ScannerStatus status={scannerStatus} />

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1 bg-surface rounded-lg p-1 border border-border">
          {["ALL", "LONG", "SHORT"].map((dir) => (
            <button
              key={dir}
              onClick={() => setFilterDir(dir as "ALL" | "LONG" | "SHORT")}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
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
          {["ALL", "5m", "15m", "1H", "4H"].map((tf) => (
            <button
              key={tf}
              onClick={() => setFilterTf(tf)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                filterTf === tf
                  ? "bg-blue text-white"
                  : "text-text-muted hover:text-text-primary"
              }`}
            >
              {tf}
            </button>
          ))}
        </div>

        <button
          onClick={() => refetch()}
          className="ml-auto flex items-center gap-2 px-4 py-2 bg-surface border border-border rounded-lg text-sm text-text-secondary hover:text-text-primary transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Signal Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 9 }).map((_, i) => (
            <div
              key={i}
              className="h-48 bg-surface border border-border rounded-xl animate-pulse"
            />
          ))}
        </div>
      ) : filteredSignals.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-text-muted">
          <Zap className="w-12 h-12 mb-4 opacity-30" />
          <p className="text-lg font-medium">No signals found</p>
          <p className="text-sm mt-1">Adjust filters or wait for next scan</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredSignals.map((signal) => (
            <SignalCard key={signal.id} signal={signal} />
          ))}
        </div>
      )}

      {/* Market Heatmap */}
      <MarketHeatmap signals={signals?.signals || []} />
    </div>
  );
}
