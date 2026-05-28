"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Zap, LayoutDashboard, ClipboardList, BrainCircuit, Settings, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/track", label: "Applications", icon: ClipboardList },
  { href: "/track?prep=1", label: "Interview Prep", icon: BrainCircuit, matchHref: "/interview" },
  { href: "/analyze", label: "Match CV", icon: Sparkles },
];

export default function AppNav() {
  const pathname = usePathname();
  const [initials, setInitials] = useState("T");

  useEffect(() => {
    const uid = localStorage.getItem("tapapply_user_id");
    if (uid) setInitials(uid.slice(0, 2).toUpperCase());
  }, []);

  function isActive(link: (typeof NAV_LINKS)[number]) {
    if (link.matchHref) return pathname.startsWith(link.matchHref);
    const base = link.href.split("?")[0];
    return pathname === base || (base !== "/dashboard" && pathname.startsWith(base));
  }

  return (
    <nav className="sticky top-0 z-40 w-full bg-zinc-950/80 backdrop-blur-xl border-b border-zinc-800/60">
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between gap-4">

        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-2.5 group shrink-0">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center transition-shadow group-hover:shadow-[0_0_16px_rgba(99,102,241,0.5)]">
            <Zap size={14} className="text-white" fill="white" />
          </div>
          <span className="text-sm font-bold text-zinc-50 tracking-tight">TapApply</span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-0.5">
          {NAV_LINKS.map((link) => {
            const active = isActive(link);
            const Icon = link.icon;
            return (
              <Link
                key={link.label}
                href={link.href}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                  active
                    ? "bg-zinc-800/80 text-zinc-100"
                    : "text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800/50"
                )}
              >
                <Icon size={13} className={active ? "text-indigo-400" : ""} />
                <span>{link.label}</span>
                {active && (
                  <span className="w-1 h-1 rounded-full bg-indigo-400 ml-0.5" />
                )}
              </Link>
            );
          })}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2 shrink-0">
          <Link
            href="/onboarding"
            className="p-1.5 rounded-lg text-zinc-600 hover:text-zinc-300 hover:bg-zinc-800/60 transition-colors"
            title="Edit profile / Back to setup"
          >
            <Settings size={14} />
          </Link>
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-600 to-violet-700 flex items-center justify-center text-[10px] font-bold text-white shadow-sm select-none">
            {initials}
          </div>
        </div>
      </div>
    </nav>
  );
}
