"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import {
  LayoutDashboard, Share2, Users, FolderKanban, AlertTriangle,
  FlaskConical, Lightbulb, MessageSquareText, LogOut,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/graph", label: "Org Graph", icon: Share2 },
  { href: "/employees", label: "Employees", icon: Users },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/risks", label: "Risks", icon: AlertTriangle },
  { href: "/simulation", label: "Simulation", icon: FlaskConical },
  { href: "/recommendations", label: "Recommendations", icon: Lightbulb },
  { href: "/assistant", label: "AI Assistant", icon: MessageSquareText },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const { token, loading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !token) router.replace("/login");
  }, [loading, token, router]);

  if (loading || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center text-ink-500 text-sm">
        Loading OrgBrain…
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 border-r hairline bg-graphite-900/60 flex flex-col">
        <div className="px-5 py-6">
          <div className="font-display italic text-xl text-ink-100">OrgBrain</div>
          <div className="text-[11px] text-ink-500 tracking-wide uppercase mt-0.5">Execution Intelligence</div>
        </div>
        <nav className="flex-1 px-3 space-y-0.5">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-2.5 px-3 py-2 rounded text-sm transition-colors",
                  active
                    ? "bg-graphite-700 text-ink-100"
                    : "text-ink-300 hover:bg-graphite-800 hover:text-ink-100"
                )}
              >
                <Icon size={16} strokeWidth={1.75} />
                {label}
              </Link>
            );
          })}
        </nav>
        <button
          onClick={logout}
          className="flex items-center gap-2.5 mx-3 mb-5 px-3 py-2 rounded text-sm text-ink-500 hover:text-ink-100 hover:bg-graphite-800 transition-colors"
        >
          <LogOut size={16} strokeWidth={1.75} />
          Log out
        </button>
      </aside>
      <main className="flex-1 min-w-0">{children}</main>
    </div>
  );
}
