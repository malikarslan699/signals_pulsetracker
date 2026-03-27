"use client";
import { useState } from "react";
import { Menu, Bell, ChevronDown, User, Settings2, LogOut } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useUserStore } from "@/store/userStore";
import { useLogout } from "@/hooks/useAuth";
import Link from "next/link";

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

  const formatHeaderPrice = (price: number) =>
    price >= 10000
      ? `$${price.toLocaleString("en-US", { maximumFractionDigits: 0 })}`
      : `$${price.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;

  const initials = user
    ? user.username.slice(0, 2).toUpperCase()
    : "??";

  return (
    <header className="h-16 bg-surface border-b border-border flex items-center px-4 gap-4 z-20 flex-shrink-0">
      {/* Hamburger (mobile) */}
      <button
        onClick={onMenuClick}
        className="lg:hidden p-2 text-text-muted hover:text-text-primary transition-colors"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Center: Live indicator + prices */}
      <div className="flex-1 flex items-center justify-center gap-4">
        <div className="flex items-center gap-1.5">
          <span className="live-dot" />
          <span className="text-xs font-bold text-long tracking-widest">LIVE</span>
        </div>

        {btc && (
          <div className="hidden sm:flex items-center gap-1.5 text-xs">
            <span className="font-mono font-bold text-text-secondary">BTC</span>
            <span className="font-mono text-text-primary">{formatHeaderPrice(btc.price)}</span>
            <span
              className={`font-mono font-medium ${
                btc.change_pct >= 0 ? "text-long" : "text-short"
              }`}
            >
              {btc.change_pct >= 0 ? "+" : ""}
              {btc.change_pct.toFixed(2)}%
            </span>
          </div>
        )}

        {eth && (
          <div className="hidden md:flex items-center gap-1.5 text-xs">
            <span className="font-mono font-bold text-text-secondary">ETH</span>
            <span className="font-mono text-text-primary">{formatHeaderPrice(eth.price)}</span>
            <span
              className={`font-mono font-medium ${
                eth.change_pct >= 0 ? "text-long" : "text-short"
              }`}
            >
              {eth.change_pct >= 0 ? "+" : ""}
              {eth.change_pct.toFixed(2)}%
            </span>
          </div>
        )}
      </div>

      {/* Right: Bell + User */}
      <div className="flex items-center gap-2">
        {/* Notification bell */}
        <button className="relative p-2 text-text-muted hover:text-text-primary transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-purple rounded-full" />
        </button>

        {/* User dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 pl-2 pr-3 py-1.5 bg-surface-2 border border-border rounded-lg hover:border-border-light transition-colors"
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
              <div
                className="fixed inset-0 z-10"
                onClick={() => setDropdownOpen(false)}
              />
              <div className="absolute right-0 top-full mt-2 w-48 bg-surface border border-border rounded-xl shadow-xl z-20 py-1 overflow-hidden">
                <div className="px-3 py-2 border-b border-border">
                  <p className="text-xs font-medium text-text-primary truncate">
                    {user?.username}
                  </p>
                  <p className="text-xs text-text-muted truncate">{user?.email}</p>
                </div>
                <Link
                  href="/settings"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors"
                >
                  <User className="w-4 h-4" />
                  Profile
                </Link>
                <Link
                  href="/settings"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors"
                >
                  <Settings2 className="w-4 h-4" />
                  Settings
                </Link>
                <div className="border-t border-border mt-1 pt-1">
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      logout.mutate();
                    }}
                    className="flex items-center gap-2.5 px-3 py-2 text-sm text-short hover:bg-short/10 transition-colors w-full text-left"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
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
