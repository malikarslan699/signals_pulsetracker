"use client";

import { useState } from "react";
import Link from "next/link";
import { useUserStore } from "@/store/userStore";
import { api } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { Check, Zap, Star, TrendingUp, Crown, ChevronDown } from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface SubscriptionPlan {
  id: string;
  name: string;
  price_usd: number;
  duration_days: number | null;
  duration_label: string;
  description: string;
  badge_text: string;
  badge_color: string;
  features: string[];
  feature_flags?: Record<string, unknown>;
}

const FAQ_ITEMS = [
  {
    question: "Can I cancel my subscription anytime?",
    answer:
      "Yes. You can cancel your Monthly or Yearly plan at any time. Your access continues until the end of the current billing period and you will not be charged again.",
  },
  {
    question: "How does the Trial plan work?",
    answer:
      "The Trial plan gives you access for 24 hours with limited features — delayed signals, 7 days of history, and crypto access only. It's perfect for exploring the platform before committing to a paid plan.",
  },
  {
    question: "How do I set up Telegram alerts?",
    answer:
      "After upgrading to Monthly or higher, navigate to Settings → Telegram and follow the bot link. Authorize the bot and you'll receive real-time signal alerts directly in Telegram.",
  },
  {
    question: "What is the difference between Yearly and Lifetime?",
    answer:
      "Yearly Pro gives you 12 months of full access at a 43% discount vs Monthly. Lifetime Pro is a one-time payment for unlimited, permanent access with no recurring fees — the best long-term value.",
  },
  {
    question: "What is your refund policy?",
    answer:
      "We offer a 7-day money-back guarantee on Monthly and Yearly plans. Lifetime purchases are refundable within 14 days if you haven't used advanced features. Contact support to initiate a refund.",
  },
];

const PLAN_ICONS: Record<string, React.ReactNode> = {
  trial: <Zap className="w-5 h-5" />,
  monthly: <Star className="w-5 h-5" />,
  yearly: <TrendingUp className="w-5 h-5" />,
  lifetime: <Crown className="w-5 h-5" />,
};

const PLAN_ACCENT: Record<string, { border: string; glow: string; btn: string; text: string; bg: string }> = {
  trial:    { border: "#374151", glow: "none", btn: "#374151", text: "#9CA3AF", bg: "#1F2937" },
  monthly:  { border: "#8B5CF6", glow: "0 0 40px rgba(139,92,246,0.2)", btn: "#8B5CF6", text: "#8B5CF6", bg: "#1F2937" },
  yearly:   { border: "#10B981", glow: "0 0 40px rgba(16,185,129,0.2)", btn: "#10B981", text: "#10B981", bg: "#1F2937" },
  lifetime: { border: "#F59E0B", glow: "0 0 40px rgba(245,158,11,0.2)", btn: "#F59E0B", text: "#F59E0B", bg: "#1F2937" },
};

// ---------------------------------------------------------------------------
// Checkout hook
// ---------------------------------------------------------------------------
function useCheckout() {
  const { isAuthenticated } = useUserStore();
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function startCheckout(planId: string) {
    if (planId === "trial") {
      window.location.href = "/register";
      return;
    }
    if (!isAuthenticated) {
      window.location.href = `/register?plan=${planId}`;
      return;
    }
    setLoadingPlan(planId);
    setError(null);
    try {
      const response = await api.post<{ url?: string; checkout_url?: string }>(
        "/api/v1/subscriptions/checkout",
        { plan: planId }
      );
      const checkoutUrl = response.data?.checkout_url || response.data?.url;
      if (checkoutUrl) {
        window.location.href = checkoutUrl;
      } else {
        setError("Unable to start checkout. Please try again.");
      }
    } catch {
      setError("Something went wrong. Please try again later.");
    } finally {
      setLoadingPlan(null);
    }
  }

  return { startCheckout, loadingPlan, error };
}

