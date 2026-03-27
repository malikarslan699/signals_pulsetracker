"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Search, Bell, BarChart2, User, Shield } from "lucide-react";
import { useUserStore } from "@/store/userStore";

const BASE_NAV_ITEMS = [
  { label: "Home", href: "/dashboard", icon: LayoutDashboard },
  { label: "Scanner", href: "/scanner", icon: Search },
  { label: "Alerts", href: "/alerts", icon: Bell },
  { label: "Stats", href: "/stats", icon: BarChart2 },
  { label: "Profile", href: "/settings", icon: User },
];

export function MobileNav() {
  const pathname = usePathname();
  const { user } = useUserStore();
  const isStaff =
    user?.role === "admin" || user?.role === "owner" || user?.role === "superadmin";
  const navItems = isStaff
    ? [...BASE_NAV_ITEMS.slice(0, 4), { label: "Admin", href: "/admin", icon: Shield }]
    : BASE_NAV_ITEMS;

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-surface border-t border-border">
      <div className="flex items-center justify-around px-2 py-2">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center gap-1 px-3 py-1 rounded-lg transition-colors ${
                isActive ? "text-purple" : "text-text-muted"
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-xs font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
