import { Panel } from "@/components/terminal/Panel";
import { Save, Send, AlertTriangle, CheckCircle, XCircle, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

const Toggle = ({ label, defaultChecked = false }: { label: string; defaultChecked?: boolean }) => (
  <div className="flex items-center justify-between py-1">
    <span className="text-xs text-foreground">{label}</span>
    <button className={cn("h-5 w-9 rounded-full transition-colors relative", defaultChecked ? "bg-primary" : "bg-secondary")}>
      <span className={cn("absolute top-0.5 h-4 w-4 rounded-full bg-primary-foreground transition-transform", defaultChecked ? "left-[18px]" : "left-0.5")} />
    </button>
  </div>
);

const ConfigInput = ({ label, value, secret }: { label: string; value: string; secret?: boolean }) => (
  <div>
    <label className="text-2xs font-medium text-muted-foreground uppercase tracking-wider mb-1 block">{label}</label>
    <input
      type={secret ? "password" : "text"}
      defaultValue={value}
      className="w-full h-7 px-2.5 text-xs bg-secondary border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary font-mono"
    />
  </div>
);

const HealthCheck = ({ label, healthy }: { label: string; healthy: boolean }) => (
  <div className="flex items-center gap-2 text-xs">
    {healthy ? <CheckCircle className="h-3.5 w-3.5 text-long" /> : <XCircle className="h-3.5 w-3.5 text-short" />}
    <span className="text-foreground">{label}</span>
    <span className={cn("text-2xs font-semibold", healthy ? "text-long" : "text-short")}>
      {healthy ? "Connected" : "Error"}
    </span>
  </div>
);

export default function AdminConfigPage() {
  return (
    <div className="space-y-3 max-w-3xl">
      {/* Auth & Trial */}
      <Panel title="Authentication & Trial">
        <div className="space-y-2">
          <Toggle label="Email verification required" defaultChecked />
          <Toggle label="Allow registration" defaultChecked />
          <ConfigInput label="Trial Duration (days)" value="7" />
        </div>
      </Panel>

      {/* Scanner */}
      <Panel title="Scanner Configuration">
        <div className="space-y-2">
          <Toggle label="Scanner enabled" defaultChecked />
          <ConfigInput label="Scan interval (minutes)" value="5" />
          <ConfigInput label="Min confidence threshold" value="60" />
          <ConfigInput label="Max concurrent pairs" value="50" />
        </div>
      </Panel>

      {/* Notifications */}
      <Panel title="Notifications">
        <Toggle label="Email notifications enabled" defaultChecked />
        <Toggle label="Telegram notifications enabled" defaultChecked />
      </Panel>

      {/* SMTP */}
      <Panel title="SMTP Settings">
        <div className="space-y-2">
          <HealthCheck label="SMTP" healthy />
          <div className="grid grid-cols-2 gap-2">
            <ConfigInput label="Host" value="smtp.example.com" />
            <ConfigInput label="Port" value="587" />
            <ConfigInput label="Username" value="noreply@pulse.io" />
            <ConfigInput label="Password" value="••••••••" secret />
          </div>
          <button className="filter-pill gap-1 text-info border-info/30">
            <Send className="h-3 w-3" />
            Send Test Email
          </button>
        </div>
      </Panel>

      {/* Telegram */}
      <Panel title="Telegram Bot">
        <div className="space-y-2">
          <HealthCheck label="Telegram Bot" healthy />
          <ConfigInput label="Bot Token" value="••••••••" secret />
          <button className="filter-pill gap-1 text-info border-info/30">
            <Send className="h-3 w-3" />
            Send Test Message
          </button>
        </div>
      </Panel>

      {/* API Keys */}
      <Panel title="API Keys & Billing">
        <div className="space-y-2">
          <ConfigInput label="Exchange API Key" value="••••••••" secret />
          <ConfigInput label="Exchange API Secret" value="••••••••" secret />
          <ConfigInput label="Stripe Secret Key" value="••••••••" secret />
        </div>
      </Panel>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <button className="filter-pill gap-1 text-short border-short/30 hover:bg-short/10">
          <Trash2 className="h-3 w-3" />
          Purge Low-Quality Signals
        </button>
        <button className="px-3 py-1.5 bg-primary text-primary-foreground rounded text-xs font-medium hover:opacity-90 flex items-center gap-1">
          <Save className="h-3 w-3" />
          Save Configuration
        </button>
      </div>
    </div>
  );
}
