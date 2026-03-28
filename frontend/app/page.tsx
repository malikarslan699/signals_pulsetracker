import Link from "next/link";
import { Zap, TrendingUp, Bell, BarChart2, Shield, Globe, CheckCircle2, ArrowRight } from "lucide-react";

const FEATURES = [
  {
    icon: Zap,
    title: "ICT Smart Money Engine",
    description:
      "Advanced ICT concepts including Order Blocks, FVGs, Liquidity levels, and Premium/Discount zones.",
    color: "text-purple",
    bg: "bg-purple/10",
  },
  {
    icon: Globe,
    title: "500+ Pairs Covered",
    description:
      "Comprehensive coverage of crypto and forex pairs scanned in real-time across multiple exchanges.",
    color: "text-blue",
    bg: "bg-blue/10",
  },
  {
    icon: Bell,
    title: "Real-time Alerts",
    description:
      "Instant Telegram notifications the moment a high-quality setup fires on any pair.",
    color: "text-gold",
    bg: "bg-gold/10",
  },
  {
    icon: BarChart2,
    title: "Multi-Timeframe Analysis",
    description:
      "Signals validated across 5m, 15m, 1H, 4H and 1D timeframes for maximum confluence.",
    color: "text-long",
    bg: "bg-long/10",
  },
  {
    icon: TrendingUp,
    title: "Setup Score + P(TP1)",
    description:
      "Every signal includes a structural setup score plus calibrated TP1 probability guidance.",
    color: "text-short",
    bg: "bg-short/10",
  },
  {
    icon: Shield,
    title: "Risk Management Built-in",
    description:
      "Automatic Stop Loss, Take Profit targets and R:R ratio calculated for every signal.",
    color: "text-gold",
    bg: "bg-gold/10",
  },
];

const HOW_IT_WORKS = [
  {
    step: "01",
    title: "Scanner Runs 24/7",
    description:
      "Our engine continuously scans 500+ pairs across crypto and forex markets, applying ICT Smart Money analysis and 35+ indicators.",
  },
  {
    step: "02",
    title: "Signal Fired with Ranked Quality",
    description:
      "When a high-confluence setup is detected, a signal is generated with entry, SL, TP targets, setup score, and TP1 probability.",
  },
  {
    step: "03",
    title: "You Trade with Confidence",
    description:
      "Receive instant alerts via Telegram or check the dashboard. Every signal includes full analysis and ICT zone mapping.",
  },
];

