"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Radio } from "lucide-react";
import { LiveChart } from "@/components/charts/LiveChart";
import { SignalDetailPanel } from "@/components/live/SignalDetailPanel";
import { Panel } from "@/components/terminal/Panel";
import { api } from "@/lib/api";
import { Signal, SignalsResponse } from "@/types/signal";

const QUICK_SYMBOLS = [
  "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
  "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT",
];

const TIMEFRAMES = ["5m", "15m", "1H", "4H", "1D"];

const OPEN_STATUSES = new Set(["CREATED", "ARMED", "FILLED", "TP1_REACHED"]);

export default function LiveChartPage() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [inputValue, setInputValue] = useState("BTCUSDT");
  const [timeframe, setTimeframe] = useState("1H");

  // Fetch active signal for selected symbol (right sidebar)
  const { data: activeSignal, isLoading: signalLoading } = useQuery<Signal | null>({
    queryKey: ["live-signal-sidebar", symbol],
    queryFn: async () => {
      const res = await api.get<SignalsResponse>(
        `/api/v1/signals/?symbol=${encodeURIComponent(symbol)}&limit=5`
      );
      const items: Signal[] = res.data?.signals || (res.data as any)?.items || [];
      return items.find((s) => OPEN_STATUSES.has(s.status)) ?? null;
    },
    refetchInterval: 15_000,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim().toUpperCase();
    if (trimmed) setSymbol(trimmed);
  };

  const handleQuickSymbol = (s: string) => {
    setSymbol(s);
    setInputValue(s);
  };

  return (
    <div className="flex flex-col gap-3 pb-20 lg:pb-4 h-full">
      {/* Header row */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-long/15 border border-long/25 flex items-center justify-center flex-shrink-0">
          <Radio className="w-4 h-4 text-long" />
        </div>
        <div>
          <h1 className="text-base font-bold text-text-primary leading-tight">Live Chart</h1>
          <p className="text-xs text-text-muted">Real-time candles · 5s refresh · Signal overlays</p>
        </div>
      </div>

      {/* Controls bar */}
      <Panel className="py-2.5">
        <div className="flex flex-col sm:flex-row sm:items-center gap-2">
          {/* Symbol search */}
          <form onSubmit={handleSearch} className="flex gap-2 flex-shrink-0">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted pointer-events-none" />
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value.toUpperCase())}
                placeholder="BTCUSDT"
                className="w-32 pl-7 pr-2 py-1.5 text-sm bg-surface-2 border border-border rounded-lg
                  text-text-primary placeholder:text-text-muted
                  focus:outline-none focus:ring-1 focus:ring-long/50 focus:border-long/50"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-1.5 text-sm font-medium bg-long text-white rounded-lg hover:bg-long/90 transition-colors"
            >
              Go
            </button>
          </form>

          {/* Quick symbols */}
          <div className="flex flex-wrap gap-1">
            {QUICK_SYMBOLS.map((s) => (
              <button
                key={s}
                onClick={() => handleQuickSymbol(s)}
                className={`px-2 py-1 rounded-md text-[11px] font-medium border transition-all ${
                  symbol === s
                    ? "bg-long/15 border-long/30 text-long"
                    : "bg-surface-2 border-border text-text-muted hover:text-text-primary"
                }`}
              >
                {s.replace("USDT", "")}
              </button>
            ))}
          </div>

          {/* Timeframe */}
          <div className="flex items-center gap-1 ml-auto">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-semibold border transition-all ${
                  timeframe === tf
                    ? "bg-long/15 border-long/30 text-long"
                    : "bg-surface-2 border-border text-text-muted hover:text-text-primary"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
      </Panel>

      {/* Main content: chart (left 70%) + signal panel (right 30%) */}
      <div className="flex flex-col lg:flex-row gap-3 flex-1 min-h-0">
        {/* Chart column */}
        <div className="flex-1 min-w-0">
          <Panel className="h-full">
            {/* Chart header */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-bold text-text-primary">{symbol}</span>
                <span className="text-text-muted text-xs">· {timeframe}</span>
              </div>
              <span className="flex items-center gap-1.5 text-xs text-long">
                <span className="w-1.5 h-1.5 rounded-full bg-long animate-pulse" />
                LIVE
              </span>
            </div>
            <LiveChart symbol={symbol} timeframe={timeframe} height={500} />
          </Panel>
        </div>

        {/* Right sidebar — Signal Detail Panel */}
        <div className="w-full lg:w-64 xl:w-72 flex-shrink-0">
          <Panel className="h-full lg:min-h-[580px]">
            <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-3">
              Active Signal
            </p>
            <SignalDetailPanel signal={activeSignal ?? null} loading={signalLoading} />
          </Panel>
        </div>
      </div>
    </div>
  );
}
