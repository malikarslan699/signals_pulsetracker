import { useState } from "react";
import { KPICard } from "@/components/terminal/KPIChip";
import { Panel } from "@/components/terminal/Panel";
import { TrendingUp, Activity, Target, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";

const dailyData = [
  { day: "Mar 14", total: 8, wins: 5, losses: 3 },
  { day: "Mar 15", total: 12, wins: 9, losses: 3 },
  { day: "Mar 16", total: 6, wins: 4, losses: 2 },
  { day: "Mar 17", total: 10, wins: 7, losses: 3 },
  { day: "Mar 18", total: 14, wins: 10, losses: 4 },
  { day: "Mar 19", total: 9, wins: 6, losses: 3 },
  { day: "Mar 20", total: 11, wins: 8, losses: 3 },
  { day: "Mar 21", total: 7, wins: 5, losses: 2 },
  { day: "Mar 22", total: 13, wins: 9, losses: 4 },
  { day: "Mar 23", total: 10, wins: 7, losses: 3 },
  { day: "Mar 24", total: 8, wins: 6, losses: 2 },
  { day: "Mar 25", total: 15, wins: 11, losses: 4 },
  { day: "Mar 26", total: 11, wins: 8, losses: 3 },
  { day: "Mar 27", total: 9, wins: 7, losses: 2 },
];

const tfData = [
  { tf: "15M", count: 24 },
  { tf: "1H", count: 38 },
  { tf: "4H", count: 52 },
  { tf: "1D", count: 18 },
  { tf: "1W", count: 6 },
];

export default function StatsPage() {
  const [range, setRange] = useState("14d");

  return (
    <div className="p-3 space-y-3">
      <div className="flex items-center justify-between">
        <h1 className="text-sm font-semibold text-foreground">Trading Stats</h1>
        <div className="flex items-center gap-0.5">
          {["7d", "14d", "30d", "90d"].map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={cn("filter-pill", range === r && "filter-pill-active")}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KPICard label="Win Rate" value="68.4%" icon={<TrendingUp className="h-3.5 w-3.5" />} trend="up" subtitle="↑ 2.1% vs last period" />
        <KPICard label="Total Signals" value="156" icon={<Activity className="h-3.5 w-3.5" />} subtitle="14-day period" />
        <KPICard label="Active" value="12" icon={<Target className="h-3.5 w-3.5" />} trend="up" />
        <KPICard label="Avg Confidence" value="76%" icon={<BarChart3 className="h-3.5 w-3.5" />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* Daily Activity Chart */}
        <Panel title="Daily Activity" className="lg:col-span-2">
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dailyData}>
                <XAxis dataKey="day" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} width={24} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "6px",
                    fontSize: "11px",
                  }}
                />
                <Area type="monotone" dataKey="wins" stackId="1" stroke="hsl(var(--long))" fill="hsl(var(--long))" fillOpacity={0.3} />
                <Area type="monotone" dataKey="losses" stackId="1" stroke="hsl(var(--short))" fill="hsl(var(--short))" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        {/* Timeframe Distribution */}
        <Panel title="By Timeframe">
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={tfData}>
                <XAxis dataKey="tf" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} width={24} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "6px",
                    fontSize: "11px",
                  }}
                />
                <Bar dataKey="count" fill="hsl(var(--primary))" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
    </div>
  );
}
