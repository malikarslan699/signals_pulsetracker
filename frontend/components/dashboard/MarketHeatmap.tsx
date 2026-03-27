"use client";
import { Signal } from "@/types/signal";

interface MarketHeatmapProps {
  signals: Signal[];
}

export function MarketHeatmap({ signals }: MarketHeatmapProps) {
  if (!signals || signals.length === 0) {
    return null;
  }

  // Build map of symbol -> direction (latest signal wins)
  const symbolMap = new Map<string, "LONG" | "SHORT" | "BOTH">();
  for (const signal of signals) {
    const existing = symbolMap.get(signal.symbol);
    if (!existing) {
      symbolMap.set(signal.symbol, signal.direction);
    } else if (existing !== signal.direction) {
      symbolMap.set(signal.symbol, "BOTH");
    }
  }

  const entries = Array.from(symbolMap.entries());

  return (
    <div className="bg-surface border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-text-primary">
          Market Heatmap
        </h2>
        <div className="flex items-center gap-4 text-xs text-text-muted">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-long/50 inline-block" />
            LONG
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-short/50 inline-block" />
            SHORT
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-surface-2 inline-block" />
            Neutral
          </span>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {entries.map(([symbol, direction]) => {
          let cellClass = "bg-surface-2 text-text-muted border-border";
          if (direction === "LONG") {
            cellClass = "bg-long/20 text-long border-long/30";
          } else if (direction === "SHORT") {
            cellClass = "bg-short/20 text-short border-short/30";
          } else if (direction === "BOTH") {
            cellClass = "bg-gold/20 text-gold border-gold/30";
          }

          const cleanSymbol = symbol
            .replace("USDT", "")
            .replace("USD", "")
            .replace("/", "");

          return (
            <div
              key={symbol}
              className={`flex flex-col items-center justify-center w-16 h-16 rounded-lg border text-xs font-bold font-mono transition-all hover:scale-105 cursor-default ${cellClass}`}
              title={`${symbol}: ${direction}`}
            >
              <span className="text-xs font-bold">{cleanSymbol}</span>
              <span className="text-xs opacity-70 mt-0.5 font-normal">
                {direction === "BOTH" ? "±" : direction === "LONG" ? "▲" : "▼"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
