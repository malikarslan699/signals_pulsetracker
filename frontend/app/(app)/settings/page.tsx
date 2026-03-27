"use client";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/userStore";
import { User, Shield, Bell, LogOut, Copy, Check, Mail } from "lucide-react";
import toast from "react-hot-toast";
import { useLogout } from "@/hooks/useAuth";

export default function SettingsPage() {
  const { user } = useAuthStore();
  const logout = useLogout();
  const [copied, setCopied] = useState(false);
  const [telegramCode, setTelegramCode] = useState<string | null>(null);
  const [profileForm, setProfileForm] = useState({ username: user?.username || "" });

  const updateProfileMutation = useMutation({
    mutationFn: (data: { username: string }) => api.put("/api/v1/auth/me", data),
    onSuccess: () => toast.success("Profile updated!"),
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Update failed"),
  });

  const resendVerificationMutation = useMutation({
    mutationFn: async () =>
      api.post("/api/v1/auth/resend-verification", { email: user?.email }),
    onSuccess: () => toast.success("Verification email sent (if account exists)."),
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || "Failed to send verification email"),
  });

  const generateTelegramCode = async () => {
    try {
      const res = await api.post("/api/v1/auth/connect-telegram");
      setTelegramCode(res.data.verification_code);
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
    trial:    "Trial",
    monthly:  "Monthly Pro",
    yearly:   "Yearly Pro",
    lifetime: "Lifetime Pro",
  };

  const planColors: Record<string, string> = {
    trial:    "text-text-muted",
    monthly:  "text-purple",
    yearly:   "text-long",
    lifetime: "text-gold",
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 pb-20 lg:pb-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Settings</h1>
        <p className="text-text-muted text-sm mt-1">Manage your account and preferences</p>
      </div>

      {/* Plan Info */}
      <div className="bg-surface border border-border rounded-xl p-5">
        <div className="flex items-center gap-3 mb-4">
          <Shield className="w-5 h-5 text-purple" />
          <h2 className="font-semibold text-text-primary">Subscription</h2>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className={`text-lg font-bold ${planColors[user?.plan || "trial"]}`}>
              {planLabels[user?.plan || "trial"] ?? user?.plan}
            </p>
            {user?.plan_expires_at && user.plan !== "lifetime" && (
              <p className="text-xs text-text-muted mt-1">
                Expires: {new Date(user.plan_expires_at).toLocaleDateString()}
              </p>
            )}
          </div>
          {user?.plan === "trial" ? (
            <a
              href="/pricing"
              className="px-4 py-2 bg-purple text-white rounded-lg text-sm font-medium hover:bg-purple/90 transition-colors"
            >
              Upgrade
            </a>
          ) : null}
        </div>
      </div>

      {/* Profile */}
      <div className="bg-surface border border-border rounded-xl p-5">
        <div className="flex items-center gap-3 mb-4">
          <User className="w-5 h-5 text-blue" />
          <h2 className="font-semibold text-text-primary">Profile</h2>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-text-muted mb-1.5">Email</label>
            <input
              type="email"
              value={user?.email || ""}
              disabled
              className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-text-muted text-sm cursor-not-allowed"
            />
            {user?.is_verified === false && (
              <div className="mt-2 flex items-center gap-2">
                <span className="text-xs text-gold">Email not verified</span>
                <button
                  onClick={() => resendVerificationMutation.mutate()}
                  disabled={resendVerificationMutation.isPending}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-gold/10 border border-gold/30 text-gold rounded text-xs"
                >
                  <Mail className="w-3 h-3" />
                  {resendVerificationMutation.isPending ? "Sending..." : "Resend"}
                </button>
              </div>
            )}
          </div>
          <div>
            <label className="block text-sm text-text-muted mb-1.5">Username</label>
            <input
              type="text"
              value={profileForm.username}
              onChange={(e) => setProfileForm({ username: e.target.value })}
              className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-text-primary text-sm focus:outline-none focus:border-purple"
            />
          </div>
          <button
            onClick={() => updateProfileMutation.mutate(profileForm)}
            disabled={updateProfileMutation.isPending}
            className="px-5 py-2.5 bg-blue text-white rounded-lg text-sm font-medium hover:bg-blue/90 transition-colors"
          >
            {updateProfileMutation.isPending ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      {/* Telegram Connect */}
      <div className="bg-surface border border-border rounded-xl p-5">
        <div className="flex items-center gap-3 mb-4">
          <Bell className="w-5 h-5 text-gold" />
          <h2 className="font-semibold text-text-primary">Telegram Alerts</h2>
        </div>

        {user?.telegram_chat_id ? (
          <div className="flex items-center gap-2 text-long text-sm">
            <Check className="w-4 h-4" />
            <span>Telegram connected (ID: {user.telegram_chat_id})</span>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-text-secondary">
              Connect your Telegram to receive signal alerts.
            </p>
            <ol className="text-sm text-text-muted space-y-1 list-decimal list-inside">
              <li>Open <span className="text-blue font-mono">@PulseSignalProBot</span> on Telegram</li>
              <li>Click "Generate Code" below and copy it</li>
              <li>Send <span className="font-mono text-gold">/start YOUR_CODE</span> to the bot</li>
            </ol>
            {telegramCode ? (
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-gold font-mono text-sm">
                  {telegramCode}
                </code>
                <button
                  onClick={copyCode}
                  className="p-2.5 bg-surface-2 border border-border rounded-lg hover:border-gold transition-colors"
                >
                  {copied ? <Check className="w-4 h-4 text-long" /> : <Copy className="w-4 h-4 text-text-muted" />}
                </button>
              </div>
            ) : (
              <button
                onClick={generateTelegramCode}
                className="px-5 py-2.5 bg-gold/10 border border-gold/30 text-gold rounded-lg text-sm font-medium hover:bg-gold/20 transition-colors"
              >
                Generate Verification Code
              </button>
            )}
          </div>
        )}
      </div>

      {/* Danger Zone */}
      <div className="bg-surface border border-short/20 rounded-xl p-5">
        <h2 className="font-semibold text-short mb-4">Danger Zone</h2>
        <button
          onClick={() => logout.mutate()}
          className="flex items-center gap-2 px-4 py-2.5 bg-short/10 border border-short/30 text-short rounded-lg text-sm font-medium hover:bg-short/20 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </div>
  );
}
