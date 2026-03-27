import { Zap } from "lucide-react";
import Link from "next/link";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Gradient background */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at 50% 0%, rgba(139,92,246,0.15) 0%, transparent 60%)",
        }}
      />

      {/* Logo */}
      <Link
        href="/"
        className="flex items-center gap-2.5 mb-8 group"
      >
        <div className="w-10 h-10 bg-purple rounded-xl flex items-center justify-center shadow-lg shadow-purple/30 group-hover:scale-105 transition-transform">
          <Zap className="w-6 h-6 text-white" />
        </div>
        <div>
          <span className="text-xl font-bold text-text-primary">
            PulseSignal
          </span>
          <span className="text-xl font-bold text-purple ml-1">Pro</span>
        </div>
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
