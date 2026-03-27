"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface TickerItem {
  symbol: string;
  price: number;
  change_pct: number;
}

const FALLBACK_PAIRS = [
  "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
  "ADAUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT", "AVAXUSDT",
];

export function LiveTicker() {
  const { data: prices } = useQuery<TickerItem[]>({
    queryKey: ["ticker-prices"],
    queryFn: async () => {
      const res = await api.get<TickerItem[]>("/api/v1/pairs/ticker");
      return res.data;
    },
    refetchInterval: 15_000,
    retry: false,
  });

  const items: TickerItem[] = prices?.length
    ? prices
    : FALLBACK_PAIRS.map((sym) => ({
        symbol: sym,
        price: 0,
        change_pct: 0,
      }));

  // Duplicate for seamless loop
  const doubled = [...items, ...items];

  return (
    <div className="bg-surface border-b border-border py-2 overflow-hidden -mx-4 lg:-mx-6 px-0">
      <div className="flex items-center ticker-scroll gap-8 w-max">
        {doubled.map((item, idx) => (
          <div
            key={`${item.symbol}-${idx}`}
            className="flex items-center gap-2 whitespace-nowrap px-3"
          >
            <span className="text-xs font-mono font-bold text-text-secondary">
              {item.symbol.replace("USDT", "").replace("USD", "")}
            </span>
            {item.price > 0 && (
              <span className="text-xs font-mono text-text-primary">
                {item.price >= 1000
                  ? `$${item.price.toLocaleString("en-US", { maximumFractionDigits: 2 })}`
                  : item.price >= 1
                  ? `$${item.price.toFixed(4)}`
                  : `$${item.price.toFixed(6)}`}
              </span>
            )}
            {item.change_pct !== 0 && (
              <span
                className={`text-xs font-mono font-medium ${
                  item.change_pct >= 0 ? "text-long" : "text-short"
                }`}
              >
                {item.change_pct >= 0 ? "+" : ""}
                {item.change_pct.toFixed(2)}%
              </span>
            )}
            <span className="text-border">|</span>
          </div>
        ))}
      </div>
    </div>
  );
}
