import { useState } from "react";
import { Panel } from "@/components/terminal/Panel";
import { FilterBar } from "@/components/terminal/FilterBar";
import { PlanBadge, RoleBadge } from "@/components/terminal/Badges";
import { Plus, RefreshCw, Edit, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

const mockUsers = [
  { id: "1", username: "trader_pro", email: "trader@example.com", plan: "yearly" as const, role: "user" as const, active: true, verified: true, joined: "Jan 15, 2024", telegram: true },
  { id: "2", username: "crypto_king", email: "king@example.com", plan: "monthly" as const, role: "user" as const, active: true, verified: true, joined: "Feb 20, 2024", telegram: false },
  { id: "3", username: "fx_master", email: "fx@example.com", plan: "trial" as const, role: "user" as const, active: true, verified: false, joined: "Mar 10, 2024", telegram: false },
  { id: "4", username: "admin_jane", email: "jane@team.com", plan: "lifetime" as const, role: "admin" as const, active: true, verified: true, joined: "Dec 1, 2023", telegram: true },
  { id: "5", username: "mod_bob", email: "bob@team.com", plan: "lifetime" as const, role: "admin" as const, active: false, verified: true, joined: "Nov 15, 2023", telegram: true },
];

export default function AdminUsersPage() {
  const [search, setSearch] = useState("");

  const filtered = mockUsers.filter(u =>
    !search || u.username.includes(search) || u.email.includes(search)
  );

  return (
    <div className="space-y-3">
      <Panel noPad>
        {/* Toolbar */}
        <div className="px-3 py-2 border-b border-border flex items-center justify-between">
          <FilterBar onSearch={setSearch} searchPlaceholder="Search users..." />
          <div className="flex items-center gap-1.5">
            <button className="filter-pill gap-1">
              <RefreshCw className="h-3 w-3" />
            </button>
            <button className="px-2.5 py-1 bg-primary text-primary-foreground rounded text-xs font-medium hover:opacity-90 flex items-center gap-1">
              <Plus className="h-3 w-3" />
              Add User
            </button>
          </div>
        </div>

        {/* Table Header */}
        <div className="grid grid-cols-[1fr_1.2fr_70px_60px_50px_50px_80px_50px_40px] px-3 py-1.5 text-2xs font-semibold text-muted-foreground uppercase tracking-wider border-b border-border">
          <span>Username</span>
          <span>Email</span>
          <span>Plan</span>
          <span>Role</span>
          <span>Active</span>
          <span>Verified</span>
          <span>Joined</span>
          <span>TG</span>
          <span></span>
        </div>

        {/* Rows */}
        {filtered.map((u) => (
          <div key={u.id} className="grid grid-cols-[1fr_1.2fr_70px_60px_50px_50px_80px_50px_40px] data-row">
            <span className="font-medium text-foreground">{u.username}</span>
            <span className="text-muted-foreground truncate">{u.email}</span>
            <span><PlanBadge plan={u.plan} /></span>
            <span><RoleBadge role={u.role} /></span>
            <span className={cn("text-2xs font-semibold", u.active ? "text-long" : "text-short")}>{u.active ? "Yes" : "No"}</span>
            <span className={cn("text-2xs font-semibold", u.verified ? "text-long" : "text-warning")}>{u.verified ? "✓" : "✗"}</span>
            <span className="text-2xs text-muted-foreground">{u.joined}</span>
            <span className={cn("text-2xs", u.telegram ? "text-info" : "text-muted-foreground")}>{u.telegram ? "✓" : "—"}</span>
            <button className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground">
              <Edit className="h-3 w-3" />
            </button>
          </div>
        ))}

        {/* Pagination */}
        <div className="flex items-center justify-between px-3 py-2 border-t border-border">
          <span className="text-2xs text-muted-foreground">Showing 1-5 of 520</span>
          <div className="flex items-center gap-1">
            <button className="p-1 rounded hover:bg-accent text-muted-foreground"><ChevronLeft className="h-3.5 w-3.5" /></button>
            <span className="text-2xs font-mono text-foreground px-2">1</span>
            <button className="p-1 rounded hover:bg-accent text-muted-foreground"><ChevronRight className="h-3.5 w-3.5" /></button>
          </div>
        </div>
      </Panel>
    </div>
  );
}
