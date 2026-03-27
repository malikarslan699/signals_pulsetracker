"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";

export default function VerifyEmailPage() {
  const [token, setToken] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    setToken(params.get("token") || "");
  }, []);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["verify-email", token],
    enabled: token.length > 0,
    retry: false,
    queryFn: async () => {
      const res = await api.get("/api/v1/auth/verify-email", {
        params: { token },
      });
      return res.data;
    },
  });

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-surface border border-border rounded-2xl p-8 text-center">
        {isLoading ? (
          <div className="space-y-3">
            <Loader2 className="w-10 h-10 mx-auto text-blue animate-spin" />
            <p className="text-text-secondary text-sm">Verifying your email...</p>
          </div>
        ) : token.length === 0 || isError ? (
          <div className="space-y-3">
            <XCircle className="w-10 h-10 mx-auto text-short" />
            <h1 className="text-xl font-semibold text-text-primary">Verification failed</h1>
            <p className="text-sm text-text-muted">
              Link is invalid or expired. Please request a new verification link.
            </p>
            <Link
              href="/login"
              className="inline-block mt-2 px-4 py-2 bg-purple text-white rounded-lg text-sm"
            >
              Back to Login
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            <CheckCircle2 className="w-10 h-10 mx-auto text-long" />
            <h1 className="text-xl font-semibold text-text-primary">Email verified</h1>
            <p className="text-sm text-text-muted">
              {data?.message || "Your account is verified. You can now sign in."}
            </p>
            <Link
              href="/login"
              className="inline-block mt-2 px-4 py-2 bg-purple text-white rounded-lg text-sm"
            >
              Continue to Login
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
