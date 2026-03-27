"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  Package, Settings, ToggleLeft, ToggleRight, Save, ChevronDown, ChevronUp,
  Zap, Star, TrendingUp, Crown, Check, X
} from "lucide-react";
import toast from "react-hot-toast";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface FeatureFlags {
  realtime_signals: boolean;
  signal_history: boolean;
  history_days: number;
  crypto_access: boolean;
  forex_access: boolean;
  telegram_alerts: boolean;
  advanced_analytics: boolean;
  advanced_indicator_breakdown: boolean;
  export_data: boolean;
  api_access: boolean;
  max_alerts: number;
  max_watchlist: number;
  max_signals_per_day: number;
  websocket_connections: number;
}

interface PackageDef {
  slug: string;
  name: string;
  price: number;
  duration_days: number | null;
  duration_label: string;
  is_active: boolean;
  sort_order: number;
  description: string;
  badge_text: string;
  badge_color: string;
  features: FeatureFlags;
}

const PLAN_ICONS: Record<string, React.ReactNode> = {
  trial:    <Zap className="w-4 h-4" />,
  monthly:  <Star className="w-4 h-4" />,
  yearly:   <TrendingUp className="w-4 h-4" />,
  lifetime: <Crown className="w-4 h-4" />,
};

const PLAN_COLORS: Record<string, string> = {
  trial:    "#6B7280",
  monthly:  "#8B5CF6",
  yearly:   "#10B981",
  lifetime: "#F59E0B",
};

// ---------------------------------------------------------------------------
// Feature flag labels
// ---------------------------------------------------------------------------
const FEATURE_LABELS: { key: keyof FeatureFlags; label: string; type: "bool" | "number" }[] = [
  { key: "realtime_signals",               label: "Real-time signals",            type: "bool"   },
  { key: "signal_history",                 label: "Signal history",               type: "bool"   },
  { key: "history_days",                   label: "History days (0 = unlimited)", type: "number" },
  { key: "crypto_access",                  label: "Crypto market access",         type: "bool"   },
  { key: "forex_access",                   label: "Forex market access",          type: "bool"   },
  { key: "telegram_alerts",                label: "Telegram alerts",              type: "bool"   },
  { key: "advanced_analytics",             label: "Advanced analytics",           type: "bool"   },
  { key: "advanced_indicator_breakdown",   label: "ICT & indicator breakdown",    type: "bool"   },
  { key: "export_data",                    label: "Data export (CSV)",            type: "bool"   },
  { key: "api_access",                     label: "API access",                   type: "bool"   },
  { key: "max_alerts",                     label: "Max alerts (0 = unlimited)",   type: "number" },
  { key: "max_watchlist",                  label: "Max watchlist pairs (0 = ∞)",  type: "number" },
  { key: "max_signals_per_day",            label: "Signals/day (0 = unlimited)",  type: "number" },
  { key: "websocket_connections",          label: "WebSocket connections (0 = disabled)", type: "number" },
];

