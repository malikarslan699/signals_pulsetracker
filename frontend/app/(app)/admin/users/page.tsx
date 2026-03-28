"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatTimeAgo } from "@/lib/formatters";
import { Panel } from "@/components/terminal/Panel";
import { FilterBar } from "@/components/terminal/FilterBar";
import {
  ChevronLeft,
  ChevronRight,
  Edit2,
  X,
  UserPlus,
  Shield,
  Eye,
  EyeOff,
  CheckCircle2,
  XCircle,
  RefreshCw,
  KeyRound,
  ToggleLeft,
  ToggleRight,
  Trash2,
} from "lucide-react";
import toast from "react-hot-toast";
import { useAuthStore } from "@/store/userStore";
import { cn } from "@/lib/utils";

interface AdminUser {
  id: string;
  username: string;
  email: string;
  plan: string;
  plan_expires_at: string | null;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  qa_access: boolean;
  telegram_chat_id: string | null;
  telegram_username: string | null;
  created_at: string;
}

interface UsersResponse {
  items: AdminUser[];
  total: number;
  pages: number;
  page: number;
}

const PLAN_BADGE: Record<string, string> = {
  trial: "text-text-muted bg-surface-2 border-border",
  monthly: "text-purple bg-purple/10 border-purple/20",
  yearly: "text-long bg-long/10 border-long/20",
  lifetime: "text-gold bg-gold/10 border-gold/20",
};

const ROLE_BADGE: Record<string, string> = {
  user: "text-text-muted",
  reseller: "text-gold",
  admin: "text-purple",
  superadmin: "text-purple",
  owner: "text-short",
};

const PLAN_OPTIONS = ["trial", "monthly", "yearly", "lifetime"];
const ROLE_OPTIONS_BASE = ["user", "reseller", "admin"];

