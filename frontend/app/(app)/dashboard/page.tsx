"use client";
import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { RefreshCw, Zap } from "lucide-react";
import { useSignals } from "@/hooks/useSignals";
import { useScanner } from "@/hooks/useScanner";
import { SignalRow } from "@/components/signals/SignalRow";
import { ScannerStatus } from "@/components/scanner/ScannerStatus";
import { StatsRow } from "@/components/dashboard/StatsRow";
import { MarketHeatmap } from "@/components/dashboard/MarketHeatmap";
import { LiveTicker } from "@/components/layout/LiveTicker";
import { Panel } from "@/components/terminal/Panel";
import { FilterBar } from "@/components/terminal/FilterBar";

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const [filterDir, setFilterDir] = useState<"ALL" | "LONG" | "SHORT">("ALL");
  const [filterTf, setFilterTf] = useState<string>("ALL");
  const [search, setSearch] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);

  const { data: signals, isLoading, refetch } = useSignals({
    direction: filterDir === "ALL" ? undefined : filterDir,
    timeframe: filterTf === "ALL" ? undefined : filterTf,
    status: "active",
    min_confidence: 75,
    limit: 40,
  });

  const { data: scannerStatus } = useScanner();
  const filteredSignals = useMemo(() => {
    const rows = (signals?.signals || []).filter(
      (s) => String(s.status || "").toLowerCase() === "active"
    );
    if (!search.trim()) return rows;
    const q = search.trim().toUpperCase();
    return rows.filter((s) => s.symbol.toUpperCase().includes(q));
  }, [signals?.signals, search]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        refetch(),
        queryClient.invalidateQueries({ queryKey: ["platform-stats"] }),
        queryClient.invalidateQueries({ queryKey: ["scanner", "status"] }),
        queryClient.invalidateQueries({ queryKey: ["ticker-prices"] }),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="space-y-3 pb-20 lg:pb-6">
      <LiveTicker />

      <div className="space-y-2">
        <StatsRow />
        <ScannerStatus status={scannerStatus} />
      </div>

      <Panel
        title="Live Signals"
        actions={
          <button
            onClick={handleRefresh}
            className="p-1.5 rounded hover:bg-surface-2 text-text-muted hover:text-text-primary transition-colors"
            title="Refresh"
            disabled={isRefreshing}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
          </button>
        }
        noPad
      >
        <div className="px-3 py-2 border-b border-border">
          <FilterBar
            onSearch={setSearch}
            searchPlaceholder="Search symbol (e.g. BTC)"
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
                label: "Timeframe",
                options: [
                  { label: "All", value: "ALL" },
                  { label: "5m", value: "5m" },
                  { label: "15m", value: "15m" },
                  { label: "1H", value: "1H" },
                  { label: "4H", value: "4H" },
                ],
                value: filterTf,
                onChange: setFilterTf,
              },
            ]}
          />
        </div>

        <div className="overflow-x-auto">
          <div className="min-w-[980px]">
            <div className="grid grid-cols-[minmax(140px,1fr)_64px_48px_116px_86px_86px_86px_52px_78px_52px] items-center gap-2 px-3 py-1.5 bg-surface-2 border-b border-border text-[10px] font-semibold text-text-muted uppercase tracking-wider">
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
              <div className="divide-y divide-border/40">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="h-10 px-3 flex items-center gap-3 animate-pulse">
                    <div className="w-24 h-2 bg-surface-2 rounded" />
                    <div className="w-14 h-2 bg-surface-2 rounded" />
                    <div className="w-8 h-2 bg-surface-2 rounded" />
                    <div className="w-28 h-2 bg-surface-2 rounded" />
                    <div className="flex-1 h-2 bg-surface-2 rounded" />
                  </div>
                ))}
              </div>
            ) : filteredSignals.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-text-muted">
                <Zap className="w-8 h-8 mb-3 opacity-30" />
                <p className="text-sm font-medium">No signals found</p>
                <p className="text-xs mt-1">Adjust filters/search or wait for next scan</p>
              </div>
            ) : (
              <div>
                {filteredSignals.map((signal) => (
                  <SignalRow key={signal.id} signal={signal} />
                ))}
              </div>
            )}
          </div>
        </div>
      </Panel>

      <MarketHeatmap signals={signals?.signals || []} />
    </div>
  );
}
