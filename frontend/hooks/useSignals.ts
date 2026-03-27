import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Signal, SignalsResponse } from "@/types/signal";

interface UseSignalsOptions {
  direction?: string;
  timeframe?: string;
  market?: string;
  min_confidence?: number;
  limit?: number;
  page?: number;
  status?: string;
}

export function useSignals(options: UseSignalsOptions = {}) {
  const params = new URLSearchParams();
  if (options.direction) params.set("direction", options.direction);
  if (options.timeframe) params.set("timeframe", options.timeframe);
  if (options.market) params.set("market", options.market);
  if (options.min_confidence !== undefined)
    params.set("min_confidence", options.min_confidence.toString());
  if (options.limit !== undefined) params.set("limit", options.limit.toString());
  if (options.page !== undefined) params.set("page", options.page.toString());
  if (options.status) params.set("status", options.status);

  return useQuery<SignalsResponse>({
    queryKey: ["signals", options],
    queryFn: async () => {
      const res = await api.get<{
        items: Signal[];
        total: number;
        page: number;
        limit: number;
        pages: number;
      }>(
        `/api/v1/signals/?${params.toString()}`
      );
      return {
        signals: res.data.items || [],
        total: res.data.total || 0,
        page: res.data.page || 1,
        limit: res.data.limit || options.limit || 20,
        pages: res.data.pages || 1,
      };
    },
    refetchInterval: 30_000,
  });
}

export function useSignal(id: string) {
  return useQuery<Signal>({
    queryKey: ["signal", id],
    queryFn: async () => {
      const res = await api.get<Signal>(`/api/v1/signals/${id}`);
      return res.data;
    },
    enabled: Boolean(id),
    refetchInterval: 30_000,
  });
}

export function useLiveSignals() {
  return useQuery<Signal[]>({
    queryKey: ["signals", "live"],
    queryFn: async () => {
      const res = await api.get<{ signals: Signal[] }>("/api/v1/signals/live");
      return res.data?.signals || [];
    },
    refetchInterval: 10_000,
  });
}
