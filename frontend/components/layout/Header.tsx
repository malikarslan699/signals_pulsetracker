"use client";
import { useEffect, useState } from "react";
import { Menu, Bell, ChevronDown, User, Settings2, LogOut, Sun, Moon } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useUserStore } from "@/store/userStore";
import { useLogout } from "@/hooks/useAuth";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface HeaderProps {
  onMenuClick: () => void;
}

interface TickerPrice {
  symbol: string;
  price: number;
  change_pct: number;
}

export function Header({ onMenuClick }: HeaderProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
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

  useEffect(() => {
    if (typeof window === "undefined") return;
    setDarkMode(document.documentElement.classList.contains("dark"));
  }, []);

  const formatPrice = (price: number) =>
    price >= 10000
      ? price.toLocaleString("en-US", { maximumFractionDigits: 0 })
      : price.toLocaleString("en-US", { maximumFractionDigits: 2 });

  return (
    <header className="flex items-center h-11 px-3 border-b border-border bg-surface gap-3 z-20 flex-shrink-0">
      {/* Mobile hamburger */}
      <button
        onClick={onMenuClick}
        className="lg:hidden text-text-muted hover:text-text-primary"
      >
        <Menu className="h-4 w-4" />
      </button>

      {/* Live indicator */}
      <div className="flex items-center gap-1.5">
        <span className="h-1.5 w-1.5 rounded-full bg-long animate-pulse" />
        <span className="text-2xs font-semibold text-long uppercase tracking-wider">Live</span>
      </div>

      {/* Ticker */}
      <div className="flex-1 overflow-hidden">
        <div className="flex items-center gap-4 text-2xs">
          {btc && (
            <div className="hidden sm:flex items-center gap-1.5 shrink-0">
              <span className="font-medium text-text-primary">BTC/USDT</span>
              <span className="font-mono text-text-muted">{formatPrice(btc.price)}</span>
              <span className={cn(
                "font-mono font-medium",
                btc.change_pct >= 0 ? "text-long" : "text-short"
              )}>
                {btc.change_pct >= 0 ? "+" : ""}{btc.change_pct.toFixed(2)}%
              </span>
            </div>
          )}
          {eth && (
            <div className="hidden md:flex items-center gap-1.5 shrink-0">
              <span className="font-medium text-text-primary">ETH/USDT</span>
              <span className="font-mono text-text-muted">{formatPrice(eth.price)}</span>
              <span className={cn(
                "font-mono font-medium",
                eth.change_pct >= 0 ? "text-long" : "text-short"
              )}>
                {eth.change_pct >= 0 ? "+" : ""}{eth.change_pct.toFixed(2)}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1">
        {/* Dark mode toggle */}
        <button
          onClick={() => {
            const next = !darkMode;
            setDarkMode(next);
            document.documentElement.classList.toggle("dark", next);
            localStorage.setItem("theme", next ? "dark" : "light");
          }}
          className="p-1.5 rounded text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
        >
          {darkMode ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
        </button>

        {/* Bell */}
        <button className="p-1.5 rounded text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors relative">
          <Bell className="h-3.5 w-3.5" />
          <span className="absolute top-1 right-1 h-1.5 w-1.5 rounded-full bg-long" />
        </button>

        {/* User dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-1.5 pl-1.5 pr-2 py-1 bg-surface-2 border border-border rounded hover:border-border transition-all"
          >
            <div className="w-5 h-5 rounded-full bg-long/20 border border-long/30 flex items-center justify-center text-long text-xs font-bold">
              {initials}
            </div>
            <span className="hidden sm:block text-xs font-medium text-text-secondary max-w-20 truncate">
              {user?.username ?? "Guest"}
            </span>
            <ChevronDown className="w-3 h-3 text-text-muted" />
          </button>

          {dropdownOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setDropdownOpen(false)} />
              <div className="absolute right-0 top-full mt-1 w-48 bg-surface border border-border rounded-lg shadow-2xl z-20 py-1 overflow-hidden">
                <div className="px-3 py-2 border-b border-border">
                  <p className="text-xs font-semibold text-text-primary truncate">{user?.username}</p>
                  <p className="text-xs text-text-muted truncate mt-0.5">{user?.email}</p>
                  {user?.plan && (
                    <span className="inline-flex mt-1 text-xs px-1.5 py-0.5 rounded bg-long/10 text-long border border-long/20 font-medium capitalize">
                      {user.plan}
                    </span>
                  )}
                </div>
                <Link
                  href="/settings"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-2 px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors"
                >
                  <User className="w-3.5 h-3.5" /> Profile
                </Link>
                <Link
                  href="/settings"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-2 px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors"
                >
                  <Settings2 className="w-3.5 h-3.5" /> Settings
                </Link>
                <div className="border-t border-border mt-0.5 pt-0.5">
                  <button
                    onClick={() => { setDropdownOpen(false); logout.mutate(); }}
                    className="flex items-center gap-2 px-3 py-1.5 text-xs text-short hover:bg-short/10 transition-colors w-full text-left"
                  >
                    <LogOut className="w-3.5 h-3.5" /> Sign Out
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
