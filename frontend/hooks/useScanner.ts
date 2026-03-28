import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface ScannerStatus {
  is_running: boolean;
  current_market?: string | null;
  pairs_total: number;
  pairs_done: number;
  signals_found_this_run: number;
  last_run_at?: string | null;
  next_run_at?: string | null;
  queue_length: number;
  uptime_seconds?: number | null;
}

export interface ScannerResult {
  symbol: string;
  market: string;
  signals_count: number;
  last_signal?: string;
  confidence?: number;
}

interface ScannerResultsResponse {
  results: ScannerResult[];
  count: number;
  min_confidence: number;
  market_filter?: string;
}

interface UseScannerResultsOptions {
  market?: string;
  timeframe?: string;
  limit?: number;
}

export function useScanner() {
  return useQuery<ScannerStatus>({
    queryKey: ["scanner", "status"],
    queryFn: async () => {
      const res = await api.get<ScannerStatus>("/api/v1/scanner/status");
      return res.data;
    },
    refetchInterval: 15_000,
  });
}

export function useScannerResults(options: UseScannerResultsOptions = {}) {
  const params = new URLSearchParams();
  if (options.market) params.set("market", options.market);
  if (options.timeframe) params.set("timeframe", options.timeframe);
  if (options.limit !== undefined) params.set("limit", options.limit.toString());

  return useQuery<ScannerResultsResponse>({
    queryKey: ["scanner", "results", options],
    queryFn: async () => {
      const res = await api.get<ScannerResultsResponse>(
        `/api/v1/scanner/results?${params.toString()}`
      );
      return res.data;
    },
    refetchInterval: 15_000,
  });
}
