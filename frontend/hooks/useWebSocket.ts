"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { useSignalStore } from "@/store/signalStore";
import { Signal } from "@/types/signal";
import { useUserStore } from "@/store/userStore";

type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

interface UseSignalWebSocketOptions {
  minConfidence?: number;
}

interface UseSignalWebSocketReturn {
  isConnected: boolean;
  lastSignal: Signal | null;
  connectionStatus: ConnectionStatus;
}

export function useSignalWebSocket(
  options: UseSignalWebSocketOptions = {}
): UseSignalWebSocketReturn {
  const { minConfidence = 0 } = options;
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const MAX_RECONNECT_ATTEMPTS = 10;
  const BASE_RECONNECT_DELAY = 2000;

  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("disconnected");
  const [lastSignal, setLastSignal] = useState<Signal | null>(null);

  const { addLiveSignal } = useSignalStore();
  const { accessToken } = useUserStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const WS_BASE =
      process.env.NEXT_PUBLIC_WS_URL ||
      (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(
        /^http/,
        "ws"
      );

    const params = new URLSearchParams();
    if (accessToken) params.set("token", accessToken);
    if (minConfidence > 0) params.set("min_confidence", minConfidence.toString());

    const url = `${WS_BASE}/ws/signals?${params.toString()}`;

    setConnectionStatus("connecting");

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionStatus("connected");
      reconnectAttemptsRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "signal" && data.payload) {
          const signal: Signal = data.payload;
          addLiveSignal(signal);
          setLastSignal(signal);
        }
      } catch {
        // Ignore parse errors
      }
    };

    ws.onerror = () => {
      setConnectionStatus("error");
    };

    ws.onclose = () => {
      setConnectionStatus("disconnected");
      wsRef.current = null;

      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = Math.min(
          BASE_RECONNECT_DELAY * Math.pow(1.5, reconnectAttemptsRef.current),
          30_000
        );
        reconnectAttemptsRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(connect, delay);
      }
    };
  }, [accessToken, minConfidence, addLiveSignal]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return {
    isConnected: connectionStatus === "connected",
    lastSignal,
    connectionStatus,
  };
}
