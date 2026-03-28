import { Panel } from "@/components/terminal/Panel";
import { ExternalLink, XCircle } from "lucide-react";

const payments = [
  { id: "1", user: "trader_pro", plan: "Yearly", network: "BTC", amount: "0.00385", expected: "0.00380", txid: "abc123...def789", time: "2h ago" },
  { id: "2", user: "crypto_king", plan: "Monthly", network: "ETH", amount: "0.0092", expected: "0.0090", txid: "xyz456...uvw012", time: "5h ago" },
];

export default function AdminPaymentsPage() {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h2 className="text-xs font-semibold text-foreground">Pending Payments</h2>
        <span className="text-2xs text-muted-foreground font-mono">{payments.length} pending</span>
      </div>

      {payments.map((p) => (
        <Panel key={p.id} noPad>
          <div className="px-3 py-2 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 text-xs">
                <span className="font-medium text-foreground">{p.user}</span>
                <span className="text-muted-foreground">→ {p.plan}</span>
                <span className="font-mono text-foreground">{p.network}</span>
              </div>
              <span className="text-2xs text-muted-foreground">{p.time}</span>
            </div>
            <div className="flex items-center gap-4 text-2xs">
              <div><span className="text-muted-foreground">Amount: </span><span className="font-mono text-foreground">{p.amount}</span></div>
              <div><span className="text-muted-foreground">Expected: </span><span className="font-mono text-foreground">{p.expected}</span></div>
              <div className="truncate"><span className="text-muted-foreground">TxID: </span><span className="font-mono text-foreground">{p.txid}</span></div>
            </div>
            <div className="flex items-center gap-1.5">
              <button className="filter-pill gap-1 text-info border-info/30">
                <ExternalLink className="h-3 w-3" />
                Explorer
              </button>
              <button className="filter-pill gap-1 text-short border-short/30 hover:bg-short/10">
                <XCircle className="h-3 w-3" />
                Reject
              </button>
            </div>
          </div>
        </Panel>
      ))}
    </div>
  );
}
