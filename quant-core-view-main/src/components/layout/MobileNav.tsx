import { NavLink, useLocation } from "react-router-dom";
import { LayoutDashboard, Scan, Bell, BarChart3, User } from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Home" },
  { to: "/scanner", icon: Scan, label: "Scanner" },
  { to: "/alerts", icon: Bell, label: "Alerts" },
  { to: "/stats", icon: BarChart3, label: "Stats" },
  { to: "/settings", icon: User, label: "Profile" },
];

export function MobileNav() {
  const location = useLocation();

  return (
    <nav className="md:hidden flex items-center justify-around h-12 border-t border-border bg-card">
      {items.map((item) => {
        const active = location.pathname === item.to || location.pathname.startsWith(item.to + "/");
        return (
          <NavLink
            key={item.to}
            to={item.to}
            className={cn(
              "flex flex-col items-center gap-0.5 text-2xs font-medium transition-colors",
              active ? "text-primary" : "text-muted-foreground"
            )}
          >
            <item.icon className="h-4 w-4" />
            <span>{item.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}
