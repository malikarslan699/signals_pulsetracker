"use client";
import { useState } from "react";
import Link from "next/link";
import { Mail, ArrowLeft, AlertCircle, CheckCircle2 } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import toast from "react-hot-toast";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  const mutation = useMutation({
    mutationFn: (email: string) =>
      api.post("/api/v1/auth/forgot-password", { email }).then((r) => r.data),
    onSuccess: () => {
      setSent(true);
    },
    onError: () => {},
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    mutation.mutate(email);
  };

  if (sent) {
    return (
      <div className="bg-surface border border-border rounded-2xl p-8 shadow-2xl text-center">
        <div className="flex justify-center mb-4">
          <div className="w-14 h-14 rounded-full bg-long/10 border border-long/20 flex items-center justify-center">
            <CheckCircle2 className="w-7 h-7 text-long" />
          </div>
        </div>
        <h1 className="text-xl font-bold text-text-primary mb-2">Check your email</h1>
        <p className="text-sm text-text-muted mb-6">
          If <span className="text-text-primary font-medium">{email}</span> is registered,
          a 6-digit OTP has been sent. It expires in 10 minutes.
        </p>
        <Link
          href={`/reset-password?email=${encodeURIComponent(email)}`}
          className="inline-flex items-center justify-center w-full py-2.5 bg-purple hover:bg-purple/90 text-white font-semibold rounded-lg transition-all text-sm"
        >
          Enter OTP &amp; Reset Password
        </Link>
        <button
          onClick={() => { setSent(false); mutation.reset(); }}
          className="mt-3 w-full text-xs text-text-muted hover:text-text-primary transition-colors"
        >
          Use a different email
        </button>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-2xl p-8 shadow-2xl">
      <div className="mb-6 text-center">
        <div className="flex justify-center mb-4">
          <div className="w-12 h-12 rounded-full bg-purple/10 border border-purple/20 flex items-center justify-center">
            <Mail className="w-6 h-6 text-purple" />
          </div>
        </div>
        <h1 className="text-2xl font-bold text-text-primary">Forgot password?</h1>
        <p className="text-sm text-text-muted mt-1">
          Enter your email to receive a reset code
        </p>
      </div>

      {mutation.isError && (
        <div className="flex items-center gap-2 bg-short/10 border border-short/20 rounded-lg px-4 py-3 mb-1 text-sm text-short">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {(mutation.error as any)?.response?.data?.detail || "Something went wrong. Please try again."}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
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
            onChange={(e) => { setEmail(e.target.value); mutation.reset(); }}
            placeholder="you@example.com"
            className={`w-full px-4 py-2.5 bg-surface-2 border rounded-lg text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-purple transition-colors ${mutation.isError ? "border-short" : "border-border"}`}
          />
        </div>

        <button
          type="submit"
          disabled={mutation.isPending}
          className="w-full flex items-center justify-center gap-2 py-3 bg-purple hover:bg-purple/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all shadow-lg shadow-purple/20"
        >
          {mutation.isPending ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Sending...
            </>
          ) : (
            <>
              <Mail className="w-4 h-4" />
              Send Reset Code
            </>
          )}
        </button>
      </form>

      <div className="mt-6 text-center">
        <Link
          href="/login"
          className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Sign In
        </Link>
      </div>
    </div>
  );
}
