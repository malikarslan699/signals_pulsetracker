export const TIMEFRAMES = ["5m", "15m", "1H", "4H", "1D"];
export const MARKETS = ["crypto", "forex"];
export const DIRECTIONS = ["LONG", "SHORT"];

export const CONFIDENCE_COLORS = {
  ULTRA_HIGH: "#10B981",
  HIGH: "#34D399",
  MEDIUM: "#F59E0B",
  LOW: "#EF4444",
  NO_SIGNAL: "#6B7280",
};

export const PLAN_FEATURES = {
  free:     { maxSignals: 20, hasAlerts: false, hasICT: true,  hasHistory: true,  hasRealtime: false },
  trial:    { maxSignals: 20, hasAlerts: false, hasICT: true,  hasHistory: true,  hasRealtime: false },
  monthly:  { maxSignals: -1, hasAlerts: true,  hasICT: true,  hasHistory: true,  hasRealtime: true  },
  yearly:   { maxSignals: -1, hasAlerts: true,  hasICT: true,  hasHistory: true,  hasRealtime: true  },
  lifetime: { maxSignals: -1, hasAlerts: true,  hasICT: true,  hasHistory: true,  hasRealtime: true  },
};

export const PLAN_LABELS: Record<string, string> = {
  trial:    "Trial",
  monthly:  "Monthly Pro",
  yearly:   "Yearly Pro",
  lifetime: "Lifetime Pro",
};

export const PLAN_COLORS: Record<string, string> = {
  trial:    "text-text-muted",
  monthly:  "text-purple",
  yearly:   "text-long",
  lifetime: "text-gold",
};
