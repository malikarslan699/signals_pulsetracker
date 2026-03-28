import { NavLink, useLocation } from "react-router-dom";
import { 
  LayoutDashboard, Scan, Clock, BarChart3, Bell, Settings, Shield, 
  ChevronLeft, Zap
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/scanner", icon: Scan, label: "Scanner" },
  { to: "/history", icon: Clock, label: "History" },
  { to: "/stats", icon: BarChart3, label: "Stats" },
  { to: "/alerts", icon: Bell, label: "Alerts" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

const adminItems = [
  { to: "/admin", icon: Shield, label: "Admin" },
];

interface AppSidebarProps {
  open: boolean;
  onToggle: () => void;
}

export function AppSidebar({ open, onToggle }: AppSidebarProps) {
  const location = useLocation();

  return (
    <aside
      className={cn(
        "hidden md:flex flex-col border-r border-border bg-card transition-all duration-200",
        open ? "w-48" : "w-14"
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-11 px-3 border-b border-border gap-2">
        <Zap className="h-5 w-5 text-primary shrink-0" />
        {open && (
          <span className="text-sm font-semibold text-foreground tracking-tight truncate">
            PulseSignal
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-2 space-y-0.5 px-2">
        {navItems.map((item) => {
          const active = location.pathname === item.to || location.pathname.startsWith(item.to + "/");
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={cn(
                "flex items-center gap-2.5 px-2 py-1.5 rounded text-xs font-medium transition-colors",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              )}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {open && <span className="truncate">{item.label}</span>}
            </NavLink>
          );
        })}

        <div className="pt-3 pb-1">
          {open && (
            <span className="px-2 text-2xs font-semibold text-muted-foreground uppercase tracking-widest">
              Admin
            </span>
          )}
        </div>

        {adminItems.map((item) => {
          const active = location.pathname.startsWith(item.to);
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={cn(
                "flex items-center gap-2.5 px-2 py-1.5 rounded text-xs font-medium transition-colors",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              )}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {open && <span className="truncate">{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <button
        onClick={onToggle}
        className="flex items-center justify-center h-9 border-t border-border text-muted-foreground hover:text-foreground transition-colors"
      >
        <ChevronLeft className={cn("h-4 w-4 transition-transform", !open && "rotate-180")} />
      </button>
    </aside>
  );
}
