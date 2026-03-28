"use client";
import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/userStore";
import { Panel } from "@/components/terminal/Panel";
import { User, Shield, Bell, LogOut, Copy, Check, Mail, AlertTriangle, MessageCircle, RefreshCw } from "lucide-react";
import toast from "react-hot-toast";
import { useLogout } from "@/hooks/useAuth";
import { User as UserType } from "@/types/user";

export default function SettingsPage() {
  const { user, setUser } = useAuthStore();
  const logout = useLogout();
  const [copied, setCopied] = useState(false);
  const [telegramCode, setTelegramCode] = useState<string | null>(null);
  const [profileForm, setProfileForm] = useState({ username: user?.username || "" });

  const {
    data: meData,
    refetch: refetchMe,
    isFetching: isRefreshingMe,
  } = useQuery<UserType>({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const res = await api.get<UserType>("/api/v1/auth/me");
      return res.data;
    },
    enabled: Boolean(user),
    refetchInterval: user?.telegram_chat_id ? 30_000 : 8_000,
  });

  useEffect(() => {
    if (!meData) return;
    const prevUsername = user?.username || "";
    setUser(meData);
    setProfileForm((prev) =>
      prev.username === prevUsername ? { username: meData.username || "" } : prev
    );
    if (meData.telegram_chat_id) {
      setTelegramCode(null);
    }
  }, [meData, setUser, user?.username]);

  const updateProfileMutation = useMutation({
    mutationFn: (data: { username: string }) => api.put("/api/v1/auth/me", data),
    onSuccess: (res: any) => {
      const nextUser = res?.data as UserType | undefined;
      if (nextUser) setUser(nextUser);
      toast.success("Profile updated!");
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || "Update failed"),
  });

  const resendVerificationMutation = useMutation({
    mutationFn: async () =>
      api.post("/api/v1/auth/resend-verification", { email: user?.email }),
    onSuccess: () =>
      toast.success("Verification email sent (if account exists)."),
    onError: (e: any) =>
      toast.error(
        e?.response?.data?.detail || "Failed to send verification email"
      ),
  });

  const generateTelegramCode = async () => {
    try {
      const res = await api.post("/api/v1/auth/connect-telegram");
      setTelegramCode(res.data.verification_code);
      toast.success("Telegram verification code generated.");
      refetchMe();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Failed to generate code");
    }
  };

  const copyCode = () => {
    if (telegramCode) {
      navigator.clipboard.writeText(telegramCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success("Code copied!");
    }
  };

  const planLabels: Record<string, string> = {
    trial: "Trial",
    monthly: "Monthly Pro",
    yearly: "Yearly Pro",
    lifetime: "Lifetime Pro",
  };

  const planColors: Record<string, string> = {
    trial: "text-text-muted",
    monthly: "text-long",
    yearly: "text-long",
    lifetime: "text-gold",
  };

  return (
    <div className="p-3 space-y-3 max-w-2xl pb-20 lg:pb-6">
      <h1 className="text-sm font-semibold text-text-primary">Settings</h1>

      {/* Subscription */}
      <Panel noPad>
        <div className="terminal-header">
          <span className="text-2xs font-semibold uppercase tracking-widest text-text-muted">Subscription</span>
        </div>
        <div className="px-3 py-2 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-4 h-4 text-long" />
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-text-primary">Current Plan</span>
                <span className={`text-xs font-bold capitalize ${planColors[user?.plan || "trial"]}`}>
                  {planLabels[user?.plan || "trial"] ?? user?.plan}
                </span>
              </div>
              {user?.plan_expires_at && user.plan !== "lifetime" && (
                <span className="text-2xs text-text-muted">
                  Expires: {new Date(user.plan_expires_at).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
          {user?.plan === "trial" ? (
            <a
              href="/pricing"
              className="filter-pill text-long border-long/30 hover:bg-long/10"
            >
              Upgrade
            </a>
          ) : (
            <button className="filter-pill">Manage</button>
          )}
        </div>
      </Panel>

      {/* Profile */}
      <Panel title="PROFILE">
        <div className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 block">
                Username
              </label>
              <input
                type="text"
                value={profileForm.username}
                onChange={(e) => setProfileForm({ username: e.target.value })}
                className="w-full h-8 px-2.5 text-xs bg-surface-2 border border-border rounded focus:outline-none focus:ring-1 focus:ring-long text-text-primary"
              />
            </div>
            <div>
              <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 block">
                Email
              </label>
              <div className="flex gap-1.5">
                <input
                  type="email"
                  value={user?.email || ""}
                  disabled
                  className="flex-1 h-8 px-2.5 text-xs bg-surface-2 border border-border rounded text-text-muted cursor-not-allowed"
                />
                {user?.is_verified !== false ? (
                  <span className="flex items-center px-2 text-2xs font-semibold text-long bg-long/10 rounded">
                    Verified
                  </span>
                ) : (
                  <span className="flex items-center px-2 text-2xs font-semibold text-gold bg-gold/10 rounded">
                    Unverified
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            {user?.is_verified === false && (
              <button
                onClick={() => resendVerificationMutation.mutate()}
                disabled={resendVerificationMutation.isPending}
                className="filter-pill gap-1 disabled:opacity-60"
              >
                {resendVerificationMutation.isPending ? (
                  <RefreshCw className="h-3 w-3 animate-spin" />
                ) : (
                  <Mail className="h-3 w-3" />
                )}
                {resendVerificationMutation.isPending ? "Sending..." : "Resend Verification"}
              </button>
            )}
            <button
              onClick={() => updateProfileMutation.mutate(profileForm)}
              disabled={updateProfileMutation.isPending}
              className="px-3 py-1.5 bg-long text-white rounded text-xs font-medium hover:opacity-90 transition-opacity disabled:opacity-60"
            >
              {updateProfileMutation.isPending ? "Saving..." : "Save Profile"}
            </button>
          </div>
        </div>
      </Panel>

      {/* Telegram */}
      <Panel noPad>
        <div className="terminal-header">
          <span className="text-2xs font-semibold uppercase tracking-widest text-text-muted">Telegram Integration</span>
        </div>
        <div className="px-3 py-2 space-y-2">
          <div className="flex justify-end">
            <button
              onClick={() => refetchMe()}
              disabled={isRefreshingMe}
              className="filter-pill gap-1 disabled:opacity-60"
            >
              <RefreshCw className={`h-3 w-3 ${isRefreshingMe ? "animate-spin" : ""}`} />
              Refresh Status
            </button>
          </div>
          {user?.telegram_chat_id ? (
            <div className="flex items-center gap-2 text-xs text-long">
              <Check className="w-3.5 h-3.5" />
              <span>Telegram connected (ID: {user.telegram_chat_id})</span>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-2 text-xs">
                <MessageCircle className="h-3.5 w-3.5 text-blue" />
                <span className="text-text-primary font-medium">Not Connected</span>
              </div>
              <p className="text-2xs text-text-muted">
                Generate a verification code and send it to{" "}
                <span className="text-blue font-mono">@PulseSignalProBot</span> on Telegram
                using <span className="font-mono text-gold">/start YOUR_CODE</span>.
              </p>
              {telegramCode ? (
                <div className="flex items-center gap-2">
                  <code className="flex-1 bg-surface-2 border border-border rounded px-3 py-1.5 text-gold font-mono text-xs">
                    {telegramCode}
                  </code>
                  <button
                    onClick={copyCode}
                    className="p-1.5 bg-surface-2 border border-border rounded hover:border-gold transition-colors"
                  >
                    {copied ? (
                      <Check className="w-3.5 h-3.5 text-long" />
                    ) : (
                      <Copy className="w-3.5 h-3.5 text-text-muted" />
                    )}
                  </button>
                </div>
              ) : (
                <button
                  onClick={generateTelegramCode}
                  className="px-3 py-1.5 bg-long text-white rounded text-xs font-medium hover:opacity-90 transition-opacity"
                >
                  Generate Code
                </button>
              )}
            </>
          )}
        </div>
      </Panel>

      {/* Danger Zone */}
      <Panel noPad>
        <div className="terminal-header">
          <div className="flex items-center gap-1.5 text-short">
            <AlertTriangle className="h-3 w-3" />
            <span>Danger Zone</span>
          </div>
        </div>
        <div className="px-3 py-2 flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-text-primary">Sign Out</span>
            <p className="text-2xs text-text-muted">End your current session</p>
          </div>
          <button
            onClick={() => logout.mutate()}
            className="filter-pill gap-1 border-short/30 text-short hover:bg-short/10"
          >
            <LogOut className="h-3 w-3" />
            Sign Out
          </button>
        </div>
      </Panel>
    </div>
  );
}
