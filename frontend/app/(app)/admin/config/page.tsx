"use client";
import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Save, RefreshCw, ShieldAlert, Eye, EyeOff } from "lucide-react";
import toast from "react-hot-toast";

import { api } from "@/lib/api";
import { useAuthStore } from "@/store/userStore";

interface SystemConfig {
  scanner_interval_minutes: number;
  min_signal_confidence: number;
  enable_crypto_scan: boolean;
  enable_forex_scan: boolean;
  maintenance_mode: boolean;
  scanner_enabled: boolean;
  max_signals_per_scan: number;
  ict_weight: number;
  trend_weight: number;
  momentum_weight: number;
  auth: {
    require_email_verification: boolean;
    trial_hours: number;
  };
  notifications: {
    enable_telegram_alerts: boolean;
    enable_email_alerts: boolean;
  };
  smtp: {
    enabled: boolean;
    host: string;
    port: number;
    username: string;
    password: string;
    from_email: string;
    from_name: string;
    use_tls: boolean;
    use_ssl: boolean;
  };
  integrations: {
    telegram_bot_token: string;
    telegram_vip_channel_id: string;
    binance_api_key: string;
    binance_api_secret: string;
    twelvedata_api_key: string;
    stripe_secret_key: string;
    stripe_webhook_secret: string;
    stripe_monthly_price_id: string;
    stripe_lifetime_price_id: string;
  };
}

interface ProviderHealthEntry {
  status: "unknown" | "healthy" | "issue";
  message: string;
  checked_at?: string | null;
  details?: Record<string, any>;
}

interface ProviderHealthState {
  smtp: ProviderHealthEntry;
  telegram: ProviderHealthEntry;
}

const defaultConfig: SystemConfig = {
  scanner_interval_minutes: 10,
  min_signal_confidence: 60,
  enable_crypto_scan: true,
  enable_forex_scan: true,
  maintenance_mode: false,
  scanner_enabled: true,
  max_signals_per_scan: 50,
  ict_weight: 1,
  trend_weight: 1,
  momentum_weight: 1,
  auth: {
    require_email_verification: true,
    trial_hours: 24,
  },
  notifications: {
    enable_telegram_alerts: true,
    enable_email_alerts: false,
  },
  smtp: {
    enabled: false,
    host: "",
    port: 587,
    username: "",
    password: "",
    from_email: "",
    from_name: "PulseSignal Pro",
    use_tls: true,
    use_ssl: false,
  },
  integrations: {
    telegram_bot_token: "",
    telegram_vip_channel_id: "",
    binance_api_key: "",
    binance_api_secret: "",
    twelvedata_api_key: "",
    stripe_secret_key: "",
    stripe_webhook_secret: "",
    stripe_monthly_price_id: "",
    stripe_lifetime_price_id: "",
  },
};

const defaultProviderHealth: ProviderHealthState = {
  smtp: { status: "unknown", message: "Not checked yet." },
  telegram: { status: "unknown", message: "Not checked yet." },
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-surface border border-border rounded-xl p-5 space-y-4">
      <h2 className="font-semibold text-text-primary border-b border-border pb-2">{title}</h2>
      {children}
    </div>
  );
}

function Toggle({
  label,
  checked,
  onChange,
  disabled,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <label className="flex items-center justify-between py-1.5">
      <span className="text-sm text-text-secondary">{label}</span>
      <button
        type="button"
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`relative w-11 h-6 rounded-full transition-colors ${
          checked ? "bg-purple" : "bg-surface-2 border border-border"
        } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        <span
          className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
            checked ? "translate-x-5" : "translate-x-0"
          }`}
        />
      </button>
    </label>
  );
}

function Input({
  label,
  value,
  onChange,
  type = "text",
  disabled,
  placeholder,
}: {
  label: string;
  value: string | number;
  onChange: (v: string) => void;
  type?: string;
  disabled?: boolean;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className="block text-xs text-text-muted mb-1.5">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-purple disabled:opacity-60"
      />
    </label>
  );
}

