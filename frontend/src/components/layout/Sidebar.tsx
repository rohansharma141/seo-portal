"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/sites", label: "Sites" },
  // Addendum v1.1 — between Sites and API Tokens
  { href: "/compare", label: "Compare Sites" },
  { href: "/api-tokens", label: "API Tokens" },
  { href: "/settings", label: "Settings" },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col bg-sidebar text-sidebar-fg">
      <div className="px-5 py-5">
        <div className="text-sm font-semibold tracking-tight text-white">
          Prithvi
        </div>
        <div className="text-xs text-slate-400">SEO Portal</div>
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {NAV.map((item) => {
          const active = isActive(pathname, item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "block rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-sidebar-active font-medium text-white"
                  : "text-sidebar-fg hover:bg-sidebar-active/60 hover:text-white",
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="px-5 py-4 text-[11px] text-slate-500">
        v1.0.0 · Kedar Estate / PropOS
      </div>
    </aside>
  );
}
