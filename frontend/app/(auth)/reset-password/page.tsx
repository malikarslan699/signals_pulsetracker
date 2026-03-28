"use client";
import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { Eye, EyeOff, KeyRound, ArrowLeft, CheckCircle2 } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import toast from "react-hot-toast";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [email, setEmail] = useState(searchParams.get("email") || "");
  const [otp, setOtp] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [done, setDone] = useState(false);

  const mutation = useMutation({
    mutationFn: (data: { email: string; otp: string; new_password: string }) =>
      api.post("/api/v1/auth/reset-password", data).then((r) => r.data),
    onSuccess: () => {
      setDone(true);
      setTimeout(() => router.push("/login"), 3000);
    },
    onError: (e: any) => {
      toast.error(e?.response?.data?.detail || "Invalid or expired OTP.");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      toast.error("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }
    mutation.mutate({ email, otp: otp.trim(), new_password: password });
  };

  if (done) {
    return (
      <div className="bg-surface border border-border rounded-2xl p-8 shadow-2xl text-center">
        <div className="flex justify-center mb-4">
          <div className="w-14 h-14 rounded-full bg-long/10 border border-long/20 flex items-center justify-center">
            <CheckCircle2 className="w-7 h-7 text-long" />
          </div>
        </div>
        <h1 className="text-xl font-bold text-text-primary mb-2">Password reset!</h1>
        <p className="text-sm text-text-muted mb-4">
          Your password has been updated. Redirecting to sign in...
        </p>
        <Link
          href="/login"
          className="inline-flex items-center justify-center w-full py-2.5 bg-long hover:bg-long/90 text-white font-semibold rounded-lg transition-all text-sm"
        >
          Sign In Now
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-2xl p-8 shadow-2xl">
      <div className="mb-6 text-center">
        <div className="flex justify-center mb-4">
          <div className="w-12 h-12 rounded-full bg-long/10 border border-long/20 flex items-center justify-center">
            <KeyRound className="w-6 h-6 text-long" />
          </div>
        </div>
        <h1 className="text-2xl font-bold text-text-primary">Reset password</h1>
        <p className="text-sm text-text-muted mt-1">
          Enter the OTP sent to your email
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Email (editable in case user navigated directly) */}
        <div>
          <label htmlFor="email" className="block text-xs font-medium text-text-secondary mb-1.5">
            Email Address
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full px-4 py-2.5 bg-surface-2 border border-border rounded-lg text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-long transition-colors"
          />
        </div>

        {/* OTP */}
        <div>
          <label htmlFor="otp" className="block text-xs font-medium text-text-secondary mb-1.5">
            OTP Code
          </label>
          <input
            id="otp"
            type="text"
            inputMode="numeric"
            maxLength={6}
            required
            value={otp}
            onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
            placeholder="123456"
            className="w-full px-4 py-2.5 bg-surface-2 border border-border rounded-lg text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-long transition-colors tracking-widest font-mono text-center"
          />
        </div>

        {/* New password */}
        <div>
          <label htmlFor="password" className="block text-xs font-medium text-text-secondary mb-1.5">
            New Password
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              required
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
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Confirm password */}
        <div>
          <label htmlFor="confirm" className="block text-xs font-medium text-text-secondary mb-1.5">
            Confirm New Password
          </label>
          <input
            id="confirm"
            type={showPassword ? "text" : "password"}
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Repeat password"
            className="w-full px-4 py-2.5 bg-surface-2 border border-border rounded-lg text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-long transition-colors"
          />
        </div>

        <button
          type="submit"
          disabled={mutation.isPending}
          className="w-full flex items-center justify-center gap-2 py-3 bg-long hover:bg-long/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all shadow-lg shadow-long/20 mt-2"
        >
          {mutation.isPending ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Resetting...
            </>
          ) : (
            <>
              <KeyRound className="w-4 h-4" />
              Reset Password
            </>
          )}
        </button>
      </form>

      <div className="mt-6 text-center">
        <Link
          href="/forgot-password"
          className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Resend OTP
        </Link>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="bg-surface border border-border rounded-2xl p-8 shadow-2xl animate-pulse h-96" />}>
      <ResetPasswordForm />
    </Suspense>
  );
}