const PRICING = [
  {
    name: "Free Trial",
    price: "$0",
    period: "forever",
    description: "Get started with limited signals",
    features: [
      "5 signals per day",
      "Basic indicators",
      "Dashboard access",
      "30-day history",
    ],
    cta: "Start Free",
    href: "/register",
    highlight: false,
  },
  {
    name: "Pro Monthly",
    price: "$29",
    period: "per month",
    description: "Full access for active traders",
    features: [
      "Unlimited signals",
      "All 35+ indicators",
      "ICT Smart Money analysis",
      "Telegram alerts",
      "Full signal history",
      "Multi-timeframe analysis",
    ],
    cta: "Get Pro",
    href: "/register",
    highlight: true,
  },
  {
    name: "Lifetime",
    price: "$149",
    period: "one-time",
    description: "Best value for serious traders",
    features: [
      "Everything in Pro",
      "Lifetime access",
      "Priority support",
      "Early feature access",
      "API access",
    ],
    cta: "Get Lifetime",
    href: "/register",
    highlight: false,
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-text-primary">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-purple rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-text-primary">
              PulseSignal <span className="text-purple">Pro</span>
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8 text-sm text-text-muted">
            <a href="#features" className="hover:text-text-primary transition-colors">
              Features
            </a>
            <a href="#pricing" className="hover:text-text-primary transition-colors">
              Pricing
            </a>
            <Link href="/login" className="hover:text-text-primary transition-colors">
              Login
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="hidden sm:block text-sm text-text-secondary hover:text-text-primary transition-colors px-4 py-2"
            >
              Login
            </Link>
            <Link
              href="/register"
              className="flex items-center gap-1.5 bg-purple hover:bg-purple/90 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-all shadow-lg shadow-purple/20"
            >
              Get Started
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-4 relative overflow-hidden">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse at 50% 0%, rgba(139,92,246,0.2) 0%, transparent 70%)",
          }}
        />
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 bg-purple/10 border border-purple/20 rounded-full px-4 py-1.5 text-sm text-purple font-medium mb-6">
            <span className="w-2 h-2 bg-purple rounded-full animate-pulse" />
            Live signals firing now
          </div>

          <h1 className="text-4xl md:text-6xl font-black text-text-primary leading-tight mb-6">
            Professional Trading Signals
            <br />
            <span className="text-purple">Powered by ICT Smart Money</span>
          </h1>

          <p className="text-lg text-text-secondary max-w-2xl mx-auto mb-10 leading-relaxed">
            Real-time crypto and forex signals with 35+ indicators, ICT analysis,
            and calibrated TP1 probability plus setup scoring. Never miss a high-quality setup again.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/register"
              className="flex items-center gap-2 bg-purple hover:bg-purple/90 text-white font-bold px-8 py-4 rounded-xl text-base transition-all shadow-xl shadow-purple/30 hover:shadow-purple/40 hover:scale-105"
            >
              <Zap className="w-5 h-5" />
              Start Free Trial
            </Link>
            <Link
              href="/dashboard"
              className="flex items-center gap-2 bg-surface hover:bg-surface-2 border border-border text-text-primary font-semibold px-8 py-4 rounded-xl text-base transition-all"
            >
              View Live Demo
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Stats bar */}
      <section className="py-8 border-y border-border bg-surface">
        <div className="max-w-5xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            {[
              { value: "500+", label: "Pairs Scanned" },
              { value: "35+", label: "Indicators" },
              { value: "ICT", label: "Smart Money" },
              { value: "24/7", label: "Real-time Alerts" },
            ].map((stat) => (
              <div key={stat.label}>
                <p className="text-2xl md:text-3xl font-black text-purple font-mono">
                  {stat.value}
                </p>
                <p className="text-sm text-text-muted mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-black text-text-primary mb-4">
              Everything You Need to Trade Smarter
            </h2>
            <p className="text-text-secondary max-w-2xl mx-auto">
              Professional-grade tools powered by institutional-level market analysis.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((feature) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className="bg-surface border border-border rounded-xl p-6 hover:border-border-light transition-all card-hover"
                >
                  <div className={`inline-flex p-3 rounded-xl ${feature.bg} mb-4`}>
                    <Icon className={`w-6 h-6 ${feature.color}`} />
                  </div>
                  <h3 className="text-lg font-bold text-text-primary mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-text-secondary text-sm leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 px-4 bg-surface border-y border-border">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-black text-text-primary mb-4">
              How It Works
            </h2>
            <p className="text-text-secondary">
              From market scan to your trade in seconds.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {HOW_IT_WORKS.map((step) => (
              <div key={step.step} className="text-center">
                <div className="w-16 h-16 bg-purple/10 border border-purple/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-black text-purple font-mono">
                    {step.step}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-text-primary mb-2">
                  {step.title}
                </h3>
                <p className="text-text-secondary text-sm leading-relaxed">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-black text-text-primary mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-text-secondary">
              Start free. Upgrade when you&apos;re ready.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {PRICING.map((plan) => (
              <div
                key={plan.name}
                className={`bg-surface rounded-2xl p-6 flex flex-col border transition-all ${
                  plan.highlight
                    ? "border-purple shadow-xl shadow-purple/10 relative"
                    : "border-border"
                }`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="bg-purple text-white text-xs font-bold px-4 py-1.5 rounded-full whitespace-nowrap">
                      Most Popular
                    </span>
                  </div>
                )}
                <div className="mb-5">
                  <h3 className="text-lg font-bold text-text-primary mb-1">
                    {plan.name}
                  </h3>
                  <p className="text-text-muted text-sm mb-4">{plan.description}</p>
                  <div className="flex items-end gap-1">
                    <span className="text-4xl font-black text-text-primary">
                      {plan.price}
                    </span>
                    <span className="text-text-muted text-sm mb-1">
                      /{plan.period}
                    </span>
                  </div>
                </div>

                <ul className="space-y-2.5 flex-1 mb-6">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2.5 text-sm">
                      <CheckCircle2 className="w-4 h-4 text-long flex-shrink-0" />
                      <span className="text-text-secondary">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  href={plan.href}
                  className={`w-full text-center font-semibold py-3 rounded-xl transition-all text-sm ${
                    plan.highlight
                      ? "bg-purple hover:bg-purple/90 text-white shadow-lg shadow-purple/20"
                      : "bg-surface-2 hover:bg-border text-text-primary border border-border"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 px-4 border-t border-border bg-surface">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-purple rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-text-primary text-sm">
              PulseSignal <span className="text-purple">Pro</span>
            </span>
          </div>

          <p className="text-xs text-text-muted text-center">
            &copy; {new Date().getFullYear()} PulseSignal Pro. For educational purposes only.
            Not financial advice.
          </p>

          <div className="flex items-center gap-5 text-xs text-text-muted">
            <Link href="/login" className="hover:text-text-primary transition-colors">
              Login
            </Link>
            <Link href="/register" className="hover:text-text-primary transition-colors">
              Register
            </Link>
            <Link href="/dashboard" className="hover:text-text-primary transition-colors">
              Dashboard
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
