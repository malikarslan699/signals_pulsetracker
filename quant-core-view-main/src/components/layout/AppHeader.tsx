import { Menu, Sun, Moon, Bell, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface AppHeaderProps {
  onToggleSidebar: () => void;
  darkMode: boolean;
  onToggleDarkMode: () => void;
}

const tickerData = [
  { symbol: "BTC/USDT", price: "67,432.50", change: "+2.34%" },
  { symbol: "ETH/USDT", price: "3,521.80", change: "+1.12%" },
  { symbol: "EUR/USD", price: "1.0842", change: "-0.15%" },
  { symbol: "GBP/USD", price: "1.2731", change: "+0.08%" },
  { symbol: "XAU/USD", price: "2,341.60", change: "+0.52%" },
];

export function AppHeader({ onToggleSidebar, darkMode, onToggleDarkMode }: AppHeaderProps) {
  return (
    <header className="flex items-center h-11 px-3 border-b border-border bg-card gap-3">
      <button onClick={onToggleSidebar} className="md:hidden text-muted-foreground hover:text-foreground">
        <Menu className="h-4 w-4" />
      </button>

      {/* Live indicator */}
      <div className="flex items-center gap-1.5">
        <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse-glow" />
        <span className="text-2xs font-semibold text-primary uppercase tracking-wider">Live</span>
      </div>

      {/* Ticker */}
      <div className="flex-1 overflow-hidden">
        <div className="flex items-center gap-4 text-2xs">
          {tickerData.map((t) => (
            <div key={t.symbol} className="flex items-center gap-1.5 shrink-0">
              <span className="font-medium text-foreground">{t.symbol}</span>
              <span className="font-mono text-muted-foreground">{t.price}</span>
              <span className={cn(
                "font-mono font-medium",
                t.change.startsWith("+") ? "text-long" : "text-short"
              )}>
                {t.change}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1">
        <button
          onClick={onToggleDarkMode}
          className="p-1.5 rounded text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
        >
          {darkMode ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
        </button>
        <button className="p-1.5 rounded text-muted-foreground hover:text-foreground hover:bg-accent transition-colors relative">
          <Bell className="h-3.5 w-3.5" />
          <span className="absolute top-1 right-1 h-1.5 w-1.5 rounded-full bg-primary" />
        </button>
        <button className="p-1.5 rounded text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
          <User className="h-3.5 w-3.5" />
        </button>
      </div>
    </header>
  );
}
