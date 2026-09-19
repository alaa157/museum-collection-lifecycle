"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Archive,
  Bell,
  Beaker,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  MapPin,
  PackageCheck,
  Settings,
  ShieldCheck,
  Users,
  WalletCards
} from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useCurrentUser } from "@/components/auth-guard";
import { can } from "@/lib/permissions";

const navigation = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, permission: "collection:read" },
  { href: "/collection", label: "Collection", icon: Archive, permission: "collection:read" },
  { href: "/movements", label: "Movements", icon: MapPin, permission: "collection:move" },
  { href: "/conservation", label: "Conservation", icon: Beaker, permission: "conservation:read" },
  { href: "/loans", label: "Loans", icon: WalletCards, permission: "loans:read" },
  { href: "/exhibitions", label: "Exhibitions", icon: PackageCheck, permission: "loans:read" },
  { href: "/users", label: "Users", icon: Users, permission: "users:read" },
  { href: "/audit", label: "Audit", icon: ClipboardList, permission: "audit:read" },
  // ...
];

export function AppShell({
  children
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useCurrentUser();

  async function logout() {
    await api.logout();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen bg-slate-50 lg:flex">
      <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white lg:flex lg:flex-col">
        <div className="flex h-16 items-center gap-3 border-b border-slate-200 px-5">
          <div className="rounded-lg bg-slate-900 p-2 text-white">
            <Archive className="h-5 w-5" />
          </div>

          <div>
            <p className="text-sm font-semibold">
              Museum Lifecycle
            </p>

            <p className="text-[11px] text-slate-400">
              Collection workspace
            </p>
          </div>
        </div>

        <nav
          aria-label="Primary navigation"
          className="flex-1 space-y-1 overflow-y-auto p-3"
        >
          {navigation.map((item) => {
            const Icon = item.icon;

            const active =
              pathname === item.href ||
              pathname.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition",
                  active
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-slate-200 p-3">
          <Button
            variant="ghost"
            className="w-full justify-start"
            onClick={logout}
          >
            <LogOut className="mr-3 h-4 w-4" />
            Sign out
          </Button>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 px-5 py-3 backdrop-blur lg:hidden">
          <div className="flex items-center justify-between">
            <Link
              href="/dashboard"
              className="flex items-center gap-2 font-semibold"
            >
              <Archive className="h-5 w-5" />
              Museum Lifecycle
            </Link>

            <Button
              variant="ghost"
              size="sm"
              onClick={logout}
              aria-label="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>

          <nav className="mt-3 flex gap-2 overflow-x-auto pb-1">
            {navigation.slice(0, 8).map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="whitespace-nowrap rounded-lg bg-slate-100 px-3 py-2 text-xs font-medium text-slate-600"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </header>

        {children}
      </div>
    </div>
  );
}
