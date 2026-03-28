"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
import { Panel } from "@/components/terminal/Panel";
import { RefreshCw, CheckCircle2, XCircle, Clock, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";

interface CryptoPayment {
  user_id: string;
  user_email: string;
  username: string;
  plan: string;
  txid: string;
  network: string;
  amount_usd: number;
  expected_usd: number;
  submitted_at: string;
  status: string;
}

const EXPLORER_URLS: Record<string, (txid: string) => string> = {
  "USDT-BEP20": (tx) => `https://bscscan.com/tx/${tx}`,
  "USDT-TRC20": (tx) => `https://tronscan.org/#/transaction/${tx}`,
  BTC: (tx) => `https://blockstream.info/tx/${tx}`,
  ETH: (tx) => `https://etherscan.io/tx/${tx}`,
  "USDT-ERC20": (tx) => `https://etherscan.io/tx/${tx}`,
  BNB: (tx) => `https://bscscan.com/tx/${tx}`,
};

const PLAN_COLOR: Record<string, string> = {
  monthly: "text-purple bg-purple/10 border-purple/20",
  yearly: "text-long bg-long/10 border-long/20",
  lifetime: "text-gold bg-gold/10 border-gold/20",
};

export default function AdminPaymentsPage() {
  const queryClient = useQueryClient();

  const { data, isLoading, refetch } = useQuery<{ payments: CryptoPayment[] }>({
    queryKey: ["admin-crypto-payments"],
    queryFn: () =>
      api.get("/api/v1/admin/config/crypto-payments").then((r) => r.data),
    refetchInterval: 30000,
  });

  const rejectMutation = useMutation({
    mutationFn: ({ user_id, plan }: { user_id: string; plan: string }) =>
      api
        .post(`/api/v1/admin/config/crypto-payments/${user_id}/${plan}/reject`)
        .then((r) => r.data),
    onSuccess: () => {
      toast.success("Payment rejected and removed");
      queryClient.invalidateQueries({ queryKey: ["admin-crypto-payments"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || "Failed to reject"),
  });

  const payments = data?.payments || [];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-xs font-semibold text-text-primary">Pending Payments</h2>
          <span className="text-2xs text-text-muted font-mono">{payments.length} pending</span>
        </div>
        <button
          onClick={() => refetch()}
          className="filter-pill"
          title="Refresh"
        >
          <RefreshCw className="h-3 w-3" />
        </button>
      </div>

      <div className="text-2xs text-text-muted bg-surface-2 border border-border rounded px-3 py-2">
        Manual verification required. Check TxID on blockchain explorer, then set the user plan via Admin → Users → Edit.
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-surface border border-border rounded animate-pulse" />
          ))}
        </div>
      ) : payments.length === 0 ? (
        <Panel noPad>
          <div className="flex flex-col items-center justify-center py-12">
            <CheckCircle2 className="w-8 h-8 text-long opacity-40 mb-2" />
            <p className="text-text-muted text-xs">No pending crypto payments</p>
          </div>
        </Panel>
      ) : (
        <div className="space-y-2">
          {payments.map((p) => {
            const explorerUrl = EXPLORER_URLS[p.network]?.(p.txid);
            const amountMatch = Math.abs(p.amount_usd - p.expected_usd) < 2;
            return (
              <Panel key={`${p.user_id}-${p.plan}`} noPad>
                <div className="px-3 py-2 space-y-2">
                  {/* Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 text-xs">
                      <span className="font-medium text-text-primary">{p.username}</span>
                      <span className="text-text-muted font-mono text-2xs">{p.user_email}</span>
                      <span className="text-text-muted">→</span>
                      <span
                        className={cn(
                          "text-2xs px-1.5 py-0.5 rounded-full border font-medium capitalize",
                          PLAN_COLOR[p.plan] ?? "text-text-muted bg-surface-2 border-border"
                        )}
                      >
                        {p.plan}
                      </span>
                      <span className="font-mono text-text-primary">{p.network}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="flex items-center gap-1 text-2xs text-gold">
                        <Clock className="w-3 h-3" /> Pending
                      </span>
                      <span className="text-2xs text-text-muted">
                        {new Date(p.submitted_at).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {/* Payment details */}
                  <div className="flex items-center gap-4 text-2xs">
                    <div>
                      <span className="text-text-muted">Amount: </span>
                      <span className={cn("font-mono", amountMatch ? "text-text-primary" : "text-short")}>
                        ${p.amount_usd}
                      </span>
                    </div>
                    <div>
                      <span className="text-text-muted">Expected: </span>
                      <span className="font-mono text-text-primary">${p.expected_usd}</span>
                    </div>
                    <div className="truncate flex items-center gap-1">
                      <span className="text-text-muted">TxID: </span>
                      <span className="font-mono text-text-primary truncate">{p.txid}</span>
                      {explorerUrl && (
                        <a
                          href={explorerUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-purple hover:text-purple/80 shrink-0"
                        >
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1.5">
                    {explorerUrl && (
                      <a
                        href={explorerUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="filter-pill gap-1 text-blue border-blue/30"
                      >
                        <ExternalLink className="h-3 w-3" />
                        Explorer
                      </a>
                    )}
                    <div className="flex-1 text-2xs text-text-muted">
                      After verifying →{" "}
                      <a href="/admin/users" className="text-purple underline">
                        Users
                      </a>{" "}
                      → Edit → set plan to <b>{p.plan}</b>
                    </div>
                    <button
                      onClick={() => {
                        if (confirm(`Reject this payment from ${p.user_email}?`)) {
                          rejectMutation.mutate({ user_id: p.user_id, plan: p.plan });
                        }
                      }}
                      disabled={rejectMutation.isPending}
                      className="filter-pill gap-1 text-short border-short/30 hover:bg-short/10 disabled:opacity-40"
                    >
                      <XCircle className="h-3 w-3" />
                      Reject
                    </button>
                  </div>
                </div>
              </Panel>
            );
          })}
        </div>
      )}
    </div>
  );
}
