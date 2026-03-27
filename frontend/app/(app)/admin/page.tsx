"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatTimeAgo, getStatusColor, getStatusLabel } from "@/lib/formatters";
import {
  Users,
  Zap,
  DollarSign,
  BarChart2,
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

function StatCard({
  icon: Icon,
  value,
  label,
  color,
}: {
  icon: React.ElementType;
  value: string | number;
  label: string;
  color: string;
}) {
  return (
    <div className="bg-surface border border-border rounded-xl p-5 flex items-center gap-4">
      <div className={`p-3 rounded-lg bg-opacity-10 ${color} bg-current`}>
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      <div>
        <p className="text-2xl font-bold font-mono text-text-primary">{value}</p>
        <p className="text-sm text-text-muted mt-0.5">{label}</p>
      </div>
    </div>
  );
}

const planBadgeColors: Record<string, string> = {
  free: "text-text-muted bg-surface-2 border-border",
  trial: "text-gold bg-gold/10 border-gold/20",
  monthly: "text-purple bg-purple/10 border-purple/20",
  lifetime: "text-gold bg-gold/10 border-gold/30",
};

export default function AdminOverviewPage() {
  const {
    data: overview,
    isLoading: overviewLoading,
  } = useQuery<OverviewData>({
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
    <div className="space-y-6">
      {/* Stat Cards */}
      {overviewLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-24 bg-surface border border-border rounded-xl animate-pulse"
            />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          <StatCard
            icon={Users}
            value={overview?.users?.customers_total ?? 0}
            label="Total Customers"
            color="text-blue"
          />
          <StatCard
            icon={Zap}
            value={overview?.signals?.active ?? 0}
            label="Active Signals"
            color="text-long"
          />
          <StatCard
            icon={DollarSign}
            value={`$${(overview?.revenue?.mrr_usd ?? 0).toFixed(2)}`}
            label="Monthly Revenue"
            color="text-gold"
          />
          <StatCard
            icon={BarChart2}
            value={overview?.users?.new_customers_this_month ?? 0}
            label="New Customers (Month)"
            color="text-purple"
          />
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Recent Signals Table */}
        <div className="xl:col-span-2 bg-surface border border-border rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-border">
            <h2 className="font-semibold text-text-primary">Recent Signals</h2>
          </div>
          {signalsLoading ? (
            <div className="p-4 space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <div
                  key={i}
                  className="h-10 bg-surface-2 rounded animate-pulse"
                />
              ))}
            </div>
          ) : signals.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-text-muted">
              <Zap className="w-8 h-8 mb-3 opacity-30" />
              <p className="text-sm">No signals yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-surface-2">
                    <th className="text-left px-4 py-3 text-text-muted font-medium">
                      Symbol
                    </th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">
                      Direction
                    </th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">
                      TF
                    </th>
                    <th className="text-right px-4 py-3 text-text-muted font-medium">
                      Confidence
                    </th>
                    <th className="text-center px-4 py-3 text-text-muted font-medium">
                      Status
                    </th>
                    <th className="text-right px-4 py-3 text-text-muted font-medium">
                      Time
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {signals.map((signal, i) => {
                    const isLong = signal.direction === "LONG";
                    return (
                      <tr
                        key={signal.id}
                        className={`border-b border-border hover:bg-surface-2 transition-colors ${
                          i % 2 !== 0 ? "bg-surface-2/30" : ""
                        }`}
                      >
                        <td className="px-4 py-3 font-mono font-semibold text-text-primary">
                          {signal.symbol}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`flex items-center gap-1 text-xs font-medium ${
                              isLong ? "text-long" : "text-short"
                            }`}
                          >
                            {isLong ? (
                              <TrendingUp className="w-3 h-3" />
                            ) : (
                              <TrendingDown className="w-3 h-3" />
                            )}
                            {signal.direction}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-text-muted">
                          {signal.timeframe}
                        </td>
                        <td className="px-4 py-3 text-right font-mono text-text-primary">
                          {signal.confidence}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(
                              signal.status
                            )}`}
                          >
                            {getStatusLabel(signal.status)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right text-text-muted text-xs">
                          {formatTimeAgo(signal.fired_at)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Plan Distribution */}
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-border">
            <h2 className="font-semibold text-text-primary">Plan Distribution</h2>
          </div>
          {overviewLoading ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div
                  key={i}
                  className="h-10 bg-surface-2 rounded animate-pulse"
                />
              ))}
            </div>
          ) : !overview?.users?.by_plan_customers ? (
            <div className="flex items-center justify-center py-12 text-text-muted text-sm">
              No data available
            </div>
          ) : (
            <div className="divide-y divide-border">
              {Object.entries(overview.users.by_plan_customers).map(
                ([plan, count]) => {
                  const total = Object.values(
                    overview.users.by_plan_customers
                  ).reduce((a, b) => a + b, 0);
                  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                  return (
                    <div
                      key={plan}
                      className="px-5 py-3.5 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={`text-xs px-2.5 py-1 rounded-full border font-medium capitalize ${
                            planBadgeColors[plan] ??
                            "text-text-muted bg-surface-2 border-border"
                          }`}
                        >
                          {plan}
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-20 bg-surface-2 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="h-full bg-purple rounded-full"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className="text-sm font-mono font-semibold text-text-primary w-8 text-right">
                          {count}
                        </span>
                        <span className="text-xs text-text-muted w-8 text-right">
                          {pct}%
                        </span>
                      </div>
                    </div>
                  );
                }
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
