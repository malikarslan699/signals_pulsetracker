import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface ScannerStatus {
  status: "active" | "idle" | "scanning";
  last_scan?: string;
  next_scan?: string;
  pairs_scanned?: number;
  signals_found?: number;
  is_running?: boolean;
}

export interface ScannerResult {
  symbol: string;
  market: string;
  signals_count: number;
  last_signal?: string;
  confidence?: number;
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

  return useQuery<ScannerResult[]>({
    queryKey: ["scanner", "results", options],
    queryFn: async () => {
      const res = await api.get<ScannerResult[]>(
        `/api/v1/scanner/results?${params.toString()}`
      );
      return res.data;
    },
    refetchInterval: 15_000,
  });
}
