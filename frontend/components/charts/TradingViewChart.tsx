"use client";
import { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface SignalLevels {
  direction: string;
  entry: number;
  stop_loss: number;
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

export function TradingViewChart({
  symbol,
  timeframe,
  signal,
  height = 400,
}: TradingViewChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const seriesRef = useRef<any>(null);

  const { data: candles } = useQuery<Candle[]>({
    queryKey: ["candles", symbol, timeframe],
    queryFn: async () => {
      const res = await api.get<Candle[]>(
        `/api/v1/pairs/${symbol}/candles?timeframe=${timeframe}&limit=200`
      );
      return res.data;
    },
    retry: false,
  });

  useEffect(() => {
    if (!containerRef.current) return;

    let chart: any;
    let resizeObserver: ResizeObserver;

    const init = async () => {
      try {
        const { createChart, ColorType, LineStyle } = await import(
          "lightweight-charts"
        );

        chart = createChart(containerRef.current!, {
          layout: {
            background: { type: ColorType.Solid, color: "#111827" },
            textColor: "#6B7280",
          },
          grid: {
            vertLines: { color: "#1F2937" },
            horzLines: { color: "#1F2937" },
          },
          crosshair: {
            vertLine: { color: "#374151" },
            horzLine: { color: "#374151" },
          },
          rightPriceScale: {
            borderColor: "#374151",
          },
          timeScale: {
            borderColor: "#374151",
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

        seriesRef.current = candleSeries;

        if (candles && candles.length > 0) {
          const sorted = [...candles].sort((a, b) => a.time - b.time);
          candleSeries.setData(sorted);
        }

        // Draw signal levels
        if (signal) {
          const lineStyle = LineStyle.Dashed;

          // Entry line (gold)
          chart.addLineSeries({
            color: "#F59E0B",
            lineWidth: 1,
            lineStyle,
            title: "Entry",
            priceLineVisible: false,
          }).setData(
            candles?.length
              ? [
                  { time: candles[0].time, value: signal.entry },
                  { time: candles[candles.length - 1].time, value: signal.entry },
                ]
              : []
          );

          // Stop Loss line (red)
          chart.addLineSeries({
            color: "#EF4444",
            lineWidth: 1,
            lineStyle,
            title: "SL",
            priceLineVisible: false,
          }).setData(
            candles?.length
              ? [
                  { time: candles[0].time, value: signal.stop_loss },
                  { time: candles[candles.length - 1].time, value: signal.stop_loss },
                ]
              : []
          );

          // TP1 line (light green)
          chart.addLineSeries({
            color: "#34D399",
            lineWidth: 1,
            lineStyle,
            title: "TP1",
            priceLineVisible: false,
          }).setData(
            candles?.length
              ? [
                  { time: candles[0].time, value: signal.take_profit_1 },
                  { time: candles[candles.length - 1].time, value: signal.take_profit_1 },
                ]
              : []
          );

          // TP2 line (green)
          chart.addLineSeries({
            color: "#10B981",
            lineWidth: 1,
            lineStyle,
            title: "TP2",
            priceLineVisible: false,
          }).setData(
            candles?.length
              ? [
                  { time: candles[0].time, value: signal.take_profit_2 },
                  { time: candles[candles.length - 1].time, value: signal.take_profit_2 },
                ]
              : []
          );
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
      }
    };

    init();

    return () => {
      resizeObserver?.disconnect();
      if (chart) {
        chart.remove();
        chartRef.current = null;
        seriesRef.current = null;
      }
    };
  }, [candles, signal, height]);

  if (!candles || candles.length === 0) {
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

  return (
    <div
      ref={containerRef}
      style={{ height }}
      className="w-full"
    />
  );
}
