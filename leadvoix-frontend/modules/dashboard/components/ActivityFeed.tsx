"use client";

import React, { useMemo } from "react";
import Link from "next/link";
import {
  Activity,
  UserPlus,
  DollarSign,
  CheckSquare,
  Clock,
  ArrowUpRight,
} from "lucide-react";

import { useLeads } from "@/modules/leads/hooks/useLeads";
import { useDeals } from "@/modules/deals/hooks/useDeals";
import { useTasks } from "@/modules/tasks/hooks/useTasks";
import { cn } from "@/lib/utils";

interface TimelineEvent {
  id: string;
  type: "lead" | "deal" | "task";
  title: string;
  description: string;
  timestamp: string;
  href: string;
  badge: string;
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return "-";

  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) return "Just now";
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours}h ago`;
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) return `${diffInDays}d ago`;

  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function ActivityFeed() {
  const { data: leadsData, isLoading: leadsLoading } = useLeads({
    page: 1,
    limit: 4,
    sort_by: "created_at",
    order: "desc",
  });

  const { data: dealsData, isLoading: dealsLoading } = useDeals({
    page: 1,
    limit: 4,
  });

  const { data: tasksData, isLoading: tasksLoading } = useTasks({
    page: 1,
    limit: 4,
  });

  const isLoading = leadsLoading || dealsLoading || tasksLoading;

  // Aggregate and sort real operational events
  const events = useMemo(() => {
    const list: TimelineEvent[] = [];

    // Leads events
    if (leadsData?.items) {
      leadsData.items.forEach((lead) => {
        const name = [lead.first_name, lead.last_name].filter(Boolean).join(" ") || "Prospect";
        list.push({
          id: `lead-${lead.id}`,
          type: "lead",
          title: `New Lead: ${name}`,
          description: lead.company ? `Company: ${lead.company}` : `Status: ${lead.status}`,
          timestamp: lead.created_at,
          href: `/leads/${lead.id}`,
          badge: lead.status || "Lead",
        });
      });
    }

    // Deals events
    if (dealsData?.items) {
      dealsData.items.forEach((deal) => {
        list.push({
          id: `deal-${deal.id}`,
          type: "deal",
          title: `Deal: ${deal.title}`,
          description: `Value: $${Number(deal.amount || 0).toLocaleString()} • ${deal.status}`,
          timestamp: deal.created_at,
          href: "/deals",
          badge: deal.status || "Deal",
        });
      });
    }

    // Tasks events
    if (tasksData?.items) {
      tasksData.items.forEach((task) => {
        list.push({
          id: `task-${task.id}`,
          type: "task",
          title: `Task: ${task.title}`,
          description: `Priority: ${task.priority} • Status: ${task.status}`,
          timestamp: task.created_at,
          href: "/tasks",
          badge: task.status || "Task",
        });
      });
    }

    // Chronological order descending
    return list
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 6);
  }, [leadsData, dealsData, tasksData]);

  const getEventIcon = (type: "lead" | "deal" | "task") => {
    switch (type) {
      case "lead":
        return {
          icon: UserPlus,
          bg: "bg-[#7657F6]/15 text-[#7657F6] border-[#7657F6]/30",
        };
      case "deal":
        return {
          icon: DollarSign,
          bg: "bg-[#35D6C1]/15 text-[#35D6C1] border-[#35D6C1]/30",
        };
      case "task":
        return {
          icon: CheckSquare,
          bg: "bg-amber-500/15 text-amber-400 border-amber-500/30",
        };
    }
  };

  return (
    <div className="flex h-full flex-col rounded-2xl border border-slate-800/80 bg-[#151D32] shadow-xl shadow-black/40 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 px-6 py-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#24C8D8]/15 text-[#24C8D8] border border-[#24C8D8]/30">
            <Activity className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-[#F5F7FC]">Recent Activity</h2>
            <p className="text-xs text-[#AAB4CC]/70">Real-time CRM events</p>
          </div>
        </div>
        <span className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-400">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          Live
        </span>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="p-6 space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex gap-3 animate-pulse">
              <div className="h-8 w-8 rounded-lg bg-slate-800 shrink-0" />
              <div className="flex-1 space-y-1.5">
                <div className="h-3.5 w-3/4 rounded bg-slate-800" />
                <div className="h-2.5 w-1/2 rounded bg-slate-800" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && events.length === 0 && (
        <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-800/60 text-[#AAB4CC] border border-slate-700/60 mb-3">
            <Clock className="h-6 w-6" />
          </div>
          <p className="text-sm font-bold text-[#F5F7FC]">No activity logged yet</p>
          <p className="mt-1 text-xs text-[#AAB4CC] max-w-xs">
            As you manage leads, close deals, or assign tasks, operational milestones will stream here automatically.
          </p>
          <div className="mt-4 flex gap-2">
            <Link
              href="/leads"
              className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-semibold text-[#F5F7FC] hover:bg-slate-700 transition-colors"
            >
              Add Lead
            </Link>
            <Link
              href="/tasks"
              className="rounded-lg bg-[#7657F6] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#6846ed] transition-colors"
            >
              Add Task
            </Link>
          </div>
        </div>
      )}

      {/* Timeline List */}
      {!isLoading && events.length > 0 && (
        <div className="flex-1 p-5 overflow-y-auto max-h-[380px]">
          <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-px before:bg-slate-800">
            {events.map((event) => {
              const { icon: EventIcon, bg } = getEventIcon(event.type);

              return (
                <div key={event.id} className="relative group">
                  {/* Timeline Dot / Icon */}
                  <div
                    className={cn(
                      "absolute -left-6 top-0.5 flex h-6 w-6 items-center justify-center rounded-lg border text-xs shadow transition-transform group-hover:scale-110",
                      bg
                    )}
                  >
                    <EventIcon className="h-3 w-3" />
                  </div>

                  {/* Content */}
                  <div className="rounded-xl border border-slate-800/60 bg-slate-900/40 p-3 transition-colors group-hover:border-slate-700/80 group-hover:bg-slate-900/70">
                    <div className="flex items-start justify-between gap-2">
                      <Link
                        href={event.href}
                        className="font-semibold text-xs text-[#F5F7FC] hover:text-[#24C8D8] transition-colors line-clamp-1"
                      >
                        {event.title}
                      </Link>
                      <span className="shrink-0 text-[10px] text-[#AAB4CC]/70">
                        {formatRelativeTime(event.timestamp)}
                      </span>
                    </div>

                    <p className="mt-1 text-[11px] text-[#AAB4CC] line-clamp-1">
                      {event.description}
                    </p>

                    <div className="mt-2 flex items-center justify-between pt-1 border-t border-slate-800/40">
                      <span className="text-[10px] font-medium text-[#AAB4CC]/60 uppercase tracking-wider">
                        {event.badge}
                      </span>
                      <Link
                        href={event.href}
                        className="inline-flex items-center gap-1 text-[10px] font-medium text-[#24C8D8] hover:underline"
                      >
                        <span>View</span>
                        <ArrowUpRight className="h-2.5 w-2.5" />
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
