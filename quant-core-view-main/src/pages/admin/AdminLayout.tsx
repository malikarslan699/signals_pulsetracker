import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Shield, Users, Package, CreditCard, Wrench, BarChart3, FlaskConical } from "lucide-react";

const adminTabs = [
  { to: "/admin", icon: Shield, label: "Overview", end: true },
  { to: "/admin/users", icon: Users, label: "Users" },
  { to: "/admin/packages", icon: Package, label: "Packages" },
  { to: "/admin/payments", icon: CreditCard, label: "Payments" },
  { to: "/admin/config", icon: Wrench, label: "Config" },
  { to: "/admin/analytics", icon: BarChart3, label: "Analytics" },
  { to: "/admin/qa", icon: FlaskConical, label: "QA" },
];

export default function AdminLayout() {
  const location = useLocation();

  return (
    <div className="p-3 space-y-3">
      {/* Admin Tab Nav */}
      <div className="flex items-center gap-1 overflow-x-auto">
        {adminTabs.map((tab) => {
          const active = tab.end ? location.pathname === tab.to : location.pathname.startsWith(tab.to);
          return (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={tab.end}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-medium whitespace-nowrap transition-colors",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              )}
            >
              <tab.icon className="h-3.5 w-3.5" />
              {tab.label}
            </NavLink>
          );
        })}
      </div>

      <Outlet />
    </div>
  );
}
