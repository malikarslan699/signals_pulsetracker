"use client";
import { CheckCircle2, Circle } from "lucide-react";
import { ScoreItem } from "@/types/signal";

interface IndicatorBreakdownProps {
  breakdown?: Record<string, ScoreItem>;
}

const CATEGORY_MAP: Record<string, string[]> = {
  "ICT Smart Money": [
    "order_block",
    "order_blocks",
    "fvg",
    "fair_value_gap",
    "liquidity",
    "premium_discount",
    "daily_bias",
    "breaker_block",
    "mitigation_block",
  ],
  "Trend": [
    "ema_trend",
    "ema",
    "sma",
    "trend",
    "trend_strength",
    "adx",
    "supertrend",
    "ichimoku",
  ],
  "Momentum": [
    "rsi",
    "macd",
    "stochastic",
    "cci",
    "momentum",
    "williams_r",
    "awesome_oscillator",
  ],
  "Volatility": [
    "atr",
    "bollinger",
    "keltner",
    "volatility",
    "squeeze",
    "donchian",
  ],
  "Volume": [
    "volume",
    "obv",
    "vwap",
    "volume_profile",
    "mfi",
    "cmf",
  ],
  "Fibonacci": [
    "fibonacci",
    "fib",
    "retracement",
    "extension",
    "golden_ratio",
  ],
};

function categorize(key: string): string {
  const lower = key.toLowerCase();
  for (const [category, keywords] of Object.entries(CATEGORY_MAP)) {
    if (keywords.some((kw) => lower.includes(kw))) {
      return category;
    }
  }
  return "Other";
}

export function IndicatorBreakdown({ breakdown }: IndicatorBreakdownProps) {
  if (!breakdown || Object.keys(breakdown).length === 0) {
    return null;
  }

  // Group by category
  const grouped: Record<string, Array<[string, ScoreItem]>> = {};
  for (const entry of Object.entries(breakdown)) {
    const category = categorize(entry[0]);
    if (!grouped[category]) grouped[category] = [];
    grouped[category].push(entry);
  }

  const totalScore = Object.values(breakdown).reduce(
    (sum, item) => sum + (item.triggered ? item.score : 0),
    0
  );
  const maxScore = Object.values(breakdown).reduce(
    (sum, item) => sum + item.score,
    0
  );
  const triggeredCount = Object.values(breakdown).filter((i) => i.triggered).length;

  return (
    <div className="bg-surface border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-text-primary">
          Indicator Breakdown
        </h2>
        <div className="flex items-center gap-4 text-xs text-text-muted">
          <span>
            <span className="text-long font-mono font-bold">{triggeredCount}</span>/{Object.keys(breakdown).length} triggered
          </span>
          <span>
            Score:{" "}
            <span className="text-purple font-mono font-bold">
              {totalScore}/{maxScore}
            </span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(grouped).map(([category, items]) => (
          <div
            key={category}
            className="bg-surface-2 rounded-lg p-3 border border-border"
          >
            <h3 className="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wider">
              {category}
            </h3>
            <div className="space-y-1.5">
              {items.map(([key, item]) => (
                <div key={key} className="flex items-start gap-2">
                  {item.triggered ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-long flex-shrink-0 mt-0.5" />
                  ) : (
                    <Circle className="w-3.5 h-3.5 text-text-faint flex-shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <span
                        className={`text-xs truncate ${
                          item.triggered ? "text-text-secondary" : "text-text-muted"
                        }`}
                      >
                        {key
                          .replace(/_/g, " ")
                          .replace(/\b\w/g, (l) => l.toUpperCase())}
                      </span>
                      <span
                        className={`text-xs font-mono flex-shrink-0 ${
                          item.triggered ? "text-long" : "text-text-faint"
                        }`}
                      >
                        +{item.score}
                      </span>
                    </div>
                    {item.details && (
                      <p className="text-xs text-text-muted mt-0.5 truncate">
                        {item.details}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
