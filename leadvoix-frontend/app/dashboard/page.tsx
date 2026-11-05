"use client";

import React from "react";
import Link from "next/link";
import { UserPlus, DollarSign, Bot } from "lucide-react";

import DashboardLayout from "@/modules/dashboard/components/DashboardLayout";
import DashboardGrid from "@/modules/dashboard/components/DashboardGrid";
import RecentLeads from "@/modules/dashboard/components/RecentLeads";
import ActivityFeed from "@/modules/dashboard/components/ActivityFeed";
import AgentAnalytics from "@/modules/dashboard/components/AgentAnalytics";
import { useBackendHealth } from "@/lib/hooks/useBackendHealth";

export default function DashboardPage() {
  const { data: isBackendOnline, isLoading: isHealthLoading } = useBackendHealth();
  return (
    <DashboardLayout>
      <div className="space-y-8 pb-10">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F5F7FC]">
                Dashboard Overview
              </h1>
              {isHealthLoading ? (
                <span className="text-[11px] font-semibold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-slate-800 text-[#94A3B8] border border-slate-700 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-pulse" />
                  Connecting...
                </span>
              ) : isBackendOnline ? (
                <span className="text-[11px] font-semibold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                  AI Engine Active
                </span>
              ) : (
                <span className="text-[11px] font-semibold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/30 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                  AI Engine Offline
                </span>
              )}
            </div>
            <p className="mt-1 text-xs text-[#AAB4CC]">
              Real-time visibility across CRM pipelines, contact records, and autonomous voice agents.
            </p>
          </div>

          {/* Quick Action Buttons */}
          <div className="flex items-center gap-2.5">
            <Link
              href="/leads"
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700/80 bg-[#151D32] px-3.5 py-2 text-xs font-semibold text-[#F5F7FC] shadow-sm transition-colors hover:border-slate-600 hover:bg-slate-800"
            >
              <UserPlus className="h-3.5 w-3.5 text-[#24C8D8]" />
              <span>+ New Lead</span>
            </Link>

            <Link
              href="/deals"
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700/80 bg-[#151D32] px-3.5 py-2 text-xs font-semibold text-[#F5F7FC] shadow-sm transition-colors hover:border-slate-600 hover:bg-slate-800"
            >
              <DollarSign className="h-3.5 w-3.5 text-[#35D6C1]" />
              <span>+ New Deal</span>
            </Link>

            <Link
              href="/agents"
              className="inline-flex items-center gap-1.5 rounded-lg bg-[#7657F6] px-3.5 py-2 text-xs font-semibold text-white shadow-md shadow-violet-950/40 transition-all hover:bg-[#6846ed]"
            >
              <Bot className="h-3.5 w-3.5" />
              <span>Deploy Agent</span>
            </Link>
          </div>
        </div>

        {/* 1. KPI Metric Cards */}
        <section aria-label="Key Performance Indicators">
          <DashboardGrid />
        </section>

        {/* 2. AI Voice Agent Intelligence & Analytics */}
        <section aria-label="AI Voice Agent Intelligence">
          <AgentAnalytics />
        </section>

        {/* 3. Recent Leads & Real-time Activity Timeline */}
        <section aria-label="Recent CRM Activity" className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <RecentLeads />
          </div>
          <div className="lg:col-span-1">
            <ActivityFeed />
          </div>
        </section>
      </div>
    </DashboardLayout>
  );
}
