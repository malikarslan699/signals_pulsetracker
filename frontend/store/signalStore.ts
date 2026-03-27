import { create } from "zustand";
import { Signal } from "@/types/signal";

interface SignalFilters {
  direction?: string;
  timeframe?: string;
  market?: string;
  minConfidence: number;
}

interface SignalState {
  liveSignals: Signal[];
  filters: SignalFilters;
  addLiveSignal: (signal: Signal) => void;
  setFilters: (filters: Partial<SignalFilters>) => void;
  clearLiveSignals: () => void;
}

export const useSignalStore = create<SignalState>((set) => ({
  liveSignals: [],
  filters: {
    direction: undefined,
    timeframe: undefined,
    market: undefined,
    minConfidence: 50,
  },

  addLiveSignal: (signal: Signal) =>
    set((state) => {
      // Avoid duplicates, keep latest 50
      const filtered = state.liveSignals.filter((s) => s.id !== signal.id);
      return {
        liveSignals: [signal, ...filtered].slice(0, 50),
      };
    }),

  setFilters: (filters: Partial<SignalFilters>) =>
    set((state) => ({
      filters: { ...state.filters, ...filters },
    })),

  clearLiveSignals: () => set({ liveSignals: [] }),
}));
