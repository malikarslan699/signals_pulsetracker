import { Panel } from "@/components/terminal/Panel";
import { PlanBadge } from "@/components/terminal/Badges";
import { User, Mail, Shield, MessageCircle, LogOut, Copy, RefreshCw, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  return (
    <div className="p-3 space-y-3 max-w-2xl">
      <h1 className="text-sm font-semibold text-foreground">Settings</h1>

      {/* Subscription */}
      <Panel title="Subscription" noPad>
        <div className="px-3 py-2 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-foreground">Current Plan</span>
                <PlanBadge plan="yearly" />
              </div>
              <span className="text-2xs text-muted-foreground">Expires: Apr 15, 2025</span>
            </div>
          </div>
          <button className="filter-pill">Manage</button>
        </div>
      </Panel>

      {/* Profile */}
      <Panel title="Profile">
        <div className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-2xs font-medium text-muted-foreground uppercase tracking-wider mb-1 block">Username</label>
              <input
                type="text"
                defaultValue="trader_pro"
                className="w-full h-8 px-2.5 text-xs bg-secondary border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div>
              <label className="text-2xs font-medium text-muted-foreground uppercase tracking-wider mb-1 block">Email</label>
              <div className="flex gap-1.5">
                <input
                  type="email"
                  defaultValue="trader@example.com"
                  className="flex-1 h-8 px-2.5 text-xs bg-secondary border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <span className="flex items-center px-2 text-2xs font-semibold text-long bg-long/10 rounded">Verified</span>
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <button className="filter-pill gap-1">
              <RefreshCw className="h-3 w-3" />
              Resend Verification
            </button>
            <button className="px-3 py-1.5 bg-primary text-primary-foreground rounded text-xs font-medium hover:opacity-90 transition-opacity">
              Save Profile
            </button>
          </div>
        </div>
      </Panel>

      {/* Telegram */}
      <Panel title="Telegram Integration" noPad>
        <div className="px-3 py-2 space-y-2">
          <div className="flex items-center gap-2 text-xs">
            <MessageCircle className="h-3.5 w-3.5 text-info" />
            <span className="text-foreground font-medium">Not Connected</span>
          </div>
          <p className="text-2xs text-muted-foreground">
            Generate a verification code and send it to our Telegram bot to connect.
          </p>
          <div className="flex gap-1.5">
            <button className="px-3 py-1.5 bg-primary text-primary-foreground rounded text-xs font-medium hover:opacity-90 transition-opacity">
              Generate Code
            </button>
          </div>
        </div>
      </Panel>

      {/* Danger Zone */}
      <Panel noPad>
        <div className="terminal-header">
          <div className="flex items-center gap-1.5 text-short">
            <AlertTriangle className="h-3 w-3" />
            <span>Danger Zone</span>
          </div>
        </div>
        <div className="px-3 py-2 flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-foreground">Sign Out</span>
            <p className="text-2xs text-muted-foreground">End your current session</p>
          </div>
          <button className="filter-pill gap-1 border-short/30 text-short hover:bg-short/10">
            <LogOut className="h-3 w-3" />
            Sign Out
          </button>
        </div>
      </Panel>
    </div>
  );
}
