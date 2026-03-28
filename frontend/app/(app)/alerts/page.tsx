"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Panel } from "@/components/terminal/Panel";
import { Bell, Plus, Trash2, Send } from "lucide-react";
import { cn } from "@/lib/utils";
import toast from "react-hot-toast";

interface AlertConfig {
  id: string;
  channel: string;
  min_confidence: number;
  directions: string[];
  timeframes: string[];
  markets: string[];
  pairs: string[] | null;
  is_active: boolean;
  created_at: string;
}

const defaultForm = {
  channel: "telegram",
  min_confidence: 70,
  directions: ["LONG", "SHORT"],
  timeframes: ["1H", "4H"],
  markets: ["crypto"],
  pairs: null as string[] | null,
};

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ...defaultForm });

  const { data: alerts, isLoading } = useQuery<AlertConfig[]>({
    queryKey: ["alerts"],
    queryFn: () => api.get("/api/v1/alerts/").then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof form) => api.post("/api/v1/alerts/", data),
    onSuccess: () => {
      toast.success("Alert created!");
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      setShowForm(false);
      setForm({ ...defaultForm });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || "Failed to create alert"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/alerts/${id}`),
    onSuccess: () => {
      toast.success("Alert deleted");
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      api.put(`/api/v1/alerts/${id}`, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
    onError: () => toast.error("Failed to update alert"),
  });

  const testMutation = useMutation({
    mutationFn: () => api.post("/api/v1/alerts/test", {}),
    onSuccess: () => toast.success("Test alert sent to Telegram!"),
    onError: (e: any) =>
      toast.error(
        e?.response?.data?.detail || "Test failed — connect Telegram first"
      ),
  });

  const toggle = (arr: string[], val: string) =>
    arr.includes(val) ? arr.filter((x) => x !== val) : [...arr, val];

  const alertList = alerts || [];

  return (
    <div className="p-3 space-y-3 pb-20 lg:pb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h1 className="text-sm font-semibold text-text-primary">Alert Rules</h1>
          <span className="text-2xs text-text-muted font-mono">{alertList.length} rules</span>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => testMutation.mutate()}
            disabled={testMutation.isPending}
            className="filter-pill gap-1"
          >
            <Send className="h-3 w-3" />
            Test Alert
          </button>
          <button
            onClick={() => setShowForm(!showForm)}
            className={cn("filter-pill gap-1", showForm && "filter-pill-active")}
          >
            <Plus className="h-3 w-3" />
            New Rule
          </button>
        </div>
      </div>

      {/* Info Banner */}
      <div className="flex items-center gap-2 px-3 py-2 bg-blue/10 border border-blue/20 rounded text-2xs text-blue">
        <Bell className="h-3.5 w-3.5 shrink-0" />
        <span>
          Connect Telegram in Settings to receive real-time signal alerts based on your rules.
          Use <span className="font-mono">@PulseSignalProBot</span> → <span className="font-mono">/start</span>.
        </span>
      </div>

      {/* Create Form */}
      {showForm && (
        <Panel title="Create Alert Rule">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 block">
                Min Confidence: <span className="font-mono text-long">{form.min_confidence}</span>
              </label>
              <input
                type="range"
                min="50"
                max="95"
                step="5"
                value={form.min_confidence}
                onChange={(e) =>
                  setForm({ ...form, min_confidence: Number(e.target.value) })
                }
                className="w-full accent-long"
              />
              <div className="flex justify-between text-2xs text-text-muted mt-0.5">
                <span>50</span>
                <span>95</span>
              </div>
            </div>
            <div>
              <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 block">
                Direction
              </label>
              <div className="flex gap-1">
                {["LONG", "SHORT"].map((d) => (
                  <button
                    key={d}
                    onClick={() =>
                      setForm({ ...form, directions: toggle(form.directions, d) })
                    }
                    className={cn(
                      "filter-pill",
                      form.directions.includes(d) && "filter-pill-active"
                    )}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 block">
                Timeframes
              </label>
              <div className="flex gap-1 flex-wrap">
                {["5m", "15m", "1H", "4H", "1D"].map((tf) => (
                  <button
                    key={tf}
                    onClick={() =>
                      setForm({ ...form, timeframes: toggle(form.timeframes, tf) })
                    }
                    className={cn(
                      "filter-pill",
                      form.timeframes.includes(tf) && "filter-pill-active"
                    )}
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 block">
                Markets
              </label>
              <div className="flex gap-1">
                {["crypto", "forex"].map((m) => (
                  <button
                    key={m}
                    onClick={() =>
                      setForm({ ...form, markets: toggle(form.markets, m) })
                    }
                    className={cn(
                      "filter-pill capitalize",
                      form.markets.includes(m) && "filter-pill-active"
                    )}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-3">
            <button
              onClick={() => setShowForm(false)}
              className="filter-pill"
            >
              Cancel
            </button>
            <button
              onClick={() => createMutation.mutate(form)}
              disabled={createMutation.isPending}
              className="px-3 py-1.5 bg-long text-white rounded text-xs font-medium hover:opacity-90 transition-opacity disabled:opacity-60"
            >
              {createMutation.isPending ? "Creating..." : "Create Rule"}
            </button>
          </div>
        </Panel>
      )}

      {/* Alert List */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2].map((i) => (
            <div key={i} className="h-16 bg-surface border border-border rounded animate-pulse" />
          ))}
        </div>
      ) : alertList.length > 0 ? (
        <div className="space-y-2">
          {alertList.map((alert) => (
            <Panel key={alert.id} noPad>
              <div className="flex items-center justify-between px-3 py-2">
                <div className="flex items-center gap-3 flex-wrap text-xs">
                  <div className="flex items-center gap-1">
                    <span className="text-2xs text-text-muted">Confidence ≥</span>
                    <span className="font-mono font-semibold text-text-primary">
                      {alert.min_confidence}%
                    </span>
                  </div>
                  <div className="h-3 w-px bg-border" />
                  <div className="flex gap-1">
                    {alert.directions.map((d) => (
                      <span
                        key={d}
                        className={cn(
                          "text-2xs font-bold",
                          d === "LONG" ? "text-long" : "text-short"
                        )}
                      >
                        {d}
                      </span>
                    ))}
                  </div>
                  <div className="h-3 w-px bg-border" />
                  <div className="flex gap-1">
                    {alert.timeframes.map((tf) => (
                      <span key={tf} className="text-2xs text-text-muted">
                        {tf}
                      </span>
                    ))}
                  </div>
                  <div className="h-3 w-px bg-border" />
                  <div className="flex gap-1">
                    {alert.markets.map((m) => (
                      <span key={m} className="text-2xs text-text-muted capitalize">
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <button
                    onClick={() => toggleMutation.mutate({ id: alert.id, is_active: !alert.is_active })}
                    className={cn(
                      "relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none",
                      alert.is_active ? "bg-long" : "bg-surface-2 border border-border"
                    )}
                  >
                    <span
                      className={cn(
                        "absolute left-0.5 top-0.5 inline-block h-4 w-4 rounded-full bg-white shadow transition-transform",
                        alert.is_active ? "translate-x-4" : "translate-x-0"
                      )}
                    />
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(alert.id)}
                    className="p-1 rounded text-text-muted hover:text-short transition-colors"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              </div>
            </Panel>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-text-muted">
          <Bell className="w-10 h-10 mb-3 opacity-30" />
          <p className="text-sm font-medium">No alerts configured</p>
          <p className="text-xs mt-1">Create your first rule to receive Telegram notifications</p>
        </div>
      )}
    </div>
  );
}
