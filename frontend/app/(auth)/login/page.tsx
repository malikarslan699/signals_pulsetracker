"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Eye, EyeOff, LogIn, AlertCircle } from "lucide-react";
import { useLogin } from "@/hooks/useAuth";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import toast from "react-hot-toast";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [resendEmail, setResendEmail] = useState("");
  const [verifyPending, setVerifyPending] = useState(false);

  const { mutate: login, isPending, error } = useLogin();

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    setVerifyPending(params.get("verify") === "pending");
    setResendEmail(params.get("email") || "");
  }, []);

  const resendMutation = useMutation({
    mutationFn: async (targetEmail: string) =>
      api.post("/api/v1/auth/resend-verification", { email: targetEmail }),
    onSuccess: () => {
      toast.success("If email exists, verification link has been sent.");
    },
    onError: (e: any) => {
      toast.error(
        e?.response?.data?.detail || "Could not send verification email."
      );
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login({ email, password });
  };

  const errorMessage =
    (error as any)?.response?.data?.detail ||
    (error as any)?.response?.data?.message ||
    (error ? "Login failed. Please check your credentials." : null);

  return (
    <div className="bg-surface border border-border rounded-2xl p-8 shadow-2xl">
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-text-primary">Sign in</h1>
        <p className="text-sm text-text-muted mt-1">
          Sign in to PulseSignal Pro
        </p>
      </div>

      {errorMessage && (
        <div className="flex items-center gap-2 bg-short/10 border border-short/20 rounded-lg px-4 py-3 mb-5 text-sm text-short">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {errorMessage}
        </div>
      )}

      {verifyPending && (
        <div className="bg-blue/10 border border-blue/20 rounded-lg px-4 py-3 mb-5">
          <p className="text-sm text-blue mb-2">
            Account created. Please verify your email before login.
          </p>
          <div className="flex gap-2">
            <input
              type="email"
              value={resendEmail}
              onChange={(e) => setResendEmail(e.target.value)}
              placeholder="your@email.com"
              className="flex-1 px-3 py-2 bg-surface-2 border border-border rounded-lg text-xs text-text-primary focus:outline-none focus:border-blue"
            />
            <button
              type="button"
              onClick={() => {
                if (!resendEmail) {
                  toast.error("Email required");
                  return;
                }
                resendMutation.mutate(resendEmail);
              }}
              disabled={resendMutation.isPending}
              className="px-3 py-2 bg-blue text-white rounded-lg text-xs font-medium hover:bg-blue/90 disabled:opacity-60"
            >
              {resendMutation.isPending ? "Sending..." : "Resend Link"}
            </button>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
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
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full px-4 py-2.5 bg-surface-2 border border-border rounded-lg text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-purple transition-colors"
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
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-4 py-2.5 pr-10 bg-surface-2 border border-border rounded-lg text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-purple transition-colors"
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
          className="w-full flex items-center justify-center gap-2 py-3 bg-purple hover:bg-purple/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all shadow-lg shadow-purple/20 mt-2"
        >
          {isPending ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Signing in...
            </>
          ) : (
            <>
              <LogIn className="w-4 h-4" />
              Sign In
            </>
          )}
        </button>
      </form>

      <p className="text-center text-sm text-text-muted mt-6">
        Don&apos;t have an account?{" "}
        <Link
          href="/register"
          className="text-purple hover:text-purple/80 font-medium transition-colors"
        >
          Register for free
        </Link>
      </p>
    </div>
  );
}
