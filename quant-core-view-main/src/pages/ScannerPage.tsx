import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FilterBar } from "@/components/terminal/FilterBar";
import { Panel } from "@/components/terminal/Panel";
import { DirectionBadge, ConfidenceBadge } from "@/components/terminal/Badges";
import { ConfidenceBar } from "@/components/terminal/ConfidenceBar";
import { ArrowUpDown } from "lucide-react";
import { cn } from "@/lib/utils";

const mockSignals = [
  { id: "1", pair: "BTC/USDT", market: "Crypto", direction: "LONG" as const, timeframe: "4H", confidence: 87, entry: "67,200", sl: "66,400", tp1: "68,800", rr: "2.0", age: "12m" },
  { id: "2", pair: "ETH/USDT", market: "Crypto", direction: "LONG" as const, timeframe: "1H", confidence: 74, entry: "3,510", sl: "3,460", tp1: "3,620", rr: "2.2", age: "34m" },
  { id: "3", pair: "EUR/USD", market: "Forex", direction: "SHORT" as const, timeframe: "4H", confidence: 82, entry: "1.0855", sl: "1.0890", tp1: "1.0780", rr: "2.1", age: "1h" },
  { id: "4", pair: "GBP/JPY", market: "Forex", direction: "LONG" as const, timeframe: "1D", confidence: 91, entry: "192.40", sl: "191.20", tp1: "194.80", rr: "2.0", age: "2h" },
  { id: "5", pair: "SOL/USDT", market: "Crypto", direction: "SHORT" as const, timeframe: "15M", confidence: 63, entry: "142.50", sl: "144.80", tp1: "138.20", rr: "1.9", age: "45m" },
  { id: "6", pair: "XAU/USD", market: "Commodity", direction: "LONG" as const, timeframe: "1H", confidence: 79, entry: "2,338", sl: "2,325", tp1: "2,365", rr: "2.1", age: "18m" },
  { id: "7", pair: "ADA/USDT", market: "Crypto", direction: "LONG" as const, timeframe: "4H", confidence: 68, entry: "0.4520", sl: "0.4410", tp1: "0.4740", rr: "2.0", age: "3h" },
  { id: "8", pair: "USD/CHF", market: "Forex", direction: "SHORT" as const, timeframe: "1H", confidence: 85, entry: "0.8920", sl: "0.8955", tp1: "0.8845", rr: "2.1", age: "55m" },
  { id: "9", pair: "DOGE/USDT", market: "Crypto", direction: "LONG" as const, timeframe: "15M", confidence: 56, entry: "0.1245", sl: "0.1210", tp1: "0.1315", rr: "2.0", age: "8m" },
  { id: "10", pair: "NZD/USD", market: "Forex", direction: "SHORT" as const, timeframe: "4H", confidence: 72, entry: "0.6120", sl: "0.6155", tp1: "0.6050", rr: "2.0", age: "1.5h" },
];

export default function ScannerPage() {
  const navigate = useNavigate();
  const [dirFilter, setDirFilter] = useState("all");
  const [marketFilter, setMarketFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<string>("confidence");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const filtered = mockSignals
    .filter(s => {
      if (dirFilter !== "all" && s.direction !== dirFilter) return false;
      if (marketFilter !== "all" && s.market !== marketFilter) return false;
      if (search && !s.pair.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    })
    .sort((a, b) => {
      const mult = sortDir === "desc" ? -1 : 1;
      if (sortBy === "confidence") return (a.confidence - b.confidence) * mult;
      if (sortBy === "pair") return a.pair.localeCompare(b.pair) * mult;
      return 0;
    });

  const toggleSort = (col: string) => {
    if (sortBy === col) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortBy(col); setSortDir("desc"); }
  };

  const SortHeader = ({ col, children, className }: { col: string; children: React.ReactNode; className?: string }) => (
    <button onClick={() => toggleSort(col)} className={cn("flex items-center gap-0.5 hover:text-foreground transition-colors", className)}>
      {children}
      <ArrowUpDown className={cn("h-2.5 w-2.5", sortBy === col ? "text-primary" : "opacity-30")} />
    </button>
  );

  return (
    <div className="p-3 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h1 className="text-sm font-semibold text-foreground">Scanner</h1>
          <span className="text-2xs text-muted-foreground font-mono">{filtered.length} signals</span>
        </div>
      </div>

      <Panel noPad>
        {/* Filter Bar */}
        <div className="px-3 py-2 border-b border-border">
          <FilterBar
            onSearch={setSearch}
            searchPlaceholder="Search pairs..."
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
                label: "Market",
                options: [
                  { label: "All", value: "all" },
                  { label: "Crypto", value: "Crypto" },
                  { label: "Forex", value: "Forex" },
                  { label: "Commodity", value: "Commodity" },
                ],
                value: marketFilter,
                onChange: setMarketFilter,
              },
            ]}
          />
        </div>

        {/* Table */}
        <div className="grid grid-cols-[1fr_70px_60px_50px_100px_80px_80px_80px_50px_45px] px-3 py-1.5 text-2xs font-semibold text-muted-foreground uppercase tracking-wider border-b border-border">
          <SortHeader col="pair">Pair</SortHeader>
          <span>Market</span>
          <span>Dir</span>
          <span>TF</span>
          <SortHeader col="confidence">Confidence</SortHeader>
          <span className="text-right">Entry</span>
          <span className="text-right">SL</span>
          <span className="text-right">TP1</span>
          <span className="text-right">RR</span>
          <span className="text-right">Age</span>
        </div>

        {filtered.map((s) => (
          <div
            key={s.id}
            onClick={() => navigate(`/signal/${s.id}`)}
            className="grid grid-cols-[1fr_70px_60px_50px_100px_80px_80px_80px_50px_45px] data-row"
          >
            <span className="font-medium text-foreground">{s.pair}</span>
            <span className="text-muted-foreground">{s.market}</span>
            <span><DirectionBadge direction={s.direction} /></span>
            <span className="text-muted-foreground">{s.timeframe}</span>
            <span><ConfidenceBar value={s.confidence} /></span>
            <span className="text-right font-mono text-foreground">{s.entry}</span>
            <span className="text-right font-mono text-short">{s.sl}</span>
            <span className="text-right font-mono text-long">{s.tp1}</span>
            <span className="text-right font-mono text-foreground">{s.rr}</span>
            <span className="text-right text-muted-foreground">{s.age}</span>
          </div>
        ))}
      </Panel>
    </div>
  );
}
