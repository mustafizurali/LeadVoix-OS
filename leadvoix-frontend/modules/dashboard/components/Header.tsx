"use client";

import React, { useState, useRef, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import {
  Menu,
  Search,
  Bell,
  LogOut,
  Settings,
  ChevronDown,
  Sparkles,
  CheckCircle2,
  PhoneCall,
} from "lucide-react";

import { useAuthStore } from "@/modules/auth/store/authStore";
import { useSidebar } from "../context/SidebarContext";
import { useBackendHealth } from "@/lib/hooks/useBackendHealth";

export default function Header() {
  const router = useRouter();
  const pathname = usePathname();
  const { toggleMobile } = useSidebar();

  const rawUser = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const user = mounted ? rawUser : null;

  const { data: isBackendOnline, isLoading: isHealthLoading } = useBackendHealth();

  const [searchQuery, setSearchQuery] = useState("");
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const userMenuRef = useRef<HTMLDivElement>(null);
  const notificationsRef = useRef<HTMLDivElement>(null);

  // Close menus when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        userMenuRef.current &&
        !userMenuRef.current.contains(event.target as Node)
      ) {
        setUserMenuOpen(false);
      }
      if (
        notificationsRef.current &&
        !notificationsRef.current.contains(event.target as Node)
      ) {
        setNotificationsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  // Derive breadcrumbs based on pathname
  const getBreadcrumbTitle = () => {
    if (!pathname || pathname === "/dashboard") return { section: "Platform", current: "Dashboard" };
    if (pathname.startsWith("/leads")) return { section: "CRM", current: "Leads" };
    if (pathname.startsWith("/contacts")) return { section: "CRM", current: "Contacts" };
    if (pathname.startsWith("/companies")) return { section: "CRM", current: "Companies" };
    if (pathname.startsWith("/pipelines")) return { section: "CRM", current: "Pipelines" };
    if (pathname.startsWith("/deals")) return { section: "CRM", current: "Deals" };
    if (pathname.startsWith("/tasks")) return { section: "CRM", current: "Tasks" };
    if (pathname.startsWith("/agents")) return { section: "AI Voice", current: "Agents" };
    if (pathname.startsWith("/agent-calls")) return { section: "AI Voice", current: "Call Logs" };
    if (pathname.startsWith("/demo-requests")) return { section: "Admin", current: "Demo Requests" };
    if (pathname.startsWith("/settings")) return { section: "System", current: "Settings" };
    return { section: "LeadVoix OS", current: "Overview" };
  };

  const breadcrumbs = getBreadcrumbTitle();

  return (
    <header className="sticky top-0 z-20 flex h-16 shrink-0 items-center justify-between border-b border-slate-800/80 bg-[#151D32]/95 px-4 sm:px-6 backdrop-blur-md">
      {/* Left: Mobile Menu Toggle & Breadcrumbs */}
      <div className="flex items-center gap-3 sm:gap-4">
        <button
          type="button"
          onClick={toggleMobile}
          className="rounded-lg p-2 text-[#AAB4CC] transition-colors hover:bg-slate-800 hover:text-white lg:hidden"
          aria-label="Open mobile navigation"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Breadcrumb Title */}
        <div className="flex items-center gap-2 text-xs sm:text-sm">
          <span className="hidden font-medium text-[#AAB4CC]/70 sm:inline">
            {breadcrumbs.section}
          </span>
          <span className="hidden text-slate-600 sm:inline">/</span>
          <h1 className="font-semibold tracking-tight text-[#F5F7FC]">
            {breadcrumbs.current}
          </h1>
        </div>
      </div>

      {/* Center: Search Interface */}
      <div className="hidden md:flex items-center flex-1 max-w-md mx-6">
        <div className="relative w-full">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6F7D9E]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search leads, deals, contacts... (Ctrl+K)"
            className="h-9 w-full rounded-lg border border-slate-700/80 bg-[#0E1528] pl-9 pr-12 text-xs text-[#F5F7FC] placeholder:text-[#6F7D9E] transition-colors outline-none focus:border-[#7657F6] focus:ring-1 focus:ring-[#7657F6]"
          />
          <kbd className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[10px] font-medium text-[#AAB4CC]">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right: Status Pill, Notifications & User Menu */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Real Live AI Engine Health Status Pill */}
        <div className="hidden xl:flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium border-[#273449]">
          {isHealthLoading ? (
            <span className="flex items-center gap-1.5 text-[#94A3B8]">
              <span className="h-2 w-2 rounded-full bg-slate-600 animate-pulse" />
              Connecting...
            </span>
          ) : isBackendOnline ? (
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
              </span>
              AI Engine Active
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-red-400">
              <span className="h-2 w-2 rounded-full bg-red-400" />
              AI Engine Offline
            </span>
          )}
        </div>

        {/* Notifications Popover */}
        <div className="relative" ref={notificationsRef}>
          <button
            type="button"
            onClick={() => setNotificationsOpen((prev) => !prev)}
            className="relative rounded-lg p-2 text-[#AAB4CC] transition-colors hover:bg-slate-800/60 hover:text-white"
            aria-label="View notifications"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[#24C8D8] shadow-sm shadow-[#24C8D8]" />
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-80 rounded-xl border border-slate-800/90 bg-[#151D32] p-3 shadow-2xl shadow-black/80 z-30 animate-in fade-in-50 zoom-in-95 duration-150">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2 px-1">
                <span className="text-xs font-semibold text-[#F5F7FC]">System Notifications</span>
                <span className="text-[10px] text-[#24C8D8] font-medium">Real-time</span>
              </div>
              <div className="space-y-2 pt-2 text-xs">
                <div className="flex items-start gap-2.5 rounded-lg p-2 bg-slate-900/60 hover:bg-slate-900 transition-colors">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-[#35D6C1] mt-0.5" />
                  <div>
                    <p className="font-medium text-[#F5F7FC]">Voice Pipeline Ready</p>
                    <p className="text-[10px] text-[#AAB4CC]">Telephony and CRM webhooks synchronized.</p>
                  </div>
                </div>
                <div className="flex items-start gap-2.5 rounded-lg p-2 bg-slate-900/60 hover:bg-slate-900 transition-colors">
                  <PhoneCall className="h-4 w-4 shrink-0 text-[#7657F6] mt-0.5" />
                  <div>
                    <p className="font-medium text-[#F5F7FC]">Autonomous Agents</p>
                    <p className="text-[10px] text-[#AAB4CC]">AI call processing worker active.</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Dropdown */}
        <div className="relative" ref={userMenuRef}>
          <button
            type="button"
            onClick={() => setUserMenuOpen((prev) => !prev)}
            className="flex items-center gap-2.5 rounded-xl border border-slate-800/80 bg-[#0E1528] px-2.5 py-1.5 transition-all hover:border-slate-700 hover:bg-slate-900"
            aria-expanded={userMenuOpen}
            aria-label="User account menu"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-tr from-[#7657F6] to-[#24C8D8] text-xs font-bold text-white shadow-sm">
              {user?.name ? user.name.slice(0, 2).toUpperCase() : "LV"}
            </div>
            <div className="hidden sm:flex flex-col text-left">
              <span className="max-w-[120px] truncate text-xs font-semibold text-[#F5F7FC]">
                {user?.name || "Account"}
              </span>
              <span className="text-[10px] text-[#AAB4CC]/70 capitalize">
                {user?.role || "Member"}
              </span>
            </div>
            <ChevronDown className="h-3.5 w-3.5 text-[#AAB4CC]" />
          </button>

          {userMenuOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl border border-slate-800/90 bg-[#151D32] p-2 shadow-2xl shadow-black/80 z-30 animate-in fade-in-50 zoom-in-95 duration-150">
              <div className="border-b border-slate-800/80 px-3 py-2">
                <p className="text-xs font-semibold text-[#F5F7FC] truncate">
                  {user?.name || "LeadVoix User"}
                </p>
                <p className="text-[11px] text-[#AAB4CC] truncate">
                  {user?.email || "user@leadvoix.com"}
                </p>
                <div className="mt-1 flex items-center gap-1.5">
                  <span className="rounded bg-[#7657F6]/20 px-1.5 py-0.5 text-[9px] font-semibold text-[#7657F6] uppercase">
                    {user?.role || "USER"}
                  </span>
                  {user?.organization_id && (
                    <span className="text-[10px] text-[#AAB4CC]/60">
                      Org #{user.organization_id}
                    </span>
                  )}
                </div>
              </div>

              <div className="py-1">
                <Link
                  href="/settings"
                  onClick={() => setUserMenuOpen(false)}
                  className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-medium text-[#AAB4CC] transition-colors hover:bg-slate-800/60 hover:text-[#F5F7FC]"
                >
                  <Settings className="h-3.5 w-3.5" />
                  Account Settings
                </Link>
                <Link
                  href="/agents"
                  onClick={() => setUserMenuOpen(false)}
                  className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-medium text-[#AAB4CC] transition-colors hover:bg-slate-800/60 hover:text-[#F5F7FC]"
                >
                  <Sparkles className="h-3.5 w-3.5 text-[#24C8D8]" />
                  AI Voice Agents
                </Link>
              </div>

              <div className="border-t border-slate-800/80 pt-1">
                <button
                  type="button"
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-medium text-red-400 transition-colors hover:bg-red-500/10 hover:text-red-300"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
