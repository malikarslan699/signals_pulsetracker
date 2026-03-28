export interface ScoreItem {
  score: number;
  triggered: boolean;
  details: string;
}

export interface Signal {
  id: string;
  symbol: string;
  market: "crypto" | "forex";
  direction: "LONG" | "SHORT";
  timeframe: string;
  confidence: number;
  setup_score?: number;
  pwin_tp1?: number;
  pwin_tp2?: number;
  ranking_score?: number;
  confidence_band: "ULTRA_HIGH" | "HIGH" | "MEDIUM" | "LOW" | "NO_SIGNAL";
  entry: number;
  entry_zone_low?: number;
  entry_zone_high?: number;
  entry_type?: string;
  stop_loss: number;
  invalidation_price?: number;
  take_profit_1: number;
  take_profit_2: number;
  take_profit_3?: number;
  rr_ratio: number;
  rr_tp1?: number;
  rr_tp2?: number;
  raw_score?: number;
  max_possible_score?: number;
  status:
    | "active"
    | "tp1_hit"
    | "tp2_hit"
    | "tp3_hit"
    | "sl_hit"
    | "expired"
    | "invalidated"
    | "CREATED"
    | "ARMED"
    | "FILLED"
    | "TP1_REACHED"
    | "TP2_REACHED"
    | "STOPPED"
    | "EXPIRED"
    | "INVALIDATED";
  score_breakdown?: Record<string, ScoreItem>;
  ict_zones?: {
    order_blocks?: { bullish: any[]; bearish: any[] };
    fvg?: { bullish: any[]; bearish: any[] };
    liquidity?: { bsl: number[]; ssl: number[] };
    premium_discount?: { zone: string; current_pct: number };
    daily_bias?: { bias: string; pdh?: number; pdl?: number };
  };
  mtf_analysis?: Record<
    string,
    {
      long_confidence: number;
      short_confidence: number;
      direction: string;
      aligned: boolean;
    }
  >;
  top_confluences?: string[];
  fired_at: string;
  valid_until?: string;
  expires_at?: string;
  pnl_pct?: number;
}

export interface SignalsResponse {
  signals: Signal[];
  total: number;
  page: number;
  limit?: number;
  pages: number;
}

export interface PlatformStats {
  active_signals: number;
  total_signals: number;
  signals_last_30d?: number;
  win_rate_pct?: number;
  avg_confidence?: number;
  tp_hits_90d?: number;
  sl_hits_90d?: number;
  closed_total_90d?: number;
  scanner_queue_length?: number;
  // Backward-compatible optional fields
  win_rate_7d?: number;
  pairs_scanned?: number;
  next_scan_in?: string;
  win_rate_all?: number;
}
