"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Zap,
  LayoutDashboard,
  Search,
  History,
  BarChart2,
  Bell,
  Settings2,
  Shield,
  X,
} from "lucide-react";
import { useUserStore } from "@/store/userStore";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const BASE_NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Scanner", href: "/scanner", icon: Search },
  { label: "Signal History", href: "/history", icon: History },
  { label: "Trading Stats", href: "/stats", icon: BarChart2 },
  { label: "Alerts", href: "/alerts", icon: Bell },
  { label: "Settings", href: "/settings", icon: Settings2 },
];

const PLAN_COLORS: Record<string, string> = {
  free: "bg-surface-2 text-text-muted border-border",
  trial: "bg-blue/10 text-blue border-blue/20",
  monthly: "bg-purple/10 text-purple border-purple/20",
  lifetime: "bg-gold/10 text-gold border-gold/20",
};

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { user } = useUserStore();
  const isStaff =
    user?.role === "admin" || user?.role === "owner" || user?.role === "superadmin";
  const navItems = isStaff
    ? [...BASE_NAV_ITEMS, { label: "Admin", href: "/admin", icon: Shield }]
    : BASE_NAV_ITEMS;

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center justify-between px-6 py-5 border-b border-border">
        <Link href="/dashboard" className="flex items-center gap-2.5" onClick={onClose}>
          <div className="w-8 h-8 bg-purple rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-text-primary text-sm leading-tight">
            PulseSignal
            <br />
            <span className="text-purple">Pro</span>
          </span>
        </Link>
        <button
          onClick={onClose}
          className="lg:hidden p-1 text-text-muted hover:text-text-primary transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? "bg-purple text-white shadow-lg shadow-purple/20"
                  : "text-text-muted hover:text-text-primary hover:bg-surface-2"
              }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      {user && (
        <div className="px-4 py-4 border-t border-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-purple/20 border border-purple/30 flex items-center justify-center text-purple text-xs font-bold uppercase flex-shrink-0">
              {user.username.slice(0, 2)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">
                {user.username}
              </p>
              <span
                className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium border capitalize mt-0.5 ${
                  PLAN_COLORS[user.plan] || PLAN_COLORS.free
                }`}
              >
                {user.plan}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col w-64 bg-surface border-r border-border fixed left-0 top-0 h-full z-30">
        {sidebarContent}
      </aside>

      {/* Mobile overlay */}
      {isOpen && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />
          <aside className="relative z-50 w-64 bg-surface border-r border-border flex flex-col h-full animate-slide-up">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}
