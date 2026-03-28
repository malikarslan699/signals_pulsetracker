"use client";
import { useEffect, useState } from "react";
import { Activity, Clock, Search, Zap } from "lucide-react";
import { ScannerStatus as ScannerStatusType } from "@/hooks/useScanner";
import { formatTimeAgo } from "@/lib/formatters";

interface ScannerStatusProps {
  status?: ScannerStatusType;
}

export function ScannerStatus({ status }: ScannerStatusProps) {
  const [countdown, setCountdown] = useState<string>("--:--");

  useEffect(() => {
    if (status?.is_running) {
      setCountdown("Running");
      return;
    }

    if (!status?.next_run_at) {
      setCountdown("--:--");
      return;
    }

    const updateCountdown = () => {
      const now = Date.now();
      const target = new Date(status.next_run_at!).getTime();
      const diff = target - now;

      if (diff <= 0) {
        setCountdown("Now");
        return;
      }

      const mins = Math.floor(diff / 60_000);
      const secs = Math.floor((diff % 60_000) / 1000);
      setCountdown(`${mins}:${secs.toString().padStart(2, "0")}`);
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, [status?.is_running, status?.next_run_at]);

  const isActive = Boolean(status?.is_running);

  return (
    <div
      className={`flex flex-wrap items-center gap-3 px-3 py-1.5 rounded-lg border text-xs font-mono ${
        isActive
          ? "bg-long/5 border-long/20"
          : "bg-surface border-border"
      }`}
    >
      <div className="flex items-center gap-1.5">
        <div className={`w-1.5 h-1.5 rounded-full ${isActive ? "bg-long animate-pulse" : "bg-text-muted"}`} />
        <span className={`font-bold tracking-widest text-[10px] ${isActive ? "text-long" : "text-text-muted"}`}>
          {isActive ? "SCANNING" : "IDLE"}
        </span>
      </div>

      <div className="w-px h-3 bg-border hidden sm:block" />

      {status?.last_run_at && (
        <div className="flex items-center gap-1 text-text-muted">
          <Clock className="w-3 h-3" />
          <span>Last: {formatTimeAgo(status.last_run_at)}</span>
        </div>
      )}

      <div className="flex items-center gap-1 text-text-muted">
        <Zap className="w-3 h-3 text-gold" />
        <span>Next: <span className="font-bold text-gold">{countdown}</span></span>
      </div>

      {status && (
        <>
          <div className="w-px h-3 bg-border hidden sm:block" />
          <div className="flex items-center gap-1 text-text-muted">
            <Search className="w-3 h-3 text-blue" />
            <span>
              <span className="font-bold text-blue">{status.pairs_done}</span>
              {status.pairs_total > 0 ? ` / ${status.pairs_total}` : ""} pairs
            </span>
          </div>
        </>
      )}

      {status && (
        <div className="flex items-center gap-1 text-text-muted ml-auto">
          <Activity className="w-3 h-3 text-long" />
          <span><span className="font-bold text-long">{status.signals_found_this_run}</span> found</span>
        </div>
      )}
    </div>
  );
}
