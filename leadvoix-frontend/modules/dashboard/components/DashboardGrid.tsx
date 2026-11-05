"use client";

import React from "react";
import { UserPlus, Building2, DollarSign, CheckSquare, AlertCircle } from "lucide-react";
import StatCard from "./StatCard";
import { useDashboard } from "../hooks/useDashboard";

export default function DashboardGrid() {
  const { data, isLoading, isError, refetch } = useDashboard();

  if (isLoading) {
    return (
      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-36 animate-pulse rounded-2xl border border-slate-800/80 bg-[#151D32] p-5"
          >
            <div className="flex justify-between">
              <div className="h-4 w-24 rounded bg-slate-800" />
              <div className="h-9 w-9 rounded-xl bg-slate-800" />
            </div>
            <div className="mt-4 h-8 w-16 rounded bg-slate-800" />
            <div className="mt-5 h-3 w-32 rounded bg-slate-800" />
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-between rounded-2xl border border-red-500/30 bg-red-500/10 p-5 text-red-200">
        <div className="flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-400" />
          <span className="text-sm font-medium">
            Failed to load dashboard metrics. Check your database connection.
          </span>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          className="rounded-lg bg-red-500/20 px-3 py-1.5 text-xs font-semibold text-red-300 transition-colors hover:bg-red-500/30"
        >
          Retry
        </button>
      </div>
    );
  }

  const openDealsCount = data?.open_deals ?? 0;
  const wonDealsCount = data?.won_deals ?? 0;
  const completedTasksCount = data?.completed_tasks ?? 0;
  const overdueTasksCount = data?.overdue_tasks ?? 0;

  return (
    <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard
        title="Total Leads"
        value={data?.total_leads ?? 0}
        subtitle="Prospects & active pipeline"
        icon={UserPlus}
        accentColor="violet"
        indicatorText="CRM"
      />

      <StatCard
        title="Companies"
        value={data?.total_companies ?? 0}
        subtitle="Target accounts & clients"
        icon={Building2}
        accentColor="cyan"
        indicatorText="Accounts"
      />

      <StatCard
        title="Deals"
        value={data?.total_deals ?? 0}
        subtitle={`${openDealsCount} open • ${wonDealsCount} won`}
        icon={DollarSign}
        accentColor="emerald"
        indicatorText="Pipeline"
      />

      <StatCard
        title="Tasks"
        value={data?.total_tasks ?? 0}
        subtitle={`${completedTasksCount} done • ${overdueTasksCount} overdue`}
        icon={CheckSquare}
        accentColor="amber"
        indicatorText="Execution"
      />
    </div>
  );
}