function SecretInput({
  label,
  value,
  onChange,
  disabled,
  placeholder,
  hint,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
  placeholder?: string;
  hint?: string;
}) {
  const [show, setShow] = useState(false);
  return (
    <label className="block">
      <span className="block text-xs text-text-muted mb-1.5">{label}</span>
      <div className="relative">
        <input
          type={show ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder={placeholder}
          className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 pr-9 text-sm text-text-primary focus:outline-none focus:border-purple disabled:opacity-60"
        />
        <button
          type="button"
          onClick={() => setShow((v) => !v)}
          disabled={disabled}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary disabled:opacity-40"
        >
          {show ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
        </button>
      </div>
      {hint && <p className="text-xs text-text-faint mt-1">{hint}</p>}
    </label>
  );
}

export default function AdminConfigPage() {
  const { user } = useAuthStore();
  const isOwner = user?.role === "owner" || user?.role === "superadmin";
  const [form, setForm] = useState<SystemConfig>(defaultConfig);
  const [dirty, setDirty] = useState(false);
  const [smtpTestEmail, setSmtpTestEmail] = useState("");
  const [telegramTestChatId, setTelegramTestChatId] = useState("");

  const { data, isLoading, isError } = useQuery<SystemConfig>({
    queryKey: ["admin-config"],
    queryFn: () => api.get("/api/v1/admin/config/").then((r) => r.data),
  });
  const {
    data: providerHealth = defaultProviderHealth,
    refetch: refetchProviderHealth,
  } = useQuery<ProviderHealthState>({
    queryKey: ["admin-provider-health"],
    queryFn: () =>
      api.get("/api/v1/admin/config/provider-status").then((r) => r.data),
  });

  useEffect(() => {
    if (data) {
      setForm(data);
      setDirty(false);
      if (!telegramTestChatId) {
        setTelegramTestChatId(data.integrations.telegram_vip_channel_id || "");
      }
    }
  }, [data, telegramTestChatId]);

  useEffect(() => {
    if (!smtpTestEmail) {
      setSmtpTestEmail(user?.email || "");
    }
  }, [smtpTestEmail, user?.email]);

  const saveMutation = useMutation({
    mutationFn: (payload: SystemConfig) =>
      api.put("/api/v1/admin/config/", payload).then((r) => r.data),
    onSuccess: (saved: SystemConfig) => {
      setForm(saved);
      setDirty(false);
      toast.success("Configuration saved");
    },
    onError: (e: any) => {
      toast.error(e?.response?.data?.detail || "Failed to save config");
    },
  });

  const smtpCheckMutation = useMutation({
    mutationFn: async (sendTestEmail: boolean) =>
      api.post("/api/v1/admin/config/check-smtp", {
        test_email: sendTestEmail && smtpTestEmail ? smtpTestEmail : null,
      }),
    onSuccess: async () => {
      await refetchProviderHealth();
      toast.success("SMTP check completed");
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || "SMTP check failed"),
  });

  const telegramCheckMutation = useMutation({
    mutationFn: async (sendTestMessage: boolean) =>
      api.post("/api/v1/admin/config/check-telegram", {
        chat_id: telegramTestChatId || null,
        send_test_message: sendTestMessage,
      }),
    onSuccess: async () => {
      await refetchProviderHealth();
      toast.success("Telegram check completed");
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || "Telegram check failed"),
  });

  const statusClass = (status: string) => {
    if (status === "healthy") return "text-long bg-long/10 border-long/20";
    if (status === "issue") return "text-short bg-short/10 border-short/20";
    return "text-text-muted bg-surface-2 border-border";
  };

  const statusLabel = (status: string) => {
    if (status === "healthy") return "Healthy";
    if (status === "issue") return "Provider Issue";
    return "Not Checked";
  };

  const formatCheckedAt = (raw?: string | null) => {
    if (!raw) return "Never";
    try {
      return new Date(raw).toLocaleString();
    } catch {
      return raw;
    }
  };

  const setTop = <K extends keyof SystemConfig>(key: K, value: SystemConfig[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setDirty(true);
  };

  const setAuth = (key: keyof SystemConfig["auth"], value: boolean | number) => {
    setForm((prev) => ({ ...prev, auth: { ...prev.auth, [key]: value } }));
    setDirty(true);
  };

  const setNotifications = (
    key: keyof SystemConfig["notifications"],
    value: boolean
  ) => {
    setForm((prev) => ({
      ...prev,
      notifications: { ...prev.notifications, [key]: value },
    }));
    setDirty(true);
  };

  const setSmtp = (
    key: keyof SystemConfig["smtp"],
    value: string | boolean | number
  ) => {
    setForm((prev) => ({ ...prev, smtp: { ...prev.smtp, [key]: value } }));
    setDirty(true);
  };

  const setIntegration = (
    key: keyof SystemConfig["integrations"],
    value: string
  ) => {
    setForm((prev) => ({
      ...prev,
      integrations: { ...prev.integrations, [key]: value },
    }));
    setDirty(true);
  };

  if (isLoading) {
    return (
      <div className="space-y-4 max-w-4xl">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-32 rounded-xl bg-surface border border-border animate-pulse" />
        ))}
      </div>
    );
  }

  if (isError) {
    return <div className="text-sm text-short">Failed to load configuration.</div>;
  }

  return (
    <div className="space-y-5 max-w-4xl">
      {!isOwner && (
        <div className="flex items-center gap-2 bg-gold/10 border border-gold/20 rounded-lg px-3 py-2 text-xs text-gold">
          <ShieldAlert className="w-4 h-4" />
          SMTP and API keys are owner-only. You can view masked values but cannot update them.
        </div>
      )}

      <Section title="Auth & Trial">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Input
            label="Trial Duration (hours)"
            type="number"
            value={form.auth.trial_hours}
            onChange={(v) => setAuth("trial_hours", Number(v))}
          />
          <Input
            label="Min Signal Confidence"
            type="number"
            value={form.min_signal_confidence}
            onChange={(v) => setTop("min_signal_confidence", Number(v))}
          />
        </div>
        <Toggle
          label="Require Email Verification on Login"
          checked={form.auth.require_email_verification}
          onChange={(v) => setAuth("require_email_verification", v)}
        />
        <Toggle
          label="Maintenance Mode"
          checked={form.maintenance_mode}
          onChange={(v) => setTop("maintenance_mode", v)}
        />
      </Section>

      <Section title="Scanner">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Input
            label="Interval (minutes)"
            type="number"
            value={form.scanner_interval_minutes}
            onChange={(v) => setTop("scanner_interval_minutes", Number(v))}
          />
          <Input
            label="Max Signals Per Scan"
            type="number"
            value={form.max_signals_per_scan}
            onChange={(v) => setTop("max_signals_per_scan", Number(v))}
          />
          <Input
            label="ICT Weight (0..5)"
            type="number"
            value={form.ict_weight}
            onChange={(v) => setTop("ict_weight", Number(v))}
          />
          <Input
            label="Trend Weight (0..5)"
            type="number"
            value={form.trend_weight}
            onChange={(v) => setTop("trend_weight", Number(v))}
          />
          <Input
            label="Momentum Weight (0..5)"
            type="number"
            value={form.momentum_weight}
            onChange={(v) => setTop("momentum_weight", Number(v))}
          />
        </div>
        <Toggle
          label="Scanner Enabled"
          checked={form.scanner_enabled}
          onChange={(v) => setTop("scanner_enabled", v)}
        />
        <Toggle
          label="Enable Crypto Scan"
          checked={form.enable_crypto_scan}
          onChange={(v) => setTop("enable_crypto_scan", v)}
        />
        <Toggle
          label="Enable Forex Scan"
          checked={form.enable_forex_scan}
          onChange={(v) => setTop("enable_forex_scan", v)}
        />
      </Section>

      <Section title="Notifications">
        <Toggle
          label="Enable Telegram Alerts"
          checked={form.notifications.enable_telegram_alerts}
          onChange={(v) => setNotifications("enable_telegram_alerts", v)}
        />
        <Toggle
          label="Enable Email Alerts"
          checked={form.notifications.enable_email_alerts}
          onChange={(v) => setNotifications("enable_email_alerts", v)}
        />
      </Section>

      <Section title="SMTP (Owner)">
        <div className="border border-border rounded-lg p-3 bg-surface-2/40">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-text-primary">SMTP Health</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${statusClass(providerHealth.smtp.status)}`}>
              {statusLabel(providerHealth.smtp.status)}
            </span>
          </div>
          <p className="text-xs text-text-secondary">{providerHealth.smtp.message}</p>
          <p className="text-xs text-text-muted mt-1">
            Last checked: {formatCheckedAt(providerHealth.smtp.checked_at)}
          </p>
          {providerHealth.smtp.details?.missing_fields?.length ? (
            <p className="text-xs text-gold mt-1">
              Missing: {providerHealth.smtp.details.missing_fields.join(", ")}
            </p>
          ) : null}
        </div>

        <Toggle
          label="SMTP Enabled"
          checked={form.smtp.enabled}
          onChange={(v) => setSmtp("enabled", v)}
          disabled={!isOwner}
        />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Input label="Host" value={form.smtp.host} onChange={(v) => setSmtp("host", v)} disabled={!isOwner} />
          <Input label="Port" type="number" value={form.smtp.port} onChange={(v) => setSmtp("port", Number(v))} disabled={!isOwner} />
          <Input label="Username (Email Address)" value={form.smtp.username} onChange={(v) => setSmtp("username", v)} disabled={!isOwner} placeholder="signals@yourdomain.com" />
          <SecretInput
            label="Password (Mailbox Password)"
            value={form.smtp.password}
            onChange={(v) => setSmtp("password", v)}
            disabled={!isOwner}
            placeholder="Your mailbox password"
            hint="Hostinger: use the password you set when creating the mailbox in hPanel"
          />
          <Input label="From Email" value={form.smtp.from_email} onChange={(v) => setSmtp("from_email", v)} disabled={!isOwner} />
          <Input label="From Name" value={form.smtp.from_name} onChange={(v) => setSmtp("from_name", v)} disabled={!isOwner} />
        </div>
        <Toggle label="Use TLS" checked={form.smtp.use_tls} onChange={(v) => setSmtp("use_tls", v)} disabled={!isOwner} />
        <Toggle label="Use SSL" checked={form.smtp.use_ssl} onChange={(v) => setSmtp("use_ssl", v)} disabled={!isOwner} />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-border">
          <Input
            label="SMTP Test Email"
            value={smtpTestEmail}
            onChange={setSmtpTestEmail}
            type="email"
            placeholder="owner@email.com"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => smtpCheckMutation.mutate(false)}
            disabled={smtpCheckMutation.isPending}
            className="px-3 py-2 text-xs rounded-lg border border-border bg-surface-2 text-text-primary hover:border-purple disabled:opacity-60"
          >
            {smtpCheckMutation.isPending ? "Checking..." : "Check SMTP"}
          </button>
          <button
            type="button"
            onClick={() => smtpCheckMutation.mutate(true)}
            disabled={smtpCheckMutation.isPending}
            className="px-3 py-2 text-xs rounded-lg border border-long/30 bg-long/10 text-long hover:bg-long/20 disabled:opacity-60"
          >
            Send Test Email
          </button>
        </div>
      </Section>

      <Section title="Telegram (Owner)">
        <div className="border border-border rounded-lg p-3 bg-surface-2/40">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-text-primary">Telegram Health</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${statusClass(providerHealth.telegram.status)}`}>
              {statusLabel(providerHealth.telegram.status)}
            </span>
          </div>
          <p className="text-xs text-text-secondary">{providerHealth.telegram.message}</p>
          <p className="text-xs text-text-muted mt-1">
            Last checked: {formatCheckedAt(providerHealth.telegram.checked_at)}
          </p>
          {providerHealth.telegram.details?.error ? (
            <p className="text-xs text-short mt-1">
              Error: {providerHealth.telegram.details.error}
            </p>
          ) : null}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <SecretInput label="Telegram Bot Token" value={form.integrations.telegram_bot_token} onChange={(v) => setIntegration("telegram_bot_token", v)} disabled={!isOwner} hint="From @BotFather — starts with numbers:ABC..." />
          <Input label="Telegram VIP Channel ID" value={form.integrations.telegram_vip_channel_id} onChange={(v) => setIntegration("telegram_vip_channel_id", v)} disabled={!isOwner} />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-border">
          <Input
            label="Telegram Test Chat ID"
            value={telegramTestChatId}
            onChange={setTelegramTestChatId}
            placeholder="5230257927 or @channelusername"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => telegramCheckMutation.mutate(false)}
            disabled={telegramCheckMutation.isPending}
            className="px-3 py-2 text-xs rounded-lg border border-border bg-surface-2 text-text-primary hover:border-purple disabled:opacity-60"
          >
            {telegramCheckMutation.isPending ? "Checking..." : "Check Telegram"}
          </button>
          <button
            type="button"
            onClick={() => telegramCheckMutation.mutate(true)}
            disabled={telegramCheckMutation.isPending}
            className="px-3 py-2 text-xs rounded-lg border border-long/30 bg-long/10 text-long hover:bg-long/20 disabled:opacity-60"
          >
            Send Test Message
          </button>
        </div>
      </Section>

      <Section title="API Keys & Billing (Owner)">
        <div className="space-y-2 text-xs text-text-muted bg-surface-2 rounded-lg p-3 border border-border">
          <p className="font-medium text-text-secondary">What each key does:</p>
          <p><span className="text-blue font-mono">Binance API</span> — Fetches live crypto prices &amp; candles for the scanner</p>
          <p><span className="text-blue font-mono">TwelveData API</span> — Fetches Forex (EUR/USD etc.) data for scanner</p>
          <p><span className="text-blue font-mono">Stripe Secret Key</span> — Processes card payments automatically (instant access on payment)</p>
          <p><span className="text-blue font-mono">Stripe Webhook Secret</span> — Verifies payment events from Stripe are genuine</p>
          <p><span className="text-blue font-mono">Stripe Price IDs</span> — Product price IDs from your Stripe dashboard (Products → Prices)</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-2">
          <SecretInput label="Binance API Key" value={form.integrations.binance_api_key} onChange={(v) => setIntegration("binance_api_key", v)} disabled={!isOwner} />
          <SecretInput label="Binance API Secret" value={form.integrations.binance_api_secret} onChange={(v) => setIntegration("binance_api_secret", v)} disabled={!isOwner} />
          <SecretInput label="TwelveData API Key" value={form.integrations.twelvedata_api_key} onChange={(v) => setIntegration("twelvedata_api_key", v)} disabled={!isOwner} hint="Get free key at twelvedata.com — 800 req/day free" />
          <SecretInput label="Stripe Secret Key" value={form.integrations.stripe_secret_key} onChange={(v) => setIntegration("stripe_secret_key", v)} disabled={!isOwner} hint="Stripe Dashboard → Developers → API Keys → Secret key" />
          <SecretInput label="Stripe Webhook Secret" value={form.integrations.stripe_webhook_secret} onChange={(v) => setIntegration("stripe_webhook_secret", v)} disabled={!isOwner} hint="Stripe → Webhooks → your endpoint → Signing secret" />
          <Input label="Stripe Monthly Price ID" value={form.integrations.stripe_monthly_price_id} onChange={(v) => setIntegration("stripe_monthly_price_id", v)} disabled={!isOwner} placeholder="price_xxx" />
          <Input label="Stripe Lifetime Price ID" value={form.integrations.stripe_lifetime_price_id} onChange={(v) => setIntegration("stripe_lifetime_price_id", v)} disabled={!isOwner} placeholder="price_xxx" />
        </div>
      </Section>

      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={() => saveMutation.mutate(form)}
          disabled={!dirty || saveMutation.isPending}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-purple text-white rounded-lg text-sm font-medium hover:bg-purple/90 disabled:opacity-60"
        >
          {saveMutation.isPending ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          {saveMutation.isPending ? "Saving..." : "Save Configuration"}
        </button>

        <button
          type="button"
          onClick={async () => {
            try {
              await api.post("/api/v1/admin/config/purge-signals", null, {
                params: { min_confidence: form.min_signal_confidence },
              });
              toast.success("Purge queued — low-quality signals will be cleared shortly");
            } catch {
              toast.error("Purge failed");
            }
          }}
          className="inline-flex items-center gap-2 px-4 py-2.5 border border-short/30 bg-short/10 text-short rounded-lg text-sm hover:bg-short/20 transition-colors"
        >
          <ShieldAlert className="w-4 h-4" />
          Purge Low-Quality Signals
        </button>
      </div>
    </div>
  );
}
