"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Bell, Plus, Trash2, Edit2, Send, CheckCircle, AlertCircle } from "lucide-react";
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
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Failed to create alert"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/alerts/${id}`),
    onSuccess: () => {
      toast.success("Alert deleted");
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });

  const testMutation = useMutation({
    mutationFn: () => api.post("/api/v1/alerts/test"),
    onSuccess: () => toast.success("Test alert sent to Telegram!"),
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Test failed — connect Telegram first"),
  });

  const toggle = (arr: string[], val: string) =>
    arr.includes(val) ? arr.filter((x) => x !== val) : [...arr, val];

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-20 lg:pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Alert Configuration</h1>
          <p className="text-text-muted text-sm mt-1">
            Configure Telegram alerts for new signals
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => testMutation.mutate()}
            disabled={testMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-surface border border-border rounded-lg text-sm text-text-secondary hover:text-text-primary transition-colors"
          >
            <Send className="w-4 h-4" />
            Test Alert
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple text-white rounded-lg text-sm font-medium hover:bg-purple/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Alert
          </button>
        </div>
      </div>

      {/* Info banner */}
      <div className="bg-surface border border-blue/30 rounded-xl p-4 flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-blue mt-0.5 flex-shrink-0" />
        <div className="text-sm text-text-secondary">
          <p className="font-medium text-text-primary mb-1">Connect Telegram First</p>
          <p>
            Go to <span className="text-blue font-mono">@PulseSignalProBot</span> on Telegram and use{" "}
            <span className="font-mono text-gold">/start</span> to get a verification code, then link it in Settings.
          </p>
        </div>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="bg-surface border border-border rounded-xl p-6 space-y-5">
          <h2 className="text-lg font-semibold text-text-primary">New Alert Rule</h2>

          {/* Min confidence */}
          <div>
            <label className="block text-sm text-text-muted mb-2">
              Minimum Confidence: <span className="text-text-primary font-mono">{form.min_confidence}</span>
            </label>
            <input
              type="range"
              min={50}
              max={95}
              step={5}
              value={form.min_confidence}
              onChange={(e) => setForm({ ...form, min_confidence: Number(e.target.value) })}
              className="w-full accent-purple"
            />
            <div className="flex justify-between text-xs text-text-muted mt-1">
              <span>50</span><span>95</span>
            </div>
          </div>

          {/* Direction */}
          <div>
            <label className="block text-sm text-text-muted mb-2">Direction</label>
            <div className="flex gap-2">
              {["LONG", "SHORT"].map((d) => (
                <button
                  key={d}
                  onClick={() => setForm({ ...form, directions: toggle(form.directions, d) })}
                  className={`px-4 py-2 rounded-lg text-sm font-medium border transition-all ${
                    form.directions.includes(d)
                      ? d === "LONG"
                        ? "bg-long border-long text-white"
                        : "bg-short border-short text-white"
                      : "border-border text-text-muted hover:border-border-light"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          {/* Timeframes */}
          <div>
            <label className="block text-sm text-text-muted mb-2">Timeframes</label>
            <div className="flex gap-2 flex-wrap">
              {["5m", "15m", "1H", "4H", "1D"].map((tf) => (
                <button
                  key={tf}
                  onClick={() => setForm({ ...form, timeframes: toggle(form.timeframes, tf) })}
                  className={`px-3 py-1.5 rounded-lg text-sm border transition-all ${
                    form.timeframes.includes(tf)
                      ? "bg-blue border-blue text-white"
                      : "border-border text-text-muted hover:border-border-light"
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>

          {/* Markets */}
          <div>
            <label className="block text-sm text-text-muted mb-2">Markets</label>
            <div className="flex gap-2">
              {["crypto", "forex"].map((m) => (
                <button
                  key={m}
                  onClick={() => setForm({ ...form, markets: toggle(form.markets, m) })}
                  className={`px-4 py-2 rounded-lg text-sm border capitalize transition-all ${
                    form.markets.includes(m)
                      ? "bg-purple border-purple text-white"
                      : "border-border text-text-muted hover:border-border-light"
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              onClick={() => createMutation.mutate(form)}
              disabled={createMutation.isPending}
              className="flex-1 py-2.5 bg-purple text-white rounded-lg font-medium hover:bg-purple/90 transition-colors"
            >
              {createMutation.isPending ? "Creating..." : "Create Alert"}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-6 py-2.5 bg-surface-2 text-text-secondary rounded-lg hover:text-text-primary transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Alert list */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="h-24 bg-surface border border-border rounded-xl animate-pulse" />
          ))}
        </div>
      ) : alerts && alerts.length > 0 ? (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div key={alert.id} className="bg-surface border border-border rounded-xl p-5">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${alert.is_active ? "bg-long/10" : "bg-surface-2"}`}>
                    <Bell className={`w-5 h-5 ${alert.is_active ? "text-long" : "text-text-muted"}`} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-text-primary capitalize">{alert.channel}</span>
                      {alert.is_active ? (
                        <span className="text-xs px-2 py-0.5 bg-long/10 text-long rounded-full">Active</span>
                      ) : (
                        <span className="text-xs px-2 py-0.5 bg-surface-2 text-text-muted rounded-full">Paused</span>
                      )}
                    </div>
                    <p className="text-sm text-text-muted mt-0.5">
                      Min confidence: <span className="text-text-secondary font-mono">{alert.min_confidence}</span> ·{" "}
                      {alert.directions.join("/")} · {alert.timeframes.join(", ")} · {alert.markets.join(", ")}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => deleteMutation.mutate(alert.id)}
                  className="p-2 text-text-muted hover:text-short transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 text-text-muted">
          <Bell className="w-12 h-12 mb-4 opacity-30" />
          <p className="text-lg font-medium">No alerts configured</p>
          <p className="text-sm mt-1">Create your first alert to receive Telegram notifications</p>
        </div>
      )}
    </div>
  );
}
