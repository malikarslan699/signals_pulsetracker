import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { RefreshCw, Activity, TrendingUp, Target, Crosshair, Clock } from "lucide-react";
import { KPIChip } from "@/components/terminal/KPIChip";
import { FilterBar } from "@/components/terminal/FilterBar";
import { Panel } from "@/components/terminal/Panel";
import { DirectionBadge, StatusBadge, ConfidenceBadge } from "@/components/terminal/Badges";
import { ConfidenceBar } from "@/components/terminal/ConfidenceBar";
import { cn } from "@/lib/utils";

const mockSignals = [
  { id: "1", symbol: "BTC/USDT", direction: "LONG" as const, timeframe: "4H", confidence: 87, entry: "67,200", sl: "66,400", tp1: "68,800", rr: "2.0", status: "active" as const, age: "12m" },
  { id: "2", symbol: "ETH/USDT", direction: "LONG" as const, timeframe: "1H", confidence: 74, entry: "3,510", sl: "3,460", tp1: "3,620", rr: "2.2", status: "tp1" as const, age: "34m" },
  { id: "3", symbol: "EUR/USD", direction: "SHORT" as const, timeframe: "4H", confidence: 82, entry: "1.0855", sl: "1.0890", tp1: "1.0780", rr: "2.1", status: "active" as const, age: "1h" },
  { id: "4", symbol: "GBP/JPY", direction: "LONG" as const, timeframe: "1D", confidence: 91, entry: "192.40", sl: "191.20", tp1: "194.80", rr: "2.0", status: "active" as const, age: "2h" },
  { id: "5", symbol: "SOL/USDT", direction: "SHORT" as const, timeframe: "15M", confidence: 63, entry: "142.50", sl: "144.80", tp1: "138.20", rr: "1.9", status: "sl" as const, age: "45m" },
  { id: "6", symbol: "XAU/USD", direction: "LONG" as const, timeframe: "1H", confidence: 79, entry: "2,338", sl: "2,325", tp1: "2,365", rr: "2.1", status: "active" as const, age: "18m" },
  { id: "7", symbol: "ADA/USDT", direction: "LONG" as const, timeframe: "4H", confidence: 68, entry: "0.4520", sl: "0.4410", tp1: "0.4740", rr: "2.0", status: "expired" as const, age: "3h" },
  { id: "8", symbol: "USD/CHF", direction: "SHORT" as const, timeframe: "1H", confidence: 85, entry: "0.8920", sl: "0.8955", tp1: "0.8845", rr: "2.1", status: "tp2" as const, age: "55m" },
];

const heatmapData = [
  { symbol: "BTC", direction: "LONG", strength: 87 },
  { symbol: "ETH", direction: "LONG", strength: 74 },
  { symbol: "SOL", direction: "SHORT", strength: 63 },
  { symbol: "ADA", direction: "LONG", strength: 68 },
  { symbol: "XRP", direction: "SHORT", strength: 55 },
  { symbol: "DOT", direction: "LONG", strength: 71 },
  { symbol: "AVAX", direction: "LONG", strength: 78 },
  { symbol: "MATIC", direction: "SHORT", strength: 61 },
  { symbol: "LINK", direction: "LONG", strength: 82 },
  { symbol: "UNI", direction: "SHORT", strength: 59 },
];

