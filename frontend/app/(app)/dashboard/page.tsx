"use client";
import { useSignals } from "@/hooks/useSignals";
import { useScanner } from "@/hooks/useScanner";
import { SignalRow } from "@/components/signals/SignalRow";
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
    min_confidence: 78,
    limit: 30,
  });

  const { data: scannerStatus } = useScanner();

  const filteredSignals = signals?.signals || [];

  return (
    <div className="space-y-3 pb-20 lg:pb-6">
      {/* Live Ticker */}
      <LiveTicker />

      {/* Stats + Scanner in one compact block */}
      <div className="space-y-1.5">
        <StatsRow />
        <ScannerStatus status={scannerStatus} />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-0.5 bg-surface rounded-md p-0.5 border border-border">
          {["ALL", "LONG", "SHORT"].map((dir) => (
            <button
              key={dir}
              onClick={() => setFilterDir(dir as "ALL" | "LONG" | "SHORT")}
              className={`px-3 py-1 rounded text-xs font-medium transition-all ${
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

        <div className="flex items-center gap-0.5 bg-surface rounded-md p-0.5 border border-border">
          {["ALL", "5m", "15m", "1H", "4H"].map((tf) => (
            <button
              key={tf}
              onClick={() => setFilterTf(tf)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
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
          className="ml-auto flex items-center gap-1.5 px-3 py-1 bg-surface border border-border rounded-md text-xs text-text-secondary hover:text-text-primary transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
          Refresh
        </button>
      </div>

      {/* Signal Table */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        {/* Table header */}
        <div className="flex items-center gap-0 px-3 py-1.5 bg-surface-2 border-b border-border text-[10px] font-mono font-semibold text-text-muted uppercase tracking-wider">
          <div className="w-5 shrink-0" />
          <div className="w-28 shrink-0">Symbol</div>
          <div className="w-20 shrink-0">Dir / TF</div>
          <div className="w-28 shrink-0">Confidence</div>
          <div className="flex-1 px-3">Entry · SL · TP1</div>
          <div className="w-12 shrink-0 text-right">RR</div>
          <div className="w-8 shrink-0 text-center">St</div>
          <div className="w-16 shrink-0 text-right">Age</div>
        </div>

        {isLoading ? (
          <div className="divide-y divide-border/40">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-9 px-3 flex items-center gap-3 animate-pulse">
                <div className="w-5 h-2 bg-surface-2 rounded" />
                <div className="w-24 h-2 bg-surface-2 rounded" />
                <div className="w-16 h-2 bg-surface-2 rounded" />
                <div className="flex-1 h-2 bg-surface-2 rounded" />
              </div>
            ))}
          </div>
        ) : filteredSignals.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-text-muted">
            <Zap className="w-8 h-8 mb-3 opacity-30" />
            <p className="text-sm font-medium">No signals found</p>
            <p className="text-xs mt-1">Adjust filters or wait for next scan</p>
          </div>
        ) : (
          <div>
            {filteredSignals.map((signal) => (
              <SignalRow key={signal.id} signal={signal} />
            ))}
          </div>
        )}
      </div>

      {/* Market Heatmap */}
      <MarketHeatmap signals={signals?.signals || []} />
    </div>
  );
}
