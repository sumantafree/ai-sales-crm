"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import {
  Zap, LayoutDashboard, Users, Megaphone, Bot,
  MessageSquare, CreditCard, LogOut, Menu, X,
} from "lucide-react";
import { clearAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import clsx from "clsx";

const NAV = [
  { label: "Dashboard",   href: "/dashboard",   icon: LayoutDashboard },
  { label: "Leads",       href: "/leads",       icon: Users },
  { label: "Campaigns",   href: "/campaigns",   icon: Megaphone },
  { label: "Automations", href: "/automations", icon: Bot },
  { label: "Chat",        href: "/chat",        icon: MessageSquare },
  { label: "Billing",     href: "/billing",     icon: CreditCard },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router   = useRouter();
  const [open, setOpen] = useState(false);

  // close drawer whenever route changes
  useEffect(() => { setOpen(false); }, [pathname]);

  const handleLogout = () => { clearAuth(); router.replace("/auth/login"); };

  return (
    <>
      {/* ── Mobile top bar ─────────────────────────────────────────── */}
      <div className="lg:hidden fixed top-0 inset-x-0 z-40 flex items-center justify-between
                      px-4 py-3 bg-slate-900 text-white shadow-lg h-14">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-indigo-500 rounded-lg flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-sm tracking-tight">AI Sales CRM</span>
        </div>
        <button onClick={() => setOpen(true)}
          className="p-2 rounded-lg hover:bg-slate-800 transition-colors">
          <Menu className="w-5 h-5" />
        </button>
      </div>

      {/* ── Mobile backdrop ─────────────────────────────────────────── */}
      {open && (
        <div className="lg:hidden fixed inset-0 bg-black/60 z-50 backdrop-blur-sm"
          onClick={() => setOpen(false)} />
      )}

      {/* ── Mobile slide drawer ─────────────────────────────────────── */}
      <div className={clsx(
        "lg:hidden fixed top-0 left-0 h-full w-64 bg-slate-900 z-50 flex flex-col shadow-2xl",
        "transition-transform duration-300 ease-in-out",
        open ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex items-center justify-between px-4 py-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="font-bold text-white text-sm">AI Sales CRM</p>
              <p className="text-xs text-slate-400">Lead Intelligence</p>
            </div>
          </div>
          <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-white p-1">
            <X className="w-5 h-5" />
          </button>
        </div>
        <NavLinks pathname={pathname} onLogout={handleLogout} />
      </div>

      {/* ── Desktop sidebar ─────────────────────────────────────────── */}
      <aside className="hidden lg:flex flex-col w-60 h-screen bg-slate-900 text-white flex-shrink-0">
        <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-800">
          <div className="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center flex-shrink-0">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="font-bold text-sm leading-none">AI Sales CRM</p>
            <p className="text-xs text-slate-400 mt-0.5">Lead Intelligence</p>
          </div>
        </div>
        <NavLinks pathname={pathname} onLogout={handleLogout} />
      </aside>

      {/* ── Mobile bottom tab bar ───────────────────────────────────── */}
      <nav className="lg:hidden fixed bottom-0 inset-x-0 z-40 bg-white border-t border-slate-200
                      flex items-center justify-around px-1 pb-safe">
        {NAV.slice(0, 5).map(({ href, icon: Icon, label }) => {
          const active = pathname.startsWith(href);
          return (
            <Link key={href} href={href}
              className={clsx(
                "flex flex-col items-center gap-0.5 px-2 py-2 rounded-xl min-w-0 flex-1",
                active ? "text-indigo-600" : "text-slate-400"
              )}>
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span className="text-[10px] font-medium truncate">{label}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}

function NavLinks({ pathname, onLogout }: { pathname: string; onLogout: () => void }) {
  return (
    <>
      <nav className="flex-1 px-2 py-4 space-y-0.5 overflow-y-auto">
        {NAV.map(({ label, href, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link key={href} href={href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                active ? "bg-indigo-600 text-white" : "text-slate-400 hover:bg-slate-800 hover:text-white"
              )}>
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="px-2 py-3 border-t border-slate-800">
        <button onClick={onLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                     text-slate-400 hover:bg-slate-800 hover:text-white transition-colors">
          <LogOut className="w-4 h-4 flex-shrink-0" />
          <span>Logout</span>
        </button>
      </div>
    </>
  );
}
