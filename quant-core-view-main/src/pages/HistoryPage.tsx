import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { KPIChip } from "@/components/terminal/KPIChip";
import { FilterBar } from "@/components/terminal/FilterBar";
import { Panel } from "@/components/terminal/Panel";
import { DirectionBadge, StatusBadge, ConfidenceBadge } from "@/components/terminal/Badges";
import { TrendingUp, Target, Crosshair, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

const mockHistory = [
  { id: "1", pair: "BTC/USDT", direction: "LONG" as const, tf: "4H", confidence: 87, entry: "67,200", tp1: "68,800", sl: "66,400", status: "tp1" as const, pnl: "+2.38%", time: "2h ago" },
  { id: "2", pair: "EUR/USD", direction: "SHORT" as const, tf: "1H", confidence: 74, entry: "1.0855", tp1: "1.0780", sl: "1.0890", status: "sl" as const, pnl: "-0.32%", time: "4h ago" },
  { id: "3", pair: "ETH/USDT", direction: "LONG" as const, tf: "4H", confidence: 91, entry: "3,510", tp1: "3,620", sl: "3,460", status: "tp2" as const, pnl: "+4.12%", time: "6h ago" },
  { id: "4", pair: "GBP/JPY", direction: "LONG" as const, tf: "1D", confidence: 68, entry: "192.40", tp1: "194.80", sl: "191.20", status: "expired" as const, pnl: "0.00%", time: "8h ago" },
  { id: "5", pair: "SOL/USDT", direction: "SHORT" as const, tf: "15M", confidence: 63, entry: "142.50", tp1: "138.20", sl: "144.80", status: "sl" as const, pnl: "-1.61%", time: "12h ago" },
  { id: "6", pair: "XAU/USD", direction: "LONG" as const, tf: "1H", confidence: 82, entry: "2,338", tp1: "2,365", sl: "2,325", status: "tp1" as const, pnl: "+1.15%", time: "14h ago" },
  { id: "7", pair: "ADA/USDT", direction: "LONG" as const, tf: "4H", confidence: 79, entry: "0.4520", tp1: "0.4740", sl: "0.4410", status: "tp3" as const, pnl: "+6.42%", time: "1d ago" },
  { id: "8", pair: "USD/CHF", direction: "SHORT" as const, tf: "1H", confidence: 85, entry: "0.8920", tp1: "0.8845", sl: "0.8955", status: "tp1" as const, pnl: "+0.84%", time: "1d ago" },
];

export default function HistoryPage() {
  const navigate = useNavigate();
  const [dirFilter, setDirFilter] = useState("all");

  const filtered = mockHistory.filter(s => dirFilter === "all" || s.direction === dirFilter);

  return (
    <div className="p-3 space-y-3">
      <h1 className="text-sm font-semibold text-foreground">Signal History</h1>

      {/* KPI Strip */}
      <div className="flex items-center gap-2 flex-wrap">
        <KPIChip label="Total" value="156" icon={<Activity className="h-3 w-3" />} />
        <KPIChip label="Win Rate" value="68.4%" icon={<TrendingUp className="h-3 w-3" />} trend="up" />
        <KPIChip label="TP Hits" value="82" icon={<Target className="h-3 w-3" />} trend="up" />
        <KPIChip label="SL Hits" value="38" icon={<Crosshair className="h-3 w-3" />} trend="down" />
        <KPIChip label="Expired" value="36" />
      </div>

      <Panel noPad>
        <div className="px-3 py-2 border-b border-border">
          <FilterBar
            segments={[{
              label: "Direction",
              options: [
                { label: "All", value: "all" },
                { label: "Long", value: "LONG" },
                { label: "Short", value: "SHORT" },
              ],
              value: dirFilter,
              onChange: setDirFilter,
            }]}
          />
        </div>

        <div className="grid grid-cols-[1fr_60px_50px_55px_80px_80px_80px_55px_70px_60px] px-3 py-1.5 text-2xs font-semibold text-muted-foreground uppercase tracking-wider border-b border-border">
          <span>Pair</span>
          <span>Dir</span>
          <span>TF</span>
          <span>Conf</span>
          <span className="text-right">Entry</span>
          <span className="text-right">TP1</span>
          <span className="text-right">SL</span>
          <span>Status</span>
          <span className="text-right">PnL</span>
          <span className="text-right">Time</span>
        </div>

        {filtered.map((s) => (
          <div
            key={s.id}
            onClick={() => navigate(`/signal/${s.id}`)}
            className="grid grid-cols-[1fr_60px_50px_55px_80px_80px_80px_55px_70px_60px] data-row"
          >
            <span className="font-medium text-foreground">{s.pair}</span>
            <span><DirectionBadge direction={s.direction} /></span>
            <span className="text-muted-foreground">{s.tf}</span>
            <span><ConfidenceBadge value={s.confidence} /></span>
            <span className="text-right font-mono text-foreground">{s.entry}</span>
            <span className="text-right font-mono text-long">{s.tp1}</span>
            <span className="text-right font-mono text-short">{s.sl}</span>
            <span><StatusBadge status={s.status} /></span>
            <span className={cn("text-right font-mono font-semibold", s.pnl.startsWith("+") ? "text-long" : s.pnl.startsWith("-") ? "text-short" : "text-muted-foreground")}>{s.pnl}</span>
            <span className="text-right text-muted-foreground">{s.time}</span>
          </div>
        ))}
      </Panel>
    </div>
  );
}
