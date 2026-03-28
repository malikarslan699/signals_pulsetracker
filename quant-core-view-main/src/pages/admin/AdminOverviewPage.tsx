import { KPICard } from "@/components/terminal/KPIChip";
import { Panel } from "@/components/terminal/Panel";
import { StatusBadge, DirectionBadge } from "@/components/terminal/Badges";
import { Users, Activity, DollarSign, UserPlus } from "lucide-react";

const recentSignals = [
  { symbol: "BTC/USDT", direction: "LONG" as const, status: "active" as const, time: "12m ago" },
  { symbol: "EUR/USD", direction: "SHORT" as const, status: "tp1" as const, time: "34m ago" },
  { symbol: "ETH/USDT", direction: "LONG" as const, status: "sl" as const, time: "1h ago" },
  { symbol: "GBP/JPY", direction: "LONG" as const, status: "active" as const, time: "2h ago" },
  { symbol: "SOL/USDT", direction: "SHORT" as const, status: "expired" as const, time: "3h ago" },
];

const planDist = [
  { plan: "Trial", count: 234, pct: 45 },
  { plan: "Monthly", count: 156, pct: 30 },
  { plan: "Yearly", count: 98, pct: 19 },
  { plan: "Lifetime", count: 32, pct: 6 },
];

export default function AdminOverviewPage() {
  return (
    <div className="space-y-3">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KPICard label="Total Customers" value="520" icon={<Users className="h-3.5 w-3.5" />} />
        <KPICard label="Active Signals" value="12" icon={<Activity className="h-3.5 w-3.5" />} trend="up" />
        <KPICard label="MRR" value="$4,280" icon={<DollarSign className="h-3.5 w-3.5" />} trend="up" subtitle="↑ 8% vs last month" />
        <KPICard label="New This Month" value="34" icon={<UserPlus className="h-3.5 w-3.5" />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Recent Signals */}
        <Panel title="Recent Signals" noPad>
          {recentSignals.map((s, i) => (
            <div key={i} className="flex items-center justify-between px-3 py-1.5 border-b border-border last:border-0 text-xs">
              <div className="flex items-center gap-2">
                <span className="font-medium text-foreground">{s.symbol}</span>
                <DirectionBadge direction={s.direction} />
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={s.status} />
                <span className="text-2xs text-muted-foreground">{s.time}</span>
              </div>
            </div>
          ))}
        </Panel>

        {/* Plan Distribution */}
        <Panel title="Plan Distribution" noPad>
          {planDist.map((p) => (
            <div key={p.plan} className="flex items-center gap-3 px-3 py-2 border-b border-border last:border-0">
              <span className="text-xs text-foreground w-20">{p.plan}</span>
              <div className="flex-1 h-1.5 bg-secondary rounded-full overflow-hidden">
                <div className="h-full bg-primary rounded-full" style={{ width: `${p.pct}%` }} />
              </div>
              <span className="font-mono text-2xs text-muted-foreground w-8 text-right">{p.count}</span>
              <span className="font-mono text-2xs text-foreground w-8 text-right">{p.pct}%</span>
            </div>
          ))}
        </Panel>
      </div>
    </div>
  );
}
