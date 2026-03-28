import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Share2, TrendingUp, TrendingDown, Clock, Target } from "lucide-react";
import { Panel } from "@/components/terminal/Panel";
import { DirectionBadge, StatusBadge } from "@/components/terminal/Badges";
import { ConfidenceBar } from "@/components/terminal/ConfidenceBar";
import { cn } from "@/lib/utils";

const signal = {
  id: "1",
  symbol: "BTC/USDT",
  direction: "LONG" as const,
  timeframe: "4H",
  confidence: 87,
  status: "active" as const,
  entry: "67,200.00",
  sl: "66,400.00",
  tp1: "68,800.00",
  tp2: "70,200.00",
  tp3: "72,000.00",
  rr: "2.0",
  pnl: "+1.24%",
  createdAt: "2024-03-27 14:30 UTC",
  mtf: [
    { tf: "15M", direction: "LONG", confidence: 72, aligned: true },
    { tf: "1H", direction: "LONG", confidence: 81, aligned: true },
    { tf: "4H", direction: "LONG", confidence: 87, aligned: true },
    { tf: "1D", direction: "LONG", confidence: 64, aligned: true },
    { tf: "1W", direction: "SHORT", confidence: 45, aligned: false },
  ],
  confluences: [
    "Strong bullish divergence on RSI (4H)",
    "Price above 200 EMA on multiple timeframes",
    "ICT bullish order block at 67,000",
    "Volume profile POC acting as support",
    "Fibonacci 0.618 retracement confluence",
  ],
  categories: [
    { name: "Trend", score: 82 },
    { name: "Momentum", score: 78 },
    { name: "Volume", score: 71 },
    { name: "Volatility", score: 65 },
    { name: "ICT/SMC", score: 88 },
    { name: "Support/Resistance", score: 74 },
  ],
};

export default function SignalDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams();

  return (
    <div className="p-3 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div className="flex items-center gap-2">
            <span className="text-base font-bold text-foreground">{signal.symbol}</span>
            <DirectionBadge direction={signal.direction} />
            <StatusBadge status={signal.status} />
            <span className="text-2xs text-muted-foreground">{signal.timeframe}</span>
          </div>
        </div>
        <button className="filter-pill gap-1">
          <Share2 className="h-3 w-3" />
          Share
        </button>
      </div>

      {/* Hero Stats Row */}
      <div className="flex items-center gap-4 px-3 py-2.5 bg-card border border-border rounded">
        <div className="flex items-center gap-2">
          <span className="text-2xs text-muted-foreground uppercase">Confidence</span>
          <ConfidenceBar value={signal.confidence} className="w-24" />
        </div>
        <div className="h-4 w-px bg-border" />
        <div className="flex items-center gap-1.5">
          <span className="text-2xs text-muted-foreground uppercase">RR</span>
          <span className="font-mono font-bold text-sm text-foreground">{signal.rr}</span>
        </div>
        <div className="h-4 w-px bg-border" />
        <div className="flex items-center gap-1.5">
          <span className="text-2xs text-muted-foreground uppercase">PnL</span>
          <span className="font-mono font-bold text-sm text-long">{signal.pnl}</span>
        </div>
        <div className="h-4 w-px bg-border" />
        <div className="flex items-center gap-1.5">
          <Clock className="h-3 w-3 text-muted-foreground" />
          <span className="text-2xs text-muted-foreground">{signal.createdAt}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* Chart Area */}
        <div className="lg:col-span-2">
          <Panel title="Chart" className="h-80">
            <div className="h-full flex items-center justify-center text-muted-foreground text-xs">
              <div className="text-center space-y-2">
                <TrendingUp className="h-8 w-8 mx-auto opacity-30" />
                <p>TradingView Chart</p>
                <p className="text-2xs">Entry / SL / TP overlays</p>
              </div>
            </div>
          </Panel>
        </div>

        {/* Price Levels */}
        <div className="space-y-3">
          <Panel title="Price Levels" noPad>
            {[
              { label: "Entry", value: signal.entry, color: "text-foreground" },
              { label: "Stop Loss", value: signal.sl, color: "text-short" },
              { label: "TP1", value: signal.tp1, color: "text-long" },
              { label: "TP2", value: signal.tp2, color: "text-long" },
              { label: "TP3", value: signal.tp3, color: "text-long" },
            ].map((level) => (
              <div key={level.label} className="flex items-center justify-between px-3 py-1.5 border-b border-border last:border-0 text-xs">
                <span className="text-muted-foreground">{level.label}</span>
                <span className={cn("font-mono font-semibold", level.color)}>{level.value}</span>
              </div>
            ))}
          </Panel>

          {/* Top Confluences */}
          <Panel title="Top Confluences" noPad>
            {signal.confluences.map((c, i) => (
              <div key={i} className="flex items-start gap-2 px-3 py-1.5 border-b border-border last:border-0 text-2xs">
                <Target className="h-3 w-3 text-primary shrink-0 mt-0.5" />
                <span className="text-foreground">{c}</span>
              </div>
            ))}
          </Panel>
        </div>
      </div>

      {/* MTF Analysis & Indicator Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Panel title="Multi-Timeframe Analysis" noPad>
          <div className="grid grid-cols-[60px_60px_1fr_50px] px-3 py-1 text-2xs font-semibold text-muted-foreground uppercase border-b border-border">
            <span>TF</span>
            <span>Dir</span>
            <span>Confidence</span>
            <span>Aligned</span>
          </div>
          {signal.mtf.map((tf) => (
            <div key={tf.tf} className="grid grid-cols-[60px_60px_1fr_50px] items-center px-3 py-1.5 border-b border-border last:border-0 text-xs">
              <span className="font-mono text-foreground">{tf.tf}</span>
              <DirectionBadge direction={tf.direction as "LONG" | "SHORT"} />
              <ConfidenceBar value={tf.confidence} />
              <span className={cn("text-2xs font-semibold", tf.aligned ? "text-long" : "text-short")}>
                {tf.aligned ? "✓" : "✗"}
              </span>
            </div>
          ))}
        </Panel>

        <Panel title="Indicator Breakdown" noPad>
          {signal.categories.map((cat) => (
            <div key={cat.name} className="flex items-center gap-3 px-3 py-2 border-b border-border last:border-0">
              <span className="text-xs text-muted-foreground w-28">{cat.name}</span>
              <ConfidenceBar value={cat.score} className="flex-1" />
            </div>
          ))}
        </Panel>
      </div>
    </div>
  );
}