/* ── Add User Modal ─────────────────────────────────────────────────── */
function AddUserModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    email: "",
    username: "",
    password: "",
    role: "user",
    plan: "trial",
  });
  const [showPwd, setShowPwd] = useState(false);

  const mutation = useMutation({
    mutationFn: (data: typeof form) =>
      api
        .post("/api/v1/auth/register", {
          email: data.email,
          username: data.username,
          password: data.password,
        })
        .then(async (r) => {
          const userId = r.data.id;
          if (userId) {
            await api.put(`/api/v1/admin/users/${userId}`, {
              role: data.role,
              plan: data.plan,
              is_verified: true,
            });
          }
          return r.data;
        }),
    onSuccess: (u) => {
      toast.success(`User ${u.email || form.email} created`);
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      onClose();
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || "Failed to create user"),
  });

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-surface border border-border rounded-xl p-5 w-full max-w-md shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-text-primary flex items-center gap-2">
            <UserPlus className="w-4 h-4 text-purple" /> Add New User
          </h2>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 block">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
              className="w-full h-8 bg-surface-2 border border-border rounded px-2.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-purple"
              placeholder="user@example.com"
            />
          </div>
          <div>
            <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 block">Username</label>
            <input
              type="text"
              value={form.username}
              onChange={(e) => setForm((p) => ({ ...p, username: e.target.value }))}
              className="w-full h-8 bg-surface-2 border border-border rounded px-2.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-purple"
              placeholder="username"
            />
          </div>
          <div>
            <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 block">Password</label>
            <div className="relative">
              <input
                type={showPwd ? "text" : "password"}
                value={form.password}
                onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))}
                className="w-full h-8 bg-surface-2 border border-border rounded px-2.5 pr-8 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-purple"
                placeholder="Min 8 characters"
              />
              <button
                type="button"
                onClick={() => setShowPwd((v) => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
              >
                {showPwd ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 block">Role</label>
              <select
                value={form.role}
                onChange={(e) => setForm((p) => ({ ...p, role: e.target.value }))}
                className="w-full h-8 bg-surface-2 border border-border rounded px-2.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-purple"
              >
                {ROLE_OPTIONS_BASE.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 block">Plan</label>
              <select
                value={form.plan}
                onChange={(e) => setForm((p) => ({ ...p, plan: e.target.value }))}
                className="w-full h-8 bg-surface-2 border border-border rounded px-2.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-purple"
              >
                {PLAN_OPTIONS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
        <div className="flex gap-2 mt-4">
          <button
            onClick={onClose}
            className="flex-1 filter-pill justify-center"
          >
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate(form)}
            disabled={mutation.isPending || !form.email || !form.password}
            className="flex-1 px-3 py-1.5 bg-purple text-white rounded text-xs font-medium hover:opacity-90 disabled:opacity-40"
          >
            {mutation.isPending ? "Creating..." : "Create User"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Edit User Modal ─────────────────────────────────────────────────── */
function EditUserModal({
  user,
  canManageOwner,
  isOwner,
  onClose,
}: {
  user: AdminUser;
  canManageOwner: boolean;
  isOwner: boolean;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [plan, setPlan] = useState(user.plan);
  const [role, setRole] = useState(user.role);
  const [isActive, setIsActive] = useState(user.is_active);
  const [isVerified, setIsVerified] = useState(user.is_verified);
  const [qaAccess, setQaAccess] = useState(user.qa_access ?? false);
  const [newPassword, setNewPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);

  const autoExpiry = (selectedPlan: string): string => {
    const now = new Date();
    if (selectedPlan === "trial") now.setDate(now.getDate() + 30);
    else if (selectedPlan === "monthly") now.setDate(now.getDate() + 30);
    else if (selectedPlan === "yearly") now.setFullYear(now.getFullYear() + 1);
    else return "";
    return now.toISOString().slice(0, 10);
  };

  const [planExpiry, setPlanExpiry] = useState<string>(
    user.plan_expires_at
      ? new Date(user.plan_expires_at).toISOString().slice(0, 10)
      : ""
  );
  const roleOptions = canManageOwner
    ? [...ROLE_OPTIONS_BASE, "superadmin"]
    : ROLE_OPTIONS_BASE;
  const isTimeLimited =
    plan === "monthly" || plan === "yearly" || plan === "trial";

  const handlePlanChange = (newPlan: string) => {
    setPlan(newPlan);
    setPlanExpiry(autoExpiry(newPlan));
  };

  const updateMutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, any> = {
        plan,
        role,
        is_active: isActive,
        is_verified: isVerified,
      };
      if (isTimeLimited && planExpiry) {
        payload.plan_expires_at = new Date(planExpiry).toISOString();
      } else if (!isTimeLimited) {
        payload.plan_expires_at = null;
      }
      if (newPassword && newPassword.length >= 8) {
        payload.password = newPassword;
      }
      if (isOwner) payload.qa_access = qaAccess;
      return api.put(`/api/v1/admin/users/${user.id}`, payload).then((r) => r.data);
    },
    onSuccess: () => {
      toast.success(`Updated ${user.username || user.email}`);
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      onClose();
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || "Update failed"),
  });

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-surface border border-border rounded-xl p-5 w-full max-w-md shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-text-primary flex items-center gap-2">
              <Edit2 className="w-3.5 h-3.5 text-purple" /> Edit User
            </h2>
            <p className="text-2xs text-text-muted mt-0.5">{user.email}</p>
          </div>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-3">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setIsActive((v) => !v)}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1.5 rounded border text-xs flex-1 transition-colors",
                isActive
                  ? "bg-long/10 border-long/30 text-long"
                  : "bg-surface-2 border-border text-text-muted"
              )}
            >
              {isActive ? <ToggleRight className="w-3.5 h-3.5" /> : <ToggleLeft className="w-3.5 h-3.5" />}
              {isActive ? "Active" : "Inactive"}
            </button>
            <button
              type="button"
              onClick={() => setIsVerified((v) => !v)}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1.5 rounded border text-xs flex-1 transition-colors",
                isVerified
                  ? "bg-blue/10 border-blue/30 text-blue"
                  : "bg-surface-2 border-border text-text-muted"
              )}
            >
              {isVerified ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
              {isVerified ? "Verified" : "Unverified"}
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 flex items-center gap-1">
                <Shield className="w-3 h-3" /> Role
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full h-8 bg-surface-2 border border-border rounded px-2.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-purple"
              >
                {roleOptions.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 block">Plan</label>
              <select
                value={plan}
                onChange={(e) => handlePlanChange(e.target.value)}
                className="w-full h-8 bg-surface-2 border border-border rounded px-2.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-purple"
              >
                {PLAN_OPTIONS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>

          {isTimeLimited && (
            <div>
              <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 block">
                Plan Expires
              </label>
              <input
                type="date"
                value={planExpiry}
                onChange={(e) => setPlanExpiry(e.target.value)}
                className="w-full h-8 bg-surface-2 border border-border rounded px-2.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-purple"
              />
            </div>
          )}

          {isOwner && (role === "admin" || role === "superadmin") && (
            <div className="flex items-center justify-between px-2.5 py-2 bg-surface-2 border border-purple/20 rounded">
              <div>
                <p className="text-xs font-medium text-text-primary flex items-center gap-1">
                  <Shield className="w-3 h-3 text-purple" /> QA Lab Access
                </p>
                <p className="text-2xs text-text-muted mt-0.5">Allow viewing QA research</p>
              </div>
              <button
                type="button"
                onClick={() => setQaAccess((v) => !v)}
                className={cn(
                  "flex items-center gap-1 px-2.5 py-1 rounded border text-xs transition-colors",
                  qaAccess
                    ? "bg-purple/10 border-purple/30 text-purple"
                    : "bg-surface border-border text-text-muted"
                )}
              >
                {qaAccess ? <ToggleRight className="w-3.5 h-3.5" /> : <ToggleLeft className="w-3.5 h-3.5" />}
                {qaAccess ? "Granted" : "Revoked"}
              </button>
            </div>
          )}

          <div>
            <label className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1 flex items-center gap-1">
              <KeyRound className="w-3 h-3" /> New Password (optional)
            </label>
            <div className="relative">
              <input
                type={showPwd ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full h-8 bg-surface-2 border border-border rounded px-2.5 pr-8 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-purple"
                placeholder="Leave blank to keep current"
              />
              <button
                type="button"
                onClick={() => setShowPwd((v) => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
              >
                {showPwd ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
            {newPassword && newPassword.length < 8 && (
              <p className="text-2xs text-short mt-0.5">Min 8 characters</p>
            )}
          </div>
        </div>

        <div className="flex gap-2 mt-4">
          <button onClick={onClose} className="flex-1 filter-pill justify-center">
            Cancel
          </button>
          <button
            onClick={() => updateMutation.mutate()}
            disabled={
              updateMutation.isPending ||
              (!!newPassword && newPassword.length < 8)
            }
            className="flex-1 px-3 py-1.5 bg-purple text-white rounded text-xs font-medium hover:opacity-90 disabled:opacity-40"
          >
            {updateMutation.isPending ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Main Page ─────────────────────────────────────────────────────── */
export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuthStore();
  const canManageOwner =
    currentUser?.role === "owner" || currentUser?.role === "superadmin";
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery<UsersResponse>({
    queryKey: ["admin-users", page, search],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), limit: "25" });
      if (search.trim()) params.set("search", search.trim());
      return api.get(`/api/v1/admin/users/?${params}`).then((r) => r.data);
    },
    retry: 2,
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      api.put(`/api/v1/admin/users/${id}`, { is_active }),
    onSuccess: (_, { is_active }) => {
      toast.success(is_active ? "User activated" : "User deactivated");
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || "Failed to update status"),
  });

  const deleteUserMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/admin/users/${id}`),
    onSuccess: () => {
      toast.success("User deleted");
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || "Failed to delete user"),
  });

  const users: AdminUser[] = data?.items || [];
  const totalPages = data?.pages ?? 1;

  return (
    <div className="space-y-3">
      <Panel noPad>
        {/* Toolbar */}
        <div className="px-3 py-2 border-b border-border flex items-center justify-between gap-2">
          <FilterBar
            onSearch={(q) => { setSearch(q); setPage(1); }}
            searchPlaceholder="Search users..."
          />
          <div className="flex items-center gap-1.5 shrink-0">
            <span className="text-2xs text-text-muted">{data?.total ?? 0} users</span>
            <button
              onClick={() => refetch()}
              className="filter-pill"
              title="Refresh"
            >
              <RefreshCw className="h-3 w-3" />
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-2.5 py-1 bg-purple text-white rounded text-xs font-medium hover:opacity-90 flex items-center gap-1"
            >
              <UserPlus className="h-3 w-3" />
              Add User
            </button>
          </div>
        </div>

        {/* Table Header */}
        <div className="grid grid-cols-[1fr_1.2fr_70px_60px_50px_50px_80px_50px_110px] px-3 py-1.5 text-2xs font-semibold text-text-muted uppercase tracking-wider border-b border-border">
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
        {isLoading ? (
          <div className="p-3 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-8 bg-surface-2 rounded animate-pulse" />
            ))}
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-8 gap-2">
            <XCircle className="w-6 h-6 text-short opacity-60" />
            <p className="text-text-muted text-xs">Failed to load users.</p>
            <button
              onClick={() => refetch()}
              className="filter-pill text-purple border-purple/30"
            >
              Try Again
            </button>
          </div>
        ) : users.length === 0 ? (
          <div className="flex items-center justify-center py-8 text-text-muted text-xs">
            No users found
          </div>
        ) : (
          users.map((u) => (
            <div
              key={u.id}
              className="grid grid-cols-[1fr_1.2fr_70px_60px_50px_50px_80px_50px_110px] data-row"
            >
              <span className="font-medium text-text-primary">{u.username || "—"}</span>
              <span className="text-text-muted truncate text-2xs font-mono">{u.email}</span>
              <span>
                <span
                  className={cn(
                    "text-2xs px-1.5 py-0.5 rounded-full border font-medium capitalize",
                    PLAN_BADGE[u.plan] ?? "text-text-muted bg-surface-2 border-border"
                  )}
                >
                  {u.plan}
                </span>
              </span>
              <span
                className={cn(
                  "text-2xs font-medium capitalize",
                  ROLE_BADGE[u.role] ?? "text-text-muted"
                )}
              >
                {u.role === "superadmin" ? "owner" : u.role}
              </span>
              <button
                onClick={() =>
                  toggleActiveMutation.mutate({ id: u.id, is_active: !u.is_active })
                }
                disabled={toggleActiveMutation.isPending}
                className={cn(
                  "text-2xs font-semibold text-left",
                  u.is_active ? "text-long" : "text-short"
                )}
              >
                {u.is_active ? "Yes" : "No"}
              </button>
              <span
                className={cn(
                  "text-2xs font-semibold",
                  u.is_verified ? "text-long" : "text-gold"
                )}
              >
                {u.is_verified ? "✓" : "✗"}
              </span>
              <span className="text-2xs text-text-muted">
                {formatTimeAgo(u.created_at)}
              </span>
              <span
                className={cn(
                  "text-2xs",
                  u.telegram_chat_id ? "text-blue" : "text-text-muted"
                )}
              >
                {u.telegram_chat_id ? "✓" : "—"}
              </span>
              <div className="flex items-center gap-1 justify-end">
                <button
                  onClick={() => setEditingUser(u)}
                  className="px-1.5 py-1 rounded hover:bg-surface-2 text-text-muted hover:text-text-primary text-2xs"
                  title="Edit user"
                >
                  <span className="inline-flex items-center gap-1">
                    <Edit2 className="h-3 w-3" />
                    Edit
                  </span>
                </button>
                <button
                  onClick={() => {
                    const canDelete = currentUser?.id !== u.id;
                    if (!canDelete) {
                      toast.error("You cannot delete your own account.");
                      return;
                    }
                    const ok = window.confirm(
                      `Delete user "${u.username || u.email}" permanently?`
                    );
                    if (ok) deleteUserMutation.mutate(u.id);
                  }}
                  disabled={deleteUserMutation.isPending}
                  className="px-1.5 py-1 rounded hover:bg-short/10 text-text-muted hover:text-short disabled:opacity-40 text-2xs"
                  title="Delete user"
                >
                  <span className="inline-flex items-center gap-1">
                    <Trash2 className="h-3 w-3" />
                    Delete
                  </span>
                </button>
              </div>
            </div>
          ))
        )}

        {/* Pagination */}
        {!isLoading && !isError && totalPages > 1 && (
          <div className="flex items-center justify-between px-3 py-2 border-t border-border">
            <span className="text-2xs text-text-muted">
              Page {page} of {totalPages} · {data?.total ?? 0} total
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-1 rounded hover:bg-surface-2 text-text-muted disabled:opacity-40"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
              </button>
              <span className="text-2xs font-mono text-text-primary px-2">{page}</span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-1 rounded hover:bg-surface-2 text-text-muted disabled:opacity-40"
              >
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        )}
      </Panel>

      {showAddModal && <AddUserModal onClose={() => setShowAddModal(false)} />}
      {editingUser && (
        <EditUserModal
          user={editingUser}
          canManageOwner={canManageOwner}
          isOwner={canManageOwner}
          onClose={() => setEditingUser(null)}
        />
      )}
    </div>
  );
}
