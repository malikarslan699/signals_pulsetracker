"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatTimeAgo, getStatusColor, getStatusLabel } from "@/lib/formatters";
import { Panel } from "@/components/terminal/Panel";
import { KPICard } from "@/components/terminal/KPIChip";
import { DirectionBadge, StatusBadge } from "@/components/terminal/Badges";
import {
  Users,
  Zap,
  DollarSign,
  UserPlus,
  TrendingUp,
  TrendingDown,
} from "lucide-react";

interface OverviewData {
  users: {
    total_accounts: number;
    active_accounts: number;
    staff_total: number;
    customers_total: number;
    customers_active: number;
    paid_customers: number;
    new_customers_this_month: number;
    by_plan_customers: Record<string, number>;
  };
  signals: {
    active: number;
    win_rate_pct_90d: number;
  };
  revenue: {
    mrr_usd: number;
    lifetime_total_usd: number;
  };
}

interface Signal {
  id: string;
  symbol: string;
  direction: string;
  timeframe: string;
  confidence: number;
  status: string;
  fired_at: string;
}

const planBadgeColors: Record<string, string> = {
  free: "text-text-muted bg-surface-2 border-border",
  trial: "text-gold bg-gold/10 border-gold/20",
  monthly: "text-long bg-long/10 border-long/20",
  lifetime: "text-gold bg-gold/10 border-gold/30",
};

export default function AdminOverviewPage() {
  const { data: overview, isLoading: overviewLoading } =
    useQuery<OverviewData>({
      queryKey: ["admin-overview"],
      queryFn: () =>
        api.get("/api/v1/admin/analytics/overview").then((r) => r.data),
      refetchInterval: 30_000,
    });

  const { data: signalsData, isLoading: signalsLoading } = useQuery<{
    items: Signal[];
  }>({
    queryKey: ["admin-recent-signals"],
    queryFn: () =>
      api.get("/api/v1/signals/?limit=10").then((r) => r.data),
    refetchInterval: 30_000,
  });

  const signals: Signal[] = signalsData?.items || [];

  return (
    <div className="space-y-3">
      {/* KPI Cards */}
      {overviewLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-20 bg-surface border border-border rounded animate-pulse"
            />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <KPICard
            label="Total Customers"
            value={String(overview?.users?.customers_total ?? 0)}
            icon={<Users className="h-3.5 w-3.5" />}
          />
          <KPICard
            label="Active Signals"
            value={String(overview?.signals?.active ?? 0)}
            icon={<Zap className="h-3.5 w-3.5" />}
            trend="up"
          />
          <KPICard
            label="MRR"
            value={`$${(overview?.revenue?.mrr_usd ?? 0).toFixed(2)}`}
            icon={<DollarSign className="h-3.5 w-3.5" />}
            trend="up"
          />
          <KPICard
            label="New This Month"
            value={String(overview?.users?.new_customers_this_month ?? 0)}
            icon={<UserPlus className="h-3.5 w-3.5" />}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Recent Signals */}
        <Panel title="Recent Signals" noPad>
          {signalsLoading ? (
            <div className="p-3 space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-8 bg-surface-2 rounded animate-pulse" />
              ))}
            </div>
          ) : signals.length === 0 ? (
            <div className="flex items-center justify-center py-8 text-text-muted text-xs">
              No signals yet
            </div>
          ) : (
            signals.map((s, i) => (
              <div
                key={s.id}
                className="flex items-center justify-between px-3 py-1.5 border-b border-border last:border-0 text-xs"
              >
                <div className="flex items-center gap-2">
                  <span className="font-medium text-text-primary font-mono">{s.symbol}</span>
                  <DirectionBadge direction={s.direction as "LONG" | "SHORT"} />
                  <span className="text-text-muted">{s.timeframe}</span>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={s.status as any} />
                  <span className="text-2xs text-text-muted">{formatTimeAgo(s.fired_at)}</span>
                </div>
              </div>
            ))
          )}
        </Panel>

        {/* Plan Distribution */}
        <Panel title="Plan Distribution" noPad>
          {overviewLoading ? (
            <div className="p-3 space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-8 bg-surface-2 rounded animate-pulse" />
              ))}
            </div>
          ) : !overview?.users?.by_plan_customers ? (
            <div className="flex items-center justify-center py-8 text-text-muted text-xs">
              No data available
            </div>
          ) : (
            Object.entries(overview.users.by_plan_customers).map(([plan, count]) => {
              const total = Object.values(overview.users.by_plan_customers).reduce(
                (a, b) => a + b,
                0
              );
              const pct = total > 0 ? Math.round((count / total) * 100) : 0;
              return (
                <div
                  key={plan}
                  className="flex items-center gap-3 px-3 py-2 border-b border-border last:border-0"
                >
                  <span className="text-xs text-text-primary w-20 capitalize">{plan}</span>
                  <div className="flex-1 h-1.5 bg-surface-2 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-long rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="font-mono text-2xs text-text-muted w-8 text-right">
                    {count}
                  </span>
                  <span className="font-mono text-2xs text-text-primary w-8 text-right">
                    {pct}%
                  </span>
                </div>
              );
            })
          )}
        </Panel>
      </div>
    </div>
  );
}
