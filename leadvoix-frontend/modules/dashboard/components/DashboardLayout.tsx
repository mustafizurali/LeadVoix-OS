"use client";

import React, { useEffect } from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";
import { SidebarProvider } from "../context/SidebarContext";
import { useAuthStore } from "@/modules/auth/store/authStore";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

function DashboardInnerLayout({ children }: DashboardLayoutProps) {
  const hydrate = useAuthStore((state) => state.hydrate);
  const isHydrated = useAuthStore((state) => state.isHydrated);

  useEffect(() => {
    if (!isHydrated) {
      hydrate();
    }
  }, [hydrate, isHydrated]);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#0B1020] text-[#F5F7FC] font-sans antialiased selection:bg-[#7657F6]/30 selection:text-white">
      {/* Sidebar (Desktop + Mobile Drawer) */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        <Header />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <SidebarProvider>
      <DashboardInnerLayout>
        {children}
      </DashboardInnerLayout>
    </SidebarProvider>
  );
}
