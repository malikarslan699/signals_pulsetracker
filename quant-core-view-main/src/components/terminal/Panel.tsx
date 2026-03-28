import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface PanelProps {
  title?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  noPad?: boolean;
}

export function Panel({ title, actions, children, className, noPad }: PanelProps) {
  return (
    <div className={cn("terminal-panel", className)}>
      {(title || actions) && (
        <div className="terminal-header">
          <span>{title}</span>
          {actions && <div className="flex items-center gap-1">{actions}</div>}
        </div>
      )}
      <div className={cn(!noPad && "p-3")}>
        {children}
      </div>
    </div>
  );
}