// ---------------------------------------------------------------------------
// Pricing Card
// ---------------------------------------------------------------------------
function PricingCard({
  plan,
  onSelect,
  loading,
  isAuthenticated,
}: {
  plan: SubscriptionPlan;
  onSelect: (id: string) => void;
  loading: boolean;
  isAuthenticated: boolean;
}) {
  const accent = PLAN_ACCENT[plan.id] ?? PLAN_ACCENT.monthly;
  const isFeatured = plan.badge_text !== "";

  const ctaLabel = () => {
    if (loading) return "Redirecting…";
    if (plan.id === "trial") return isAuthenticated ? "Go to Dashboard" : "Start Free Trial";
    if (plan.id === "lifetime") return "Get Lifetime Access";
    return `Start ${plan.name}`;
  };

  const ctaHref = plan.id === "trial" && isAuthenticated ? "/dashboard" : undefined;

  return (
    <div
      className="rounded-2xl border flex flex-col h-full relative"
      style={{
        backgroundColor: accent.bg,
        borderColor: accent.border,
        borderWidth: isFeatured ? "2px" : "1px",
        boxShadow: accent.glow,
      }}
    >
      {plan.badge_text && (
        <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 z-10">
          <span
            className="px-4 py-1 rounded-full text-xs font-semibold text-white whitespace-nowrap"
            style={{ backgroundColor: plan.badge_color }}
          >
            {plan.badge_text}
          </span>
        </div>
      )}

      <div className="p-7 flex flex-col flex-1">
        {/* Plan header */}
        <div className="mb-6" style={{ marginTop: plan.badge_text ? "0.5rem" : "0" }}>
          <div className="flex items-center gap-2 mb-3" style={{ color: accent.text }}>
            {PLAN_ICONS[plan.id]}
            <span className="text-sm font-semibold uppercase tracking-wider">{plan.name}</span>
          </div>
          <div className="flex items-end gap-1.5 mb-1">
            <span className="text-4xl font-bold text-white">
              {plan.price_usd === 0 ? "Free" : `$${plan.price_usd}`}
            </span>
            {plan.price_usd > 0 && (
              <span className="text-gray-500 mb-1.5 text-sm">{plan.duration_label}</span>
            )}
          </div>
          <p className="text-sm text-gray-400">{plan.description}</p>
        </div>

        {/* Features */}
        <ul className="space-y-2.5 flex-1 mb-7">
          {plan.features.map((f) => (
            <li key={f} className="flex items-start gap-2.5 text-sm text-gray-300">
              <Check className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: accent.text }} />
              {f}
            </li>
          ))}
        </ul>

        {/* CTA */}
        {ctaHref ? (
          <Link
            href={ctaHref}
            className="block w-full text-center py-3 rounded-xl font-semibold text-sm text-white transition-opacity"
            style={{ backgroundColor: accent.btn }}
          >
            {ctaLabel()}
          </Link>
        ) : (
          <button
            onClick={() => onSelect(plan.id)}
            disabled={loading}
            className="w-full py-3 rounded-xl font-semibold text-sm text-white transition-opacity disabled:opacity-60"
            style={{ backgroundColor: accent.btn }}
          >
            {ctaLabel()}
          </button>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// FAQ item
// ---------------------------------------------------------------------------
function FaqItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-gray-700 rounded-xl overflow-hidden" style={{ backgroundColor: "#111827" }}>
      <button
        className="w-full flex items-center justify-between px-6 py-4 text-left"
        onClick={() => setOpen((p) => !p)}
      >
        <span className="font-medium text-white text-sm">{question}</span>
        <ChevronDown
          className="w-4 h-4 text-gray-400 transition-transform duration-200 flex-shrink-0"
          style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)" }}
        />
      </button>
      {open && (
        <div className="px-6 pb-5 text-sm text-gray-400 leading-relaxed">{answer}</div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function PricingPage() {
  const { startCheckout, loadingPlan, error } = useCheckout();
  const { isAuthenticated } = useUserStore();

  const { data: plansData, isLoading } = useQuery<{ plans: SubscriptionPlan[] }>({
    queryKey: ["subscription-plans"],
    queryFn: async () => {
      const res = await api.get<{ plans: SubscriptionPlan[] }>("/api/v1/subscriptions/plans");
      return res.data;
    },
    retry: 1,
    staleTime: 5 * 60 * 1000,
  });

  const plans = plansData?.plans ?? [];

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "#0B0E1A", color: "white" }}>
      {/* Nav */}
      <header className="border-b border-gray-800 sticky top-0 z-50" style={{ backgroundColor: "#0B0E1A" }}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm"
              style={{ background: "linear-gradient(135deg, #8B5CF6, #3B82F6)" }}
            >
              P
            </div>
            <span className="font-semibold text-white text-base tracking-tight">
              PulseSignal <span style={{ color: "#8B5CF6" }}>Pro</span>
            </span>
          </Link>
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <Link href="/dashboard" className="px-4 py-2 text-sm font-medium rounded-lg text-white transition-colors" style={{ backgroundColor: "#8B5CF6" }}>
                Dashboard
              </Link>
            ) : (
              <>
                <Link href="/login" className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white transition-colors">Login</Link>
                <Link href="/register" className="px-4 py-2 text-sm font-medium rounded-lg text-white transition-colors" style={{ backgroundColor: "#8B5CF6" }}>
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="pt-16 pb-12 text-center px-4">
          <div
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium mb-6 border border-purple-800"
            style={{ backgroundColor: "rgba(139,92,246,0.1)", color: "#8B5CF6" }}
          >
            AI-powered trading signals
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-lg max-w-xl mx-auto" style={{ color: "#D1D5DB" }}>
            Start free. Upgrade when you're ready. Every plan includes ICT methodology, smart money analysis, and precision entry signals.
          </p>
        </section>

        {/* Error banner */}
        {error && (
          <div className="max-w-lg mx-auto mb-6 px-4">
            <div
              className="rounded-lg px-4 py-3 text-sm text-center border border-red-700"
              style={{ backgroundColor: "rgba(239,68,68,0.1)", color: "#EF4444" }}
            >
              {error}
            </div>
          </div>
        )}

        {/* Pricing Cards */}
        <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-96 rounded-2xl animate-pulse" style={{ backgroundColor: "#1F2937" }} />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-start mt-6">
              {plans.map((plan) => (
                <PricingCard
                  key={plan.id}
                  plan={plan}
                  onSelect={startCheckout}
                  loading={loadingPlan === plan.id}
                  isAuthenticated={!!isAuthenticated}
                />
              ))}
            </div>
          )}

          {/* Comparison note */}
          <p className="text-center text-sm text-gray-500 mt-8">
            All prices in USD. Yearly plan saves 43% vs Monthly. Lifetime is a one-time payment.
          </p>
        </section>

        {/* FAQ */}
        <section className="max-w-2xl mx-auto px-4 sm:px-6 pb-24">
          <h2 className="text-2xl font-bold text-center mb-8">Frequently Asked Questions</h2>
          <div className="space-y-3">
            {FAQ_ITEMS.map((item) => (
              <FaqItem key={item.question} question={item.question} answer={item.answer} />
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t border-gray-800 py-6 text-center">
        <p className="text-sm" style={{ color: "#6B7280" }}>
          © {new Date().getFullYear()} PulseSignal Pro. All rights reserved.
        </p>
      </footer>
    </div>
  );
}
