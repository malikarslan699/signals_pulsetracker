"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatTimeAgo } from "@/lib/formatters";
import {
  Search, ChevronLeft, ChevronRight, Edit2, Check, X,
  UserPlus, Shield, Eye, EyeOff, CheckCircle2, XCircle, RefreshCw,
  KeyRound, ToggleLeft, ToggleRight,
} from "lucide-react";
import toast from "react-hot-toast";
import { useAuthStore } from "@/store/userStore";

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
  trial:    "text-text-muted bg-surface-2 border-border",
  monthly:  "text-purple bg-purple/10 border-purple/20",
  yearly:   "text-long bg-long/10 border-long/20",
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

/* ──────────────────────────────────────────────────────
   Add User Modal
────────────────────────────────────────────────────── */
function AddUserModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ email: "", username: "", password: "", role: "user", plan: "trial" });
  const [showPwd, setShowPwd] = useState(false);

  const mutation = useMutation({
    mutationFn: (data: typeof form) =>
      api.post("/api/v1/auth/register", { email: data.email, username: data.username, password: data.password })
        .then(async (r) => {
          const userId = r.data.id;
          if (userId) {
            await api.put(`/api/v1/admin/users/${userId}`, {
              role: data.role, plan: data.plan, is_verified: true,
            });
          }
          return r.data;
        }),
    onSuccess: (u) => {
      toast.success(`User ${u.email || form.email} created`);
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      onClose();
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Failed to create user"),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-surface border border-border rounded-2xl p-6 w-full max-w-md shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-purple" /> Add New User
          </h2>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs text-text-muted mb-1.5">Email</label>
            <input type="email" value={form.email} onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
              className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-purple"
              placeholder="user@example.com" />
          </div>
          <div>
            <label className="block text-xs text-text-muted mb-1.5">Username</label>
            <input type="text" value={form.username} onChange={(e) => setForm((p) => ({ ...p, username: e.target.value }))}
              className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-purple"
              placeholder="username" />
          </div>
          <div>
            <label className="block text-xs text-text-muted mb-1.5">Password</label>
            <div className="relative">
              <input type={showPwd ? "text" : "password"} value={form.password}
                onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 pr-10 text-sm text-text-primary focus:outline-none focus:border-purple"
                placeholder="Min 8 characters" />
              <button type="button" onClick={() => setShowPwd((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary">
                {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-text-muted mb-1.5">Role</label>
              <select value={form.role} onChange={(e) => setForm((p) => ({ ...p, role: e.target.value }))}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-purple">
                {ROLE_OPTIONS_BASE.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1.5">Plan</label>
              <select value={form.plan} onChange={(e) => setForm((p) => ({ ...p, plan: e.target.value }))}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-purple">
                {PLAN_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={onClose}
            className="flex-1 px-4 py-2 bg-surface-2 border border-border text-text-muted rounded-lg text-sm hover:border-short transition-colors">
            Cancel
          </button>
          <button onClick={() => mutation.mutate(form)} disabled={mutation.isPending || !form.email || !form.password}
            className="flex-1 px-4 py-2 bg-purple text-white rounded-lg text-sm font-medium hover:bg-purple/80 transition-colors disabled:opacity-40">
            {mutation.isPending ? "Creating..." : "Create User"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────
   Edit User Modal (full editing)
────────────────────────────────────────────────────── */
function EditUserModal({ user, canManageOwner, isOwner, onClose }: {
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

  // Always auto-compute expiry from today when plan changes
  const autoExpiry = (selectedPlan: string): string => {
    const now = new Date();
    if (selectedPlan === "trial") {
      now.setHours(now.getHours() + 24);
    } else if (selectedPlan === "monthly") {
      now.setDate(now.getDate() + 30);
    } else if (selectedPlan === "yearly") {
      now.setFullYear(now.getFullYear() + 1);
    } else {
      return ""; // lifetime — no expiry
    }
    return now.toISOString().slice(0, 10);
  };

  const [planExpiry, setPlanExpiry] = useState<string>(
    user.plan_expires_at ? new Date(user.plan_expires_at).toISOString().slice(0, 10) : ""
  );
  const roleOptions = canManageOwner ? [...ROLE_OPTIONS_BASE, "superadmin"] : ROLE_OPTIONS_BASE;
  const isTimeLimited = plan === "monthly" || plan === "yearly" || plan === "trial";

  // Always recalculate from today when plan changes
  const handlePlanChange = (newPlan: string) => {
    setPlan(newPlan);
    setPlanExpiry(autoExpiry(newPlan));
  };

  const updateMutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, any> = { plan, role, is_active: isActive, is_verified: isVerified };
      if (isTimeLimited && planExpiry) {
        payload.plan_expires_at = new Date(planExpiry).toISOString();
      } else if (!isTimeLimited) {
        payload.plan_expires_at = null;
      }
      if (newPassword && newPassword.length >= 8) {
        payload.password = newPassword;
      }
      // Only send qa_access if current user is owner
      if (isOwner) {
        payload.qa_access = qaAccess;
      }
      return api.put(`/api/v1/admin/users/${user.id}`, payload).then((r) => r.data);
    },
    onSuccess: () => {
      toast.success(`Updated ${user.username || user.email}`);
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      onClose();
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Update failed"),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-surface border border-border rounded-2xl p-6 w-full max-w-md shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
              <Edit2 className="w-4 h-4 text-purple" /> Edit User
            </h2>
            <p className="text-xs text-text-muted mt-0.5">{user.email}</p>
          </div>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Status toggles */}
          <div className="flex gap-3">
            <button type="button" onClick={() => setIsActive((v) => !v)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm flex-1 transition-colors ${
                isActive ? "bg-long/10 border-long/30 text-long" : "bg-surface-2 border-border text-text-muted"
              }`}>
              {isActive ? <ToggleRight className="w-4 h-4" /> : <ToggleLeft className="w-4 h-4" />}
              {isActive ? "Active" : "Inactive"}
            </button>
            <button type="button" onClick={() => setIsVerified((v) => !v)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm flex-1 transition-colors ${
                isVerified ? "bg-blue/10 border-blue/30 text-blue" : "bg-surface-2 border-border text-text-muted"
              }`}>
              {isVerified ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
              {isVerified ? "Verified" : "Unverified"}
            </button>
          </div>

          {/* Role & Plan */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-text-muted mb-1.5 flex items-center gap-1">
                <Shield className="w-3 h-3" /> Role
              </label>
              <select value={role} onChange={(e) => setRole(e.target.value)}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-purple">
                {roleOptions.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1.5">Plan</label>
              <select value={plan} onChange={(e) => handlePlanChange(e.target.value)}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-purple">
                {PLAN_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>

          {/* Plan expiry — only shown for time-limited plans */}
          {isTimeLimited && (
            <div>
              <label className="block text-xs text-text-muted mb-1.5">
                Plan Expires (leave blank = no expiry set)
              </label>
              <input
                type="date"
                value={planExpiry}
                onChange={(e) => setPlanExpiry(e.target.value)}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-purple"
              />
            </div>
          )}

          {/* QA Lab Access — owner only, shown when editing admins */}
          {isOwner && (role === "admin" || role === "superadmin") && (
            <div className="flex items-center justify-between p-3 bg-surface-2 border border-purple/20 rounded-lg">
              <div>
                <p className="text-sm font-medium text-text-primary flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-purple" /> QA Lab Access
                </p>
                <p className="text-xs text-text-muted mt-0.5">Allow this admin to view QA research</p>
              </div>
              <button type="button" onClick={() => setQaAccess((v) => !v)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
                  qaAccess
                    ? "bg-purple/10 border-purple/30 text-purple"
                    : "bg-surface border-border text-text-muted"
                }`}>
                {qaAccess ? <ToggleRight className="w-4 h-4" /> : <ToggleLeft className="w-4 h-4" />}
                {qaAccess ? "Granted" : "Revoked"}
              </button>
            </div>
          )}

          {/* Password reset */}
          <div>
            <label className="block text-xs text-text-muted mb-1.5 flex items-center gap-1">
              <KeyRound className="w-3 h-3" /> New Password (optional)
            </label>
            <div className="relative">
              <input type={showPwd ? "text" : "password"} value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 pr-10 text-sm text-text-primary focus:outline-none focus:border-purple"
                placeholder="Leave blank to keep current" />
              <button type="button" onClick={() => setShowPwd((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary">
                {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {newPassword && newPassword.length < 8 && (
              <p className="text-xs text-short mt-1">Min 8 characters</p>
            )}
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={onClose}
            className="flex-1 px-4 py-2 bg-surface-2 border border-border text-text-muted rounded-lg text-sm hover:border-short transition-colors">
            Cancel
          </button>
          <button onClick={() => updateMutation.mutate()}
            disabled={updateMutation.isPending || (!!newPassword && newPassword.length < 8)}
            className="flex-1 px-4 py-2 bg-purple text-white rounded-lg text-sm font-medium hover:bg-purple/80 transition-colors disabled:opacity-40">
            {updateMutation.isPending ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────
   Main Page
────────────────────────────────────────────────────── */
export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuthStore();
  const canManageOwner = currentUser?.role === "owner" || currentUser?.role === "superadmin";
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
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Failed to update status"),
  });

  const users: AdminUser[] = data?.items || [];
  const totalPages = data?.pages ?? 1;

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search by email or username..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-9 pr-4 py-2 bg-surface border border-border rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-purple"
          />
        </div>

        <div className="flex items-center gap-2 ml-auto">
          <span className="text-sm text-text-muted">{data?.total ?? 0} users</span>
          <button onClick={() => refetch()}
            className="p-2 bg-surface border border-border rounded-lg text-text-muted hover:border-purple hover:text-purple transition-colors"
            title="Refresh">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple text-white rounded-lg text-sm font-medium hover:bg-purple/80 transition-colors">
            <UserPlus className="w-4 h-4" />
            Add User
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-4 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-14 bg-surface-2 rounded animate-pulse" />
            ))}
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-12 gap-3">
            <XCircle className="w-8 h-8 text-short opacity-60" />
            <p className="text-text-muted text-sm">Failed to load users.</p>
            <button onClick={() => refetch()}
              className="px-4 py-2 bg-purple/10 border border-purple/20 text-purple rounded-lg text-sm hover:bg-purple/20 transition-colors">
              Try Again
            </button>
          </div>
        ) : users.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-text-muted text-sm gap-2">
            <p>No users found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-surface-2 text-xs">
                  <th className="text-left px-4 py-3 text-text-muted font-medium">User</th>
                  <th className="text-center px-3 py-3 text-text-muted font-medium">Status</th>
                  <th className="text-left px-3 py-3 text-text-muted font-medium">Role</th>
                  <th className="text-left px-3 py-3 text-text-muted font-medium">Plan</th>
                  <th className="text-center px-3 py-3 text-text-muted font-medium">Verified</th>
                  <th className="text-right px-3 py-3 text-text-muted font-medium">Joined</th>
                  <th className="text-right px-4 py-3 text-text-muted font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u, i) => (
                  <tr
                    key={u.id}
                    className={`border-b border-border hover:bg-surface-2/60 transition-colors ${i % 2 !== 0 ? "bg-surface-2/20" : ""}`}
                  >
                    {/* User info */}
                    <td className="px-4 py-3">
                      <div className="flex flex-col">
                        <span className="font-medium text-text-primary text-sm">{u.username || "—"}</span>
                        <span className="text-xs text-text-muted font-mono">{u.email}</span>
                        {u.telegram_username && (
                          <span className="text-xs text-blue mt-0.5">@{u.telegram_username}</span>
                        )}
                      </div>
                    </td>

                    {/* Active status toggle */}
                    <td className="px-3 py-3 text-center">
                      <button
                        onClick={() => toggleActiveMutation.mutate({ id: u.id, is_active: !u.is_active })}
                        disabled={toggleActiveMutation.isPending}
                        title={u.is_active ? "Click to deactivate" : "Click to activate"}
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                          u.is_active
                            ? "bg-long/10 text-long border-long/20 hover:bg-long/20"
                            : "bg-short/10 text-short border-short/20 hover:bg-short/20"
                        }`}
                      >
                        {u.is_active ? (
                          <><CheckCircle2 className="w-3 h-3" /> Active</>
                        ) : (
                          <><XCircle className="w-3 h-3" /> Inactive</>
                        )}
                      </button>
                    </td>

                    {/* Role */}
                    <td className="px-3 py-3">
                      <span className={`text-xs font-medium capitalize ${ROLE_BADGE[u.role] ?? "text-text-muted"}`}>
                        {u.role === "superadmin" ? "owner" : u.role}
                      </span>
                    </td>

                    {/* Plan / subscription */}
                    <td className="px-3 py-3">
                      <div className="flex flex-col gap-0.5">
                        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize w-fit ${
                          PLAN_BADGE[u.plan] ?? "text-text-muted bg-surface-2 border-border"
                        }`}>
                          {u.plan}
                        </span>
                        {u.plan_expires_at && (
                          <span className="text-xs text-text-muted">
                            Exp: {new Date(u.plan_expires_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Verified */}
                    <td className="px-3 py-3 text-center">
                      {u.is_verified ? (
                        <CheckCircle2 className="w-4 h-4 text-long mx-auto" aria-label="Email verified" />
                      ) : (
                        <XCircle className="w-4 h-4 text-short mx-auto" aria-label="Not verified" />
                      )}
                    </td>

                    {/* Joined */}
                    <td className="px-3 py-3 text-right text-xs text-text-muted whitespace-nowrap">
                      {formatTimeAgo(u.created_at)}
                    </td>

                    {/* Actions */}
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end">
                        <button
                          onClick={() => setEditingUser(u)}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-purple/10 border border-purple/20 text-purple rounded-lg text-xs hover:bg-purple/20 transition-colors"
                        >
                          <Edit2 className="w-3 h-3" />
                          Edit
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!isLoading && !isError && totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <span className="text-xs text-text-muted">
              Page {page} of {totalPages} · {data?.total ?? 0} total
            </span>
            <div className="flex gap-2">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
                className="flex items-center gap-1 px-3 py-1.5 bg-surface-2 border border-border rounded-lg text-xs text-text-muted disabled:opacity-40 hover:border-purple hover:text-text-primary transition-colors">
                <ChevronLeft className="w-3.5 h-3.5" /> Prev
              </button>
              <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                className="flex items-center gap-1 px-3 py-1.5 bg-surface-2 border border-border rounded-lg text-xs text-text-muted disabled:opacity-40 hover:border-purple hover:text-text-primary transition-colors">
                Next <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
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
