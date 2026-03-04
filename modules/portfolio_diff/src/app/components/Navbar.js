"use client";

import { useEffect, useRef, useState } from "react";
import {
  Search,
  Bell,
  User,
  ChevronDown,
  Menu,
  X,
  BookOpen,
  LogOut,
  Link,
  Home
} from "lucide-react";
import { navigateTo } from "../utils/navigation";

export default function Navbar() {
  const [open, setOpen] = useState(false);          // mobile sheet
  const [menuOpen, setMenuOpen] = useState(false);  // desktop profile menu
  const [courseDashboards, setCourseDashboards] = useState([]);
  const menuRef = useRef(null);

  const dashboardLinks = [
    { name: "Home", url: "/", preserveHash: false },
    ...courseDashboards.map((dashboard) => ({
      ...dashboard,
      preserveHash: true,
    })),
  ];

  const getDashboardHref = (dashboard) => {
    if (typeof window === "undefined") return dashboard.url;

    if (!dashboard.preserveHash) return dashboard.url;
    return `${dashboard.url}${window.location.hash || ""}`;
  };

  useEffect(() => {
    const loadCourseDashboards = async () => {
      try {
        const response = await fetch("/webapi/course_dashboards");
        if (!response.ok) return;
        const dashboards = await response.json();
        if (!Array.isArray(dashboards)) return;

        setCourseDashboards(
          dashboards.filter((dashboard) => dashboard?.name && dashboard?.url)
        );
      } catch {
        setCourseDashboards([]);
      }
    };

    loadCourseDashboards();
  }, []);

  // Close profile menu on outside click
  useEffect(() => {
    const onClick = (e) => {
      if (!menuRef.current) return;
      if (!menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    const onKey = (e) => {
      if (e.key === "Escape") setMenuOpen(false);
    };
    window.addEventListener("mousedown", onClick);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("mousedown", onClick);
      window.removeEventListener("keydown", onKey);
    };
  }, []);

  return (
    <header className="sticky top-0 z-40 border-b border-white/5 bg-emerald-700/90 backdrop-blur">
      <nav className="mx-auto flex max-w-8xl items-center justify-between px-4 py-3 md:px-6">
        {/* Left: Brand */}
        <span onClick={() => navigateTo("")} className="text-lg font-semibold text-white hover:text-green-200 cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="relative h-10 w-10 overflow-hidden rounded-lg">
              <BookOpen className="w-10 h-10 text-white" />
            </div>
            <div>Writing Portfolio</div>
          </div>
        </span>

        {/* Right: actions */}
        <div className="flex items-center gap-2">
          {/* TODO implement notifications */}
          {false && (
            <button
              aria-label="Notifications"
              className="relative rounded-full p-2 text-zinc-200 hover:bg-white/10 hover:text-white"
            >
              <Bell className="h-5 w-5" />
              <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-emerald-500" />
            </button>
          )}

          {/* Profile (desktop) */}
          <div className="relative hidden md:block" ref={menuRef}>
            <button
              onClick={() => setMenuOpen((v) => !v)}
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              className="group inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2 py-1 text-sm text-zinc-200 hover:bg-white/10"
            >
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-600/20 ring-1 ring-emerald-500/40">
                <Link className="h-4 w-4 text-emerald-300" />
              </div>
              <span className="pr-1 text-white">Dashboards</span>
              <ChevronDown
                className={`h-4 w-4 text-zinc-400 group-hover:text-zinc-300 transition-transform ${
                  menuOpen ? "rotate-180" : ""
                }`}
              />
            </button>

            {/* Dropdown menu */}
            {menuOpen && (
              <div
                role="menu"
                aria-label="Profile"
                className="absolute right-0 mt-2 w-48 overflow-hidden rounded-lg border border-white/10 bg-emerald-900/95 backdrop-blur shadow-lg"
              >
                {dashboardLinks.map((dashboard, idx) => (
                  <a
                    key={`${dashboard.url}-${dashboard.name}`}
                    role="menuitem"
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-zinc-100 hover:bg-white/10"
                    href={getDashboardHref(dashboard)}
                    onClick={() => setMenuOpen(false)}
                  >
                    {idx === 0 ? (
                      <Home className="h-4 w-4 opacity-90" />
                    ) : (
                      <User className="h-4 w-4 opacity-90" />
                    )}
                    {dashboard.name}
                  </a>
                ))}
                <button
                  role="menuitem"
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-100 hover:bg-white/10"
                  onClick={() => {
                    setMenuOpen(false);
                    window.location.assign("/auth/logout");
                  }}
                >
                  <LogOut className="h-4 w-4 opacity-90" />
                  Logout
                </button>
              </div>
            )}
          </div>

          {/* Mobile toggle */}
          <button
            className="rounded-md p-2 text-zinc-200 hover:bg-white/10 md:hidden"
            onClick={() => setOpen((v) => !v)}
            aria-label="Open menu"
            aria-expanded={open}
          >
            {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </nav>

      {/* Mobile sheet */}
      <div
        className={`md:hidden ${
          open ? "block" : "hidden"
        } border-t border-white/5 bg-emerald-950`}
      >
        <div className="space-y-1 px-4 py-3">
          <div className="mb-2 flex items-center gap-2 rounded-md border border-white/10 bg-white/5 px-3 py-2">
            <Search className="h-4 w-4 text-zinc-400" />
            <input
              className="w-full bg-transparent text-sm text-zinc-100 placeholder-zinc-500 outline-none"
              placeholder="Search"
            />
          </div>

          {/* Mobile profile actions */}
          <div className="mt-2 rounded-md border border-white/10 bg-white/5">
            <div className="flex items-center justify-between px-3 py-2">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-600/20 ring-1 ring-emerald-500/40">
                  <Link className="h-4 w-4 text-emerald-300" />
                </div>
                <div>
                  <p className="text-sm text-white">Dashboards</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 divide-y divide-white/10">
              {dashboardLinks.map((dashboard) => (
                <a
                  key={`${dashboard.url}-mobile-${dashboard.name}`}
                  href={getDashboardHref(dashboard.url)}
                  className="px-3 py-2 text-sm text-zinc-100 hover:bg-white/10"
                  onClick={() => setOpen(false)}
                >
                  {dashboard.name}
                </a>
              ))}
              <button
                className="px-3 py-2 text-left text-sm text-red-100 hover:bg-white/10"
                onClick={() => {
                  setOpen(false);
                  window.location.assign("/auth/logout");
                }}
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
