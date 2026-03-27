"use client";
import { useState } from "react";
import { Menu, Bell, ChevronDown, User, Settings2, LogOut, TrendingUp, TrendingDown } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useUserStore } from "@/store/userStore";
import { useLogout } from "@/hooks/useAuth";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import Link from "next/link";

interface HeaderProps {
  onMenuClick: () => void;
}

interface TickerPrice {
  symbol: string;
  price: number;
  change_pct: number;
}

function PriceChip({ label, price, change }: { label: string; price: number; change: number }) {
  const up = change >= 0;
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-2 border border-border rounded-lg">
      <span className="text-xs font-semibold text-text-muted font-mono">{label}</span>
      <span className="text-xs font-mono font-bold text-text-primary">
        {price >= 10000
          ? `$${price.toLocaleString("en-US", { maximumFractionDigits: 0 })}`
          : `$${price.toLocaleString("en-US", { maximumFractionDigits: 2 })}`}
      </span>
      <span className={`flex items-center gap-0.5 text-xs font-mono font-semibold ${up ? "text-long" : "text-short"}`}>
        {up ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
        {up ? "+" : ""}{change.toFixed(2)}%
      </span>
    </div>
  );
}

export function Header({ onMenuClick }: HeaderProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const { user } = useUserStore();
  const logout = useLogout();

  const { data: prices } = useQuery<TickerPrice[]>({
    queryKey: ["header-prices"],
    queryFn: async () => {
      const res = await api.get<TickerPrice[]>("/api/v1/pairs/prices?symbols=BTCUSDT,ETHUSDT");
      return res.data;
    },
    refetchInterval: 15_000,
    retry: false,
  });

  const btc = prices?.find((p) => p.symbol === "BTCUSDT" || p.symbol === "BTC/USDT");
  const eth = prices?.find((p) => p.symbol === "ETHUSDT" || p.symbol === "ETH/USDT");
  const initials = user ? user.username.slice(0, 2).toUpperCase() : "??";

  return (
    <header className="h-14 bg-surface border-b border-border flex items-center px-4 gap-3 z-20 flex-shrink-0">
      {/* Mobile hamburger */}
      <button
        onClick={onMenuClick}
        className="lg:hidden p-2 text-text-muted hover:text-text-primary hover:bg-surface-2 rounded-lg transition-colors"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Left: live indicator + prices */}
      <div className="flex items-center gap-2.5 flex-1">
        <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-long/10 border border-long/20 rounded-lg">
          <span className="live-dot" />
          <span className="text-xs font-bold text-long tracking-widest">LIVE</span>
        </div>

        {btc && (
          <div className="hidden sm:block">
            <PriceChip label="BTC" price={btc.price} change={btc.change_pct} />
          </div>
        )}
        {eth && (
          <div className="hidden md:block">
            <PriceChip label="ETH" price={eth.price} change={eth.change_pct} />
          </div>
        )}
      </div>

      {/* Right: theme + bell + user */}
      <div className="flex items-center gap-1.5">
        <ThemeToggle />

        <button className="relative p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 border border-transparent hover:border-border transition-all">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-purple rounded-full" />
        </button>

        {/* User dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 pl-2 pr-2.5 py-1.5 bg-surface-2 border border-border rounded-lg hover:border-border-light transition-all"
          >
            <div className="w-6 h-6 rounded-full bg-purple/20 border border-purple/30 flex items-center justify-center text-purple text-xs font-bold">
              {initials}
            </div>
            <span className="hidden sm:block text-xs font-medium text-text-secondary max-w-24 truncate">
              {user?.username ?? "Guest"}
            </span>
            <ChevronDown className="w-3.5 h-3.5 text-text-muted" />
          </button>

          {dropdownOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setDropdownOpen(false)} />
              <div className="absolute right-0 top-full mt-2 w-52 bg-surface border border-border rounded-xl shadow-2xl z-20 py-1.5 overflow-hidden animate-fade-in">
                <div className="px-3 py-2.5 border-b border-border">
                  <p className="text-xs font-semibold text-text-primary truncate">{user?.username}</p>
                  <p className="text-xs text-text-muted truncate mt-0.5">{user?.email}</p>
                  {user?.plan && (
                    <span className="inline-flex mt-1.5 text-xs px-2 py-0.5 rounded-full bg-purple/10 text-purple border border-purple/20 font-medium capitalize">
                      {user.plan}
                    </span>
                  )}
                </div>
                <Link href="/settings" onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors">
                  <User className="w-4 h-4" />Profile
                </Link>
                <Link href="/settings" onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors">
                  <Settings2 className="w-4 h-4" />Settings
                </Link>
                <div className="border-t border-border mt-1 pt-1">
                  <button
                    onClick={() => { setDropdownOpen(false); logout.mutate(); }}
                    className="flex items-center gap-2.5 px-3 py-2 text-sm text-short hover:bg-short/10 transition-colors w-full text-left"
                  >
                    <LogOut className="w-4 h-4" />Sign Out
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
