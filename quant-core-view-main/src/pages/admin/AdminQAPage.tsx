import { useState } from "react";
import { Panel } from "@/components/terminal/Panel";
import { FilterBar } from "@/components/terminal/FilterBar";
import { KPICard } from "@/components/terminal/KPIChip";
import { DirectionBadge, StatusBadge, ConfidenceBadge } from "@/components/terminal/Badges";
import { ConfidenceBar } from "@/components/terminal/ConfidenceBar";
import { ChevronDown, ChevronUp, Activity, AlertTriangle, Target } from "lucide-react";
import { cn } from "@/lib/utils";

const tabs = ["Signal Log", "QA Stats", "Noisy Pairs", "Failure Analysis"];

const signalLog = [
  { id: "1", symbol: "BTC/USDT", direction: "LONG" as const, tf: "4H", confidence: 87, status: "tp1" as const, confirmations: 8, missing: 1, assessment: "Strong" },
  { id: "2", symbol: "EUR/USD", direction: "SHORT" as const, tf: "1H", confidence: 74, status: "sl" as const, confirmations: 5, missing: 3, assessment: "Moderate" },
  { id: "3", symbol: "SOL/USDT", direction: "SHORT" as const, tf: "15M", confidence: 63, status: "sl" as const, confirmations: 4, missing: 4, assessment: "Weak" },
];

const noisyPairs = [
  { pair: "DOGE/USDT", signals: 18, winRate: "33%", avgConf: "58%", status: "noisy" },
  { pair: "SHIB/USDT", signals: 12, winRate: "25%", avgConf: "52%", status: "noisy" },
  { pair: "TRX/USDT", signals: 8, winRate: "38%", avgConf: "61%", status: "borderline" },
];

export default function AdminQAPage() {
  const [activeTab, setActiveTab] = useState("Signal Log");
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="space-y-3">
      {/* Tabs */}
      <div className="flex items-center gap-1">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn("filter-pill", activeTab === tab && "filter-pill-active")}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "Signal Log" && (
        <Panel noPad>
          <div className="grid grid-cols-[1fr_60px_50px_55px_55px_55px_55px_70px] px-3 py-1.5 text-2xs font-semibold text-muted-foreground uppercase tracking-wider border-b border-border">
            <span>Symbol</span><span>Dir</span><span>TF</span><span>Conf</span><span>Status</span><span>Conf.</span><span>Miss.</span><span>Assessment</span>
          </div>
          {signalLog.map((s) => (
            <div key={s.id}>
              <div
                onClick={() => setExpanded(e => e === s.id ? null : s.id)}
                className="grid grid-cols-[1fr_60px_50px_55px_55px_55px_55px_70px] data-row"
              >
                <span className="font-medium text-foreground flex items-center gap-1">
                  {expanded === s.id ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                  {s.symbol}
                </span>
                <span><DirectionBadge direction={s.direction} /></span>
                <span className="text-muted-foreground">{s.tf}</span>
                <span><ConfidenceBadge value={s.confidence} /></span>
                <span><StatusBadge status={s.status} /></span>
                <span className="font-mono text-foreground">{s.confirmations}</span>
                <span className="font-mono text-short">{s.missing}</span>
                <span className={cn("text-2xs font-semibold",
                  s.assessment === "Strong" ? "text-long" : s.assessment === "Moderate" ? "text-warning" : "text-short"
                )}>{s.assessment}</span>
              </div>
              {expanded === s.id && (
                <div className="px-3 py-2 bg-accent/30 border-b border-border">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-2xs">
                    {[
                      { cat: "Trend", score: 82 },
                      { cat: "Momentum", score: 78 },
                      { cat: "Volume", score: 65 },
                      { cat: "ICT/SMC", score: 88 },
                    ].map(c => (
                      <div key={c.cat} className="flex items-center gap-2">
                        <span className="text-muted-foreground w-20">{c.cat}</span>
                        <ConfidenceBar value={c.score} className="flex-1" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </Panel>
      )}

      {activeTab === "QA Stats" && (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
          <KPICard label="Avg Confirmations" value="6.2" icon={<Target className="h-3.5 w-3.5" />} />
          <KPICard label="Avg Missing" value="2.1" icon={<AlertTriangle className="h-3.5 w-3.5" />} trend="down" />
          <KPICard label="Strong Assessments" value="64%" icon={<Activity className="h-3.5 w-3.5" />} trend="up" />
        </div>
      )}

      {activeTab === "Noisy Pairs" && (
        <Panel title="High-Volume Low-Win Pairs" noPad>
          <div className="grid grid-cols-[1fr_60px_60px_60px_70px] px-3 py-1.5 text-2xs font-semibold text-muted-foreground uppercase border-b border-border">
            <span>Pair</span><span>Signals</span><span>Win Rate</span><span>Avg Conf</span><span>Status</span>
          </div>
          {noisyPairs.map(p => (
            <div key={p.pair} className="grid grid-cols-[1fr_60px_60px_60px_70px] data-row">
              <span className="font-medium text-foreground">{p.pair}</span>
              <span className="font-mono text-foreground">{p.signals}</span>
              <span className="font-mono text-short">{p.winRate}</span>
              <span className="font-mono text-warning">{p.avgConf}</span>
              <span className={cn("text-2xs font-semibold", p.status === "noisy" ? "text-short" : "text-warning")}>
                {p.status}
              </span>
            </div>
          ))}
        </Panel>
      )}

      {activeTab === "Failure Analysis" && (
        <div className="space-y-3">
          <Panel title="SL Hits by Timeframe" noPad>
            <div className="grid grid-cols-[60px_1fr_60px] px-3 py-1 text-2xs font-semibold text-muted-foreground uppercase border-b border-border">
              <span>TF</span><span>Distribution</span><span>Count</span>
            </div>
            {[
              { tf: "15M", count: 12, pct: 38 },
              { tf: "1H", count: 8, pct: 25 },
              { tf: "4H", count: 6, pct: 19 },
              { tf: "1D", count: 4, pct: 13 },
            ].map(t => (
              <div key={t.tf} className="grid grid-cols-[60px_1fr_60px] items-center px-3 py-1.5 border-b border-border last:border-0">
                <span className="font-mono text-xs text-foreground">{t.tf}</span>
                <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                  <div className="h-full bg-short rounded-full" style={{ width: `${t.pct}%` }} />
                </div>
                <span className="font-mono text-xs text-right text-foreground">{t.count}</span>
              </div>
            ))}
          </Panel>
        </div>
      )}
    </div>
  );
}
