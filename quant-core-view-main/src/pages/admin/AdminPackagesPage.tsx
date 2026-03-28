import { Panel } from "@/components/terminal/Panel";
import { PlanBadge } from "@/components/terminal/Badges";
import { ChevronDown, ChevronUp, Save } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const packages = [
  { id: "1", name: "Trial", price: 0, duration: "7 days", badge: "Free", active: true, features: { signals: true, scanner: true, alerts: false, stats: true, maxAlerts: 0, apiAccess: false } },
  { id: "2", name: "Monthly", price: 29, duration: "30 days", badge: "Popular", active: true, features: { signals: true, scanner: true, alerts: true, stats: true, maxAlerts: 5, apiAccess: false } },
  { id: "3", name: "Yearly", price: 249, duration: "365 days", badge: "Best Value", active: true, features: { signals: true, scanner: true, alerts: true, stats: true, maxAlerts: 20, apiAccess: true } },
  { id: "4", name: "Lifetime", price: 499, duration: "Forever", badge: "Premium", active: true, features: { signals: true, scanner: true, alerts: true, stats: true, maxAlerts: -1, apiAccess: true } },
];

export default function AdminPackagesPage() {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="space-y-2">
      {packages.map((pkg) => (
        <Panel key={pkg.id} noPad>
          <button
            onClick={() => setExpanded(e => e === pkg.id ? null : pkg.id)}
            className="w-full flex items-center justify-between px-3 py-2 text-xs hover:bg-accent/30 transition-colors"
          >
            <div className="flex items-center gap-3">
              <span className="font-medium text-foreground">{pkg.name}</span>
              <span className="font-mono text-muted-foreground">${pkg.price}</span>
              <span className="text-2xs text-muted-foreground">{pkg.duration}</span>
              <PlanBadge plan={pkg.name.toLowerCase() as any} />
            </div>
            <div className="flex items-center gap-2">
              <span className={cn("text-2xs font-semibold", pkg.active ? "text-long" : "text-short")}>
                {pkg.active ? "Active" : "Inactive"}
              </span>
              {expanded === pkg.id ? <ChevronUp className="h-3.5 w-3.5 text-muted-foreground" /> : <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />}
            </div>
          </button>

          {expanded === pkg.id && (
            <div className="px-3 py-2 border-t border-border space-y-3">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {Object.entries(pkg.features).map(([key, val]) => (
                  <div key={key} className="flex items-center justify-between px-2 py-1 bg-secondary rounded text-2xs">
                    <span className="text-muted-foreground capitalize">{key.replace(/([A-Z])/g, ' $1')}</span>
                    <span className={cn("font-semibold", typeof val === "boolean" ? (val ? "text-long" : "text-short") : "text-foreground")}>
                      {typeof val === "boolean" ? (val ? "✓" : "✗") : val === -1 ? "∞" : val}
                    </span>
                  </div>
                ))}
              </div>
              <div className="flex justify-end gap-1.5">
                <button className="filter-pill">Discard</button>
                <button className="px-2.5 py-1 bg-primary text-primary-foreground rounded text-xs font-medium hover:opacity-90 flex items-center gap-1">
                  <Save className="h-3 w-3" />
                  Save
                </button>
              </div>
            </div>
          )}
        </Panel>
      ))}
    </div>
  );
}
