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
    if (!status?.next_scan) {
      setCountdown("--:--");
      return;
    }

    const updateCountdown = () => {
      const now = Date.now();
      const target = new Date(status.next_scan!).getTime();
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
  }, [status?.next_scan]);

  const isActive =
    status?.status === "active" || status?.status === "scanning";

  return (
    <div
      className={`flex flex-wrap items-center gap-4 px-4 py-3 rounded-xl border ${
        isActive
          ? "bg-long/5 border-long/20"
          : "bg-surface border-border"
      }`}
    >
      {/* Status indicator */}
      <div className="flex items-center gap-2">
        <div
          className={`w-2 h-2 rounded-full ${
            isActive ? "bg-long animate-pulse" : "bg-text-muted"
          }`}
        />
        <Activity
          className={`w-4 h-4 ${isActive ? "text-long" : "text-text-muted"}`}
        />
        <span
          className={`text-sm font-bold tracking-wide ${
            isActive ? "text-long" : "text-text-muted"
          }`}
        >
          SCANNER {isActive ? "ACTIVE" : "IDLE"}
        </span>
      </div>

      <div className="h-4 w-px bg-border hidden sm:block" />

      {/* Last scan */}
      {status?.last_scan && (
        <div className="flex items-center gap-1.5 text-xs text-text-muted">
          <Clock className="w-3.5 h-3.5" />
          <span>Last scan: {formatTimeAgo(status.last_scan)}</span>
        </div>
      )}

      {/* Next scan countdown */}
      <div className="flex items-center gap-1.5 text-xs text-text-muted">
        <Zap className="w-3.5 h-3.5 text-gold" />
        <span>
          Next scan:{" "}
          <span className="font-mono font-bold text-gold">{countdown}</span>
        </span>
      </div>

      <div className="h-4 w-px bg-border hidden sm:block" />

      {/* Pairs scanned */}
      {status?.pairs_scanned !== undefined && (
        <div className="flex items-center gap-1.5 text-xs text-text-muted">
          <Search className="w-3.5 h-3.5 text-blue" />
          <span>
            <span className="font-mono font-bold text-blue">
              {status.pairs_scanned}
            </span>{" "}
            pairs scanned
          </span>
        </div>
      )}

      {/* Signals found */}
      {status?.signals_found !== undefined && (
        <div className="flex items-center gap-1.5 text-xs text-text-muted ml-auto">
          <span>
            <span className="font-mono font-bold text-purple">
              {status.signals_found}
            </span>{" "}
            signals found
          </span>
        </div>
      )}
    </div>
  );
}
