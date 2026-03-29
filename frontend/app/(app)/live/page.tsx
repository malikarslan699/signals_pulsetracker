"use client";
import { useState } from "react";
import { Search, Radio } from "lucide-react";
import { LiveChart } from "@/components/charts/LiveChart";
import { Panel } from "@/components/terminal/Panel";

const QUICK_SYMBOLS = [
  "BTCUSDT",
  "ETHUSDT",
  "SOLUSDT",
  "BNBUSDT",
  "XRPUSDT",
  "ADAUSDT",
  "DOGEUSDT",
  "AVAXUSDT",
];

const TIMEFRAMES = ["5m", "15m", "1H", "4H", "1D"];

export default function LiveChartPage() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [inputValue, setInputValue] = useState("BTCUSDT");
  const [timeframe, setTimeframe] = useState("1H");

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
    <div className="space-y-3 pb-20 lg:pb-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-long/15 border border-long/25 flex items-center justify-center">
          <Radio className="w-4 h-4 text-long" />
        </div>
        <div>
          <h1 className="text-base font-bold text-text-primary leading-tight">Live Chart</h1>
          <p className="text-xs text-text-muted">Real-time candles · Auto-refresh 5s · Signal overlays</p>
        </div>
      </div>

      {/* Controls */}
      <Panel className="space-y-3">
        {/* Symbol Search */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted pointer-events-none" />
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value.toUpperCase())}
              placeholder="Symbol (e.g. BTCUSDT)"
              className="w-full pl-8 pr-3 py-2 text-sm bg-surface-2 border border-border rounded-lg
                text-text-primary placeholder:text-text-muted
                focus:outline-none focus:ring-1 focus:ring-long/50 focus:border-long/50"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 text-sm font-medium bg-long text-white rounded-lg hover:bg-long/90 transition-colors"
          >
            Go
          </button>
        </form>

        {/* Quick Symbols */}
        <div className="flex flex-wrap gap-1.5">
          {QUICK_SYMBOLS.map((s) => (
            <button
              key={s}
              onClick={() => handleQuickSymbol(s)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${
                symbol === s
                  ? "bg-long/15 border-long/30 text-long"
                  : "bg-surface-2 border-border text-text-muted hover:text-text-primary hover:border-border/80"
              }`}
            >
              {s.replace("USDT", "")}
            </button>
          ))}
        </div>

        {/* Timeframe Selector */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-text-muted mr-1">Timeframe:</span>
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${
                timeframe === tf
                  ? "bg-long/15 border-long/30 text-long"
                  : "bg-surface-2 border-border text-text-muted hover:text-text-primary"
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </Panel>

      {/* Chart */}
      <Panel>
        <div className="flex items-center justify-between mb-3">
          <div>
            <span className="font-bold text-text-primary text-sm">{symbol}</span>
            <span className="text-text-muted text-xs ml-2">· {timeframe}</span>
          </div>
          <span className="flex items-center gap-1.5 text-xs text-long">
            <span className="w-1.5 h-1.5 rounded-full bg-long animate-pulse" />
            LIVE
          </span>
        </div>
        <LiveChart symbol={symbol} timeframe={timeframe} height={520} />
      </Panel>
    </div>
  );
}