export default function DashboardPage() {
  const navigate = useNavigate();
  const [dirFilter, setDirFilter] = useState("all");
  const [tfFilter, setTfFilter] = useState("all");

  const filtered = mockSignals.filter(s => {
    if (dirFilter !== "all" && s.direction !== dirFilter) return false;
    if (tfFilter !== "all" && s.timeframe !== tfFilter) return false;
    return true;
  });

  return (
    <div className="p-3 space-y-3">
      {/* KPI Strip */}
      <div className="flex items-center gap-2 flex-wrap">
        <KPIChip label="Active" value="12" icon={<Activity className="h-3 w-3" />} />
        <KPIChip label="Win Rate" value="68.4%" icon={<TrendingUp className="h-3 w-3" />} trend="up" />
        <KPIChip label="TP Hit" value="34" icon={<Target className="h-3 w-3" />} trend="up" />
        <KPIChip label="SL Hit" value="16" icon={<Crosshair className="h-3 w-3" />} trend="down" />
        <KPIChip label="Avg Conf" value="76%" />
        <KPIChip label="Next Scan" value="2:34" icon={<Clock className="h-3 w-3" />} />
      </div>

      {/* Scanner Status */}
      <div className="flex items-center gap-3 px-3 py-1.5 bg-card border border-border rounded text-2xs">
        <div className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse-glow" />
          <span className="font-semibold text-primary">Scanner Active</span>
        </div>
        <span className="text-muted-foreground">Last scan: <span className="font-mono text-foreground">2m ago</span></span>
        <span className="text-muted-foreground">Next: <span className="font-mono text-foreground">2:34</span></span>
        <span className="text-muted-foreground">Pairs: <span className="font-mono text-foreground">142</span></span>
        <span className="text-muted-foreground">Found: <span className="font-mono text-foreground">8</span></span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
        {/* Signal Table - takes 3 cols */}
        <div className="lg:col-span-3">
          <Panel
            title="Live Signals"
            actions={
              <button className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
                <RefreshCw className="h-3 w-3" />
              </button>
            }
            noPad
          >
            {/* Filters */}
            <div className="px-3 py-2 border-b border-border">
              <FilterBar
                segments={[
                  {
                    label: "Direction",
                    options: [
                      { label: "All", value: "all" },
                      { label: "Long", value: "LONG" },
                      { label: "Short", value: "SHORT" },
                    ],
                    value: dirFilter,
                    onChange: setDirFilter,
                  },
                  {
                    label: "Timeframe",
                    options: [
                      { label: "All", value: "all" },
                      { label: "15M", value: "15M" },
                      { label: "1H", value: "1H" },
                      { label: "4H", value: "4H" },
                      { label: "1D", value: "1D" },
                    ],
                    value: tfFilter,
                    onChange: setTfFilter,
                  },
                ]}
              />
            </div>

            {/* Table Header */}
            <div className="grid grid-cols-[1fr_60px_50px_60px_80px_80px_80px_50px_55px_40px] px-3 py-1.5 text-2xs font-semibold text-muted-foreground uppercase tracking-wider border-b border-border">
              <span>Symbol</span>
              <span>Dir</span>
              <span>TF</span>
              <span>Conf</span>
              <span className="text-right">Entry</span>
              <span className="text-right">SL</span>
              <span className="text-right">TP1</span>
              <span className="text-right">RR</span>
              <span>Status</span>
              <span className="text-right">Age</span>
            </div>

            {/* Rows */}
            {filtered.map((s) => (
              <div
                key={s.id}
                onClick={() => navigate(`/signal/${s.id}`)}
                className="grid grid-cols-[1fr_60px_50px_60px_80px_80px_80px_50px_55px_40px] data-row"
              >
                <span className="font-medium text-foreground">{s.symbol}</span>
                <span><DirectionBadge direction={s.direction} /></span>
                <span className="text-muted-foreground">{s.timeframe}</span>
                <span><ConfidenceBadge value={s.confidence} /></span>
                <span className="text-right font-mono text-foreground">{s.entry}</span>
                <span className="text-right font-mono text-short">{s.sl}</span>
                <span className="text-right font-mono text-long">{s.tp1}</span>
                <span className="text-right font-mono text-foreground">{s.rr}</span>
                <span><StatusBadge status={s.status} /></span>
                <span className="text-right text-muted-foreground">{s.age}</span>
              </div>
            ))}
          </Panel>
        </div>

        {/* Heatmap - 1 col */}
        <div>
          <Panel title="Market Heatmap" noPad>
            <div className="grid grid-cols-2 gap-1 p-2">
              {heatmapData.map((h) => (
                <div
                  key={h.symbol}
                  className={cn(
                    "flex flex-col items-center justify-center py-2 rounded text-xs font-medium",
                    h.direction === "LONG"
                      ? "bg-long/10 text-long"
                      : "bg-short/10 text-short"
                  )}
                >
                  <span className="font-bold">{h.symbol}</span>
                  <span className="text-2xs font-mono opacity-80">{h.strength}%</span>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
