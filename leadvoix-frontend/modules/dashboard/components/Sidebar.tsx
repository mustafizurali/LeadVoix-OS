"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { VoiceWaveMark } from "@/components/brand/LeadVoixLogo";
import {
  LayoutDashboard,
  UserPlus,
  Users,
  Building2,
  Workflow,
  DollarSign,
  CheckSquare,
  Bot,
  PhoneCall,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  X,
  Sparkles,
} from "lucide-react";

import { useAuthStore } from "@/modules/auth/store/authStore";
import { useSidebar } from "../context/SidebarContext";
import { cn } from "@/lib/utils";

interface NavGroup {
  label: string;
  items: {
    title: string;
    href: string;
    icon: React.ComponentType<{ className?: string }>;
    adminOnly?: boolean;
    badge?: string;
  }[];
}

const navigationGroups: NavGroup[] = [
  {
    label: "Overview",
    items: [
      {
        title: "Dashboard",
        href: "/dashboard",
        icon: LayoutDashboard,
      },
    ],
  },
  {
    label: "CRM Core",
    items: [
      {
        title: "Leads",
        href: "/leads",
        icon: UserPlus,
      },
      {
        title: "Contacts",
        href: "/contacts",
        icon: Users,
      },
      {
        title: "Companies",
        href: "/companies",
        icon: Building2,
      },
      {
        title: "Pipelines",
        href: "/pipelines",
        icon: Workflow,
      },
      {
        title: "Deals",
        href: "/deals",
        icon: DollarSign,
      },
      {
        title: "Tasks",
        href: "/tasks",
        icon: CheckSquare,
      },
    ],
  },
  {
    label: "AI Voice Intelligence",
    items: [
      {
        title: "Agents",
        href: "/agents",
        icon: Bot,
        badge: "AI",
      },
      {
        title: "Agent Calls",
        href: "/agent-calls",
        icon: PhoneCall,
      },
    ],
  },
  {
    label: "System",
    items: [
      {
        title: "Demo Requests",
        href: "/demo-requests",
        icon: FileText,
        adminOnly: true,
      },
      {
        title: "Settings",
        href: "/settings",
        icon: Settings,
      },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const rawUser = useAuthStore((state) => state.user);
  const { isCollapsed, toggleCollapsed, mobileOpen, setMobileOpen } = useSidebar();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const user = mounted ? rawUser : null;

  const renderNavContent = (isMobile = false) => {
    const collapsed = isMobile ? false : isCollapsed;

    return (
      <div className="flex h-full flex-col justify-between overflow-hidden">
        {/* Brand Header */}
        <div>
          <div
            className={cn(
              "flex h-16 items-center border-b border-slate-800/80 px-4 transition-all",
              collapsed ? "justify-center" : "justify-between"
            )}
          >
            <Link
              href="/dashboard"
              className="flex items-center gap-3 transition-opacity hover:opacity-90"
              onClick={() => isMobile && setMobileOpen(false)}
            >
              <VoiceWaveMark size="md" glow={true} />
              {!collapsed && (
                <div className="flex flex-col leading-tight">
                  <span className="text-base font-bold tracking-tight text-[#F5F7FC]">
                    LeadVoix<span className="text-[#24C8D8]"> OS</span>
                  </span>
                  <span className="text-[10px] font-medium tracking-wider text-[#AAB4CC]/70 uppercase">
                    Enterprise SaaS CRM
                  </span>
                </div>
              )}
            </Link>

            {isMobile && (
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                className="rounded-lg p-1.5 text-[#AAB4CC] transition-colors hover:bg-slate-800 hover:text-white"
                aria-label="Close navigation"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>

          {/* Navigation Groups */}
          <nav className="space-y-6 overflow-y-auto px-3 py-4 max-h-[calc(100vh-140px)]">
            {navigationGroups.map((group) => {
              const visibleItems = group.items.filter(
                (item) => !item.adminOnly || user?.role === "admin"
              );

              if (visibleItems.length === 0) return null;

              return (
                <div key={group.label} className="space-y-1">
                  {!collapsed && (
                    <p className="px-3 pb-1 text-[10px] font-semibold tracking-wider text-[#AAB4CC]/60 uppercase">
                      {group.label}
                    </p>
                  )}
                  <ul className="space-y-0.5">
                    {visibleItems.map((item) => {
                      const Icon = item.icon;
                      const active =
                        pathname === item.href ||
                        (item.href !== "/dashboard" &&
                          pathname?.startsWith(item.href));

                      return (
                        <li key={item.href}>
                          <Link
                            href={item.href}
                            onClick={() => isMobile && setMobileOpen(false)}
                            title={collapsed ? item.title : undefined}
                            className={cn(
                              "group flex items-center rounded-lg text-sm font-medium transition-all",
                              collapsed
                                ? "h-10 w-10 justify-center mx-auto"
                                : "gap-3 px-3 py-2",
                              active
                                ? "bg-[#7657F6]/15 text-[#F5F7FC] shadow-sm shadow-violet-950/30 font-semibold"
                                : "text-[#AAB4CC] hover:bg-slate-800/60 hover:text-[#F5F7FC]"
                            )}
                          >
                            <Icon
                              className={cn(
                                "h-4 w-4 shrink-0 transition-colors",
                                active
                                  ? "text-[#7657F6]"
                                  : "text-[#AAB4CC] group-hover:text-[#F5F7FC]"
                              )}
                            />

                            {!collapsed && (
                              <span className="flex-1 truncate">{item.title}</span>
                            )}

                            {!collapsed && item.badge && (
                              <span className="flex items-center gap-1 rounded-full bg-[#24C8D8]/15 px-2 py-0.5 text-[10px] font-bold tracking-wider text-[#24C8D8] border border-[#24C8D8]/30 uppercase">
                                <Sparkles className="h-2.5 w-2.5" />
                                {item.badge}
                              </span>
                            )}

                            {active && !collapsed && (
                              <span className="h-1.5 w-1.5 rounded-full bg-[#7657F6] shadow-sm shadow-[#7657F6]" />
                            )}
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              );
            })}
          </nav>
        </div>

        {/* Bottom User / Collapse Section */}
        <div className="border-t border-slate-800/80 p-3">
          {!isMobile && (
            <button
              type="button"
              onClick={toggleCollapsed}
              className={cn(
                "flex w-full items-center rounded-lg py-2 text-xs font-medium text-[#AAB4CC] transition-colors hover:bg-slate-800/60 hover:text-white",
                collapsed ? "justify-center px-0" : "justify-between px-3"
              )}
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {!collapsed && <span>Collapse Sidebar</span>}
              {collapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </button>
          )}

          {!collapsed && (
            <div className="mt-2 flex items-center gap-3 rounded-xl bg-slate-900/60 p-2.5 border border-slate-800/50">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-tr from-[#7657F6] to-[#24C8D8] text-xs font-bold text-white shadow">
                {user?.name ? user.name.slice(0, 2).toUpperCase() : "LV"}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-semibold text-[#F5F7FC]">
                  {user?.name || "LeadVoix User"}
                </p>
                <p className="truncate text-[10px] text-[#AAB4CC]/70">
                  {user?.organization_name || "Enterprise Workspace"}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside
        className={cn(
          "hidden lg:flex shrink-0 flex-col bg-[#151D32] border-r border-slate-800/80 transition-all duration-300 ease-in-out z-20",
          isCollapsed ? "w-18" : "w-64"
        )}
      >
        {renderNavContent(false)}
      </aside>

      {/* Mobile Drawer (Slide-Over with Backdrop) */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />

          {/* Drawer Surface */}
          <aside className="relative flex w-72 max-w-[85vw] flex-col bg-[#151D32] shadow-2xl border-r border-slate-800/80 z-10 animate-in slide-in-from-left duration-200">
            {renderNavContent(true)}
          </aside>
        </div>
      )}
    </>
  );
}
