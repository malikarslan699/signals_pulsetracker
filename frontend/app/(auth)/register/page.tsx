"use client";
import { useState } from "react";
import Link from "next/link";
import { Eye, EyeOff, UserPlus, AlertCircle } from "lucide-react";
import { useRegister } from "@/hooks/useAuth";

const COMMON_EMAIL_DOMAIN_TYPOS: Record<string, string> = {
  "gamil.com": "gmail.com",
  "gmai.com": "gmail.com",
  "gmail.co": "gmail.com",
  "gmail.con": "gmail.com",
  "gmaill.com": "gmail.com",
  "gmial.com": "gmail.com",
  "gnail.com": "gmail.com",
  "hotnail.com": "hotmail.com",
  "hotmai.com": "hotmail.com",
  "yaho.com": "yahoo.com",
  "yhoo.com": "yahoo.com",
  "outlok.com": "outlook.com",
  "outllok.com": "outlook.com",
};

function getDomainSuggestion(email: string): string | null {
  const parts = email.split("@");
  if (parts.length !== 2) return null;
  const domain = parts[1].toLowerCase();
  return COMMON_EMAIL_DOMAIN_TYPOS[domain] || null;
}

export default function RegisterPage() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [confirmEmail, setConfirmEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const { mutate: register, isPending, error } = useRegister();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const normalizedEmail = email.trim().toLowerCase();
    const normalizedConfirmEmail = confirmEmail.trim().toLowerCase();
    const suggestion = getDomainSuggestion(normalizedEmail);

    if (suggestion) {
      setFormError(`Email domain looks incorrect. Did you mean ${suggestion}?`);
      return;
    }

    if (normalizedEmail !== normalizedConfirmEmail) {
      setFormError("Email and confirm email do not match.");
      return;
    }

    register({ username: username.trim(), email: normalizedEmail, password });
  };

  const errorMessage =
    formError ||
    (error as any)?.response?.data?.detail ||
    (error as any)?.response?.data?.message ||
    (error ? "Registration failed. Please try again." : null);

  return (
    <div className="bg-surface border border-border rounded-2xl p-8 shadow-2xl">
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-text-primary">Create account</h1>
        <p className="text-sm text-text-muted mt-1">
          Start your free trial today
        </p>
      </div>

      {errorMessage && (
        <div className="flex items-center gap-2 bg-short/10 border border-short/20 rounded-lg px-4 py-3 mb-5 text-sm text-short">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {errorMessage}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Username */}
        <div>
          <label
            htmlFor="username"
            className="block text-xs font-medium text-text-secondary mb-1.5"
          >
            Username
          </label>
          <input
            id="username"
            type="text"
            autoComplete="username"
            required
            minLength={3}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="tradingpro"
            className="w-full px-4 py-2.5 bg-surface-2 border border-border rounded-lg text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-long transition-colors"
          />
        </div>

        {/* Email */}
        <div>
          <label
            htmlFor="email"
            className="block text-xs font-medium text-text-secondary mb-1.5"
          >
            Email Address
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (formError) setFormError(null);
            }}
            placeholder="you@example.com"
            className="w-full px-4 py-2.5 bg-surface-2 border border-border rounded-lg text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-long transition-colors"
          />
        </div>

        {/* Confirm Email */}
        <div>
          <label
            htmlFor="confirm-email"
            className="block text-xs font-medium text-text-secondary mb-1.5"
          >
            Confirm Email
          </label>
          <input
            id="confirm-email"
            type="email"
            autoComplete="email"
            required
            value={confirmEmail}
            onChange={(e) => {
              setConfirmEmail(e.target.value);
              if (formError) setFormError(null);
            }}
            placeholder="retype your email"
            className="w-full px-4 py-2.5 bg-surface-2 border border-border rounded-lg text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-long transition-colors"
          />
        </div>

        {/* Password */}
        <div>
          <label
            htmlFor="password"
            className="block text-xs font-medium text-text-secondary mb-1.5"
          >
            Password
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min. 8 characters"
              className="w-full px-4 py-2.5 pr-10 bg-surface-2 border border-border rounded-lg text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-long transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary transition-colors"
            >
              {showPassword ? (
                <EyeOff className="w-4 h-4" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isPending}
          className="w-full flex items-center justify-center gap-2 py-3 bg-long hover:bg-long/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all shadow-lg shadow-long/20 mt-2"
        >
          {isPending ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Creating account...
            </>
          ) : (
            <>
              <UserPlus className="w-4 h-4" />
              Create Account
            </>
          )}
        </button>
      </form>

      <p className="text-center text-sm text-text-muted mt-6">
        Already have an account?{" "}
        <Link
          href="/login"
          className="text-long hover:text-long/80 font-medium transition-colors"
        >
          Sign in
        </Link>
      </p>

      <p className="text-center text-xs text-text-muted mt-3">
        Free trial includes 5 signals per day
      </p>
    </div>
  );
}
