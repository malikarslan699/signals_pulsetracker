"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
import { RefreshCw, CheckCircle2, XCircle, Clock, ExternalLink } from "lucide-react";

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
  "BTC":        (tx) => `https://blockstream.info/tx/${tx}`,
  "ETH":        (tx) => `https://etherscan.io/tx/${tx}`,
  "USDT-ERC20": (tx) => `https://etherscan.io/tx/${tx}`,
  "BNB":        (tx) => `https://bscscan.com/tx/${tx}`,
};

const PLAN_COLOR: Record<string, string> = {
  monthly:  "text-purple bg-purple/10 border-purple/20",
  yearly:   "text-long bg-long/10 border-long/20",
  lifetime: "text-gold bg-gold/10 border-gold/20",
};

export default function AdminPaymentsPage() {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState<string | null>(null);

  const { data, isLoading, refetch } = useQuery<{ payments: CryptoPayment[] }>({
    queryKey: ["admin-crypto-payments"],
    queryFn: () => api.get("/api/v1/admin/config/crypto-payments").then((r) => r.data),
    refetchInterval: 30000,
  });

  const rejectMutation = useMutation({
    mutationFn: ({ user_id, plan }: { user_id: string; plan: string }) =>
      api.post(`/api/v1/admin/config/crypto-payments/${user_id}/${plan}/reject`).then((r) => r.data),
    onSuccess: (_, { user_id }) => {
      toast.success("Payment rejected and removed");
      queryClient.invalidateQueries({ queryKey: ["admin-crypto-payments"] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Failed to reject"),
  });

  // Approve = admin manually sets plan via edit user modal; here we just guide them
  const payments = data?.payments || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-text-primary">Crypto Payments</h2>
          <p className="text-xs text-text-muted mt-0.5">
            Manual verification required. Check TxID on blockchain explorer, then set the user plan via Admin → Users → Edit.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2 bg-surface border border-border rounded-lg text-text-muted hover:border-purple hover:text-purple transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => <div key={i} className="h-24 bg-surface border border-border rounded-xl animate-pulse" />)}
        </div>
      ) : payments.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 gap-3 bg-surface border border-border rounded-xl">
          <CheckCircle2 className="w-10 h-10 text-long opacity-40" />
          <p className="text-text-muted text-sm">No pending crypto payments</p>
        </div>
      ) : (
        <div className="space-y-3">
          {payments.map((p) => {
            const explorerUrl = EXPLORER_URLS[p.network]?.(p.txid);
            const amountMatch = Math.abs(p.amount_usd - p.expected_usd) < 2;
            return (
              <div key={`${p.user_id}-${p.plan}`} className="bg-surface border border-border rounded-xl p-4 space-y-3">
                {/* Header */}
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-text-primary text-sm">{p.username}</span>
                      <span className="text-xs text-text-muted font-mono">{p.user_email}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${PLAN_COLOR[p.plan] ?? "text-text-muted bg-surface-2 border-border"}`}>
                        {p.plan}
                      </span>
                    </div>
                    <p className="text-xs text-text-muted mt-1">
                      Submitted: {new Date(p.submitted_at).toLocaleString()}
                    </p>
                  </div>
                  <span className="flex items-center gap-1 text-xs text-gold bg-gold/10 border border-gold/20 px-2 py-1 rounded-full">
                    <Clock className="w-3 h-3" /> Pending
                  </span>
                </div>

                {/* Payment details */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                  <div className="bg-surface-2 rounded-lg p-2">
                    <p className="text-text-muted mb-0.5">Network</p>
                    <p className="font-medium text-text-primary">{p.network}</p>
                  </div>
                  <div className="bg-surface-2 rounded-lg p-2">
                    <p className="text-text-muted mb-0.5">Amount Claimed</p>
                    <p className={`font-medium ${amountMatch ? "text-long" : "text-short"}`}>
                      ${p.amount_usd}
                      {!amountMatch && <span className="ml-1 text-text-muted">(exp. ${p.expected_usd})</span>}
                    </p>
                  </div>
                  <div className="bg-surface-2 rounded-lg p-2 col-span-2">
                    <p className="text-text-muted mb-0.5">Transaction ID</p>
                    <div className="flex items-center gap-1">
                      <p className="font-mono text-text-primary truncate">{p.txid}</p>
                      {explorerUrl && (
                        <a href={explorerUrl} target="_blank" rel="noopener noreferrer"
                          className="shrink-0 text-purple hover:text-purple/80">
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 pt-1 border-t border-border">
                  {explorerUrl && (
                    <a href={explorerUrl} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-purple/10 border border-purple/20 text-purple rounded-lg text-xs hover:bg-purple/20 transition-colors">
                      <ExternalLink className="w-3 h-3" />
                      Verify on Explorer
                    </a>
                  )}
                  <div className="flex-1 text-xs text-text-muted">
                    After verifying TxID → go to{" "}
                    <a href="/admin/users" className="text-purple underline underline-offset-2">Admin → Users</a>
                    {" "}→ find <b>{p.username}</b> → Edit → set plan to <b>{p.plan}</b>
                  </div>
                  <button
                    onClick={() => {
                      if (confirm(`Reject and remove this payment from ${p.user_email}?`)) {
                        rejectMutation.mutate({ user_id: p.user_id, plan: p.plan });
                      }
                    }}
                    disabled={rejectMutation.isPending}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-short/10 border border-short/20 text-short rounded-lg text-xs hover:bg-short/20 transition-colors disabled:opacity-40"
                  >
                    <XCircle className="w-3 h-3" />
                    Reject
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