// ---------------------------------------------------------------------------
// Package Card
// ---------------------------------------------------------------------------
function PackageCard({
  pkg,
  onSave,
  onToggle,
  saving,
}: {
  pkg: PackageDef;
  onSave: (updated: PackageDef) => void;
  onToggle: (slug: string) => void;
  saving: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const [draft, setDraft] = useState<PackageDef>({ ...pkg, features: { ...pkg.features } });
  const color = PLAN_COLORS[pkg.slug] ?? "#6B7280";

  const isDirty = JSON.stringify(draft) !== JSON.stringify(pkg);

  const setField = (key: keyof PackageDef, value: unknown) => {
    setDraft((d) => ({ ...d, [key]: value }));
  };

  const setFeature = (key: keyof FeatureFlags, value: boolean | number) => {
    setDraft((d) => ({ ...d, features: { ...d.features, [key]: value } }));
  };

  const handleSave = () => onSave(draft);
  const handleDiscard = () => setDraft({ ...pkg, features: { ...pkg.features } });

  return (
    <div
      className="bg-surface border rounded-xl overflow-hidden"
      style={{ borderColor: pkg.is_active ? color + "40" : "#2D3748" }}
    >
      {/* Header */}
      <div className="flex items-center gap-3 p-4">
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: color + "20", color }}
        >
          {PLAN_ICONS[pkg.slug] ?? <Package className="w-4 h-4" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-text-primary text-sm">{pkg.name}</span>
            {pkg.badge_text && (
              <span className="text-xs px-2 py-0.5 rounded-full font-medium text-white" style={{ backgroundColor: pkg.badge_color }}>
                {pkg.badge_text}
              </span>
            )}
          </div>
          <p className="text-xs text-text-muted">
            ${pkg.price} {pkg.duration_label} · {pkg.slug}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onToggle(pkg.slug)}
            className="text-text-muted hover:text-text-primary transition-colors"
            title={pkg.is_active ? "Disable" : "Enable"}
          >
            {pkg.is_active
              ? <ToggleRight className="w-6 h-6 text-long" />
              : <ToggleLeft className="w-6 h-6" />
            }
          </button>
          <button
            onClick={() => setExpanded((e) => !e)}
            className="text-text-muted hover:text-text-primary transition-colors p-1"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Expanded editor */}
      {expanded && (
        <div className="border-t border-border px-4 pb-5 pt-4 space-y-5">
          {/* Basic fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="block">
              <span className="text-xs text-text-muted mb-1 block">Name</span>
              <input
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary"
                value={draft.name}
                onChange={(e) => setField("name", e.target.value)}
              />
            </label>
            <label className="block">
              <span className="text-xs text-text-muted mb-1 block">Price (USD)</span>
              <input
                type="number"
                min={0}
                step={0.01}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary font-mono"
                value={draft.price}
                onChange={(e) => setField("price", parseFloat(e.target.value) || 0)}
              />
            </label>
            <label className="block">
              <span className="text-xs text-text-muted mb-1 block">Duration days (empty = lifetime)</span>
              <input
                type="number"
                min={0}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary font-mono"
                value={draft.duration_days ?? ""}
                onChange={(e) =>
                  setField("duration_days", e.target.value === "" ? null : parseInt(e.target.value))
                }
              />
            </label>
            <label className="block">
              <span className="text-xs text-text-muted mb-1 block">Duration label</span>
              <input
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary"
                value={draft.duration_label}
                onChange={(e) => setField("duration_label", e.target.value)}
              />
            </label>
            <label className="block sm:col-span-2">
              <span className="text-xs text-text-muted mb-1 block">Description</span>
              <input
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary"
                value={draft.description}
                onChange={(e) => setField("description", e.target.value)}
              />
            </label>
            <label className="block">
              <span className="text-xs text-text-muted mb-1 block">Badge text (optional)</span>
              <input
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary"
                value={draft.badge_text}
                onChange={(e) => setField("badge_text", e.target.value)}
              />
            </label>
            <label className="block">
              <span className="text-xs text-text-muted mb-1 block">Badge color (hex)</span>
              <div className="flex gap-2">
                <input
                  type="color"
                  className="w-10 h-10 rounded cursor-pointer border border-border bg-surface-2"
                  value={draft.badge_color}
                  onChange={(e) => setField("badge_color", e.target.value)}
                />
                <input
                  className="flex-1 bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary font-mono"
                  value={draft.badge_color}
                  onChange={(e) => setField("badge_color", e.target.value)}
                />
              </div>
            </label>
            <label className="block">
              <span className="text-xs text-text-muted mb-1 block">Sort order</span>
              <input
                type="number"
                min={0}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary font-mono"
                value={draft.sort_order}
                onChange={(e) => setField("sort_order", parseInt(e.target.value) || 0)}
              />
            </label>
          </div>

          {/* Feature flags */}
          <div>
            <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">Feature Access</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {FEATURE_LABELS.map(({ key, label, type }) => (
                <div key={key} className="flex items-center justify-between bg-surface-2 rounded-lg px-3 py-2.5">
                  <span className="text-xs text-text-secondary">{label}</span>
                  {type === "bool" ? (
                    <button
                      onClick={() => setFeature(key, !draft.features[key])}
                      className="flex-shrink-0"
                    >
                      {draft.features[key]
                        ? <Check className="w-4 h-4 text-long" />
                        : <X className="w-4 h-4 text-short" />
                      }
                    </button>
                  ) : (
                    <input
                      type="number"
                      min={0}
                      className="w-20 bg-surface border border-border rounded px-2 py-1 text-xs font-mono text-text-primary text-right"
                      value={draft.features[key] as number}
                      onChange={(e) =>
                        setFeature(key, parseInt(e.target.value) || 0)
                      }
                    />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          {isDirty && (
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 bg-purple text-white rounded-lg text-sm font-medium disabled:opacity-60"
              >
                <Save className="w-4 h-4" />
                {saving ? "Saving…" : "Save Changes"}
              </button>
              <button
                onClick={handleDiscard}
                className="px-4 py-2 border border-border text-text-muted rounded-lg text-sm"
              >
                Discard
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function AdminPackagesPage() {
  const qc = useQueryClient();

  const { data, isLoading, isError } = useQuery<{ packages: PackageDef[] }>({
    queryKey: ["admin-packages"],
    queryFn: () => api.get("/api/v1/admin/packages/").then((r) => r.data),
  });

  const saveMutation = useMutation({
    mutationFn: (pkg: PackageDef) =>
      api.put(`/api/v1/admin/packages/${pkg.slug}`, pkg).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-packages"] });
      qc.invalidateQueries({ queryKey: ["subscription-plans"] });
      toast.success("Package saved");
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Save failed"),
  });

  const toggleMutation = useMutation({
    mutationFn: (slug: string) =>
      api.patch(`/api/v1/admin/packages/${slug}/toggle`).then((r) => r.data),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["admin-packages"] });
      qc.invalidateQueries({ queryKey: ["subscription-plans"] });
      toast.success(`Package ${data.is_active ? "enabled" : "disabled"}`);
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Toggle failed"),
  });

  const packages = data?.packages ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
          <Package className="w-5 h-5 text-purple" />
          Package Management
        </h2>
        <p className="text-sm text-text-muted mt-1">
          Edit prices, features, and availability for each plan. Changes reflect live on the pricing page.
        </p>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-surface border border-border rounded-xl animate-pulse" />
          ))}
        </div>
      )}

      {isError && (
        <div className="bg-surface border border-border rounded-xl p-8 text-center text-text-muted">
          Failed to load packages.
        </div>
      )}

      <div className="space-y-3">
        {packages.map((pkg) => (
          <PackageCard
            key={pkg.slug}
            pkg={pkg}
            onSave={(updated) => saveMutation.mutate(updated)}
            onToggle={(slug) => toggleMutation.mutate(slug)}
            saving={saveMutation.isPending && (saveMutation.variables as PackageDef)?.slug === pkg.slug}
          />
        ))}
      </div>

      <div className="bg-surface border border-border rounded-xl p-4 text-xs text-text-muted">
        <Settings className="w-4 h-4 inline mr-2 text-purple" />
        Core plans (trial, monthly, yearly, lifetime) cannot be deleted — only disabled or modified.
        Changes to prices and features take effect immediately for new subscribers.
      </div>
    </div>
  );
}
