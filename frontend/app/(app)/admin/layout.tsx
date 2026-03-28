"use client";
import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { Shield } from "lucide-react";
import { useAuthStore } from "@/store/userStore";

const BASE_NAV = [
  { label: "Overview", href: "/admin" },
  { label: "Users", href: "/admin/users" },
  { label: "Packages", href: "/admin/packages" },
  { label: "Payments", href: "/admin/payments" },
  { label: "Config", href: "/admin/config" },
  { label: "Analytics", href: "/admin/analytics" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  // QA Lab: owner/superadmin always, admin only if qa_access granted by owner
  const canSeeQA =
    user?.role === "owner" ||
    user?.role === "superadmin" ||
    (user?.role === "admin" && user?.qa_access === true);

  const navLinks = canSeeQA
    ? [...BASE_NAV, { label: "QA Lab", href: "/admin/qa" }]
    : BASE_NAV;

  useEffect(() => {
    if (user && user.role !== "admin" && user.role !== "owner" && user.role !== "superadmin") {
      router.replace("/dashboard");
    }
  }, [user, router]);

  if (!user || (user.role !== "admin" && user.role !== "owner" && user.role !== "superadmin")) {
    return null;
  }

  return (
    <div className="space-y-4 pb-20 lg:pb-6">
      {/* Admin Header */}
      <div className="terminal-panel p-3 flex items-center gap-3">
        <div className="p-2 bg-long/10 border border-long/20 rounded-md">
          <Shield className="w-5 h-5 text-long" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-text-primary">Admin Control Center</h1>
          <p className="text-text-muted text-xs">System management and oversight</p>
        </div>
      </div>

      {/* Sub-navigation */}
      <div className="terminal-panel p-2">
        <nav className="flex flex-wrap gap-1">
          {navLinks.map((link) => {
            const isActive =
              link.href === "/admin"
                ? pathname === "/admin"
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`filter-pill ${isActive ? "filter-pill-active" : ""}`}
                style={{ minHeight: "2rem" }}
              >
                <span className={`${isActive ? "text-long" : "text-text-muted"} text-xs font-medium`}>
                  {link.label}
                </span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Page content */}
      <div>{children}</div>
    </div>
  );
}
