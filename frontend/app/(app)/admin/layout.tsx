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
    <div className="space-y-6 pb-20 lg:pb-6">
      {/* Admin Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-purple/10 border border-purple/20 rounded-lg">
          <Shield className="w-5 h-5 text-purple" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Admin Panel</h1>
          <p className="text-text-muted text-sm">System management and oversight</p>
        </div>
      </div>

      {/* Sub-navigation */}
      <div className="border-b border-border">
        <nav className="flex gap-1 -mb-px">
          {navLinks.map((link) => {
            const isActive =
              link.href === "/admin"
                ? pathname === "/admin"
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  isActive
                    ? "border-purple text-purple"
                    : "border-transparent text-text-muted hover:text-text-primary hover:border-border"
                }`}
              >
                {link.label}
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
