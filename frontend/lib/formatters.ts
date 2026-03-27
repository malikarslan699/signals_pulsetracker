import { formatDistanceToNow, format } from "date-fns";

export function formatPrice(price: number | string | null | undefined): string {
  const n = typeof price === "string" ? parseFloat(price) : (price ?? 0);
  if (isNaN(n)) return "$0.00";
  if (n >= 10000) {
    return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  } else if (n >= 1) {
    return "$" + n.toFixed(4);
  } else {
    return "$" + n.toFixed(6);
  }
}

export function formatPct(pct: number | string | null | undefined, showPlus?: boolean): string {
  const n = typeof pct === "string" ? parseFloat(pct) : (pct ?? 0);
  if (isNaN(n)) return "0.00%";
  const sign = n >= 0 ? (showPlus ? "+" : "") : "";
  return `${sign}${n.toFixed(2)}%`;
}

export function formatTimeAgo(isoDate: string): string {
  try {
    return formatDistanceToNow(new Date(isoDate), { addSuffix: true });
  } catch {
    return "unknown";
  }
}

export function formatDateTime(isoDate: string): string {
  try {
    return format(new Date(isoDate), "MMM d, HH:mm");
  } catch {
    return "unknown";
  }
}

export function formatVolume(volume: number | string | null | undefined): string {
  const n = typeof volume === "string" ? parseFloat(volume) : (volume ?? 0);
  if (isNaN(n)) return "0";
  if (n >= 1_000_000_000) {
    return `${(n / 1_000_000_000).toFixed(1)}B`;
  } else if (n >= 1_000_000) {
    return `${(n / 1_000_000).toFixed(1)}M`;
  } else if (n >= 1_000) {
    return `${(n / 1_000).toFixed(1)}K`;
  }
  return n.toString();
}

export function confidenceBandLabel(confidence: number): string {
  if (confidence >= 90) return "ULTRA HIGH";
  if (confidence >= 75) return "HIGH";
  if (confidence >= 55) return "MEDIUM";
  if (confidence >= 40) return "LOW";
  return "NO SIGNAL";
}

export function confidenceBandColor(confidence: number): string {
  if (confidence >= 90) return "#10B981";
  if (confidence >= 75) return "#34D399";
  if (confidence >= 55) return "#F59E0B";
  if (confidence >= 40) return "#EF4444";
  return "#6B7280";
}

export function getDirectionColor(direction: string): string {
  return direction === "LONG" ? "text-long" : "text-short";
}

export function getStatusLabel(status: string): string {
  switch (status) {
    case "active":
      return "Active";
    case "tp1_hit":
      return "TP1 Hit ✅";
    case "tp2_hit":
      return "TP2 Hit 🎯";
    case "tp3_hit":
      return "TP3 Hit 🎯";
    case "sl_hit":
      return "SL Hit ❌";
    case "expired":
      return "Expired";
    default:
      return status;
  }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case "active":
      return "text-blue";
    case "tp1_hit":
    case "tp2_hit":
    case "tp3_hit":
      return "text-long";
    case "sl_hit":
      return "text-short";
    case "expired":
      return "text-text-muted";
    default:
      return "text-text-muted";
  }
}
