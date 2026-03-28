import { Activity } from "lucide-react";
import Link from "next/link";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 relative overflow-hidden bg-background">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at top, rgb(var(--color-long) / 0.16) 0%, transparent 60%)",
        }}
      />

      {/* Logo */}
      <Link
        href="/"
        className="flex flex-col items-center mb-8 group"
      >
        <div className="flex items-center gap-2.5">
          <Activity className="w-7 h-7 text-long group-hover:scale-105 transition-transform" />
          <div>
            <span className="text-[2rem] leading-none font-bold text-text-primary">
              Pulse
            </span>
            <span className="text-[2rem] leading-none font-bold text-long">
              Signal
            </span>
          </div>
        </div>
        <p className="mt-2 text-sm text-text-muted">Sign in to your account</p>
      </Link>

      {/* Card */}
      <div className="w-full max-w-md relative z-10">
        {children}
      </div>

      {/* Footer note */}
      <p className="mt-8 text-xs text-text-muted relative z-10">
        Professional Trading Signals · Powered by ICT Smart Money
      </p>
    </div>
  );
}
