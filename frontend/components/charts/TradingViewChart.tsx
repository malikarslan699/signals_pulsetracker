"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface SignalLevels {
  direction: string;
  entry: number;
  entry_zone_low?: number;
  entry_zone_high?: number;
  stop_loss: number;
  invalidation_price?: number;
  take_profit_1: number;
  take_profit_2: number;
}

interface TradingViewChartProps {
  symbol: string;
  timeframe: string;
  signal?: SignalLevels;
  height?: number;
}

interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface CandleApi {
  timestamp: number;
  open: number | string;
  high: number | string;
  low: number | string;
  close: number | string;
  volume?: number | string;
}

export function TradingViewChart({
  symbol,
  timeframe,
  signal,
  height = 400,
}: TradingViewChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const seriesRefs = useRef<any[]>([]);
  const [chartError, setChartError] = useState<string | null>(null);
  const [isDarkTheme, setIsDarkTheme] = useState(false);

  const { data: candles, isLoading, isError, error, refetch } = useQuery<Candle[]>({
    queryKey: ["candles", symbol, timeframe],
    queryFn: async () => {
      const res = await api.get<CandleApi[]>(
        `/api/v1/pairs/${symbol}/candles?timeframe=${timeframe}&limit=200`
      );
      return (res.data || [])
        .map((c) => ({
          time: Math.floor(Number(c.timestamp) / 1000),
          open: Number(c.open),
          high: Number(c.high),
          low: Number(c.low),
          close: Number(c.close),
          volume: c.volume != null ? Number(c.volume) : undefined,
        }))
        .filter((c) => Number.isFinite(c.time));
    },
    retry: false,
    enabled: Boolean(symbol && timeframe),
  });

  const sortedCandles = useMemo(
    () => (candles && candles.length > 0 ? [...candles].sort((a, b) => a.time - b.time) : []),
    [candles]
  );

  useEffect(() => {
    const root = document.documentElement;
    const syncTheme = () => setIsDarkTheme(root.classList.contains("dark"));
    syncTheme();
    const observer = new MutationObserver(syncTheme);
    observer.observe(root, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;
    if (!sortedCandles.length) return;

    let chart: any;
    let resizeObserver: ResizeObserver;

    const init = async () => {
      try {
        setChartError(null);
        const { createChart, ColorType, LineStyle } = await import(
          "lightweight-charts"
        );

        if (chartRef.current) {
          chartRef.current.remove();
          chartRef.current = null;
          seriesRefs.current = [];
        }

        const theme = isDarkTheme
          ? {
              background: "#0E1726",
              text: "#94A3B8",
              grid: "#1E293B",
              border: "#374151",
              crosshair: "#334155",
              zone: "rgba(245, 158, 11, 0.45)",
              invalidation: "rgba(239, 68, 68, 0.55)",
            }
          : {
              background: "#FFFFFF",
              text: "#475569",
              grid: "#E2E8F0",
              border: "#CBD5E1",
              crosshair: "#94A3B8",
              zone: "rgba(245, 158, 11, 0.35)",
              invalidation: "rgba(239, 68, 68, 0.4)",
            };

        chart = createChart(containerRef.current!, {
          layout: {
            background: { type: ColorType.Solid, color: theme.background },
            textColor: theme.text,
          },
          grid: {
            vertLines: { color: theme.grid },
            horzLines: { color: theme.grid },
          },
          crosshair: {
            vertLine: { color: theme.crosshair },
            horzLine: { color: theme.crosshair },
          },
          rightPriceScale: {
            borderColor: theme.border,
          },
          timeScale: {
            borderColor: theme.border,
            timeVisible: true,
            secondsVisible: false,
          },
          width: containerRef.current!.clientWidth,
          height,
        });

        chartRef.current = chart;

        const candleSeries = chart.addCandlestickSeries({
          upColor: "#10B981",
          downColor: "#EF4444",
          borderUpColor: "#10B981",
          borderDownColor: "#EF4444",
          wickUpColor: "#10B981",
          wickDownColor: "#EF4444",
        });

        seriesRefs.current = [candleSeries];
        candleSeries.setData(sortedCandles);

        // Draw signal levels
        if (signal) {
          const lineStyle = LineStyle.Dashed;
          const start = sortedCandles[0].time;
          const end = sortedCandles[sortedCandles.length - 1].time;

          if (signal.entry_zone_low != null && signal.entry_zone_high != null) {
            const zoneLowSeries = chart.addLineSeries({
              color: theme.zone,
              lineWidth: 1,
              lineStyle,
              title: "Zone Low",
              priceLineVisible: false,
            });
            zoneLowSeries.setData([
              { time: start, value: signal.entry_zone_low },
              { time: end, value: signal.entry_zone_low },
            ]);
            seriesRefs.current.push(zoneLowSeries);

            const zoneHighSeries = chart.addLineSeries({
              color: theme.zone,
              lineWidth: 1,
              lineStyle,
              title: "Zone High",
              priceLineVisible: false,
            });
            zoneHighSeries.setData([
              { time: start, value: signal.entry_zone_high },
              { time: end, value: signal.entry_zone_high },
            ]);
            seriesRefs.current.push(zoneHighSeries);
          }

          // Entry line (gold)
          const entrySeries = chart.addLineSeries({
            color: "#F59E0B",
            lineWidth: 1,
            lineStyle,
            title: "Entry",
            priceLineVisible: false,
          });
          entrySeries.setData([
            { time: start, value: signal.entry },
            { time: end, value: signal.entry },
          ]);
          seriesRefs.current.push(entrySeries);

          // Stop Loss line (red)
          const stopSeries = chart.addLineSeries({
            color: "#EF4444",
            lineWidth: 1,
            lineStyle,
            title: "SL",
            priceLineVisible: false,
          });
          stopSeries.setData([
            { time: start, value: signal.stop_loss },
            { time: end, value: signal.stop_loss },
          ]);
          seriesRefs.current.push(stopSeries);

          if (signal.invalidation_price != null) {
            const invalidationSeries = chart.addLineSeries({
              color: theme.invalidation,
              lineWidth: 1,
              lineStyle: LineStyle.Dotted,
              title: "Invalidation",
              priceLineVisible: false,
            });
            invalidationSeries.setData([
              { time: start, value: signal.invalidation_price },
              { time: end, value: signal.invalidation_price },
            ]);
            seriesRefs.current.push(invalidationSeries);
          }

          // TP1 line (light green)
          const tp1Series = chart.addLineSeries({
            color: "#34D399",
            lineWidth: 1,
            lineStyle,
            title: "TP1",
            priceLineVisible: false,
          });
          tp1Series.setData([
            { time: start, value: signal.take_profit_1 },
            { time: end, value: signal.take_profit_1 },
          ]);
          seriesRefs.current.push(tp1Series);

          // TP2 line (green)
          const tp2Series = chart.addLineSeries({
            color: "#10B981",
            lineWidth: 1,
            lineStyle,
            title: "TP2",
            priceLineVisible: false,
          });
          tp2Series.setData([
            { time: start, value: signal.take_profit_2 },
            { time: end, value: signal.take_profit_2 },
          ]);
          seriesRefs.current.push(tp2Series);
        }

        chart.timeScale().fitContent();

        // Responsive resize
        resizeObserver = new ResizeObserver((entries) => {
          if (entries.length > 0 && chart) {
            const { width } = entries[0].contentRect;
            chart.applyOptions({ width });
          }
        });
        resizeObserver.observe(containerRef.current!);
      } catch (err) {
        console.error("Chart init error:", err);
        setChartError("Chart renderer failed. Falling back to summary mode.");
      }
    };

    init();

    return () => {
      resizeObserver?.disconnect();
      if (chart) {
        chart.remove();
        chartRef.current = null;
        seriesRefs.current = [];
      }
    };
  }, [sortedCandles, signal, height, isDarkTheme]);

  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center bg-surface-2 text-text-muted text-sm"
        style={{ height }}
      >
        <div className="flex flex-col items-center gap-2">
          <div className="w-8 h-8 border-2 border-border border-t-purple rounded-full animate-spin" />
          <span>Loading chart data...</span>
        </div>
      </div>
    );
  }

  if (isError) {
    const detail =
      (error as any)?.response?.data?.detail ||
      (error as Error | undefined)?.message ||
      "Unable to load chart candles.";
    return (
      <div
        className="flex flex-col items-center justify-center gap-2 bg-surface-2 text-text-muted text-xs p-3"
        style={{ height }}
      >
        <span>{detail}</span>
        <button onClick={() => refetch()} className="filter-pill">
          Retry
        </button>
      </div>
    );
  }

  if (!candles || candles.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-surface-2 text-text-muted text-sm"
        style={{ height }}
      >
        No chart candles available.
      </div>
    );
  }

  if (chartError) {
    return (
      <div
        className="flex flex-col items-center justify-center gap-3 bg-surface-2 text-text-muted text-xs p-4"
        style={{ height }}
      >
        <span>{chartError}</span>
        {signal && (
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 font-mono text-[11px]">
            <span>Entry</span><span>{signal.entry}</span>
            <span>Zone</span><span>{signal.entry_zone_low ?? "—"} - {signal.entry_zone_high ?? "—"}</span>
            <span>SL</span><span>{signal.stop_loss}</span>
            <span>TP1 / TP2</span><span>{signal.take_profit_1} / {signal.take_profit_2}</span>
          </div>
        )}
        <button onClick={() => refetch()} className="filter-pill">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      style={{ height }}
      className="w-full"
    />
  );
}
