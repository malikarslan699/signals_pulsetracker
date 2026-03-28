import { useState } from "react";
import { Panel } from "@/components/terminal/Panel";
import { Plus, Trash2, Bell, Send } from "lucide-react";
import { cn } from "@/lib/utils";

const mockAlerts = [
  { id: "1", minConfidence: 75, directions: ["LONG", "SHORT"], timeframes: ["4H", "1D"], markets: ["Crypto"], active: true },
  { id: "2", minConfidence: 80, directions: ["LONG"], timeframes: ["1H", "4H"], markets: ["Forex"], active: true },
  { id: "3", minConfidence: 60, directions: ["SHORT"], timeframes: ["15M"], markets: ["Crypto", "Forex"], active: false },
];

export default function AlertsPage() {
  const [showForm, setShowForm] = useState(false);
  const [alerts, setAlerts] = useState(mockAlerts);

  return (
    <div className="p-3 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h1 className="text-sm font-semibold text-foreground">Alert Rules</h1>
          <span className="text-2xs text-muted-foreground font-mono">{alerts.length} rules</span>
        </div>
        <div className="flex items-center gap-1.5">
          <button className="filter-pill gap-1">
            <Send className="h-3 w-3" />
            Test Alert
          </button>
          <button onClick={() => setShowForm(!showForm)} className={cn("filter-pill gap-1", showForm && "filter-pill-active")}>
            <Plus className="h-3 w-3" />
            New Rule
          </button>
        </div>
      </div>

      {/* Info Banner */}
      <div className="flex items-center gap-2 px-3 py-2 bg-info/10 border border-info/20 rounded text-2xs text-info">
        <Bell className="h-3.5 w-3.5 shrink-0" />
        <span>Connect Telegram in Settings to receive real-time signal alerts based on your rules.</span>
      </div>

      {/* Create Form */}
      {showForm && (
        <Panel title="Create Alert Rule">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-2xs font-medium text-muted-foreground uppercase tracking-wider mb-1 block">Min Confidence</label>
              <input type="range" min="0" max="100" defaultValue="70" className="w-full accent-primary" />
              <span className="text-2xs font-mono text-foreground">70%</span>
            </div>
            <div>
              <label className="text-2xs font-medium text-muted-foreground uppercase tracking-wider mb-1 block">Direction</label>
              <div className="flex gap-1">
                {["LONG", "SHORT"].map(d => (
                  <button key={d} className="filter-pill filter-pill-active">{d}</button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-2xs font-medium text-muted-foreground uppercase tracking-wider mb-1 block">Timeframes</label>
              <div className="flex gap-1">
                {["15M", "1H", "4H", "1D"].map(tf => (
                  <button key={tf} className="filter-pill">{tf}</button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-2xs font-medium text-muted-foreground uppercase tracking-wider mb-1 block">Markets</label>
              <div className="flex gap-1">
                {["Crypto", "Forex", "Commodity"].map(m => (
                  <button key={m} className="filter-pill">{m}</button>
                ))}
              </div>
            </div>
          </div>
          <div className="flex justify-end mt-3">
            <button className="px-3 py-1.5 bg-primary text-primary-foreground rounded text-xs font-medium hover:opacity-90 transition-opacity">
              Create Rule
            </button>
          </div>
        </Panel>
      )}

      {/* Alert List */}
      <div className="space-y-2">
        {alerts.map((alert) => (
          <Panel key={alert.id} noPad>
            <div className="flex items-center justify-between px-3 py-2">
              <div className="flex items-center gap-3 flex-wrap text-xs">
                <div className="flex items-center gap-1">
                  <span className="text-2xs text-muted-foreground">Confidence ≥</span>
                  <span className="font-mono font-semibold text-foreground">{alert.minConfidence}%</span>
                </div>
                <div className="h-3 w-px bg-border" />
                <div className="flex gap-1">
                  {alert.directions.map(d => (
                    <span key={d} className={cn("text-2xs font-bold", d === "LONG" ? "text-long" : "text-short")}>{d}</span>
                  ))}
                </div>
                <div className="h-3 w-px bg-border" />
                <div className="flex gap-1">
                  {alert.timeframes.map(tf => (
                    <span key={tf} className="text-2xs text-muted-foreground">{tf}</span>
                  ))}
                </div>
                <div className="h-3 w-px bg-border" />
                <div className="flex gap-1">
                  {alert.markets.map(m => (
                    <span key={m} className="text-2xs text-muted-foreground">{m}</span>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setAlerts(a => a.map(x => x.id === alert.id ? {...x, active: !x.active} : x))}
                  className={cn(
                    "h-5 w-9 rounded-full transition-colors relative",
                    alert.active ? "bg-primary" : "bg-secondary"
                  )}
                >
                  <span className={cn(
                    "absolute top-0.5 h-4 w-4 rounded-full bg-primary-foreground transition-transform",
                    alert.active ? "left-[18px]" : "left-0.5"
                  )} />
                </button>
                <button className="p-1 rounded text-muted-foreground hover:text-short transition-colors">
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            </div>
          </Panel>
        ))}
      </div>
    </div>
  );
}
