import { KPICard } from "@/components/terminal/KPIChip";
import { Panel } from "@/components/terminal/Panel";
import { Activity, Target, TrendingUp } from "lucide-react";

const tfStats = [
  { tf: "15M", signals: 24, winRate: "62%", avgConf: "68%" },
  { tf: "1H", signals: 38, winRate: "70%", avgConf: "74%" },
  { tf: "4H", signals: 52, winRate: "72%", avgConf: "78%" },
  { tf: "1D", signals: 18, winRate: "78%", avgConf: "82%" },
];

const topSymbols = [
  { symbol: "BTC/USDT", signals: 28, winRate: "75%" },
  { symbol: "ETH/USDT", signals: 22, winRate: "68%" },
  { symbol: "EUR/USD", signals: 18, winRate: "72%" },
  { symbol: "GBP/JPY", signals: 14, winRate: "64%" },
  { symbol: "XAU/USD", signals: 12, winRate: "83%" },
];

export default function AdminAnalyticsPage() {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        <KPICard label="Total Signals" value="156" icon={<Activity className="h-3.5 w-3.5" />} />
        <KPICard label="Avg Confidence" value="76%" icon={<Target className="h-3.5 w-3.5" />} />
        <KPICard label="Top Symbol" value="BTC/USDT" icon={<TrendingUp className="h-3.5 w-3.5" />} subtitle="28 signals" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Panel title="By Timeframe" noPad>
          <div className="grid grid-cols-[60px_1fr_60px_60px] px-3 py-1 text-2xs font-semibold text-muted-foreground uppercase border-b border-border">
            <span>TF</span><span>Signals</span><span>Win Rate</span><span>Avg Conf</span>
          </div>
          {tfStats.map(t => (
            <div key={t.tf} className="grid grid-cols-[60px_1fr_60px_60px] px-3 py-1.5 border-b border-border last:border-0 text-xs">
              <span className="font-mono text-foreground">{t.tf}</span>
              <span className="font-mono text-foreground">{t.signals}</span>
              <span className="font-mono text-long">{t.winRate}</span>
              <span className="font-mono text-foreground">{t.avgConf}</span>
            </div>
          ))}
        </Panel>

        <Panel title="Top Symbols" noPad>
          <div className="grid grid-cols-[1fr_60px_60px] px-3 py-1 text-2xs font-semibold text-muted-foreground uppercase border-b border-border">
            <span>Symbol</span><span>Signals</span><span>Win Rate</span>
          </div>
          {topSymbols.map(s => (
            <div key={s.symbol} className="grid grid-cols-[1fr_60px_60px] px-3 py-1.5 border-b border-border last:border-0 text-xs">
              <span className="font-medium text-foreground">{s.symbol}</span>
              <span className="font-mono text-foreground">{s.signals}</span>
              <span className="font-mono text-long">{s.winRate}</span>
            </div>
          ))}
        </Panel>
      </div>
    </div>
  );
}
